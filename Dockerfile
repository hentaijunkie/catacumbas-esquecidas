FROM python:3.12-slim

WORKDIR /app

# Dependência opcional do LLM (DeepSeek via API OpenAI-compatible)
RUN pip install --no-cache-dir openai

COPY rpg_loop.py server.py auth.py game_log.py balance_sim.py ./
COPY index.html LLM_RULEBOOK.md README.md ROADMAP.md ./
COPY assets ./assets
COPY artifacts ./artifacts

# Persistência: no Railway monte um volume em /data e defina:
#   DATA_DIR=/data
#   SAVE_ROOT=/data/saves
RUN mkdir -p /app/data /app/saves /app/logs /data/saves

ENV HOST=0.0.0.0
ENV PORT=8000
# PORT é sobrescrita pelo Railway em runtime
# REGISTER_KEY, DEEPSEEK_API_KEY, SESSION_SECURE via Variables no painel

EXPOSE 8000
CMD ["python", "server.py"]
