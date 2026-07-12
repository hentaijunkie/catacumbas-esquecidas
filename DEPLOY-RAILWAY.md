# Deploy no Railway — As Catacumbas Esquecidas

Guia passo a passo. O app já tem `Dockerfile` e `railway.toml`.

## 1. Conta e projeto

1. Acesse [https://railway.app](https://railway.app) e entre com **GitHub**.
2. **New Project** → **Deploy from GitHub repo**.
3. Autorize o Railway e escolha **`hentaijunkie/catacumbas-esquecidas`**.
4. Aguarde o primeiro build (Dockerfile).

## 2. Variáveis de ambiente

No serviço → **Variables** → adicione:

| Variável | Valor | Obrigatório |
|---|---|---|
| `REGISTER_KEY` | chave secreta que **você** passa aos testadores | **Sim** (senão ninguém cria conta) |
| `HOST` | `0.0.0.0` | Recomendado |
| `DATA_DIR` | `/data` | **Sim** se usar volume |
| `SAVE_ROOT` | `/data/saves` | **Sim** se usar volume |
| `SESSION_SECURE` | `1` | Sim (Railway é HTTPS) |
| `DEEPSEEK_API_KEY` | sua chave DeepSeek | Não (sem ela = narração template) |

**Não** coloque `PORT` na mão: o Railway injeta automaticamente.

## 3. Volume persistente (contas + saves)

Sem volume, cada redeploy **apaga** usuários e saves.

1. No serviço → **Settings** (ou aba **Volumes**).
2. **Add Volume**.
3. Mount path: **`/data`**
4. Confirme e redeploy se pedido.

Com `DATA_DIR=/data` e `SAVE_ROOT=/data/saves`:

- contas → `/data/users.json`
- saves → `/data/saves/<usuario>/slot_*.json`

## 4. Domínio público

1. Serviço → **Settings** → **Networking** → **Generate Domain**  
   (ou **Public Networking**).
2. Copie a URL, tipo `https://catacumbas-xxx.up.railway.app`.

## 5. Testar

1. Abra a URL.
2. **Criar conta** com a `REGISTER_KEY` que configurou.
3. Login → escolher classe → jogar.
4. Em outra janela anônima, outra conta = outra sessão (multi-jogador).

## 6. O que enviar aos testadores

1. Link do Railway  
2. **Chave de convite** (`REGISTER_KEY`) — só para criar conta  
3. Aviso: protótipo; um refresh ok; se o servidor reiniciar, a run em memória some (save em disco permanece se usou Salvar / auto-save)

## 7. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| “Cadastro desativado” | Falta `REGISTER_KEY` nas Variables |
| Site não abre | Domínio público não gerado / deploy falhou (ver **Deployments** → logs) |
| Contas somem após deploy | Volume `/data` não montado ou `DATA_DIR` errado |
| Cookie/login estranho | Falta `SESSION_SECURE=1` atrás de HTTPS |
| Build falha | Ver logs; confirme que o root tem `Dockerfile` |

## 8. Redeploy após `git push`

Com o repo conectado, push em `main` dispara build novo.  
O volume `/data` **não** é apagado no redeploy (só o filesystem da imagem).

## 9. Custos

Railway tem trial/créditos e planos pagos. Confira o uso em **Usage**.  
Para poucos testadores, o custo costuma ser baixo; o free tier/créditos mudam com o tempo — veja o painel atual.
