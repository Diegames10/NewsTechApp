# login_app/utils/jwt_auth.py
from datetime import datetime, timedelta, timezone
from flask import current_app, request
import jwt

# --- helpers internos ---
def _cfg(key, default=None):
    return current_app.config.get(key, default)

def _now():
    return datetime.now(timezone.utc)

# --- criação de tokens ---
def create_access_token(user_id: int) -> str:
    secret = _cfg("JWT_SECRET")
    alg = _cfg("JWT_ALGORITHM", "HS256")
    minutes = int(_cfg("JWT_ACCESS_MINUTES", 30))  # 30 min padrão
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=alg)

def create_refresh_token(user_id: int) -> str:
    secret = _cfg("JWT_SECRET")
    alg = _cfg("JWT_ALGORITHM", "HS256")
    days = int(_cfg("JWT_REFRESH_DAYS", 7))  # 7 dias padrão
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=days)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=alg)

# --- leitura/validação ---
def decode_token(token: str):
    secret = _cfg("JWT_SECRET")
    alg = _cfg("JWT_ALGORITHM", "HS256")
    return jwt.decode(token, secret, algorithms=[alg])

def get_access_from_request(req=None) -> str | None:
    """
    Busca o access token nos cookies ('access_token')
    ou no header Authorization: Bearer <token>.
    """
    req = req or request

    # 1) Cookie
    tok = req.cookies.get("access_token")
    if tok:
        return tok

    # 2) Header Authorization
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip() or None

    return None

# --- cookies ---
def set_jwt_cookies(resp, access_token: str, refresh_token: str):
    """
    Seta cookies HTTPOnly para access e refresh.
    Ajuste SameSite/secure conforme seu domínio.
    """
    # Em prod com HTTPS, deixe secure=True
    secure = bool(_cfg("SESSION_COOKIE_SECURE", True))
    samesite = _cfg("SESSION_COOKIE_SAMESITE", "Lax")

    # Access (curto)
    access_minutes = int(_cfg("JWT_ACCESS_MINUTES", 30))
    resp.set_cookie(
        "access_token",
        access_token,
        max_age=access_minutes * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )

    # Refresh (longo)
    refresh_days = int(_cfg("JWT_REFRESH_DAYS", 7))
    resp.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=refresh_days * 24 * 3600,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )

def clear_jwt_cookies(resp):
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")

def set_csrf_cookie(resp, csrf_token: str):
    """
    CSRF não é HttpOnly — precisa ser lido pelo JS e enviado em header.
    """
    secure = bool(_cfg("SESSION_COOKIE_SECURE", True))
    samesite = _cfg("SESSION_COOKIE_SAMESITE", "Lax")
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        max_age=12 * 3600,  # 12h
        httponly=False,
        secure=secure,
        samesite=samesite,
        path="/",
    )
