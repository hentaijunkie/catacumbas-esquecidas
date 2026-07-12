FROM python:3.12-slim

WORKDIR /app

# Dependência opcional do LLM (DeepSeek via API OpenAI-compatible)
RUN pip install --no-cache-dir openai

COPY rpg_loop.py server.py auth.py game_log.py balance_sim.py ./
COPY index.html LLM_RULEBOOK.md README.md ROADMAP.md ./
COPY assets ./assets
COPY artifacts ./artifacts

# Persistência e logs em volumes (recomendado em produção)
RUN mkdir -p /app/data /app/saves /app/logs

ENV HOST=0.0.0.0
ENV PORT=8000
# REGISTER_KEY / INVITE_KEY e DEEPSEEK_API_KEY via -e ou compose
# SESSION_SECURE=1 se estiver atrás de HTTPS

EXPOSE 8000
CMD ["python", "server.py"]
