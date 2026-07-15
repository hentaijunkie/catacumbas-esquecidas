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
| **Toque/clique na visão** | Bordas viram · centro avança · base recua · **NPC = falar** |
| **D-pad na tela** (📱) | ▲◀▼▶ sobre a visão, aparece em telas de toque |
| Texto / inventário | Interagir, equipar, usar |
| **Descer** / **Subir · Vila** | Andar 2 ↔ 1; entrada ↔ Pedralume |
| Botões de combate | Atacar, poção, magia, fugir |
| `?` | Tutorial |
| `F3` | Debug da vista (distância, saídas, hit) |

- **Vista 1ª pessoa** — raycaster com texturas de parede, billboards com **sprites PNG** em pixel art (inimigos, NPCs, altares, baús, loot, escadas). Combate com clamp de distância (alvo sempre legível e à frente dos props). Flash, vinhetas de status e fadiga.
- **Vila navegável em cenas 2D:** Pedralume é um mapa andável (praça, entrada das catacumbas, forja do Kael, loja da Mira, tenda do Ancião, curandeiro e cabana da bruxa), mas cada local renderiza uma **cena 2D composta** — céu noturno + casario ao fundo, NPC grande e nomeado no centro, props do local (fonte, brasas da forja, arco das catacumbas) e **setas de saída** com o nome do destino. O NPC da sala atual vira botão "Falar" no painel; comprar/vender só na loja da Mira e consertar só na forja.
- **Automapa** com névoa de guerra, **POIs** (altar †, alavanca ⚙, botão ▫, estátua 🗿, escada, cofre) e HUD de progresso dos puzzles do andar. Status do aventureiro: ☠️ veneno, 🩸 sangramento, ⬇️ fraqueza, ❄️ gelo/atordoamento.
- Badge: `online · DeepSeek` ou `offline · template`.
- **Áudio** via Web Audio API: batimento cardíaco com HP crítico, shake prolongado nas magias, impacto grave (hit), áudio de fadiga (pitch e LFO dinâmicos) e **ambientação por local** (vento no andar 1, gotas no 2, cripta no 3, fogo no Abismo; brisa na vila).

### Narração do LLM (opcional)

Sem chave: modo offline (template). Com chave:

- env `LLM_API_KEY` (genérico) ou `DEEPSEEK_API_KEY` (legado), ou
- `key.txt` na raiz (**não commitar** — ver `.gitignore`).

**LLM local ou endpoint custom** (Ollama, llama.cpp, vLLM, Groq, OpenRouter — API OpenAI-compatível):

```bash
# PowerShell:
$env:LLM_BASE_URL = "http://localhost:11434/v1"   # Ollama
$env:LLM_MODEL    = "llama3.1"
$env:LLM_TIMEOUT  = "45"        # opcional (segundos)
# $env:LLM_API_KEY = "..."      # se o endpoint exigir
python server.py
```

Com `LLM_BASE_URL` a chave é dispensável em endpoints locais. Timeout + **retry de rede**
(`LLM_HTTP_RETRIES`, default 2) e o loop de reparo JSON (3 tentativas) + fallback offline
seguram o jogo. Métricas (`api_ok` / `api_erro` / latência) em `logs/llm.log`.

### Contas e multi-jogador

| Item | Como |
|---|---|
| Criar conta | Precisa da **chave de convite** (`REGISTER_KEY` / `INVITE_KEY` / `invite_key.txt`) |
| Login | Cookie `session` HttpOnly (expira em 14 dias); cada jogador tem seu `GAME` |
| Saves | `saves/<usuario>/slot_1..3.json` (3 slots por conta, isolados) |
| Save legado | `savegame.json` (single-player antigo) migra **uma vez** para o 1º slot vazio e vira `savegame.json.migrated` — **não** é reaplicado em contas novas |
| API auth | `POST /api/register`, `/api/login`, `/api/logout` · `GET /api/me`, `/api/auth/status` |
| Métricas LLM | `GET /api/llm/status` (login). Persistidas em `saves/llm_metrics.json` (ou `$SAVE_ROOT/llm_metrics.json`). Se `LLM_STATUS_KEY` estiver setado, envie `?key=` ou header `X-LLM-Status-Key` |

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
- 6 atributos (FOR/DES/CON/INT/SAB/CAR) · progressão até **nível 12** (soft-cap de XP estilo Diablo: monstro muito abaixo do seu nível rende menos/zero XP)

### Exploração
- Masmorra procedural + **andares 1-4**: sidequests (Nascente Envenenada, Câmara do Carrasco), **puzzles** (botões de pressão → Cofre dos Antigos no 1; estátuas giratórias → Santuário no 2; alavancas → Templo no 3), minichefes e o **Abismo** (andar 4) com **"A Lança Perdida"**
- **Ouro** e **NPCs com serviços** na Vila (ver abaixo); **3 slots de save** por conta (`saves/<usuario>/slot_N.json`)
- Luz/tocha, Pedra de Luz Eterna, fadiga, encumbrance, descanso + wandering
- Lore tablets, altares (rezar/oferecer/saquear), armadilhas, cofres, gazua, **Loot Procedural (Afixos)** + **Identificação** (pergaminho)
- **Dano contínuo:** Gás Venenoso envenena, Lâminas Giratórias causam sangramento (tick por passo)
- **Durabilidade e Reparo:** armas e armaduras (inclusive mágicas/afixadas) desgastam em combate, estado visível no inventário (ex.: `23/25`). Conserto perfeito na forja do Kael por **ouro proporcional ao dano**; o **Guerreiro** repara no campo de graça — mas o remendo **corrói a durabilidade máxima** (estilo Diablo).
- Facing inicial aponta para uma **saída real** (entrada jogável em 1ª pessoa)
- **Auto-save:** salva a cada combate, troca de andar, poção de cura, descanso e a cada 12 passos.

### Vila de Pedralume (cenas 2D, NPC tocável)
- **Mira** vende consumíveis (e compra usados) · **Morrigan** vende os 9 grimórios de magia · **Irmão Silas** cura tudo por ouro (HP + veneno + sangramento + fadiga) · **Kael** conserta equipamento · **Ancião Brum** conta a lore
- **Toque/clique no NPC** na cena para conversar; transição vila↔catacumbas com **fade**

### Fama & Conquistas (reputação persistente)
- **Fama** sobe ao derrotar chefes/minichefes e resolver sidequests (limpar a **Nascente Envenenada**, abrir o Templo Esquecido, purificar o Golem). Ela **desbloqueia catálogo exclusivo**: Mira a partir de 30 de Fama (poção maior, espada mágica), Morrigan a partir de 50 (grimório de tempestade).
- **Ficha legível:** contador de Fama + dica do próximo marco (`N p/ itens da Mira` / `N p/ Famoso + grimório na Morrigan`).
- **NPCs reagem à Fama:** Mira, Ancião Brum, Morrigan e os demais mudam o diálogo em ≥30 e ≥50 (texto canônico da engine).
- **Conquistas** com benefício mecânico, **globais por conta** (persistem entre personagens):
  - **Purificador** — purificar o Golem → +5 HP máx, +1 luz  
  - **Famoso** — Fama ≥50 → 10% de desconto nas lojas  
  - **Explorador** — vencer o Guardião da Lança no Abismo  
  - **Sangue de Ferro** — vencer um combate após ter chegado a 1 HP → +2 HP máx  
  - **Mestre das Chamas** — 10 kills com fogo (Bola de Fogo / arma flamejante) → +2 na Bola de Fogo, +1/golpe em armas de fogo  
  - **Sobrevivente Envenenado** — curar veneno 5× (poção ou Silas) → veneno causa −1 dano (mín. 1)  
  - **Ladrão das Sombras** — 10 furtos bem-sucedidos → +10% chance de furto  
  - **Ferro Velho** — quebrar 5 armas → +5 ouro  
  - **Coração de Pedra** — descansar 20 vezes → +2 HP máx  
  Progresso dos trackers na ficha; toast ao desbloquear.

### Combate e magia
- Turnos 100% engine, hordas, 10 magias (scaling, buffs, debuffs, AoE)
- Bestiário com debuffs: **Aranha** (envenena), **Espectro** (fadiga), **Sombra Vampírica** e **Bruxo Abissal** (fraqueza)
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

## Últimas alterações (para jogadores)

Changelog in-game: modal **✨ Novidades** no login (`NOVIDADES` em `index.html` — uma vez por versão).

| Versão | O que mudou |
|---|---|
| **v3.9.2** | **Polimento Visual da Vila 2D** (restauração de pixel art para fundos e props) · UI de setas em botões interativos · Correção visual de overlap de texto (HP/Nome) em billboards inimigos |
| **v3.9.1** | **Hotfix:** restaura `tileSala` / `tileFronteira` (removidas por engano na Vila 2D) — sem elas o automapa quebrava e a vista 1ª pessoa não atualizava · `NPCS_VILA` no cliente · try/catch no automapa |
| **v3.9** | **Vila 2D multi-camadas** · billboards com partículas/HP · fix `const` duplicado · save legado não contamina contas novas · métricas LLM em disco |
| **v3.8** | Conquistas Ladrão / Ferro Velho / Coração de Pedra · volume SFX/Amb · atalhos 1–9 de magia · toast de conquista · `GET /api/llm/status` · SFX de puzzle |
| **v3.6–v3.7** | LLM robusto (timeout/retry/métricas) · automapa com POIs · botões de pressão e estátuas · QoL extra |
| **v3.4–v3.5** | Fama legível · NPCs reativos · ambientação por andar · conquistas com tracker (Sangue de Ferro, Chamas, Veneno) |

---

## Visão de longo prazo

Cliente Godot opcional · mais puzzles · missões de entrega na vila.  
~~LLM robusto~~ ✅ v3.6 · ~~automapa POIs~~ ✅ · ~~estátuas/botões~~ ✅ · ~~conquistas tracker~~ ✅ v3.5 · ~~vila 2D~~ ✅ v3.9.

---

*Protótipo v3.9.1 — hotfix automapa/vista; Vila 2D multi-camadas, billboards, saves multi-user. Antes (v3.8): QoL, conquistas, /api/llm/status.*
