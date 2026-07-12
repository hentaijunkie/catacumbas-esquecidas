# 📜 Expansão de Regras e Universo — As Catacumbas Esquecidas (v0.7+)

**Filosofia inabalável do projeto (reafirmada):**
- **A engine é a única dona do estado e das regras.** HP, mana, inventário, posição, mapa, buffs, armadilhas, combate, loot, XP, nível — tudo vive em Python, determinístico e testável.
- **O LLM (DeepSeek) só narra.** Ele recebe o estado completo da engine a cada turno e produz prosa rica, imersiva e sensorial. Nunca decide dano, nunca inventa itens, nunca altera mecânicas.
- **Whitelist + loop de reparo anti-alucinação** permanece sagrado. Qualquer sugestão do LLM que não estiver na whitelist de ações ou no estado conhecido é rejeitada automaticamente e o LLM é re-promptado com o erro.
- **Testabilidade acima de tudo:** toda mecânica nova deve passar no `python rpg_loop.py --demo` e idealmente no `balance_sim.py`.

Inspirado em:
- **Basic Fantasy RPG** (leveza old-school, 6 atributos clássicos, classes simples, bônus/penalidades claros, regras de exploração e armadilhas).
- Dicas de criação de sistemas (WikiHow, ABCDorPG, NDGames, Reddit r/rpg_brasil): simplicidade elegante, player agency real, integração mecânica-narrativa, balanceamento por simulação, remoção do desnecessário antes de adicionar.
- Molde Diablo 1 (identidade forte de classe, loot significativo, progressão tensa até o chefe).

---

## 1. Expansão do Universo (Lore para o LLM usar)

O LLM ganha contexto rico sem poder inventar fatos.

### 1.1 A Vila e o Gancho
- **Nome da Vila:** Pedralume (ou Vila do Rio Seco).
- **Lenda local:** "Há séculos o Rio Vivo fluía generoso. Então veio o Silêncio. O Golem de Barro — outrora guardião sagrado do fluxo — enlouqueceu e selou as nascentes nas catacumbas. A terra seca, as crianças choram, os anciãos sussurram que só um herói com 'coração de rio' pode libertar as águas."
- **Hook inicial:** O ancião da vila entrega ao jogador uma **Chave de Ferro enferrujada** (abre o primeiro cofre) e diz: "Desça. Ouça o rio chorando. Traga-o de volta ou morra tentando."

### 1.2 Lore Central das Catacumbas
- **Civilização antiga:** Império de Aqualith (ou "Povo da Pedra Cantante"). Construtores de templos submersos que canalizavam o rio como poder sagrado.
- **O Golem:** Não é apenas chefe final. É o **Guardião Corrompido** — um elemental de barro misturado com a essência viva do rio, aprisionado por um ritual de sacrifício que deu errado. Derrotá-lo (ou purificá-lo) decide o destino do rio.
- **Temas recorrentes para narração:**
  - Água vs. estagnação / corrupção
  - Memória da terra (paredes que "lembram" e sussurram)
  - Sacrifício vs. ganância
  - Ecos do passado (visões, vozes, runas que brilham)

### 1.3 Bestiário Temático (engine controla stats e comportamento)
- Morcego Gigante (voa, ataca de surpresa no escuro)
- Cultista do Lodo (cura aliados, invoca lodo que atrasa movimento)
- Zumbi de Raiz (lento, mas regenera se não queimado)
- Elemental Menor de Terra (imune a certos danos, vulnerável a água/magia arcana)
- Golem de Barro (chefe — fases: normal → rachado → fúria final)

### 1.4 Itens com Lore (engine armazena flavor base)
Cada grimório, arma mágica ou item especial tem um `lore_id`. O LLM recebe o texto base + instrução: "Embeleze poeticamente, conecte com a cena atual, mas não mude efeitos."

Exemplo para grimório:
> "As páginas cheiram a algas secas e ozônio. Runas azuis pulsantes formam o nome 'Raio do Rio'."

---

## 2. Novas Mecânicas (todas implementadas na Engine)

### 2.1 Raças (escolha no início do jogo — engine aplica modificadores permanentes)

| Raça     | Bônus Atributos          | Habilidades Especiais (engine)                  | Restrições / Flavor                     | Recomendado para |
|----------|---------------------------|--------------------------------------------------|-----------------------------------------|------------------|
| **Humano**   | +1 em um atributo à escolha | Adaptabilidade: +5% XP ganho                    | Nenhum                                  | Qualquer classe  |
| **Anão**     | +2 Con, -1 Car            | Visão na penumbra, +2 em checks vs armadilhas de pedra/pressure plates, bônus vs veneno | Não usa bem magias complexas (penalidade leve em mana ou Int) | Guerreiro, Ladino |
| **Elfo**     | +2 Int, -1 Con            | Visão no escuro, +1 mana por nível, bônus em checks de percepção | Armadura pesada reduz movimento mais | Mago, Ladino     |
| **Halfling** | +2 Dex, -1 For            | Sorte (reroll natural 1 em checks de Dex 1x por combate), +3 em disarm/picklock | Não carrega bem peso pesado             | Ladino           |

**Implementação:** `race.py` ou dentro de `player.py`. Modificadores aplicados uma única vez na criação. Salvam no estado.

### 2.2 Sistema de Atributos (6 clássicos — inspirado Basic Fantasy)

Gerados por **3d6** (engine) ou array fixo + modificador racial.

**Tabela de bônus/penalidade (igual Basic Fantasy):**
- 3: -3 | 4-5: -2 | 6-8: -1 | 9-12: 0 | 13-15: +1 | 16-17: +2 | 18: +3

**Usos na engine (exemplos):**
- **Força:** Dano melee, carregar peso (encumbrance), forçar portas/trancas fracas.
- **Destreza:** Ataque ranged, AC (armadura + Dex), Iniciativa, disarm traps, pick locks, furtividade.
- **Constituição:** HP máximo, resistência a veneno/gás/DoT.
- **Inteligência:** Mana máximo, número de grimórios que pode aprender simultaneamente, identificar itens mágicos.
- **Sabedoria:** Detectar armadilhas secretas/ilusões, saving throws vs mental/encantamento, percepção geral.
- **Carisma:** Futuro (reações de NPCs na vila ou cultistas que podem ser persuadidos a recuar).

**Engine expõe:** `player.get_bonus("forca")`, `player.get_saving_throw("mental")` etc.

### 2.3 Combate Aprimorado (ainda 100% engine)

- **Iniciativa:** `d20 + Dex_bonus + class_bonus`. LLM narra a ordem dramaticamente ("O morcego mergulha primeiro das sombras...").
- **Cobertura e Posicionamento:** Se o mapa suportar (coordenadas), engine dá +2 AC contra ataques ranged se houver pilar/parede entre.
- **Flanco:** +1 ou +2 para atacar se aliado está em posição oposta (fácil de checar em grid).
- **Moral dos Monstros:** Engine tracka. Se HP < 30% e "líder" morto → chance de fuga. LLM descreve hesitação ou retirada dramática.
- **Dano não-letal (Subdual):** Opção "subdue" — dano vai para "non_lethal_damage". Se chegar a 0, inimigo é nocauteado (não morto). Útil para Ladino ou roleplay.
- **Ataque pelas costas (Backstab):** Ladino ganha bônus massivo se atacar sem o alvo ter agido ou de invisibilidade.

### 2.4 Magia — Escalonamento e Duração (maior evolução estratégica)

**Spells como dados na engine** (dict/json):
```python
spells = {
    "firebolt": {
        "name": "Raio Flamejante",
        "level": 1,
        "mana_cost": 4,
        "target": "single",
        "effect": {"type": "damage", "base": 6, "scaling": "level*2", "ignore_armor": True},
        "lore": "..."
    },
    "shield": {
        "name": "Escudo Arcano",
        "level": 1,
        "mana_cost": 3,
        "target": "self",
        "effect": {"type": "buff", "stat": "ac", "value": +4, "duration_turns": 5},
        ...
    },
    "drain_life": {...},
    "cure_light": {...},
    "magic_missile": {"ignore_armor": True, "auto_hit": True},
    "fireball": {"target": "aoe_room", "effect": ...}  # engine precisa suportar
}
```

**Novidades:**
- **Escalonamento por nível do caster:** `dano = base + (nivel_caster * scaling_factor)`
- **Buffs com duração:** engine mantém lista `active_buffs = [{"id": "shield", "turns_left": 4}]`. Todo turno decrementa.
- **Novos spells sugeridos (prioridade curta):**
  1. **Escudo Arcano** (buff AC)
  2. **Toque do Rio** (cura + remove veneno leve)
  3. **Mísseis Mágicos** (ignora armadura, auto-hit — perfeito para Mago frágil)
  4. **Bola de Fogo** (AoE simples — todos inimigos na sala levam dano reduzido)
  5. **Drenar Vida** (dano + cura self)
  6. **Luz Eterna** (cria fonte de luz temporária — engine atualiza light_radius)

**Grimórios:** Ao encontrar, engine adiciona ao spellbook se o personagem tiver Int suficiente e slot livre. Mago pode "preparar" spells (limite por nível).

### 2.5 Exploração e Sobrevivência (enriquece dramaticamente a narração)

**Luz e Escuridão (altamente recomendado)**
- Itens: Tocha (30 turnos), Lanterna a óleo (100 turnos), Pedra de Luz (recarregável?).
- Engine tracka `light_sources` e `effective_light_radius`.
- Efeitos:
  - Sem luz: névoa de guerra muito mais densa, -4 em todos checks de percepção/disarm, chance maior de "surpresa" de monstros.
  - Luz fraca: penalties menores.
- LLM adora descrever: "A tocha crepita fracamente. Sombras alongadas dançam nas paredes úmidas. Você ouve água pingando... ou é respiração?"

**Descanso e Fadiga**
- Ação `descansar` só disponível em salas "seguras" (sem inimigos vivos + engine flag).
- Engine: cura parcial de HP e mana (ex: 30-50%), avança contador de tempo.
- Risco: roll de wandering monster (tabela por profundidade).
- **Fadiga:** Após X turnos sem descanso de qualidade, engine aplica debuff cumulativo (-1 em todos checks e AC). Remove ao descansar bem. LLM narra exaustão física e mental.

**Encumbrance (Peso)**
- Peso total do inventário vs `Força * 5` (ou valor ajustado por classe).
- Níveis:
  - Leve: normal
  - Médio: -1 Dex checks e movimento ligeiramente mais lento
  - Pesado: -3, movimento muito lento, fadiga rápida
- LLM: "O peso da placa + o tesouro acumulado faz suas pernas tremerem. Cada passo ecoa como um sino na masmorra."

### 2.6 Armadilhas, Portas Secretas e Cofres (mais profundidade tática)

**Tipos de armadilha (engine):**
- Dardos envenenados (dano + DoT)
- Gás paralisante (save vs Con ou ficar 1-2 turnos sem agir)
- Alçapão com queda (dano + possível nova sala)
- Ilusão (engine esconde uma passagem real até detectada)
- Pressão que invoca monstros

**Detecção e Desarme:**
- Ação `procurar` ou `examinar_parede/chao`: engine faz check (Sabedoria + nível + racial vs dificuldade da armadilha).
- Sucesso → revela tipo e localização. LLM descreve indícios sutis.
- Desarme: apenas Ladino (ou com ferramenta "Kit de Ladrão") → check % ou d20 + Dex vs diff.
- Falha crítica → ativa imediatamente.
- Sucesso → desarmada + possível componente reutilizável (mola, frasco de veneno).

**Portas e Cofres:**
- Trancadas: gazua (Ladino bônus), Chave de Ferro, forçar (Força check — barulhento → risco wandering).
- Secretas: só aparecem no mapa após detecção bem-sucedida.
- Cofre lendário: pode ter "Coração de Cristal" (item de quest para final alternativo de purificação).

### 2.7 Geração Procedural e Eventos Dinâmicos

- **Tipos de sala expandidos:** Santuário (seguro para descanso), Biblioteca Antiga (grimórios + lore tablets), Forja Abandonada (possível craft simples ou reparo), Câmara do Rio (puzzle com fluxo de água), Túmulo Profanado (undead + maldição leve), Altar Corrompido (escolha moral: purificar ou saquear).
- **Wandering Monsters:** Tabela por "profundidade" (andar). Engine rola chance ao entrar em sala nova ou ao descansar.
- **Tablets de Lore:** Engine coloca 1-2 por masmorra. Ao interagir, revela `lore_id`. LLM narra o texto de forma poética e conecta com a situação atual do jogador.
- **Escolhas com peso:** Altar que oferece poder temporário (buff forte) em troca de maldição leve permanente (engine tracka). LLM descreve o dilema dramaticamente.

### 2.8 Progressão, Nível e Múltiplos Finais

- Níveis até **8 ou 10** (tabelas de XP por monstro + bônus por exploração: salas reveladas, traps desarmadas, lore encontrado, chefe opcional).
- Level up: engine rola HP gain + Con bonus, aumenta dano base, mana, etc. LLM narra o momento de poder ("Você sente o rio antigo fluindo em suas veias...").
- **Finais alternativos (engine flags):**
  1. **Vitória Clássica:** Derrotar Golem → rio liberta → vila salva. Recompensa épica + narração de celebração.
  2. **Purificação (secreto):** Usar item específico (Coração de Cristal) + sabedoria alta → Golem é libertado em vez de destruído. Final mais "bom", talvez bênção permanente.
  3. **Fuga / Derrota:** Rio permanece seco → bad ending sombrio narrado pelo LLM.
  4. **Ganância:** Saquear tudo e ignorar o rio → maldição ou final vazio.

---

## 3. Integração LLM + Engine (Prompts e Validação)

**Prompt base estruturado (sempre enviado):**

```
Você é o Narrador das Catacumbas Esquecidas.

ESTADO ATUAL DA ENGINE (JSON):
{player: {race, class, level, hp, max_hp, mana, attributes: {...}, inventory: [...], equipped: {...}, active_buffs: [...]},
 map: {current_room_id, revealed_rooms, light_radius},
 discovered_lore: [ids],
 quest_flags: ["chave_ferro", "golem_purificado"?]}

CONTEXTO DE LORE RELEVANTE:
{lore_entries filtrados pela engine}

INSTRUÇÕES RÍGIDAS:
- Descreva em português rico, imersivo e sensorial (visão, som, cheiro, tato, gosto se relevante).
- Foque no que o jogador PERCEBE agora e no que mudou desde o último turno.
- Não decida resultados de ações, não invente dano, números, novos itens ou mecânicas.
- Se o jogador propôs uma ação, descreva o intento e o que ele vê/sente enquanto tenta.
- Use frases curtas e vívidas. Evite listas. Termine com um gancho natural para a próxima ação do jogador.
- Se algo do estado mudou (buff expirou, luz acabando, fadiga), mencione organicamente.
```

**Loop de Reparo (já existe — fortalecer):**
Se o output do LLM contiver palavras-chave de ação inválida ("você encontra", "dano X", "novo inimigo", "você agora tem"), a engine rejeita, extrai o erro e re-prompta com:
"ERRO DE NARRATIVA: Você descreveu algo que a engine não confirmou. Corrija e narre APENAS com base no estado fornecido. Estado atual: [resumo]."

---

## 4. Implementação e Testes (Recomendações Práticas)

1. **Modularize a engine:**
   - `race.py`
   - `attributes.py`
   - `spell_system.py` (com scaling e duration)
   - `light_system.py`
   - `trap_system.py`
   - `encumbrance.py`
   - `rest_fatigue.py`
   - `procedural_events.py` (wandering + lore tablets)

2. **Testes obrigatórios (adicione ao `--demo`):**
   - Criação de personagem com cada raça + verificação de modificadores
   - Geração e detecção/desarme de cada tipo de armadilha
   - Sistema de luz (sem luz vs com luz vs luz acabando)
   - Buffs com duração expirando corretamente
   - Level up em múltiplos níveis + scaling de spells
   - Encumbrance afetando checks e movimento
   - Finais alternativos (flags de engine)

3. **Balanceamento:**
   - Expanda `balance_sim.py` para testar:
     - Cada raça + classe vs Golem em níveis 4, 6, 8
     - Mago com novos spells de AoE e buffs
     - Ladino com backstab + disarm melhorado
   - Ajuste números com dados, nunca com achismo.

4. **Frontend Web:**
   - Mostrar atributos com bônus
   - Barra de luz / turnos restantes
   - Lista de buffs ativos com duração
   - Botão contextual "Procurar" / "Descansar" quando disponível
   - Mapa com ícones de luz/trevas

---

## 5. Priorização Sugerida (Curto Prazo)

**Fase 1 (fundação — alto impacto):**
1. Raças + Sistema de Atributos (6)
2. Sistema de Luz e Escuridão
3. Expansão de Magia com scaling + 3-4 novos spells + buffs com duração

**Fase 2 (profundidade tática):**
4. Armadilhas avançadas (detecção + desarme + tipos variados)
5. Encumbrance + Fadiga
6. Lore tablets + wandering monsters

**Fase 3 (replayability e polimento):**
7. Múltiplos finais + flags de purificação
8. Mais tipos de sala + puzzles simples (alavancas, fluxo de água)
9. Multi-nível (escadas para andares mais profundos com dificuldade crescente)

---

## 6. Arquivos Sugeridos para Criar/Atualizar

- `LORE.md` — Backstory completo, bestiário com flavor, textos de tablets, diálogos de cultistas.
- `RULES_ENGINE.md` — Especificação formal de todas as mecânicas (para devs e como referência no prompt do LLM).
- Atualizar `ROADMAP.md` com estas seções.
- `CLASSES_RACES.md` — Detalhes de identidade de cada combinação raça+classe.

---

**Conclusão**

Essas expansões mantêm (e reforçam) o que torna seu projeto especial: **mecânicas sólidas, testáveis e justas na engine + narrativa rica e imprevisível pelo LLM**. Nada de alucinação de regras. O jogador sente agency real porque as regras são previsíveis e o LLM só embeleza o que já aconteceu.

Quer que eu:
- Escreva o arquivo `LORE.md` completo com backstory detalhado?
- Crie exemplos de código Python para uma das novas mecânicas (ex: `light_system.py` ou `spell_system.py`)?
- Atualize o `ROADMAP.md` com essas propostas?
- Gere prompts otimizados para DeepSeek com os novos elementos?

É só pedir. Vamos manter esse projeto como referência de como fazer RPG com IA **sem perder o controle das regras**. ⛧

*Documento criado com base nas fontes fornecidas e no espírito do protótipo original.*