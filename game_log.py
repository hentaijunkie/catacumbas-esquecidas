#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging em arquivo para debug do protótipo.
============================================================================
Cria logs/ ao lado do servidor e grava:
  - game.log     — eventos da engine/servidor (movimentos, erros, API)
  - client.log   — mensagens enviadas pelo browser (raycaster, JS)

Uso:
    from game_log import get_logger, log_client
    log = get_logger()
    log.info("jogador moveu para norte")
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(AQUI, "logs")

_loggers = {}


def _ensure_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name="game"):
    """Logger com rotação (1 MB × 5 arquivos) em logs/<name>.log."""
    if name in _loggers:
        return _loggers[name]
    _ensure_dir()
    logger = logging.getLogger(f"catacumbas.{name}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if not logger.handlers:
        path = os.path.join(LOG_DIR, f"{name}.log")
        fh = RotatingFileHandler(
            path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        # espelho no console (só INFO+)
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    _loggers[name] = logger
    return logger


MAX_CLIENT_ENTRIES = 50      # /api/log é público — sem cap, qualquer um enche o disco
MAX_CLIENT_MSG = 2000


def _uma_linha(msg):
    """Quebra de linha em msg do cliente forjaria entradas falsas no log."""
    return str(msg).replace("\r", " ").replace("\n", " ⏎ ")[:MAX_CLIENT_MSG]


def log_client(entries):
    """
    Grava entradas vindas do frontend.
    entries: lista de {level, msg, data?} ou uma string.
    """
    log = get_logger("client")
    if isinstance(entries, str):
        entries = [{"level": "info", "msg": entries}]
    if not isinstance(entries, list):
        entries = [entries]
    for e in entries[:MAX_CLIENT_ENTRIES]:
        if isinstance(e, str):
            log.info(_uma_linha(e))
            continue
        level = (e.get("level") or "info").lower()
        msg = e.get("msg") or e.get("message") or str(e)
        data = e.get("data")
        if data is not None:
            try:
                msg = f"{msg} | {json.dumps(data, ensure_ascii=False, default=str)}"
            except Exception:
                msg = f"{msg} | {data!r}"
        fn = getattr(log, level if level in ("debug", "info", "warning", "error") else "info")
        fn(_uma_linha(msg))


def log_estado_resumo(state, prefix="estado"):
    """Snapshot curto do estado p/ debug (sem dumpar a masmorra inteira)."""
    if not state:
        get_logger().info("%s: (sem jogo)", prefix)
        return
    p = state["player"]
    try:
        sala = state["masmorra"][(state["pos"]["x"], state["pos"]["y"])]
        exits = sorted(sala.get("exits") or [])
    except Exception:
        exits = []
    get_logger().info(
        "%s | pos=(%s,%s) face=%s exits=%s | %s %s nv%s HP %s/%s luz=%s fadiga=%s | "
        "andar=%s superficie=%s salas=%s",
        prefix,
        state["pos"]["x"], state["pos"]["y"], state.get("facing"), exits,
        p.get("raca"), p.get("classe"), p.get("nivel"),
        p.get("hp"), p.get("hp_max"), p.get("luz"), p.get("fadiga"),
        state.get("profundidade"), state.get("na_superficie"),
        len(state.get("masmorra") or {}),
    )


def session_banner():
    log = get_logger()
    log.info("=" * 60)
    log.info("Sessão iniciada %s", datetime.now().isoformat(timespec="seconds"))
    log.info("Logs em: %s", LOG_DIR)
    log.info("=" * 60)
