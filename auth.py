#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contas + sessões HTTP para multi-jogador.
============================================================================
- Cadastro exige uma chave de convite (REGISTER_KEY / INVITE_KEY ou invite_key.txt).
- Senhas: PBKDF2-HMAC-SHA256 (stdlib).
- Sessões: token opaco em cookie HttpOnly; estado de jogo por sessão no servidor.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from typing import Any, Optional

AQUI = os.path.dirname(os.path.abspath(__file__))
# Em produção (Railway): monte um volume e defina DATA_DIR=/data (users em /data/users.json)
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(AQUI, "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
SESSIONS_PATH = os.path.join(DATA_DIR, "sessions.json")

_USER_RE = re.compile(r"^[a-zA-Z0-9_]{3,24}$")
_PBKDF2_ITERS = 120_000
SESSION_TTL_S = 60 * 60 * 24 * 14  # mesmo prazo do Max-Age do cookie
_PERSIST_LAST_A_CADA_S = 3600      # refresca o 'last' persistido no máx. 1x/hora

_lock = threading.RLock()
_users: dict = {}
_sessions: dict[str, dict] = {}  # token -> {user, created, last, state, combate, ...}
_sessions_last_persist = 0.0


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Persistência de sessões (v3.9.6): antes, um restart do servidor (todo deploy
# do Railway!) invalidava todos os cookies — cada jogador tinha de logar de novo
# e caía em "precisa_novo". Agora o essencial da sessão (token→user/created/last/
# active_slot) sobrevive em DATA_DIR/sessions.json; o ESTADO DE JOGO continua em
# memória e é retomado do auto-save pelo server (_tentar_retomar_jogo).
# Segurança: o arquivo fica no volume privado junto de users.json (mesmo perímetro).
# ---------------------------------------------------------------------------
_SESSION_PERSIST_KEYS = ("user", "created", "last", "active_slot")


def save_sessions() -> None:
    """Grava as sessões vivas (campos persistíveis; NUNCA o estado de jogo/lock)."""
    global _sessions_last_persist
    with _lock:
        now = time.time()
        vivos = {t: {k: s.get(k) for k in _SESSION_PERSIST_KEYS}
                 for t, s in _sessions.items()
                 if now - s.get("last", 0) <= SESSION_TTL_S}
        _ensure_data_dir()
        tmp = SESSIONS_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(vivos, f, ensure_ascii=False)
            os.replace(tmp, SESSIONS_PATH)
            _sessions_last_persist = now
        except OSError:
            pass  # best-effort: sem disco, as sessões seguem em memória


def load_sessions() -> None:
    """Boot: restaura sessões persistidas (jogo=None; o server retoma do auto-save)."""
    global _sessions
    try:
        with open(SESSIONS_PATH, encoding="utf-8-sig") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return
    if not isinstance(dados, dict):
        return
    now = time.time()
    with _lock:
        for token, s in dados.items():
            if not isinstance(s, dict) or not s.get("user"):
                continue
            if now - float(s.get("last") or 0) > SESSION_TTL_S:
                continue
            _sessions[token] = {
                "user": s["user"],
                "created": float(s.get("created") or now),
                "last": float(s.get("last") or now),
                "state": None,             # jogo em memória morreu com o processo
                "combate": None,
                "active_slot": int(s.get("active_slot") or 1),
                "passos_desde_save": 0,
                "retomar_pendente": True,  # server tenta reidratar do auto-save
                "lock": threading.RLock(),
            }


def invite_key() -> Optional[str]:
    """Chave de convite para criar conta. Env tem prioridade sobre arquivo."""
    for env in ("REGISTER_KEY", "INVITE_KEY"):
        v = (os.environ.get(env) or "").strip()
        if v:
            return v
    for nome in ("invite_key.txt", "register_key.txt"):
        try:
            with open(os.path.join(AQUI, nome), encoding="utf-8-sig") as f:
                for line in f:
                    v = line.strip()
                    if v and not v.startswith("#"):
                        return v
        except OSError:
            continue
    return None


def load_users() -> None:
    global _users
    _ensure_data_dir()
    try:
        # utf-8-sig: tolera BOM se o arquivo for editado por PowerShell/Notepad —
        # sem isso o json.load falha e TODAS as contas somem silenciosamente
        with open(USERS_PATH, "r", encoding="utf-8-sig") as f:
            _users = json.load(f)
        if not isinstance(_users, dict):
            _users = {}
    except (OSError, json.JSONDecodeError):
        _users = {}


def save_users() -> None:
    _ensure_data_dir()
    tmp = USERS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_users, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_PATH)


def valid_username(name: str) -> bool:
    return bool(name and _USER_RE.match(name))


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERS
    )
    return salt, dk.hex()


def verify_password(password: str, salt: str, pw_hash: str) -> bool:
    _, h = _hash_password(password, salt)
    return hmac.compare_digest(h, pw_hash)


def register(username: str, password: str, key: str) -> tuple[bool, str]:
    """Cria conta. Retorna (ok, msg)."""
    username = (username or "").strip()
    password = password or ""
    key = (key or "").strip()
    expected = invite_key()
    if not expected:
        return False, "Cadastro desativado: o administrador não configurou a chave de convite."
    if not hmac.compare_digest(key, expected):
        return False, "Chave de convite inválida."
    if not valid_username(username):
        return False, "Usuário inválido (3–24 chars: letras, números, _)."
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."
    if len(password) > 128:
        return False, "Senha longa demais."
    with _lock:
        load_users()
        if username.lower() in {u.lower() for u in _users}:
            return False, "Este nome de usuário já existe."
        salt, pw_hash = _hash_password(password)
        _users[username] = {
            "salt": salt,
            "hash": pw_hash,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_users()
    return True, "Conta criada. Faça login."


def login(username: str, password: str) -> tuple[bool, str, Optional[str]]:
    """Valida credenciais e cria sessão. Retorna (ok, msg, token|None)."""
    username = (username or "").strip()
    password = password or ""
    with _lock:
        load_users()
        # case-sensitive match first; fallback case-insensitive
        rec = _users.get(username)
        if not rec:
            for u, r in _users.items():
                if u.lower() == username.lower():
                    username, rec = u, r
                    break
        if not rec or not verify_password(password, rec["salt"], rec["hash"]):
            return False, "Usuário ou senha incorretos.", None
        token = secrets.token_urlsafe(32)
        now = time.time()
        # faxina: sessões expiradas não ficam acumulando na memória
        for t in [t for t, s in _sessions.items() if now - s.get("last", 0) > SESSION_TTL_S]:
            _sessions.pop(t, None)
        _sessions[token] = {
            "user": username,
            "created": now,
            "last": now,
            "state": None,
            "combate": None,
            "active_slot": 1,
            "passos_desde_save": 0,
            # SEM retomar_pendente: login fresco mantém o fluxo de seleção/Carregar.
            # A retomada automática é só p/ sessões restauradas de restart (load_sessions).
            "lock": threading.RLock(),  # serializa requests DESTA sessão (não o servidor todo)
        }
    save_sessions()                     # cookie sobrevive a restart/deploy
    return True, "Login OK.", token


def logout(token: Optional[str]) -> None:
    if not token:
        return
    with _lock:
        _sessions.pop(token, None)
    save_sessions()


def get_session(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    with _lock:
        s = _sessions.get(token)
        if not s:
            return None
        now = time.time()
        if now - s.get("last", 0) > SESSION_TTL_S:
            _sessions.pop(token, None)
            return None
        s["last"] = now
        precisa_persistir = now - _sessions_last_persist > _PERSIST_LAST_A_CADA_S
    if precisa_persistir:
        save_sessions()                 # mantém o 'last' persistido fresco (máx. 1x/hora)
    return s


def parse_cookie(header: str) -> dict[str, str]:
    out = {}
    if not header:
        return out
    for part in header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def session_token_from_headers(headers) -> Optional[str]:
    cookies = parse_cookie(headers.get("Cookie", "") if headers else "")
    return cookies.get("session") or None


def cookie_header(token: str, max_age: int = 60 * 60 * 24 * 14) -> str:
    """Set-Cookie para a sessão. Secure se SESSION_SECURE=1 (HTTPS)."""
    parts = [
        f"session={token}",
        "Path=/",
        "HttpOnly",
        "SameSite=Lax",
        f"Max-Age={max_age}",
    ]
    if os.environ.get("SESSION_SECURE", "").strip() in ("1", "true", "yes"):
        parts.append("Secure")
    return "; ".join(parts)


def clear_cookie_header() -> str:
    return "session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"


def safe_username(user: str) -> str:
    """Nome de pasta seguro para saves do usuário."""
    u = re.sub(r"[^a-zA-Z0-9_]", "_", user or "anon")
    return u[:64] or "anon"


def user_save_dir(base_saves: str, user: str) -> str:
    return os.path.join(base_saves, safe_username(user))


def auth_status() -> dict[str, Any]:
    """Info pública p/ a UI (sem vazar a chave)."""
    return {
        "cadastro_disponivel": bool(invite_key()),
        "mensagem": (
            "Informe usuário, senha e a chave de convite do administrador."
            if invite_key()
            else "Cadastro desativado (sem REGISTER_KEY / invite_key.txt no servidor)."
        ),
    }


# carrega usuários ao importar
load_users()
