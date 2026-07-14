#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor web fino para "As Catacumbas Esquecidas".
============================================================================
Reaproveita a engine (rpg_loop.py) INTEIRA — a engine continua a única dona do
estado; o servidor só traduz HTTP <-> chamadas de engine e serve o frontend.

Multi-jogador:
  - Conta (usuário/senha) + chave de convite no cadastro (REGISTER_KEY / invite_key.txt).
  - Cada sessão HTTP tem seu próprio estado de jogo (cookie `session`).
  - Saves em saves/<usuario>/slot_N.json.

Uso:
    set REGISTER_KEY=sua-chave-secreta
    set DEEPSEEK_API_KEY=...   # opcional
    set LLM_BASE_URL=...       # opcional: LLM local OpenAI-compatível (Ollama /v1)
    set LLM_MODEL=...          # opcional: modelo do endpoint acima
    python server.py           # http://0.0.0.0:8000
"""

import io
import os
import sys
import json
import urllib.parse
import time
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import rpg_loop as eng
import game_log
import auth

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
# Online = há um LLM para narrar: chave da DeepSeek OU endpoint local/custom
# (LLM_BASE_URL, ex.: Ollama em http://localhost:11434/v1 — ver rpg_loop.py).
ONLINE = bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("LLM_BASE_URL"))
AQUI = os.path.dirname(os.path.abspath(__file__))
log = game_log.get_logger("game")
llm_log = game_log.get_logger("llm")   # turnos do LLM (debug de jogadas online)


def _log_llm_turno(evento, **campos):
    """Hook de observabilidade do engine -> logs/llm.log. Marca cada turno online
    com o usuário atual para dar para rastrear a jogada depois."""
    user = None
    try:
        user = GAME.get("user")
    except Exception:
        pass
    partes = [evento, f"user={user}"]
    for k, v in campos.items():
        if v is None:
            continue
        s = str(v).replace("\n", " ⏎ ")
        if len(s) > 300:
            s = s[:300] + "…"
        partes.append(f"{k}={s}")
    nivel = "warning" if evento in ("turno_invalido", "turno_fallback") else "info"
    getattr(llm_log, nivel)(" | ".join(partes))


eng.LOG_LLM = _log_llm_turno

PASSOS_POR_AUTOSAVE = 12
N_SLOTS = 3
# Em produção (Railway): volume em /data e SAVE_ROOT=/data/saves (junto com DATA_DIR=/data)
SAVE_ROOT = os.environ.get("SAVE_ROOT") or os.path.join(AQUI, "saves")
_LEGACY_SAVE = os.path.join(AQUI, "savegame.json")

# Feedback dos jogadores (sugestões / bugs / reports) — persistido no volume junto
# com as contas (DATA_DIR), uma linha JSON por envio.
FEEDBACK_PATH = os.path.join(auth.DATA_DIR, "feedback.jsonl")
FEEDBACK_TIPOS = {"sugestao", "bug", "report"}
FEEDBACK_MAX = 4000        # limite do texto (relatos de bug podem ser longos)
_feedback_lock = threading.Lock()

# Sessão do request atual (thread-local). acao_* usam GAME[...] como proxy.
_ctx = threading.local()

# Limites de abuso (servidor público): corpo de request e rate-limit de login.
MAX_BODY = 128 * 1024
RL_MAX_FALHAS = 8          # falhas de login/registro por IP...
RL_JANELA_S = 600          # ...dentro desta janela => bloqueia
_rl_lock = threading.Lock()
_rl_falhas: dict[str, list] = {}   # ip -> [timestamps de falha]

# Locks de save por usuário (duas sessões do mesmo usuário não corrompem o index.json)
_save_locks: dict[str, threading.RLock] = {}
_save_locks_guard = threading.Lock()


def _user_save_lock():
    user = auth.safe_username(GAME.get("user") or "anon")
    with _save_locks_guard:
        return _save_locks.setdefault(user, threading.RLock())


class _StdoutRouter(io.TextIOBase):
    """sys.stdout global que roteia para o buffer da thread atual, se houver.
    redirect_stdout troca sys.stdout GLOBALMENTE — com uma request por sessão em
    paralelo, uma sessão capturava o texto da outra. Aqui cada thread tem o seu."""

    def __init__(self, real):
        self._real = real

    def write(self, s):
        alvo = getattr(_ctx, "stdout_buf", None) or self._real
        return alvo.write(s)

    def flush(self):
        alvo = getattr(_ctx, "stdout_buf", None) or self._real
        alvo.flush()


sys.stdout = _StdoutRouter(sys.stdout)


class _SessionGame:
    """Proxy drop-in: GAME['state'] -> sessão autenticada do request."""

    def _s(self):
        s = getattr(_ctx, "session", None)
        if s is None:
            raise RuntimeError("sem sessão autenticada")
        return s

    def __getitem__(self, k):
        return self._s()[k]

    def __setitem__(self, k, v):
        self._s()[k] = v

    def get(self, k, default=None):
        return self._s().get(k, default)


GAME = _SessionGame()


def to_json_safe(obj):
    if isinstance(obj, dict):
        return {f'{k[0]},{k[1]}' if isinstance(k, tuple) else k: to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, set):
        return list(obj)
    return obj


def from_json_safe(obj):
    """Inverso de to_json_safe para as CHAVES tupla ("x,y" -> (x,y)).
    ATENÇÃO: sets viraram listas ao salvar e NÃO são restaurados aqui (não há como saber
    o que era set) — eng.reidratar_estado() cuida dos campos conhecidos após o load."""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if isinstance(k, str) and ',' in k:
                try:
                    k = tuple(map(int, k.split(',')))
                except ValueError:
                    pass
            new_obj[k] = from_json_safe(v)
        return new_obj
    if isinstance(obj, list):
        return [from_json_safe(v) for v in obj]
    return obj


def _user_dir():
    user = GAME.get("user") or "anon"
    return auth.user_save_dir(SAVE_ROOT, user)


def _ensure_save_dir():
    os.makedirs(_user_dir(), exist_ok=True)


def _slot_path(slot):
    return os.path.join(_user_dir(), f"slot_{int(slot)}.json")


def _meta_path():
    return os.path.join(_user_dir(), "index.json")


def _ler_meta():
    _ensure_save_dir()
    try:
        with open(_meta_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"slots": {}, "active": 1}


def _escrever_meta(meta):
    _ensure_save_dir()
    caminho = _meta_path()
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def _resumo_slot(state, combate=None):
    if not state or not state.get("player"):
        return None
    p = state["player"]
    return {
        "classe": p.get("classe"),
        "raca": p.get("raca", "Humano"),
        "nivel": p.get("nivel", 1),
        "hp": p.get("hp"),
        "hp_max": p.get("hp_max"),
        "ouro": p.get("ouro", 0),
        "profundidade": state.get("profundidade", 1),
        "na_superficie": bool(state.get("na_superficie")),
        "missao_cumprida": bool(state.get("missao_cumprida")),
        "em_combate": bool(combate),
        "atualizado": time.strftime("%Y-%m-%d %H:%M"),
    }


def _migrar_legacy_save():
    """savegame.json legado -> saves/<user>/slot_1 se o slot 1 do user estiver vazio."""
    if not os.path.isfile(_LEGACY_SAVE):
        return
    if os.path.isfile(_slot_path(1)):
        return
    try:
        _ensure_save_dir()
        with open(_LEGACY_SAVE, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(_slot_path(1), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        meta = _ler_meta()
        st = from_json_safe(data.get("state"))
        resumo = _resumo_slot(st, data.get("combate"))
        if resumo:
            meta.setdefault("slots", {})["1"] = resumo
            meta["active"] = 1
            _escrever_meta(meta)
        log.info("migrou savegame.json legado -> %s", _slot_path(1))
    except Exception as e:
        log.warning("migração de save legado falhou: %s", e)


def listar_saves():
    """Lista os N_SLOTS do usuário autenticado."""
    with _user_save_lock():
        return _listar_saves_locked()


def _listar_saves_locked():
    _migrar_legacy_save()
    meta = _ler_meta()
    active = int(GAME.get("active_slot") or meta.get("active") or 1)
    slots = []
    for i in range(1, N_SLOTS + 1):
        key = str(i)
        info = (meta.get("slots") or {}).get(key)
        existe = os.path.isfile(_slot_path(i))
        if existe and not info:
            try:
                with open(_slot_path(i), "r", encoding="utf-8") as f:
                    data = from_json_safe(json.load(f))
                info = _resumo_slot(data.get("state"), data.get("combate"))
            except Exception:
                info = {"erro": "save corrompido"}
        slots.append({"slot": i, "vazio": not existe, "info": info})
    return {"slots": slots, "active": active, "n_slots": N_SLOTS,
            "user": GAME.get("user")}


def salvar_estado(slot=None, force=False):
    """Auto-save / save manual no diretório do usuário (atômico).
    
    Não salva estados finalizados (game_over/ganhou/final) no auto-save,
    para evitar que 'Jogar de novo' recarregue o jogo encerrado.
    Passe force=True para saves manuais explícitos.
    """
    if GAME["state"] is None:
        return False
    # Auto-save não persiste estado finalizado — o slot deve conter sempre
    # um jogo em progresso para que o boot não recarregue o fim de jogo.
    if not force:
        st = GAME["state"]
        if st.get("game_over") or st.get("ganhou") or st.get("final"):
            return False
    if slot is None:
        slot = GAME.get("active_slot") or 1
    try:
        slot = int(slot)
        if slot < 1 or slot > N_SLOTS:
            return False
        with _user_save_lock():
            return _salvar_estado_locked(slot)
    except Exception as e:
        log.warning("auto-save falhou: %s", e)
        return False


def _salvar_estado_locked(slot):
    _ensure_save_dir()
    payload = to_json_safe({"state": GAME["state"], "combate": GAME["combate"]})
    caminho = _slot_path(slot)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, caminho)
    meta = _ler_meta()
    meta.setdefault("slots", {})[str(slot)] = _resumo_slot(GAME["state"], GAME.get("combate"))
    meta["active"] = slot
    _escrever_meta(meta)
    GAME["active_slot"] = slot
    return True


def carregar_slot(slot):
    """Carrega o estado do slot no GAME da sessão atual."""
    try:
        slot = int(slot)
    except (TypeError, ValueError):
        return False, "Slot inválido."
    if slot < 1 or slot > N_SLOTS:
        return False, f"Slot deve ser 1..{N_SLOTS}."
    with _user_save_lock():
        return _carregar_slot_locked(slot)


def _carregar_slot_locked(slot):
    _migrar_legacy_save()
    caminho = _slot_path(slot)
    if not os.path.isfile(caminho):
        if slot == 1 and os.path.isfile(_LEGACY_SAVE):
            caminho = _LEGACY_SAVE
        else:
            return False, f"Slot {slot} está vazio."
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            data = from_json_safe(json.load(f))
    except Exception as e:
        return False, f"Erro ao carregar slot {slot}: {e}"
    GAME["state"] = eng.reidratar_estado(data.get("state"))
    GAME["combate"] = data.get("combate")
    GAME["active_slot"] = slot
    meta = _ler_meta()
    meta["active"] = slot
    if GAME["state"]:
        meta.setdefault("slots", {})[str(slot)] = _resumo_slot(GAME["state"], GAME.get("combate"))
    _escrever_meta(meta)
    return True, None


def autosave_periodico():
    """Auto-save a cada PASSOS_POR_AUTOSAVE passos (por sessão)."""
    n = int(GAME.get("passos_desde_save") or 0) + 1
    GAME["passos_desde_save"] = n
    if n >= PASSOS_POR_AUTOSAVE:
        GAME["passos_desde_save"] = 0
        salvar_estado()


# ---------------------------------------------------------------------------
# NARRAÇÃO — ancorada nos fatos da engine (online via LLM; offline via template)
# ---------------------------------------------------------------------------
def narrar_sala(state, prefixo=""):
    sala = eng.sala_atual(state)
    if ONLINE:
        evento = (f"[SISTEMA] {prefixo} Você está em uma {sala['tipo']}. "
                  f"Fatos reais (não invente além disto): {eng.ficha_sala(sala)}. "
                  f"Descreva em 1 a 2 frases APENAS o que esses fatos permitem.")
        try:
            return eng.obter_acao_do_llm(state, evento, confiavel=True)["texto_narrativo"]
        except Exception:
            pass  # cai no template offline se a API falhar
    return _narrar_template(state, prefixo)


def _narrar_template(state, prefixo=""):
    sala = eng.sala_atual(state)
    saidas = ", ".join(sorted(sala["exits"])) or "nenhuma"
    partes = []
    if prefixo:
        partes.append(prefixo)
    tipos = {"entrada": "na entrada úmida das catacumbas",
             "sala": "em uma câmara de pedra",
             "camara": "em uma câmara ampla ao fundo das catacumbas"}
    partes.append(f"Você está {tipos.get(sala['tipo'], 'em uma sala')}.")
    if sala["inimigo"] and not sala["limpa"]:
        partes.append(f"{eng.BESTIARIO[sala['inimigo']]['nome']} bloqueia o caminho.")
    elif sala["loot"] and not sala["saqueada"]:
        partes.append("Algo reluz na penumbra.")
    else:
        partes.append("O ar é frio e silencioso.")
    partes.append(f"Saídas: {saidas}.")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# INTERAÇÃO por texto — classifica a ação (online: LLM; offline: heurística)
# ---------------------------------------------------------------------------
def _achar_item(texto, candidatos, state=None):
    """Resolve item por nome/id; suporta loot procedural (itens_gerados)."""
    t = texto.lower()
    for iid in candidatos:
        info = eng.get_item_data(iid, state)
        if not info:
            continue
        nome = info["nome"].lower()
        base = iid.split("_")[0]
        if nome in t or nome.split()[0] in t or base in t:
            return iid
    return None


def classificar_offline(texto, state):
    t = texto.lower()
    inv = state["player"]["inventario"]
    if any(k in t for k in ("purific", "redim", "libert o golem", "salvar o golem")):
        return {"tipo": "purificar"}
    if any(k in t for k in ("subir", "voltar à vila", "voltar a vila", "superfície", "superficie", "pedralume")):
        return {"tipo": "subir_escada"}
    if any(k in t for k in ("descer", "escada", "andar abaixo", "próximo nível", "proximo nivel", "catacumba")):
        return {"tipo": "descer_escada"}
    if any(k in t for k in ("escond", "sumir", "embosc", "me escondo")):
        return {"tipo": "esconder"}
    if any(k in t for k in ("gazua", "arromb", "desarm")):
        sala = eng.sala_atual(state)
        if sala.get("cofre") and sala.get("trancado"):
            return {"tipo": "usar_gazua", "alvo": "cofre"}
        if sala.get("armadilha") and sala.get("armadilha_ativa"):
            return {"tipo": "usar_gazua", "alvo": "armadilha"}
        return {"tipo": "usar_gazua", "alvo": "cofre"}
    if any(k in t for k in ("furtar", "roubar", "surrup")):
        sala = eng.sala_atual(state)
        if sala.get("inimigo") and not sala.get("limpa"):
            return {"tipo": "furtar", "alvo": sala["inimigo"]}
    if any(k in t for k in ("altar", "rezar", "oferec", "saquear o altar")):
        if "saque" in t:
            return {"tipo": "ativar_altar", "escolha": "saquear"}
        if "oferec" in t or "poção" in t or "pocao" in t or "sangue" in t:
            return {"tipo": "ativar_altar", "escolha": "oferecer"}
        return {"tipo": "ativar_altar", "escolha": "rezar"}
    if any(k in t for k in ("descanso", "descans", "acamp", "recuper", "repous")):
        return {"tipo": "descansar"}
    if any(k in t for k in ("tablet", "inscri", "runa", "ler o tablet", "ler as runas", "exame")):
        if eng.sala_atual(state).get("tablet"):
            return {"tipo": "ler_tablet"}
    if any(k in t for k in ("tocha", "acend", "luz")):
        if "tocha" in inv:
            return {"tipo": "usar_item", "item": "tocha"}
    if any(k in t for k in ("equip", "empunh", "vest", "calç")):
        it = _achar_item(t, inv, state)
        if it:
            return {"tipo": "equipar_item", "item": it}
    # aprender magia de um grimório / ler / estudar
    if any(k in t for k in ("grimóri", "grimori", "aprend", "estud", "livro")):
        grim = [i for i in inv
                if (eng.get_item_data(i, state) or {}).get("tipo") == "grimorio"]
        it = _achar_item(t, grim, state)
        if it:
            return {"tipo": "usar_item", "item": it}
    if any(k in t for k in ("identific", "revel", "decifr")):
        # tenta achar item mágico não identificado no inventário
        nao_id = [i for i in inv
                  if not eng.item_esta_identificado(eng.get_item_data(i, state))]
        it = _achar_item(t, nao_id, state) if nao_id else None
        if not it and len(nao_id) == 1:
            it = nao_id[0]
        if it:
            return {"tipo": "identificar", "alvo": it}
        return {"tipo": "identificar", "alvo": ""}
    if any(k in t for k in ("compr", "quero comprar", "adquir")):
        it = _achar_item(t, list(eng.LOJA_VILA.keys()) + list(eng.LOJA_BRUXA.keys()), state)
        if it:
            return {"tipo": "comprar", "item": it}
    if any(k in t for k in ("vend", "quero vender")):
        it = _achar_item(t, inv, state)
        if it:
            return {"tipo": "vender", "item": it}
    if any(k in t for k in ("consert", "repar", "restaur")):
        # candidatos: inventário + equipados; se nada casar, o único item danificado
        candidatos = list(dict.fromkeys(
            inv + [i for i in (state["player"].get("arma"), state["player"].get("armadura")) if i]))
        it = _achar_item(t, candidatos, state)
        if not it:
            danificados = [i for i in candidatos
                           if (lambda d: d and "durabilidade" in d
                               and d["durabilidade"] < d.get("durabilidade_max", 30))
                              (eng.get_item_data(i, state))]
            if len(danificados) == 1:
                it = danificados[0]
        if it:
            # Na Vila = forja do Kael; na masmorra = reparo de campo (só Guerreiro).
            tipo_rep = "consertar" if state.get("na_superficie") else "reparar"
            return {"tipo": tipo_rep, "item": it}
    if state.get("na_superficie") and any(k in t for k in ("tratar", "tratamento", "curar", "cure", "cura ")):
        return {"tipo": "curar_vila"}
    if any(k in t for k in ("falar", "convers", "mira", "anci", " mercador", "loja",
                            "ferreiro", "kael", "forja", "curandeiro", "silas", "monge",
                            "bruxa", "morrigan", "ocultista")):
        if "anci" in t or "brum" in t:
            return {"tipo": "falar", "alvo": "anciao"}
        if any(k in t for k in ("ferreiro", "kael", "forja")):
            return {"tipo": "falar", "alvo": "ferreiro"}
        if any(k in t for k in ("curandeiro", "silas", "monge")):
            return {"tipo": "falar", "alvo": "curandeiro"}
        if any(k in t for k in ("bruxa", "morrigan", "ocultista")):
            return {"tipo": "falar", "alvo": "bruxa"}
        return {"tipo": "falar", "alvo": "mira"}
    if any(k in t for k in ("usa", "beb", "tom", "cur", "mana")):
        it = _achar_item(t, inv, state)
        if it:
            return {"tipo": "usar_item", "item": it}
    return {"tipo": "nenhuma"}


def executar_capturando(state, acao):
    """Executa uma ação da engine capturando o que ela imprime -> vira mensagens."""
    buf = io.StringIO()
    _ctx.stdout_buf = buf
    try:
        sinal = eng.executar_acao(state, acao)
    finally:
        _ctx.stdout_buf = None
    linhas = [l.strip() for l in buf.getvalue().splitlines() if l.strip()]
    # tira o prefixo "[tag] " que era decoração de terminal
    linhas = [l.split("] ", 1)[1] if l.startswith("[") and "] " in l else l for l in linhas]
    return sinal, linhas


# ---------------------------------------------------------------------------
# SERIALIZAÇÃO de resposta
# ---------------------------------------------------------------------------
def combate_json():
    cb = GAME["combate"]
    if not cb:
        return None
    e = eng.BESTIARIO[cb["enemy_id"]]
    # hp_max vem do próprio combate (já escalado por profundidade), não do bestiário base
    extras = [{"id": ex["id"], "nome": eng.BESTIARIO[ex["id"]]["nome"], "hp": ex["hp"],
               "hp_max": ex["hp_max"]} for ex in cb["extras"]]
    return {
        "id": cb["enemy_id"],
        "nome": e["nome"],
        "hp": cb["hp"],
        "hp_max": cb["hp_max"],
        "extras": extras,
        "debuffs": cb.get("debuffs", {}),
    }


def resposta(narrativa=None, mensagens=None, fim=None):
    state = GAME["state"]
    user = GAME.get("user")
    return {
        "estado": eng.serializar_estado(state) if state else None,
        "combate": combate_json(),
        "narrativa": narrativa,
        "mensagens": mensagens or [],
        "fim": fim,          # None | "vitoria" | "derrota"
        "online": ONLINE,
        "user": user,
    }


# ---------------------------------------------------------------------------
# AÇÕES (a lógica de cada endpoint)
# ---------------------------------------------------------------------------
def acao_novo(dados):
    classe = dados.get("classe", "Guerreiro")
    if classe not in eng.CLASSES:
        classe = "Guerreiro"
    raca = dados.get("raca", "Humano")
    if raca not in eng.RACAS:
        raca = "Humano"
    seed = dados.get("seed")
    GAME["state"] = eng.novo_jogo(classe, seed, raca=raca)
    GAME["combate"] = None
    game_log.log_estado_resumo(GAME["state"], f"novo_jogo {raca} {classe}")
    narrativa = narrar_sala(GAME["state"],
                            prefixo="A fonte da Vila secou; você desce às catacumbas.")
    return resposta(narrativa=narrativa)


def acao_client_log(dados):
    """Recebe logs do browser e grava em logs/client.log."""
    entries = dados.get("entries") or dados.get("logs") or []
    if not entries and dados.get("msg"):
        entries = [dados]
    game_log.log_client(entries)
    return {"ok": True}


def acao_virar(dados):
    """Gira no lugar (1ª pessoa): esquerda/direita sem gastar passo."""
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    if GAME["state"] is None:
        return resposta()
    rel = dados.get("direcao", "")
    if rel not in ("esquerda", "direita"):
        return resposta(mensagens=["Use esquerda ou direita para virar."])
    r = eng.aplicar_virar(GAME["state"], rel)
    log.debug("virar %s -> facing=%s", rel, r.get("facing"))
    return resposta()


def acao_mover(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    state = GAME["state"]
    direcao = dados.get("direcao", "")
    r = eng.aplicar_movimento(state, direcao)
    if not r["moveu"]:
        if r.get("motivo") == "superficie":
            log.info("mover bloqueado: na superfície pos=%s", state["pos"])
            return resposta(mensagens=["Você está em Pedralume. Use Descer para voltar às catacumbas."])
        log.info("mover bloqueado dir=%s face=%s pos=%s exits=%s",
                 direcao, state["facing"], state["pos"], r.get("exits"))
        return resposta(mensagens=[f"Há uma parede a {r['direcao']} — sem passagem."])
    log.info("mover ok dir=%s -> pos=%s face=%s exits_sala=%s combate=%s",
             direcao, state["pos"], state["facing"],
             sorted(eng.sala_atual(state).get("exits") or []), bool(r.get("combate")))

    msgs = []
    if r.get("luz"):
        msgs.append(r["luz"])
    for fm in (r.get("fadiga") or []):
        msgs.append(fm)
    for vm in (r.get("veneno") or []):
        msgs.append(vm)
    if r.get("armadilha"):
        msgs.append(r["armadilha"])
    if not state["player"]["hp"] > 0:      # a armadilha (ou o veneno) matou
        return resposta(mensagens=msgs, fim="derrota")
    if r.get("cofre"):
        msgs.append(r["cofre"])

    autosave_periodico()   # auto-save periódico (independente de combate/loot abaixo)

    if r["combate"]:                       # entrou numa sala com inimigo vivo
        sala = eng.sala_atual(state)
        grupo = sala["grupo"] if sala["inimigo"] == r["combate"] else None
        GAME["combate"] = eng.novo_combate(state, r["combate"], grupo)
        ataque = (f"{eng.BESTIARIO[r['combate']]['nome']} e seu bando atacam!"
                  if grupo else f"{eng.BESTIARIO[r['combate']]['nome']} ataca!")
        narrativa = narrar_sala(state, prefixo=f"Você avança para {r['direcao']}.")
        return resposta(narrativa=narrativa, mensagens=msgs + [ataque])

    narrativa = narrar_sala(state, prefixo=f"Você avança para {r['direcao']}.")
    return resposta(narrativa=narrativa, mensagens=msgs + r["loot"])


def acao_interagir(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Você está em combate — use os botões."])
    state = GAME["state"]
    # anti-injeção: o texto do jogador é DADO — nunca canal [SISTEMA]/role/etc.
    texto = eng.sanitizar_texto_jogador(dados.get("texto"))
    if not texto:
        return resposta()
    state["historico"].append(f"jogador: {texto}")
    if len(state["historico"]) > 60:      # só os últimos 6 entram no prompt
        del state["historico"][:-60]

    if ONLINE:
        d = eng.obter_acao_do_llm(state, texto)
        narrativa = d["texto_narrativo"]
        acao = d["acao"]
    else:
        narrativa = None
        acao = classificar_offline(texto, state)

    # Movimento NÃO passa por aqui — só as setas movem.
    if acao.get("tipo") == "mover":
        return resposta(narrativa=narrativa or "Para andar, use as setas do teclado.",
                        mensagens=["(movimento é pelas setas)"])

    # Combate provocado por texto: só se a sala tiver aquele inimigo vivo.
    if acao.get("tipo") == "iniciar_combate":
        sinal, _ = executar_capturando(state, acao)
        if sinal and sinal[0] == "combate":
            sala = eng.sala_atual(state)
            grupo = sala["grupo"] if sala["inimigo"] == sinal[1] else None
            GAME["combate"] = eng.novo_combate(state, sinal[1], grupo)
            return resposta(narrativa=narrativa,
                            mensagens=[f"{eng.BESTIARIO[sinal[1]]['nome']} encara você!"])
        return resposta(narrativa=narrativa)

    # Purificação: final alternativo (engine decide).
    if acao.get("tipo") == "purificar":
        sinal, linhas = executar_capturando(state, acao)
        if sinal and sinal[0] == "fim":
            return resposta(narrativa=narrativa or (linhas[0] if linhas else None),
                            mensagens=linhas, fim=sinal[1])
        return resposta(narrativa=narrativa, mensagens=linhas)

    # Descanso / furto podem emboscar (combate).
    if acao.get("tipo") in ("descansar", "furtar"):
        sinal, linhas = executar_capturando(state, acao)
        if sinal and sinal[0] == "combate":
            sala = eng.sala_atual(state)
            grupo = sala["grupo"] if sala.get("inimigo") == sinal[1] else None
            GAME["combate"] = eng.novo_combate(state, sinal[1], grupo)
            return resposta(narrativa=narrativa, mensagens=linhas + [
                f"{eng.BESTIARIO[sinal[1]]['nome']} ataca!"])
        return resposta(narrativa=narrativa, mensagens=linhas)

    _, linhas = executar_capturando(state, acao)
    if not ONLINE and not linhas:
        narrativa = "Nada de especial acontece."
    return resposta(narrativa=narrativa, mensagens=linhas)


def acao_equipar(dados):
    """Clique-para-equipar do inventário (direto por id — sem passar pelo LLM)."""
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    item = dados.get("item")
    state = GAME["state"]
    if not eng.item_conhecido(item, state):
        return resposta(mensagens=["Item inválido."])
    _, linhas = executar_capturando(state, {"tipo": "equipar_item", "item": item})
    return resposta(mensagens=linhas)


def acao_usar(dados):
    """Clique-para-usar do inventário (poção/grimório) direto por id."""
    if GAME["combate"]:
        return resposta(mensagens=["Em combate, use os botões de ação."])
    item = dados.get("item")
    state = GAME["state"]
    if not eng.item_conhecido(item, state):
        return resposta(mensagens=["Item inválido."])
    _, linhas = executar_capturando(state, {"tipo": "usar_item", "item": item})
    # momento crítico (cura HP/veneno/sangramento) — salva na hora
    info = eng.get_item_data(item, state) or {}
    if item == "pocao_cura" or info.get("cura"):
        salvar_estado()
    return resposta(mensagens=linhas)


def acao_identificar(dados):
    """Clique 'Identificar' no inventário: consome pergaminho e revela afixos."""
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    alvo = dados.get("alvo") or dados.get("item")
    state = GAME["state"]
    if not eng.item_conhecido(alvo, state):
        return resposta(mensagens=["Item inválido."])
    _, linhas = executar_capturando(state, {"tipo": "identificar", "alvo": alvo})
    return resposta(mensagens=linhas)


def acao_conjurar(dados):
    """Clique-para-conjurar FORA de combate (só cura), direto por id de magia."""
    if GAME["combate"]:
        return resposta(mensagens=["Em combate, use os botões de ação."])
    magia = dados.get("magia")
    if magia not in eng.MAGIAS:
        return resposta(mensagens=["Magia inválida."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "conjurar", "magia": magia})
    return resposta(mensagens=linhas)


def acao_descansar(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    sinal, linhas = executar_capturando(GAME["state"], {"tipo": "descansar"})
    if sinal and sinal[0] == "combate":
        GAME["combate"] = eng.novo_combate(GAME["state"], sinal[1])
        return resposta(mensagens=linhas + [f"{eng.BESTIARIO[sinal[1]]['nome']} ataca!"])
    salvar_estado()   # descanso é o momento canônico de "checkpoint" — cura HP/mana/fadiga
    return resposta(mensagens=linhas)


def acao_ler_tablet(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "ler_tablet"})
    return resposta(mensagens=linhas)


def acao_purificar(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Em combate não dá para ritualizar — fuja ou vença antes."])
    sinal, linhas = executar_capturando(GAME["state"], {"tipo": "purificar"})
    if sinal and sinal[0] == "fim":
        return resposta(narrativa=linhas[0] if linhas else None, mensagens=linhas, fim=sinal[1])
    return resposta(mensagens=linhas)


def acao_esconder(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Tarde demais — você já está em combate."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "esconder"})
    return resposta(mensagens=linhas)


def acao_gazua(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    alvo = dados.get("alvo", "cofre")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "usar_gazua", "alvo": alvo})
    return resposta(mensagens=linhas)


def acao_altar(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    escolha = dados.get("escolha", "rezar")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "ativar_altar", "escolha": escolha})
    return resposta(mensagens=linhas)


def acao_descer(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "descer_escada"})
    state = GAME["state"]
    game_log.log_estado_resumo(state, "após descer")
    salvar_estado()   # auto-save ao mudar de andar
    if state.get("na_superficie"):
        return resposta(mensagens=linhas)
    return resposta(narrativa=narrar_sala(state, prefixo=linhas[0] if linhas else "Você desce."),
                    mensagens=linhas)

def acao_puxar_alavanca(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "puxar_alavanca"})
    return resposta(narrativa=linhas[0] if linhas else "Você puxa a alavanca.", mensagens=linhas)


def acao_subir(_dados=None):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "subir_escada"})
    state = GAME["state"]
    game_log.log_estado_resumo(state, "após subir")
    salvar_estado()   # auto-save ao mudar de andar
    if state.get("na_superficie"):
        return resposta(narrativa=linhas[0] if linhas else None, mensagens=linhas)
    return resposta(narrativa=narrar_sala(state, prefixo=linhas[0] if linhas else "Você sobe."),
                    mensagens=linhas)


def acao_save(dados=None):
    """Save manual (POST). dados.slot opcional (1..N_SLOTS); default = slot ativo."""
    dados = dados or {}
    slot = dados.get("slot")
    if salvar_estado(slot, force=True):   # force=True: save manual salva qualquer estado
        s = int(slot) if slot is not None else int(GAME.get("active_slot") or 1)
        return {"msg": f"Jogo salvo no slot {s}.", "slot": s, "saves": listar_saves()}
    return {"erro": "Erro ao salvar (sem jogo ativo ou slot inválido)."}


def acao_load(dados=None):
    """Load manual (POST). dados.slot (default slot ativo da sessão)."""
    dados = dados or {}
    slot = dados.get("slot", GAME.get("active_slot") or 1)
    ok, err = carregar_slot(slot)
    if not ok:
        return {"erro": err}
    return resposta(mensagens=[f"Jogo carregado do slot {int(slot)}."])


def acao_saves(_dados=None):
    """Lista slots de save do usuário (GET ou POST)."""
    return listar_saves()


def acao_register(dados=None):
    dados = dados or {}
    ok, msg = auth.register(dados.get("username"), dados.get("password"), dados.get("invite_key"))
    if not ok:
        return {"erro": msg, "ok": False}
    return {"ok": True, "msg": msg}


def acao_login(dados=None):
    dados = dados or {}
    ok, msg, token = auth.login(dados.get("username"), dados.get("password"))
    if not ok:
        return {"erro": msg, "ok": False}
    # Handler grava o cookie a partir de _ctx.set_cookie
    _ctx.set_cookie = auth.cookie_header(token)
    _ctx.token = token
    _ctx.session = auth.get_session(token)
    return {"ok": True, "msg": msg, "user": _ctx.session["user"]}


def acao_logout(_dados=None):
    tok = getattr(_ctx, "token", None)
    auth.logout(tok)
    _ctx.set_cookie = auth.clear_cookie_header()
    _ctx.session = None
    return {"ok": True, "msg": "Sessão encerrada."}


def acao_me(_dados=None):
    s = getattr(_ctx, "session", None)
    if not s:
        return {"ok": False, "precisa_login": True}
    return {"ok": True, "user": s.get("user"), "tem_jogo": s.get("state") is not None}


def _limpar_feedback(texto):
    """Tira caracteres de controle (menos \\n\\t), colapsa espaços e limita o tamanho.
    Mantém quebras de linha — um relato de bug pode ser multilinha."""
    t = str(texto or "")
    t = "".join(c for c in t if c == "\n" or c == "\t" or ord(c) >= 0x20)
    return t.strip()[:FEEDBACK_MAX]


def acao_feedback(dados=None):
    """Recebe sugestão / bug / report do jogador e grava em data/feedback.jsonl."""
    dados = dados or {}
    tipo = (dados.get("tipo") or "sugestao").strip().lower()
    if tipo not in FEEDBACK_TIPOS:
        tipo = "sugestao"
    texto = _limpar_feedback(dados.get("texto"))
    if len(texto) < 3:
        return {"erro": "Escreva um pouco mais para o feedback ser útil.", "ok": False}

    sess = getattr(_ctx, "session", None)
    state = sess.get("state") if sess else None
    contexto = None
    if state and state.get("player"):
        p = state["player"]
        contexto = {"andar": state.get("profundidade"), "na_superficie": state.get("na_superficie"),
                    "classe": p.get("classe"), "raca": p.get("raca"), "nivel": p.get("nivel"),
                    "hp": p.get("hp"), "pos": state.get("pos")}
    entrada = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user": (sess.get("user") if sess else None),
        "tipo": tipo,
        "texto": texto,
        "online": ONLINE,
        "contexto": contexto,
    }
    try:
        with _feedback_lock:
            os.makedirs(auth.DATA_DIR, exist_ok=True)
            with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except OSError as e:
        log.error("falha ao gravar feedback: %s", e)
        return {"erro": "Não foi possível salvar agora. Tente novamente mais tarde.", "ok": False}
    log.info("feedback %s de %s (%d chars)", tipo, entrada["user"], len(texto))
    rotulo = {"sugestao": "Sugestão", "bug": "Bug", "report": "Report"}[tipo]
    return {"ok": True, "msg": f"{rotulo} enviado. Obrigado por ajudar a melhorar o jogo!"}


def acao_comprar(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    item = dados.get("item")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "comprar", "item": item})
    return resposta(mensagens=linhas)


def acao_vender(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    item = dados.get("item")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "vender", "item": item})
    return resposta(mensagens=linhas)


def acao_consertar(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    item = dados.get("item")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "consertar", "item": item})
    return resposta(mensagens=linhas)


def acao_falar(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    alvo = dados.get("alvo", "mira")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "falar", "alvo": alvo})
    return resposta(mensagens=linhas)


def acao_curar_vila(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    _, linhas = executar_capturando(GAME["state"], {"tipo": "curar_vila"})
    return resposta(mensagens=linhas)


def acao_reparar(dados):
    if GAME["combate"]:
        return resposta(mensagens=["Termine o combate primeiro."])
    item = dados.get("item")
    _, linhas = executar_capturando(GAME["state"], {"tipo": "reparar", "item": item})
    return resposta(mensagens=linhas)


def acao_combate(dados):
    if not GAME["combate"]:
        return resposta(mensagens=["Não há combate em andamento."])
    state = GAME["state"]
    escolha = dados.get("escolha", "atacar")
    status, linhas = eng.combate_passo(state, GAME["combate"], escolha)

    if status == "continua":
        return resposta(mensagens=linhas)

    enemy_id = GAME["combate"]["enemy_id"]
    GAME["combate"] = None

    if status == "fuga":
        return resposta(mensagens=linhas)

    if status == "derrota":
        return resposta(mensagens=linhas, fim="derrota")

    # vitória: a luta inteira acabou -> a sala fica segura (vale p/ hordas), saqueia e checa chefe
    sala = eng.sala_atual(state)
    sala["limpa"] = True
    salvar_estado()   # auto-save após cada combate encerrado
    if enemy_id == eng.OBJETIVO_BOSS:
        state["missao_cumprida"] = True
        state["final"] = "vitoria"
        return resposta(narrativa=("O Golem de Barro se desfaz numa poça de lama e o rio "
                                   "subterrâneo irrompe, livre outra vez. A Vila está salva."),
                        mensagens=linhas, fim="vitoria")
    linhas += eng.saquear_sala(state, sala)
    narrativa = narrar_sala(state, prefixo="Com o inimigo abatido,")
    return resposta(narrativa=narrativa, mensagens=linhas)


# Rotas que exigem login mas NÃO exigem jogo ativo
AUTH_OK_SEM_JOGO = {
    "/api/novo", "/api/load", "/api/saves", "/api/log",
    "/api/logout", "/api/me", "/api/save", "/api/feedback",
}
# Rotas públicas (sem cookie)
PUBLIC_POST = {"/api/register", "/api/login", "/api/log", "/api/auth/status"}
# Rotas públicas com rate-limit por IP (força bruta de senha/chave de convite)
RL_POST = {"/api/register", "/api/login"}


def _rl_bloqueado(ip):
    now = time.time()
    with _rl_lock:
        falhas = [t for t in _rl_falhas.get(ip, []) if now - t < RL_JANELA_S]
        if falhas:
            _rl_falhas[ip] = falhas
        else:
            _rl_falhas.pop(ip, None)
        return len(falhas) >= RL_MAX_FALHAS


def _rl_registrar(ip, ok):
    with _rl_lock:
        if ok:
            _rl_falhas.pop(ip, None)
        else:
            _rl_falhas.setdefault(ip, []).append(time.time())

ROTAS = {
    "/api/register": acao_register,
    "/api/login": acao_login,
    "/api/logout": acao_logout,
    "/api/me": acao_me,
    "/api/auth/status": lambda _=None: auth.auth_status(),
    "/api/novo": acao_novo,
    "/api/mover": acao_mover,
    "/api/virar": acao_virar,
    "/api/interagir": acao_interagir,
    "/api/combate": acao_combate,
    "/api/equipar": acao_equipar,
    "/api/usar": acao_usar,
    "/api/identificar": acao_identificar,
    "/api/conjurar": acao_conjurar,
    "/api/descansar": acao_descansar,
    "/api/ler_tablet": acao_ler_tablet,
    "/api/purificar": acao_purificar,
    "/api/esconder": acao_esconder,
    "/api/gazua": acao_gazua,
    "/api/altar": acao_altar,
    "/api/descer": acao_descer,
    "/api/subir": acao_subir,
    "/api/save": acao_save,
    "/api/load": acao_load,
    "/api/saves": acao_saves,
    "/api/comprar": acao_comprar,
    "/api/puxar_alavanca": acao_puxar_alavanca,
    "/api/vender": acao_vender,
    "/api/consertar": acao_consertar,
    "/api/falar": acao_falar,
    "/api/curar_vila": acao_curar_vila,
    "/api/reparar": acao_reparar,
    "/api/log": acao_client_log,
    "/api/feedback": acao_feedback,
}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8", extra_headers=None):
        dados = body.encode("utf-8") if isinstance(body, str) else body
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(dados)))
            # cookies de sessão
            sc = getattr(_ctx, "set_cookie", None)
            if sc:
                self.send_header("Set-Cookie", sc)
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(dados)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _bind_session(self):
        """Lê cookie e associa sessão ao thread-local. Retorna sessão ou None."""
        _ctx.session = None
        _ctx.token = None
        _ctx.set_cookie = None
        tok = auth.session_token_from_headers(self.headers)
        if not tok:
            return None
        sess = auth.get_session(tok)
        if not sess:
            return None
        _ctx.token = tok
        _ctx.session = sess
        return sess

    def do_GET(self):
        _ctx.set_cookie = None
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(os.path.join(AQUI, "index.html"), "r", encoding="utf-8") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(404, "index.html não encontrado")
            return
        if path.startswith("/assets/"):
            try:
                rel = urllib.parse.unquote(path.lstrip("/"))
                asset_path = os.path.realpath(os.path.join(AQUI, rel))
                assets_root = os.path.realpath(os.path.join(AQUI, "assets"))
                if not asset_path.startswith(assets_root + os.sep):
                    self._send(404, "asset não encontrado")
                    return
                with open(asset_path, "rb") as f:
                    ext = os.path.splitext(asset_path)[1].lower()
                    ctype = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                    self._send(200, f.read(), ctype)
            except OSError:
                self._send(404, "asset não encontrado")
            return
        if path == "/favicon.ico":
            svg = (
                b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
                b'<rect width="32" height="32" fill="#0e0f13"/>'
                b'<text x="16" y="22" text-anchor="middle" font-size="18" fill="#5fd0e0">\xe2\x9c\xa0</text>'
                b'</svg>'
            )
            self._send(200, svg, "image/svg+xml")
            return
        if path == "/api/auth/status":
            self._send(200, json.dumps(auth.auth_status(), ensure_ascii=False))
            return
        if path == "/api/me":
            self._bind_session()
            self._send(200, json.dumps(acao_me(), ensure_ascii=False))
            return
        if path in ("/api/estado", "/api/saves"):
            sess = self._bind_session()
            if not sess:
                self._send(200, json.dumps({"erro": "não autenticado", "precisa_login": True}))
                return
            with sess["lock"]:
                if path == "/api/saves":
                    body = json.dumps(listar_saves(), ensure_ascii=False)
                elif GAME["state"] is None:
                    body = json.dumps({"erro": "sem jogo", "precisa_novo": True,
                                       "user": sess.get("user")})
                elif (GAME["state"].get("game_over") or GAME["state"].get("ganhou")
                      or GAME["state"].get("final")):
                    # Jogo finalizado: trata como sem jogo para forçar nova seleção de classe
                    GAME["state"] = None
                    GAME["combate"] = None
                    body = json.dumps({"erro": "jogo encerrado", "precisa_novo": True,
                                       "user": sess.get("user")})
                else:
                    body = json.dumps(resposta(), ensure_ascii=False)
            self._send(200, body)
            return
        self._send(404, json.dumps({"erro": "rota inexistente"}))

    def do_POST(self):
        _ctx.set_cookie = None
        path = self.path.split("?", 1)[0]
        fn = ROTAS.get(path)
        if not fn:
            log.warning("rota inexistente: %s", path)
            self._send(404, json.dumps({"erro": "rota inexistente"}))
            return
        tam = int(self.headers.get("Content-Length", 0) or 0)
        if tam > MAX_BODY:
            self._send(413, json.dumps({"erro": "corpo da requisição grande demais"}))
            return
        corpo = self.rfile.read(tam) if tam else b"{}"
        try:
            dados = json.loads(corpo or b"{}")
        except json.JSONDecodeError:
            dados = {}
            log.warning("JSON inválido em %s", path)
        if not isinstance(dados, dict):
            dados = {}

        # log do cliente: aceita sem login (best-effort)
        if path == "/api/log":
            try:
                self._bind_session()
                resultado = fn(dados)
            except Exception as e:
                log.error("erro em %s: %s\n%s", path, e, traceback.format_exc())
                resultado = {"erro": str(e)}
            self._send(200, json.dumps(resultado, ensure_ascii=False))
            return

        # login/registro: rate-limit por IP contra força bruta de senha/convite
        if path in RL_POST:
            ip = self._client_ip()
            if _rl_bloqueado(ip):
                log.warning("rate-limit: %s bloqueado em %s", ip, path)
                self._send(429, json.dumps({
                    "erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."}))
                return
            _ctx.set_cookie = None
            self._bind_session()
            try:
                resultado = fn(dados)
            except Exception as e:
                log.error("erro em %s: %s\n%s", path, e, traceback.format_exc())
                resultado = {"erro": str(e)}
            _rl_registrar(ip, bool(resultado.get("ok")))
            self._send(200, json.dumps(resultado, ensure_ascii=False))
            return

        _ctx.set_cookie = None
        sess = self._bind_session()
        if path not in PUBLIC_POST and not sess:
            self._send(200, json.dumps({"erro": "não autenticado", "precisa_login": True}))
            return
        # Lock POR SESSÃO: uma chamada lenta do LLM só bloqueia o próprio jogador.
        # (O stdout roteado por thread torna executar_capturando seguro em paralelo.)
        lock = sess["lock"] if sess else threading.RLock()
        with lock:
            # rotas de jogo exigem state (exceto lista abaixo)
            if (path not in PUBLIC_POST and path not in AUTH_OK_SEM_JOGO
                    and sess and sess.get("state") is None):
                self._send(200, json.dumps({
                    "erro": "sem jogo", "precisa_novo": True,
                    "user": sess.get("user"),
                }))
                return
            try:
                resultado = fn(dados)
            except Exception as e:
                log.error("erro em %s: %s\n%s", path, e, traceback.format_exc())
                resultado = {"erro": str(e)}
            body = json.dumps(resultado, ensure_ascii=False)
            # cookie pode ter sido setado por logout
            self._send(200, body)

    def _client_ip(self):
        """IP real do cliente (Railway/proxies mandam X-Forwarded-For)."""
        xff = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return xff or self.client_address[0]

    def log_message(self, fmt, *args):
        msg = fmt % args if args else str(fmt)
        if "/api/log" in msg:
            return
        log.debug("HTTP " + msg)


def main():
    game_log.session_banner()
    # Garante pastas de persistência (volume Railway ou local)
    try:
        os.makedirs(auth.DATA_DIR, exist_ok=True)
        os.makedirs(SAVE_ROOT, exist_ok=True)
    except OSError as e:
        log.warning("não foi possível criar data/saves: %s", e)
    modo = f"ONLINE ({eng.MODELO} @ {eng.BASE_URL})" if ONLINE else "OFFLINE (narração por template)"
    convite = "configurada" if auth.invite_key() else "AUSENTE (cadastro desativado)"
    print(f"As Catacumbas Esquecidas — servidor web [{modo}]")
    print(f"Escutando http://{HOST}:{PORT}")
    print(f"Chave de convite (REGISTER_KEY/invite_key.txt): {convite}")
    print(f"DATA_DIR={auth.DATA_DIR}  SAVE_ROOT={SAVE_ROOT}")
    print(f"Logs: {game_log.LOG_DIR}")
    print("Multi-sessão: cada conta tem jogo e saves isolados.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
