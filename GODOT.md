# 🎮 Guia: Cliente Godot 4 para As Catacumbas Esquecidas

Como migrar do protótipo web (`index.html`) para um cliente Godot 4, **sem reescrever o jogo**.

---

## 0. A decisão de arquitetura (a mais importante)

**O `server.py` continua sendo o jogo. O Godot é só um cliente novo.**

Tudo que faz o jogo funcionar já vive no backend e não muda:

| Fica no servidor (Python) | Vai para o Godot |
|---|---|
| Engine inteira (`rpg_loop.py`): combate, XP, itens, puzzles, Fama | Renderização (3D da masmorra, vila, UI) |
| Narração via LLM + whitelist + anti-injection | Input (teclado/mouse/toque/gamepad) |
| Contas, sessões, saves, multi-jogador | Áudio, partículas, juice |
| Balanceamento (`balance_sim.py`) | Animações e transições |

**Por que não portar a engine para GDScript:** você duplicaria as regras em duas linguagens
(toda mudança de design teria que ser feita 2×), perderia o multi-jogador de graça
(o servidor já serializa/salva por conta), e perderia a integração LLM pronta.
O protótipo web provou que o modelo *cliente burro ↔ servidor autoritativo* funciona —
o Godot só troca o "burro" de lugar.

**Consequência ótima para o seu fluxo:** a expansão de lore, regras e integração LLM que
você vai desenhar acontece toda em `rpg_loop.py`/`LLM_RULEBOOK.md`. O cliente Godot não
precisa saber de nada disso — ele renderiza o JSON que o servidor manda. Design e cliente
evoluem em paralelo sem se bloquear.

---

## 1. Setup (dia 1)

1. Baixe **Godot 4.3+** (a versão *standard*, GDScript — não precisa da .NET).
2. Crie o projeto numa pasta separada do repo atual (ex.: `catacumbas-godot/`), com repo git próprio.
3. Estrutura sugerida:

```
catacumbas-godot/
  autoload/Api.gd          # singleton HTTP (cookie + JSON) — o coração do cliente
  autoload/Estado.gd       # último estado recebido (equivale ao window._estado)
  scenes/
    Login.tscn             # login/registro
    Jogo.tscn              # cena raiz: HUD + troca vila/masmorra/combate
    Masmorra3D.tscn        # GridMap 1ª pessoa
    Vila360.tscn           # panorama rotativo
    CombateUI.tscn         # overlay de combate
    Automapa.tscn          # mapa 2D (SubViewport no canto)
  assets/sprites/          # copie os PNGs de assets/sprites/ do repo atual
```

4. Em *Project Settings*, registre `Api.gd` e `Estado.gd` como **Autoload** (singletons).

---

## 2. O singleton de API (a única ponte com o servidor)

O Godot **não gerencia cookies** — você guarda o `Set-Cookie` do login e reenvia à mão.
Esqueleto do `Api.gd`:

```gdscript
extends Node
## Toda a comunicação com o server.py. Espelha o api() do index.html.

var base_url := "http://127.0.0.1:8000"   # produção: https://catacumbas-...railway.app
var _cookie := ""                          # "session=<token>" capturado no login

signal estado_atualizado(estado)          # HUD/cena assinam isto

func post(rota: String, dados: Dictionary = {}) -> Dictionary:
    var http := HTTPRequest.new()
    add_child(http)
    var headers := PackedStringArray(["Content-Type: application/json"])
    if _cookie != "":
        headers.append("Cookie: " + _cookie)
    http.request(base_url + rota, headers, HTTPClient.METHOD_POST, JSON.stringify(dados))
    var resp: Array = await http.request_completed
    http.queue_free()
    # resp = [result, code, headers, body]
    for h in resp[2]:
        if h.to_lower().begins_with("set-cookie:"):
            _cookie = h.split(":", true, 1)[1].strip_edges().split(";")[0]
    var json: Dictionary = JSON.parse_string(resp[3].get_string_from_utf8()) or {}
    if json.has("estado"):
        Estado.aplicar(json)               # equivale ao aplicar() do index.html
        estado_atualizado.emit(json["estado"])
    return json
```

Uso em qualquer cena: `var r = await Api.post("/api/mover", {"direcao": "frente"})`.

O `Estado.gd` guarda o último `estado` e reemite sinais específicos (`combate_iniciado`,
`mudou_de_andar`, …) — os equivalentes dos hooks do `aplicar()` atual.

> **Contrato:** o formato do JSON é o `serializar_estado()` do `rpg_loop.py`. Ele é o
> "protocolo" entre design e cliente — quando você criar regras novas, só o que aparecer
> ali precisa de trabalho no Godot.

---

## 3. Ordem de migração (incremental, sem big-bang)

O cliente web atual continua funcionando durante TODA a migração (mesmo servidor serve os
dois). Migre nesta ordem — cada etapa é jogável e testável:

1. **Login + HUD** (1ª vitória, ~1 dia): tela de login → `/api/login` → `/api/estado`
   → mostrar ficha (HP/mana/ouro/fama) com `Label`s. Valida o Api.gd inteiro.
2. **Automapa** (2D fácil): desenhar `estado.mapa.rooms` num `Node2D` com `draw_rect`
   — port direto do canvas atual.
3. **Masmorra 3D** (o salto de qualidade — seção 4).
4. **Combate**: overlay UI (botões → `/api/combate`), inimigo como `Sprite3D` na cena 3D.
5. **Vila 360**: um `TextureRect` com o `vila_panorama.png` deslocando o `region_rect`
   — port 1:1 da lógica atual (`vilaAngle`, hotspots a cada 60°, W entra via `/api/entrar`).
6. **Narrativa/log + input de texto** → `/api/interagir` (a parte LLM não muda NADA).
7. **Juice**: partículas, shaders de dano, áudio posicional, tweens.

---

## 4. A masmorra em 3D de verdade (a grande vitória)

Troque o raycaster de canvas por **3D real grid-based** (estilo Legend of Grimrock /
Shining in the Darkness):

- **`GridMap`** + `MeshLibrary` com 3 peças: parede, chão, teto (um cubo texturizado cada).
  Ao receber `estado.mapa.rooms`, preencha as células: sala visitada = chão+teto, borda
  sem `exit` = parede. É literalmente o `buildWalkable()` atual escrevendo num GridMap.
- **Câmera** (`Camera3D`) no centro da célula do jogador, altura ~1.6. Movimento em grade:
  `create_tween()` animando posição (0.25s) ao confirmar `/api/mover`, e rotação de 90°
  ao `/api/virar`. Input otimista: anima já, e reconcilia se o servidor recusar (parede).
- **Inimigos/props/NPCs**: `Sprite3D` com `billboard = true` usando os MESMOS PNGs de
  `assets/sprites/` — o estilo pixel-art-em-3D (Grimrock/DUNGEON ENCOUNTERS) fica ótimo
  e você não precisa de nenhum asset novo no dia 1.
- **Atmosfera por andar**: `WorldEnvironment` com fog + `OmniLight3D` presa à câmera
  (raio = luz da tocha do estado — a escuridão vira mecânica visual de graça).
- Nada de raycasting manual: o Godot faz oclusão, perspectiva e iluminação sozinho.

---

## 5. Ajustes necessários no servidor (pequenos)

1. **CORS** — em dev, o Godot roda em `localhost` sem origem web, então requests diretos
   funcionam. Para o **export Web** em produção, sirva o build exportado pelo próprio
   `server.py` (uma rota `/godot/` estática) → mesma origem, sem CORS e o cookie funciona
   como hoje. Evite hospedar o build em outro domínio (aí precisaria de CORS +
   `SameSite=None` no cookie).
2. **Headers do export Web**: Godot 4 com threads exige `Cross-Origin-Opener-Policy:
   same-origin` e `Cross-Origin-Embedder-Policy: require-corp` nas respostas — 2 linhas
   no `_send()` quando servir `/godot/`. (Ou exporte sem threads no 4.3+ e ignore isso.)
3. **Nada mais.** As rotas `/api/*` já são JSON puro e agnósticas de cliente.

---

## 6. Export final

| Alvo | Nota |
|---|---|
| **Desktop (Win/Linux)** | Export direto; aponte `base_url` para o Railway. O jogo vira um .exe que joga online. |
| **Web** | Servido pelo `server.py` (seção 5). Substitui o `index.html` quando estiver maduro. |
| **Mobile** | Export Android é simples; o layout de UI precisa de `Control`s responsivos desde o início (use anchors, não posições fixas). |

---

## 7. Armadilhas conhecidas (aprenda com o protótipo)

- **Não deixe o cliente "saber" regras.** Se o Godot calcular dano/preço/loot localmente,
  você recria a classe de bugs que caçamos a conversa inteira (cliente e servidor
  divergindo). Cliente renderiza, servidor decide. Sempre.
- **Um request por vez por sessão**: o servidor tem lock por sessão; no cliente, desabilite
  input enquanto `await Api.post(...)` não volta (o equivalente do `_inputBusy`).
- **Latência do LLM**: `/api/mover` com narração online leva 2–4s. Anime o passo
  imediatamente e mostre a narrativa quando chegar (o estado mecânico vem junto — a UI
  nunca fica travada esperando prosa).
- **Versione o contrato**: quando mudar `serializar_estado`, rode o cliente web antigo
  como teste de regressão — se ele quebrar, o Godot também quebraria.

---

*Criado na v3.9.6. O protótipo web (`index.html`) permanece como cliente de referência
e regressão até o Godot atingir paridade.*
