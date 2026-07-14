# ⛧ As Catacumbas Esquecidas

RPG de masmorra **narrado por LLM** (DeepSeek) com **engine determinística em Python**.
Roda no **terminal** ou na **interface web** (vista em **1ª pessoa** + automapa).

A fonte de água da Vila **Pedralume** secou. Você desce às catacumbas, fica mais forte e
derrota (ou **purifica**) o **Golem de Barro** para libertar o rio subterrâneo.

> **Como usar um LLM para narrar um jogo sem deixar que ele invente as regras.**

---

## A ideia central: a engine manda, o LLM narra

1. **A engine é a única dona do estado** — HP, mana, inventário, XP, mapa, combate, fadiga, lore.
2. **O LLM só NARRA** — sem matemática de combate nem inventar entidades.
3. **Whitelist + loop de reparo** — ações inválidas são rejeitadas e re-pedidas.
4. **Masmorra procedural da engine** — o LLM descreve o que a engine revelou.

---

## Como jogar

**Requisitos:** Python 3 (stdlib). Pacote `openai` só no modo online.

### Terminal
```bash
python rpg_loop.py            # jogo no terminal
python rpg_loop.py --demo     # testes offline (mantenha verde)
```

### Web (recomendado)
```bash
# Chave de convite (obrigatória para CRIAR conta)
# PowerShell:
$env:REGISTER_KEY = "sua-chave-secreta"
# ou crie invite_key.txt na raiz com a chave numa linha

python server.py              # http://0.0.0.0:8000
```

Abra o browser, **crie uma conta** (usuário + senha + chave de convite) e jogue.  
Cada conta tem **sessão e saves isolados** (vários jogadores ao mesmo tempo).

| Controle | Ação |
|---|---|
| `↑` / `W` | Frente (relativo ao facing) |
| `↓` / `S` | Trás |
| `←` `→` / `A` `D` | Virar no lugar |
| Texto / inventário | Interagir, equipar, usar |
| **Descer** / **Subir · Vila** | Andar 2 ↔ 1; entrada ↔ Pedralume |
| Botões de combate | Atacar, poção, magia, fugir |
| `?` | Tutorial |
| `F3` | Debug da vista (distância, saídas, hit) |

- **Vista 1ª pessoa** — raycaster com texturas de parede, billboards com **sprites PNG** em pixel art (inimigos, NPCs, altares, baús, loot, escadas). Combate com clamp de distância (alvo sempre legível e à frente dos props). Flash, vinhetas de status e fadiga.
- **Vila navegável em cenas 2D:** Pedralume é um mapa andável (praça, entrada das catacumbas, forja do Kael, loja da Mira, tenda do Ancião, curandeiro e cabana da bruxa), mas cada local renderiza uma **cena 2D composta** — céu noturno + casario ao fundo, NPC grande e nomeado no centro, props do local (fonte, brasas da forja, arco das catacumbas) e **setas de saída** com o nome do destino. O NPC da sala atual vira botão "Falar" no painel; comprar/vender só na loja da Mira e consertar só na forja.
- **Automapa** com névoa de guerra e indicadores de **status** (☠️ veneno, 🩸 sangramento, ⬇️ fraqueza, ❄️ gelo/atordoamento). O boss revela a identidade correta à distância.
- Badge: `online · DeepSeek` ou `offline · template`.
- **Áudio** via Web Audio API: batimento cardíaco com HP crítico, shake prolongado nas magias, impacto grave (hit) e áudio de fadiga (pitch e LFO dinâmicos).

### Narração do LLM (opcional)

Sem chave: modo offline (template). Com chave:

- env `DEEPSEEK_API_KEY`, ou
- `key.txt` na raiz (**não commitar** — ver `.gitignore`).

### Contas e multi-jogador

| Item | Como |
|---|---|
| Criar conta | Precisa da **chave de convite** (`REGISTER_KEY` / `INVITE_KEY` / `invite_key.txt`) |
| Login | Cookie `session` HttpOnly (expira em 14 dias); cada jogador tem seu `GAME` |
| Saves | `saves/<usuario>/slot_1..3.json` |
| API auth | `POST /api/register`, `/api/login`, `/api/logout` · `GET /api/me`, `/api/auth/status` |

**Segurança embutida no servidor** (stdlib, sem dependências):
- Senhas com **PBKDF2-HMAC-SHA256**; comparações com `compare_digest`.
- **Rate-limit por IP** no login/registro (8 falhas em 10 min → HTTP 429) — protege senha e chave de convite de força bruta (funciona atrás de proxy via `X-Forwarded-For`).
- **Lock por sessão**: a chamada lenta do LLM de um jogador não trava os outros.
- Rota `/assets/` validada contra **path traversal**; corpo de POST limitado a 128KB; `/api/log` com cap de volume.
- **Anti-jailbreak / prompt injection do narrador:** o texto livre do jogador é sanitizado (marcadores de canal, roles e cercas de código removidos) e emoldurado como *dado, não instrução*; leis idioma-agnósticas + guarda de saída rejeitam quebra de personagem e vazamento de regras. Como o LLM nunca controla os números, um jailbreak não vira ouro/HP/itens. Detalhes em [`LLM_RULEBOOK.md`](LLM_RULEBOOK.md).

### Feedback dos jogadores & logs de debug

- **💬 Feedback in-game:** botão no topo abre um formulário para **sugestão / bug / report** (texto livre). Cada envio é gravado em `data/feedback.jsonl` (uma linha JSON) com usuário, timestamp e o **contexto da partida** (andar, classe, raça, nível, HP, posição) — pronto para triagem.
- **Logs de jogada online:** cada turno narrado pelo LLM é registrado em `logs/llm.log` (entrada do jogador, ação escolhida, narrativa, reparos e fallbacks), marcado por usuário — dá para rastrear e depurar uma jogada depois. Eventos do servidor ficam em `logs/game.log` e os do browser em `logs/client.log`.

### Deploy

**Railway (recomendado):** veja o guia completo em [`DEPLOY-RAILWAY.md`](DEPLOY-RAILWAY.md).

Resumo: GitHub → New Project → Variables (`REGISTER_KEY`, `DATA_DIR=/data`, `SAVE_ROOT=/data/saves`, `SESSION_SECURE=1`) → Volume em `/data` → Generate Domain.

**Docker Compose (VPS local):**

```bash
export REGISTER_KEY="chave-que-voce-da-aos-testadores"
# export DEEPSEEK_API_KEY="..."   # opcional
docker compose up -d --build
```

**Importante:** envie aos testadores (1) o link do site e (2) a chave de convite **só para criar conta**.  
Não publique a chave no repositório.

---

## O que tem no jogo

### Personagem
- 3 classes (Guerreiro / Mago / Ladino) × 4 raças (Humano, Anão, Elfo, Halfling)
- 6 atributos (FOR/DES/CON/INT/SAB/CAR) · progressão até nível 10 (soft-cap de XP estilo Diablo: monstro muito abaixo do seu nível rende menos/zero XP)

### Exploração
- Masmorra procedural (~24 salas) + **andares 1-3** (sidequests e minichefes) + **superfície (Pedralume)**
- **Ouro** e **loja/NPCs** na Vila; **3 slots de save** por conta (`saves/<usuario>/slot_N.json`)
- Luz/tocha, Pedra de Luz Eterna, fadiga, encumbrance, descanso + wandering
- Lore tablets, altares (rezar/oferecer/saquear), armadilhas, cofres, gazua, **Loot Procedural (Afixos)** + **Identificação** (pergaminho)
- **Dano contínuo:** Gás Venenoso envenena, Lâminas Giratórias causam sangramento (tick por passo)
- **Durabilidade e Reparo:** Armas e armaduras (inclusive as mágicas/afixadas) desgastam em uso real no combate, com o estado visível no inventário (ex.: `23/25`); conserto na forja do Kael (botão no inventário, `/api/consertar` ou pedindo ao narrador) por 10 ouro.
- Facing inicial aponta para uma **saída real** (entrada jogável em 1ª pessoa)
- **Auto-save:** salva a cada combate, troca de andar, poção de cura, descanso e a cada 12 passos.

### Combate e magia
- Turnos 100% engine, hordas, 10 magias (scaling, buffs, debuffs, AoE)
- Bestiário com debuffs: **Aranha** (envenena), **Espectro** (fadiga) e **Sombra Vampírica** (drena força -> fraqueza)
- Backstab / emboscada (Ladino); dois finais (matar ou purificar o Golem)

Contrato LLM: [`LLM_RULEBOOK.md`](LLM_RULEBOOK.md) · Plano: [`ROADMAP.md`](ROADMAP.md)

---

## Estrutura do projeto

| Arquivo / pasta | Papel |
|---|---|
| `rpg_loop.py` | Engine, terminal, `--demo` |
| `server.py` | HTTP + `/api/*` + favicon + serve UI (locks por sessão, rate-limit) |
| `auth.py` | Contas (PBKDF2), sessões com expiração, cookie, chave de convite |
| `index.html` | Raycaster 1ª pessoa, automapa, UI, SFX, lerp |
| `balance_sim.py` | Simulação de balance vs Golem |
| `game_log.py` | Logs em `logs/game.log`, `logs/client.log` e `logs/llm.log` |
| `LLM_RULEBOOK.md` | Constituição do narrador |
| `DEPLOY-RAILWAY.md` | Guia de deploy (Railway + volume) |
| `artifacts/` | Lore / design notes |
| `data/` · `saves/` | Contas, feedback e saves por usuário (gitignored) |
| `logs/` | Debug runtime (gitignored) |
| `.gitignore` | key, contas, saves, logs, pycache, venv |

---

## Desenvolvimento

```bash
python rpg_loop.py --demo
python balance_sim.py
python server.py          # logs em logs/
```

**Debug:** `logs/game.log` (servidor), `logs/llm.log` (turnos do LLM online), `logs/client.log` (browser), tecla **F3**.  
**Feedback dos jogadores:** `data/feedback.jsonl` (uma linha JSON por envio).  
**Princípio:** mecânica na engine + teste; prosa no LLM; whitelist sempre.

---

## Visão de longo prazo

Polimento FP → cliente Godot opcional → LLM local (Ollama/embed) → Vila/persistência.

---

*Protótipo v2.7.2 — Vila em cenas 2D por local: o raycaster deixou de renderizar a superfície (paredes de catacumba não são praça); cada tile da vila é uma cena composta com NPC grande, legível e interagível exatamente onde os botões do painel funcionam. Corrigido o rótulo "Inimigo" nos NPCs.*
