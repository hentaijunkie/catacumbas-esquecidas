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

- **Vista 1ª pessoa** — raycaster com texturas, billboards **ASCII** (inimigos/altares/baús/loot), combate com clamp de distância (alvo sempre legível). **Vila em 2D** (praça estática). Flash, vinhetas de status e fadiga.
- **Automapa** com névoa de guerra e indicadores de **status** (☠️ veneno, 🩸 sangramento, ⬇️ fraqueza, ❄️ gelo/atordoamento).
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
| Login | Cookie `session` HttpOnly; cada jogador tem seu `GAME` |
| Saves | `saves/<usuario>/slot_1..3.json` |
| API auth | `POST /api/register`, `/api/login`, `/api/logout` · `GET /api/me`, `/api/auth/status` |

### Deploy (VPS / Docker)

```bash
# Exemplo com Docker Compose
export REGISTER_KEY="chave-que-voce-da-aos-testadores"
# export DEEPSEEK_API_KEY="..."   # opcional
docker compose up -d --build
```

Ou em um VPS sem Docker:

```bash
export HOST=0.0.0.0 PORT=8000
export REGISTER_KEY="sua-chave"
python server.py
```

Na frente, use **Caddy** ou **nginx** com HTTPS e, se HTTPS: `SESSION_SECURE=1`.

**Importante:** envie aos testadores (1) o link do site e (2) a chave de convite **só para criar conta**.  
Não publique a chave no repositório.

---

## O que tem no jogo

### Personagem
- 3 classes (Guerreiro / Mago / Ladino) × 4 raças (Humano, Anão, Elfo, Halfling)
- 6 atributos (FOR/DES/CON/INT/SAB/CAR) · progressão até nível 4

### Exploração
- Masmorra procedural (~24 salas) + **andares 2–3** (minichefes) + **superfície (Pedralume)**
- **Ouro** e **loja/NPCs** na Vila; **3 slots de save** (`saves/slot_N.json`)
- Luz/tocha, Pedra de Luz Eterna, fadiga, encumbrance, descanso + wandering
- Lore tablets, altares (rezar/oferecer/saquear), armadilhas, cofres, gazua, **Loot Procedural (Afixos)** + **Identificação** (pergaminho)
- **Dano contínuo:** Gás Venenoso envenena, Lâminas Giratórias causam sangramento (tick por passo)
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
| `server.py` | HTTP + `/api/*` + favicon + serve UI |
| `index.html` | Raycaster 1ª pessoa, automapa, UI, SFX, lerp |
| `balance_sim.py` | Simulação de balance vs Golem |
| `game_log.py` | Logs em `logs/game.log` e `logs/client.log` |
| `LLM_RULEBOOK.md` | Constituição do narrador |
| `artifacts/` | Lore / design notes |
| `logs/` | Debug runtime (gitignored) |
| `.gitignore` | key, logs, pycache, venv |

---

## Desenvolvimento

```bash
python rpg_loop.py --demo
python balance_sim.py
python server.py          # logs em logs/
```

**Debug:** `logs/game.log` (servidor), `logs/client.log` (browser), tecla **F3**.  
**Princípio:** mecânica na engine + teste; prosa no LLM; whitelist sempre.

---

## Visão de longo prazo

Polimento FP → cliente Godot opcional → LLM local (Ollama/embed) → Vila/persistência.

---

*Protótipo v2.2 — multi-sessão, contas com chave de convite, deploy Docker/VPS.*
