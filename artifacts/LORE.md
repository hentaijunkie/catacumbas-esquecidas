# ⛧ LORE — As Catacumbas Esquecidas

Este arquivo contém o **conhecimento canônico** do universo.  
A engine armazena `lore_ids` descobertos. O LLM recebe apenas os textos relevantes filtrados pela engine e deve **narrar poeticamente**, sem inventar fatos novos.

---

## 1. O Mundo e a Vila

**Nome da Vila:** Pedralume  
**Localização:** Vale estreito entre colinas de pedra cinzenta, outrora banhado pelo Rio Vivo.  
**Estado atual:** A fonte secou há três gerações. Plantas murcham, poços estão secos, crianças nascem fracas. Os anciãos sussurram que "o rio chora nas profundezas".

**Lenda da Vila (contada pelo Ancião antes da descida):**
> "Antigamente o Rio Vivo corria generoso, alimentando a terra e o povo. Então veio o Silêncio. O Golem de Barro — que os antigos chamavam de Guardião do Fluxo — enlouqueceu. Ele selou as nascentes nas catacumbas com seu próprio corpo de lama e pedra. Dizem que só um coração puro, ou um tolo muito corajoso, pode fazê-lo lembrar quem ele era... ou destruí-lo para sempre."

**Recompensa prometida:** Se o rio voltar, a vila oferecerá o que resta de suas riquezas (na prática, o jogador recebe um item bônus ou bênção narrativa ao retornar vitorioso — engine controla).

---

## 2. As Catacumbas — História Antiga

**Nome antigo:** Templo Submerso de Aqualith (ou "Coração do Rio").

**Civilização:** Império de Aqualith — construtores de pedra que cantavam com a água. Eles canalizavam o rio como poder sagrado e como defesa contra invasores do leste. Construíram templos que "respiravam" com a maré subterrânea.

**O Ritual que deu errado:**
Há 400 anos, uma seita de cultistas do Lodo (adoradores de uma entidade estagnada chamada "Aquele que Não Flui") corrompeu o ritual de renovação do Guardião. Em vez de renovar o ciclo da água, eles tentaram **aprisionar** o rio para usar sua força como arma contra inimigos. O ritual falhou parcialmente: o Golem absorveu a essência do rio, enlouqueceu, e selou as nascentes para "proteger" o que restava — matando a superfície no processo.

**O Golem de Barro (Guardião Corrompido):**
- Originalmente: elemental de terra abençoado pelo rio, com consciência simples e leal.
- Agora: mistura de lama, pedra e água estagnada. Tem momentos de lucidez dolorosa onde "lembra" o fluxo e sofre. Isso abre espaço para finais alternativos de purificação.

---

## 3. Bestiário com Flavor (engine usa stats; LLM usa flavor)

### Morcego Gigante
- **Aparência:** Asas membranosas rasgadas, olhos leitosos, corpo inchado de sangue ruim.
- **Comportamento narrativo:** Ataca de surpresa no escuro. Grita com voz quase humana quando ferido. "Ele se lembra de quando voava sob a luz das estrelas..."

### Cultista do Lodo
- **Aparência:** Mantos encharcados de lama preta, olhos brilhando com luz doentia, pele com veias escuras.
- **Diálogo típico:** "O rio parou para nos proteger... você é o verdadeiro mal!"
- **Comportamento:** Cura aliados com lodo, invoca poças que atrasam o movimento. Prefere capturar vivos para "batizar no silêncio".

### Zumbi de Raiz
- **Aparência:** Corpos de antigos sacerdotes entrelaçados com raízes e cipós secos. Movem-se como se ainda rezassem.
- **Comportamento:** Lento, mas se não for queimado ou purificado, "regenera" da terra. LLM pode descrever: "As raízes se reconstroem, como se o templo itself tentasse curá-lo..."

### Elemental Menor de Terra
- **Aparência:** Pilares de pedra e lama que ganham forma humanóide.
- **Comportamento:** Imune a cortes e perfurações leves. Vulnerável a magia arcana e água (se o jogador tiver como conjurar). "Ele é parte da masmorra... você está lutando contra a própria pedra."

### O Golem de Barro (Chefe Final)
- **Fase 1 (Normal):** Ataques pesados de slam, invoca lodo que gruda nos pés.
- **Fase 2 (Rachado):** Quando HP < 50%, rachaduras aparecem e jorram água suja. Fica mais rápido e errático. LLM descreve dor: "O Golem grita com voz de mil rios sufocados..."
- **Fase 3 (Fúria Final):** Se não for purificado, entra em fúria cega. Dano alto, mas padrões previsíveis (engine).

**Momento de Lucidez (se o jogador tiver o item certo ou alta Sabedoria):**  
O Golem para por um turno, olhos brilhando com luz azul antiga. "Eu... eu era o fluxo. Por que me fizeram parar?"  
Isso abre o caminho para o final de purificação.

---

## 4. Itens com Lore Canônico (engine armazena lore_id + efeitos)

### Grimórios
- **Raio do Rio (Firebolt)**: "As páginas cheiram a ozônio e algas secas. Runas azuis formam o nome verdadeiro do raio que dança sobre a água."
- **Escudo Arcano**: "Escrito em pele de peixe-prateado que ainda parece úmida. O texto se move como correnteza quando você o toca."
- **Drenar Vida**: "Tinta preta que parece sangue coagulado. O grimório parece... faminto."

### Itens Especiais
- **Chave de Ferro Enferrujada**: Entregue pelo ancião. Abre o primeiro cofre grande. "Forjada com o último metal que a vila tinha antes do silêncio."
- **Coração de Cristal do Rio** (item secreto de quest): Cristal azul-pálido que pulsa fracamente com luz interna. "Dizem que é um fragmento do próprio rio aprisionado. Pode ser usado para lembrar o Golem de quem ele era..."
- **Lâmina Rúnica** (recompensa do cofre do Ladino): Espada curta com runas que brilham quando perto de água ou lodo. Bônus contra elementais de terra.
- **Pedra de Luz Eterna** (possível loot ou craft): Pequena pedra que emite luz azul suave. Não acaba, mas brilha mais fraco com o tempo se não "recarregada" em santuários.

### Tablets de Lore (descobertos na masmorra)
Engine coloca 4-6 tablets por masmorra. Cada um tem `lore_id` e texto curto. LLM embeleza.

Exemplos:
- **Tablet 01 (Entrada):** "Aqui jaz o Templo de Aqualith. Que as águas sempre fluam e a sede nunca vença."
- **Tablet 03 (Câmara do Ritual):** "O Guardião aceitou o sacrifício. O rio parou para proteger o que restava. Perdoem-nos."
- **Tablet 05 (Perto do Golem):** "Ele chora. Mesmo agora, nas rachaduras, eu ouço o rio chorando dentro dele."

---

## 5. Temas e Tom de Narração (instruções para o LLM)

**Tom geral:**
- Poético, melancólico, ligeiramente sombrio, mas com esperança tênue.
- Sensorial forte: cheiro de terra úmida + mofo + ozônio quando magia de água é usada.
- Sons: pingos de água que param de repente, eco de passos, respiração pesada do Golem, sussurros nas paredes.
- Contraste: momentos de beleza antiga (runas brilhando, reflexos de água que não existe mais) vs. corrupção (lama preta, cheiro de podridão).

**Frases recorrentes que o LLM pode usar (mas engine controla quando):**
- "O rio chora aqui..."
- "As paredes se lembram..."
- "Você sente o peso da estagnação no ar..."
- "Por um instante, você jura ouvir o fluxo antigo..."

**Evitar:**
- Humor moderno ou leve demais (a menos que o jogador force com ações cômicas — engine permite, LLM segue o tom do jogador).
- Explicar mecânicas ("você ganhou +2 de dano").
- Inventar novos monstros, itens ou regras.

---

## 6. Finais e Consequências (engine controla flags)

**Flag `golem_derrotado` + `rio_libertado`:**
- Narração épica de libertação. Vila revive. LLM descreve chuva caindo pela primeira vez em décadas, crianças rindo, etc.

**Flag `golem_purificado` (requer Coração de Cristal + alta Sabedoria ou ritual específico):**
- Final mais raro e "bom". Golem se dissolve em água limpa que flui de volta. Bênção permanente (engine dá bônus leve em todos os checks de água/magia futura — ou só narração de "o rio agora te reconhece como amigo").

**Flag `fugiu_ou_derrotado_parcialmente`:**
- Rio permanece seco. Narração sombria: "Pedralume morre devagar. Você carrega o peso da falha... ou da escolha."

**Maldições leves (se saquear altares ou falhar em checks importantes):**
- Engine aplica debuff permanente leve (ex: -1 em um atributo ou vulnerabilidade a lodo). LLM narra como "uma sombra fria se agarra ao seu coração" ou "você sente o lodo dos cultistas ainda nas veias".

---

## 7. Como a Engine usa este arquivo

1. `lore_database.json` (ou dict no código) contém todos os textos acima indexados por `lore_id`.
2. Ao gerar a masmorra proceduralmente, a engine decide quais `lore_ids` colocar em quais salas (baseado em tipo de sala + profundidade).
3. Quando o jogador interage com tablet / altar / grimório, engine:
   - Adiciona o `lore_id` à lista `discovered_lore` do jogador.
   - Passa o texto base + contexto da sala para o LLM.
4. LLM recebe instrução: "Use o texto canônico abaixo como verdade absoluta. Embeleze, dramatize, conecte com o estado emocional do jogador e a cena atual. Não adicione fatos novos."

**Exemplo de prompt extra para LLM quando lore é descoberto:**
```
TEXTO CANÔNICO (use exatamente estes fatos):
"{texto_do_tablet}"

Contexto atual: O jogador está ferido, com luz fraca, depois de derrotar um Cultista do Lodo.
Instrução: Descreva o momento em que ele lê o tablet. Conecte o texto antigo com a dor dele e com o monstro que acabou de morrer. Seja poético e melancólico.
```

---

**Fim do LORE.md**

Este arquivo deve ser mantido como **fonte de verdade**.  
Qualquer expansão futura de lore (novos tablets, diálogos de cultistas, visões do Golem) deve ser adicionada aqui primeiro, depois implementada na engine como `lore_id`.

*Documento vivo — atualize conforme o projeto evolui.* ⛧