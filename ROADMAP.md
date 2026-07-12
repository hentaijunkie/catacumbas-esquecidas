# 🗺️ Roadmap — As Catacumbas Esquecidas

Cada bloco **Feito** de mecânica foi validado por `python rpg_loop.py --demo` e, quando
cabe, por `python balance_sim.py`.

---

## ✅ Feito

### Núcleo → combate tático (v0.1–v0.9)
- Loop engine×LLM com whitelist e reparo; `--demo` offline.
- Mapa procedural, web stdlib, balance_sim, classes Diablo-like, rulebook.
- Magias com scaling/buffs; hordas; backstab; cura fora de combate.

### Campanha viva (v1.0)
- Raças + atributos; lore tablets; luz/tocha; descanso + wandering.
- Purificar o Golem (Coração + Sabedoria).

### Exploração tensa (v1.1)
- Fadiga + encumbrance; Ladino (esconder/gazua/furtar); altares; multi-nível (andar 2).

### Vista 1ª pessoa + debug (v1.2)
- Raycaster canvas + automapa; `/api/virar`; F3 debug.
- Logs em arquivo (`game_log.py` → `logs/`).

### Polimento FP + superfície + qualidade (v1.3)
- **Entrada jogável:** facing inicial aponta para saída real (`facing_para_saida`).
- **Portais de névoa** na fronteira (não corredor vazio “trevas”); paredes de pedra com tijolos.
- **Parede na cara:** altura máx. ~76% da tela + dist mínima + textura legível.
- **Lerp** suave ao andar/virar (cliente).
- **SFX** mínimo (passo, virar, parede, combate, escada) via Web Audio.
- **Sprites** de inimigos/loot/escada mais legíveis.
- **Subir / Vila:** `subir_escada` (2→1 e entrada→Pedralume); `descer` reentra da superfície.
- Snapshot de andares (`pilha_andares`) ao descer.
- **Logs** incluem `exits` da sala em novo jogo e mover bloqueado.
- **favicon** SVG (sem 404).
- **`.gitignore`** (key, logs, pycache, venv).

### Texturas, UI Avançada e Renderização 3D Contínua (v1.4)
- Texturas reais de arquivos locais (`/assets/wall.jpg`, `door.jpg`) servidas via servidor HTTP.
- Motor 3D avançado: raycaster agora renderiza a planta completa das salas (mesmo inexploradas), garantindo visão contínua e imersão profunda (sem telas azuis bloqueando corredores).
- Barras de vida (HP) visíveis acima de inimigos no modo FP.
- Animações (pulso/balanço) nos inimigos em combate, com posição perfeitamente centralizada no 3D e correção da oclusão (inimigos não somem em salas fronteiriças).
- Novas magias (Nuvem de Veneno, Atordoar) com gestão de Debuffs na engine.
- Recompensa ao finalizar o jogo: Vila entrega Pedra de Luz Eterna.

### Hotfixes (v1.4.1)
Validados por `--demo`, testes de pixel-diff no canvas e jogada real (logs 11/jul 19:21 limpos,
incluindo combate com o Golem colado na parede — o cenário do bug).
- **Billboards de inimigo/loot voltaram:** `buildWalkable` usava só `all_rooms` (estrutural,
  sem flags `inimigo`/`loot`); agora sobrepõe os dados das salas visitadas.
- **Alvo de combate sempre visível:** sprite do combate era engolido pelo z-buffer ao encarar
  parede (dist < 0.9); agora clampa a distância e ignora oclusão em combate.
- **Barra de HP do inimigo correta em andares fundos:** `combate_json` usava HP base do
  bestiário como máximo (ex.: "14/12"); agora usa o `hp_max` escalado do combate. Promoção
  de extra em horda também atualiza `hp_max`.
- **Botão "Poção Mana" no combate:** checava nome numa lista de objetos; agora usa `it.id`.

### Dano continuo, bestiario de debuff e viewFlash (v1.5)
- **Veneno no JOGADOR** (dano continuo): `p["veneno"]={dano,passos}` tica por passo de
  exploracao E por round de combate; expira sozinho; **Pocao de Cura e antidoto**.
  Morte por veneno tratada fora e dentro de combate. Prompt do LLM informa `ENVENENADO`.
- **Armadilha nova - Gas Venenoso:** dano imediato + veneno; Ladino desarma como sempre.
- **Bestiario +2:** **Aranha da Cripta** (mordida envenena, 35%) e **Espectro Gelido**
  (toque drena calor: +1 fadiga/acerto; defesa 2 = fraco a magia). Garantidos no andar 2;
  aranha entra na pool leve do andar 1.
- **viewFlash:** flash colorido na vista FP - cor da escola ao conjurar (mapa `COR_MAGIA`),
  vermelho ao levar dano, verde ao curar, azul ao repor mana.
- **balance_sim andar 2:** simulador generalizado; cenarios novos com atrito.
- **Cobertura `--demo`:** serializacao superficie/pode_subir/pode_descer + testes de veneno.
- **Logs:** linhas HTTP de `POST /api/log` nao vao mais pro `game.log`.
- Rulebook v1.5: secao de passivos com veneno/toque gelido (narrar, nunca calcular).
- **Fix automapa cortado:** centralizacao segura (`margin:auto` no canvas),
  `max-height` 260px e **auto-scroll que segue o token** do jogador.

### Layout, UX de combate e Save State (v1.6)
- **Novo layout 2 colunas:** coluna esquerda larga (~70%) com visao 3D + narrativa/input
  embaixo; coluna direita (~30%) com automapa no topo + stats + inventario + combate.
  Max-width do grid subiu de 1080px para 1280px; viewport 3D de 420px para 520px.
- **Debuffs dos inimigos visiveis:** o painel de combate agora exibe os debuffs ativos
  no alvo (ex.: "Veneno (3)"), com `combate_json()` enviando a estrutura completa.
- **Vignette de veneno:** efeito visual verde pulsante nas bordas da visao 1a pessoa
  quando o jogador esta envenenado (CSS animation + toggle via estado).
- **Retomar sessao (`GET /api/estado`):** F5 durante a jogatina recupera o estado
  completo (HP, posicao, combate) sem resetar a run.
- **Limpeza do `door.jpg`:** textura de porta removida do codigo JS; o raycaster usa
  exclusivamente `wall` e `wallDark` com visao continua profunda.
- **Clamp de sprites:** sprites de combate sao clampados para nunca sair da tela;
  sprites de exploracao fora do campo de visao nao sao desenhados (sem artefatos nas bordas).
- Rulebook v1.6: narracao de veneno mais vivida (sintomas sensoriais explicitos).

### Persistência e UI Sensorial (v1.7)
- **Save / Load em arquivo:** persistência completa através de `savegame.json` e dos endpoints `GET /api/save` e `GET /api/load`. Converte e protege as chaves tuplas do dicionário do mapa para compatibilidade com o formato JSON. O estado sobrevive a reboots do servidor local.
- **UI Sensorial (Poções):** `viewFlash` vívido e específico (verde brilhante) ao consumir Poção de Cura, e azul radiante ao consumir Poção de Mana.
- **UI Sensorial (Tremedeira no Combate):** Animação de *screen shake* na visão 3D ao efetuar ataques físicos ou lançar magias ofensivas.
- **UI Sensorial (Fadiga):** Implementação de vinheta escura intermitente e áudio procedural de "respiração pesada" no `WebAudio API` quando a fadiga atinge valores altos (>= 3).
- **Badges para Debuffs:** Melhoria estética substituindo o texto puro por ícones descritivos (☠️ Veneno e ❄️ Atordoado / Gélido), visíveis tanto nas métricas do jogador quanto nas condições do adversário.
- **Balanceamento do Andar 2:** Testes confirmaram que hordas com aranhas e espectros mantêm a tensão desejada com desgaste de sobrevivência de ~12 HP. No changes na progressão e poder.

### Auto-save, Novos Debuffs e UI Refinada (v1.8)
- **Auto-save:** O servidor agora salva automaticamente em `savegame.json` (best-effort) após o fim de cada combate e sempre que o jogador muda de andar (sobe ou desce a escada).
- **Bestiário +1 (Sombra Vampírica):** Novo inimigo que causa o debuff de `Fraqueza` (cada acerto reduz em 1 o dano físico do jogador até o fim do combate, com máx. 3 stacks). Inimigo presente no Andar 2.
- **Armadilha +1 (Lâminas Giratórias):** Nova armadilha de piso que causa dano base alto e deixa o jogador com status de `Sangramento` (Dano contínuo, ou DoT).
- **Cura de Sangramento:** O sangramento cessa com o tempo, ao usar uma Poção de Cura, ou ao realizar um descanso num local seguro.
- **Melhorias de Áudio (WebAudio API):**
  - O SFX `hit` ganhou impacto grave extra e agora toca apenas nos ataques físicos.
  - Magias receberam o shake mais prolongado.
  - O áudio da fadiga agora varia sua altura (pitch bend) entre 30Hz e 55Hz num LFO lento de 0.25Hz, simulando o ritmo irregular da exaustão pesada.
  - Adicionado o som de um **Batimento Cardíaco (Heartbeat)** constante aos \~72 bpm toda vez que o jogador está com HP crítico (<30%) durante um combate.
- **Fadiga visual (Vignette):** A vinheta de fadiga agora aplica um sombreamento progressivo na tela dividida em 3 intensidades (`box-shadow`), respondendo dinamicamente às fadigas 3+, 5+ e 7+.
- **Novos badges:** `🩸 sangramento` e `⬇️ fraqueza`.

### Auto-save robusto, VFX de debuffs e verificação de persistência (v1.9)
- **Auto-save mais robusto:** além de fim de combate e troca de andar, agora também salva
  ao usar Poção de Cura (momento crítico com veneno/sangramento ativos), ao descansar
  (checkpoint canônico) e periodicamente a cada 12 passos de exploração.
- **VFX Sangramento:** vinheta vermelha pulsando rápido (`#bleedVignette`, ritmo mais
  agudo que a do veneno — ferida ativa, não intoxicação lenta).
- **VFX Fraqueza:** a vista 1ª pessoa dessatura progressivamente com os stacks
  (`filter: grayscale()/brightness()` no canvas, até 3 stacks) — a força se esvaindo,
  não uma cor de status.
- **Estado do prompt do LLM:** `estado_para_prompt` agora informa `SANGRANDO` e
  `FRAQUEZA` a cada turno (antes só `ENVENENADO` existia) — o narrador finalmente pode
  descrever os dois debuffs novos com base em fatos, não em silêncio.
- **Rulebook v1.9:** seção de passivos ganhou Sangramento (ferida física, distinta do
  veneno) e Fraqueza (força drenada, nunca cita o número exato).
- **balance_sim — debuffs empilhados:** cenário novo com veneno+sangramento já ativos
  entrando na luta contra a Sombra Vampírica (nv3-4, incluindo ferido + 1 poção). Todas
  as classes vencem — a luta é curta (Sombra tem 14 HP), então a tensão real dos DoTs
  empilhados está na exploração *depois* do combate, não na letalidade instantânea
  dentro dele. Sem retune necessário.
- **Persistência — verificado, não mudou:** round-trip determinístico confirma que
  save/load já preserva debuffs do jogador (veneno/sangramento/fraqueza_stacks/buffs/
  escondido), o estado exato do combate (debuffs do inimigo, extras de horda) e
  posição/facing/profundidade — inclusive masmorra aninhada em `pilha_andares`
  (chaves tupla). O auto-save já salvava o `GAME` inteiro; não havia lacuna real.

### Hotfixes de revisão (v1.9.1)
Revisão completa de código (engine + servidor + cliente). Bugs corrigidos, todos verificados
por `--demo`, testes de round-trip e cliques reais no browser:
- **CRÍTICO — magias em combate quebradas na web:** os botões mandavam `magia_<id>`, mas o
  contrato da engine é `magia:<id>` → toda conjuração respondia "Comando inválido". O prefixo
  errado entrou junto com o screen shake (v1.7/v1.8). Passou despercebido jogando de Guerreiro
  (0 mana, botões nem habilitam).
- **Botão "? Ajuda" morto:** apontava para `#dlgAjuda` (inexistente — o overlay é `#ovAjuda`);
  cada clique dava TypeError. Voltou a usar `toggleAjuda()`.
- **Botões Salvar/Carregar mortos:** chamavam `fetchApi()`, função que não existe em lugar
  nenhum → ReferenceError. Agora usam `fetch` direto e logam o resultado na narrativa.
- **Farm infinito no andar 2:** re-descer regenerava a masmorra do zero (loot re-spawnava,
  inimigos voltavam com XP). Agora `state["andares_gerados"]` guarda o andar explorado ao
  subir e o reutiliza ao descer — salas saqueadas/limpas persistem (e sobrevivem ao save).
- **Áudio de fadiga estourado:** o LFO (±1 full-scale) estava ligado direto no GANHO sem
  profundidade → volume oscilava entre −0.45 e +1.55 (fase invertida, ~25× mais alto que os
  sfx). Religado à FREQUÊNCIA via depth gain (42 ±12 Hz, o pitch-bend 30–55 Hz que o roadmap
  descrevia), ganho fixo 0.08.
- **Heartbeat defasado:** o check de HP crítico usava `combatendo` da resposta ANTERIOR —
  não ligava ao entrar em combate já ferido e vazava uma ação após vencer. Usa `resp.combate`.
- **Save atômico:** `savegame.json` era truncado antes de escrever (crash no meio = save
  corrompido). Agora grava em `.tmp` + `os.replace`; `/api/save` reusa `salvar_estado()`.
- **Painel de combate:** sangramento e fraqueza agora aparecem ao lado do veneno (ticam por
  round, mas ficavam invisíveis durante a luta).

### Robustez e contrato (v1.9.2) — **atual**
As 7 melhorias sugeridas na revisão, todas com teste:
- **Contrato de escolhas com teste `--demo`:** novo teste exercita exatamente os strings que
  os botões da web enviam (`atacar/pocao/pocao_mana/fugir/magia:<id>`); prefixo de magia
  errado agora falha ALTO ("Prefixo de magia inválido — o contrato é 'magia:<id>'") em vez
  do genérico "Comando inválido" que escondeu o bug da v1.7.
- **`reidratar_estado()` pós-load:** sets (exits/armaduras) viram listas no JSON e não
  voltavam; o load agora reidrata a masmorra ativa, os snapshots da `pilha_andares` e o
  cache `andares_gerados`. `from_json_safe` documenta a limitação.
- **Lock no save:** `threading.Lock` em `salvar_estado()` — `ThreadingHTTPServer` podia
  serializar o `GAME` enquanto outra thread o mutava.
- **`/api/save` e `/api/load` viraram POST** (têm efeito colateral); o GET antigo morreu.
  Carregar por cima de um jogo ativo agora pede **confirmação** na UI.
- **Volume do sfx `hit`:** 0.55 → 0.15 (estava ~10× acima dos demais sfx).
- **Debuffs não transferem na promoção de horda:** a Nuvem de Veneno do líder morto não
  "pula" mais para o extra promovido (`cb["debuffs"]` limpo na promoção).
- **Seed do andar 2 com `zlib.crc32`** (não `hash()`, que é randomizado por processo para
  strings): layout determinístico entre restarts para qualquer tipo de seed.

### Loot Procedural (Afixos) (v1.10)
- **Geração Dinâmica:** Itens mágicos com prefixos e sufixos gerados dinamicamente com base em chance que escala com o Andar.
- **Raridade visual:** A interface agora utiliza as cores de cada modificador para exibir nomes de equipamentos brilhando/coloridos.
- **Cache seguro:** `state["itens_gerados"]` criado para garantir que os dados de loot mágico gerado e encontrado persistam nos `save/load`.
- **Constituição Narrativa:** LLM_RULEBOOK.md atualizado para garantir que o narrador use termos poéticos ao descrever armas (sem mencionar os valores numéricos gerados pela engine).

### Hotfix loot procedural + robustez (v1.10.1)
Revisão de bugs pós-v1.10; todos cobertos por `--demo`:
- **Afixos nos stats reais:** `dano_bonus`/`defesa_bonus`/`peso_override`/`hp_bonus` passam a gravar `dano`/`defesa`/`peso`/`hp_bonus` utilizáveis; mithril deixa a armadura `leve`.
- **Lookup unificado:** `dano_da_arma`/`defesa_total`/`carga_total` usam `get_item_data(..., state)` — arma afixada não zera mais o dano.
- **Empilhar consumíveis no saque:** `["pocao_mana","pocao_mana"]` entrega 2; sala não “some” loot se o id já existia no inv.
- **Web equipar/usar:** aceita ids em `itens_gerados` (não só `ITENS`).
- **RNG determinístico:** loot afixado deriva de seed+andar+posição (reproduzível).
- **Efeitos de afixo no combate:** fogo (+1/golpe), veneno (30% debuff), gelo (25% atordoar); armadura das Sombras +1 check furtivo; Vitalidade sobe `hp_max` ao vestir.
- **Whitelist/classificador offline** cientes de itens procedurais; null-safe em serialização.
- **UI fadiga** alinhada a `FADIGA_MAX=3` (1/2/3); barra de luz “eterna” p/ a Pedra.
- **Lock de GAME** no POST (ThreadingHTTPServer) além do save atômico.
- **Typo** na mensagem das Lâminas Giratórias.

### Identificação de itens mágicos (v2.0)
Fecha o plano “Afixos + Identificação” (afixos já existiam na v1.10; faltava o fog of war):
- **Não identificado por padrão:** loot com afixo nasce `identificado: False` + `nome_misterioso`.
- **Display:** inventário/prompt/serialização usam nome genérico e `propriedades desconhecidas`
  até revelar (stats reais já valem se equipar — a engine é dona dos números).
- **`pergaminho_identificacao`:** consumível no loot do andar 1 (1) e 2 (2); não se “usa” solto.
- **Ação `identificar`:** whitelist + executor + `/api/identificar` + botão na UI.
- **Rulebook + system prompt:** sensação vaga ok; nome do afixo só após a engine.
- **Classificador offline:** “identifico / revelo / decifro”.
- **`--demo`:** oculto→pergaminho→revela; falha sem pergaminho; flag no JSON; loot table.

### Ladino auto-identifica (v2.0.1)
Stretch da identificação, coerente com `disarma` (vê o que outros não veem):
- **`CHANCE_AUTO_IDENTIFICAR` (0.40)** + 0.05×mod DES, clamp 15–70%, só se `player.disarma`.
- Rola **por item afixado** no `saquear_sala` (RNG seed+pos, stream separado do afixo).
- **Não consome** pergaminho; mensagem: “Seu olhar treinado decifra o artefato: …”.
- Guerreiro/Mago nunca rolam. Cobertura em `--demo`.

### Vila, Andar 3 e multi-save (v2.1)

### Polish visual raycaster + Vila (v2.1.1)
- **Combate:** alvo fixo a ~1.55u à frente da câmera; escala máx. 52% da altura; z-buffer ignorado no combate.
- **Billboards ASCII:** glifos por `inimigo_id` (S/a/E/v/G…), † altar, □/■ cofre, $ loot, ▲/▼ escadas.
- **Serialização:** rooms enviam `inimigo_id`, `altar`, `cofre`, `escada*`; combate envia `id`.
- **Vila 2D:** `na_superficie` desenha praça estática (casas, fonte, Mira/Ancião, placa LOJA) em vez do céu+sol do raycaster.
- **Automapa:** mesmos glifos ASCII nas salas visitadas.

### Multi-sessão + contas + deploy (v2.2) — **atual**
- **Contas:** registro com chave de convite (`REGISTER_KEY` / `invite_key.txt`); senha PBKDF2; cookie `session`.
- **Multi-jogador:** cada sessão tem `state`/`combate` isolados; saves em `saves/<user>/`.
- **UI:** overlay login/criar conta; badge de usuário; logout.
- **Deploy:** bind `HOST`/`PORT` (default `0.0.0.0:8000`); `Dockerfile` + `docker-compose.yml`.

---

### (histórico) Vila, Andar 3 e multi-save (v2.1)
Fecha o bloco médio do roadmap (exceto Godot/LLM local):

**NPCs / loja em Pedralume**
- **Ouro** no player (`OURO_INICIAL=20`); drop por inimigo (`BESTIARIO.ouro`).
- **`LOJA_VILA`**: poções, tocha, pergaminho, gazua, chave — comprar/vender só na superfície.
- **NPCs**: Mira (loja) e Ancião Brum (lore); ação `falar`.
- UI: painel loja+NPCs, ouro na ficha, botão Vender no inventário na Vila.
- Ações: `comprar` / `vender` / `falar` + `/api/*` + classificador offline.

**Andar 3 + minichefes**
- `MAX_PROFUNDIDADE = 3`; escada no andar 2 desce ao 3.
- **Capitão de Ossos** (câmara + horda) e **Sacerdote do Lodo** (único, veneno).
- Loot premium no 3; escala de stats por profundidade já existente.

**Persistência multi-sessão**
- 3 slots em `saves/slot_1..3.json` + `saves/index.json` (metadados).
- Auto-save no slot ativo; UI Salvar/Carregar abre seletor de slots.
- Migração: `savegame.json` legado → slot 1 se vazio.

---

## Proximos passos (curto prazo)

### Expansão da Gameplay
- [ ] Nenhum item de curto prazo pendente — próxima leva: Godot / LLM local (longo prazo).

---

## 💡 Médio / longo prazo

| Tema | Notas |
|---|---|
| Cliente Godot 4 | Mesmo `server.py`; export Web |
| LLM local | Ollama / llama.cpp embutido |

---

## Limitacoes conhecidas

- Sessões de jogo em memória: reiniciar o servidor derruba runs ativas (saves em disco persistem).
- Narracao offline = template; online depende de DeepSeek e latencia.
- Guerreiro endgame continua forte vs Golem.
- Audio e "beep" sintetico (sem arquivos de som).
- Cadastro aberto a quem tiver a chave de convite (não há papéis admin/moderador).

---

## Checklist de feature

1. Engine + dono do estado  
2. `ACOES_PERMITIDAS` + validação + executor  
3. `--demo` verde  
4. `balance_sim` se afetar combate  
5. Rulebook + system prompt  
6. Web se precisar de UI  
7. README + este roadmap  

---

*Última atualização: v2.2 — multi-sessão, contas com chave de convite, Docker/deploy.*
