# login_app/utils/jwt_auth.py
import time
import jwt
from typing import Optional, Dict, Any
from flask import current_app, Request

# ---------- helpers internos ----------
def _now() -> int:
    return int(time.time())

def _cfg(name: str, default=None):
    return current_app.config.get(name, default)

# ---------- criação de tokens ----------
def create_access_token(user_id: int) -> str:
    """
    Gera um JWT de acesso curto.
    """
    iat = _now()
    exp = iat + int(_cfg("JWT_ACCESS_EXPIRES", 900))  # 15 min default
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": iat,
        "exp": exp,
        "iss": _cfg("JWT_ISSUER", "newstechapp"),
        "aud": _cfg("JWT_AUDIENCE", "newstechapp-users"),
    }
    return jwt.encode(payload, _cfg("JWT_SECRET"), algorithm=_cfg("JWT_ALG", "HS256"))

def create_refresh_token(user_id: int) -> str:
    """
    Gera um JWT de refresh mais longo.
    """
    iat = _now()
    exp = iat + int(_cfg("JWT_REFRESH_EXPIRES", 60 * 60 * 24 * 7))  # 7 dias default
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": iat,
        "exp": exp,
        "iss": _cfg("JWT_ISSUER", "newstechapp"),
        "aud": _cfg("JWT_AUDIENCE", "newstechapp-users"),
    }
    return jwt.encode(payload, _cfg("JWT_SECRET"), algorithm=_cfg("JWT_ALG", "HS256"))

# ---------- decodificação ----------
def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida tipo (access/refresh) se esperado.
    Retorna payload dict ou None se inválido.
    """
    try:
        payload = jwt.decode(
            token,
            _cfg("JWT_SECRET"),
            algorithms=[_cfg("JWT_ALG", "HS256")],
            issuer=_cfg("JWT_ISSUER", "newstechapp"),
            audience=_cfg("JWT_AUDIENCE", "newstechapp-users"),
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except Exception:
        return None

# ---------- cookies ----------
def set_jwt_cookies(resp, access_token: str, refresh_token: Optional[str] = None):
    """
    Grava cookies de access e refresh conforme flags do config.
    """
    access_name  = _cfg("JWT_ACCESS_COOKIE_NAME",  "access_token")
    refresh_name = _cfg("JWT_REFRESH_COOKIE_NAME", "refresh_token")
    samesite     = _cfg("JWT_COOKIE_SAMESITE", "Lax")
    secure       = bool(_cfg("JWT_COOKIE_SECURE", True))
    domain       = _cfg("JWT_COOKIE_DOMAIN")  # pode ser None
    path         = "/"

    # access (curto)
    resp.set_cookie(
        access_name, access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        domain=domain,
        path=path,
        max_age=int(_cfg("JWT_ACCESS_EXPIRES", 900)),
    )

    # refresh (longo) — só se enviado
    if refresh_token:
        resp.set_cookie(
            refresh_name, refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            domain=domain,
            path=path,
            max_age=int(_cfg("JWT_REFRESH_EXPIRES", 60 * 60 * 24 * 7)),
        )

def clear_jwt_cookies(resp):
    """
    Apaga cookies de access e refresh.
    """
    access_name  = _cfg("JWT_ACCESS_COOKIE_NAME",  "access_token")
    refresh_name = _cfg("JWT_REFRESH_COOKIE_NAME", "refresh_token")
    domain       = _cfg("JWT_COOKIE_DOMAIN")
    path         = "/"

    resp.delete_cookie(access_name,  path=path, domain=domain, samesite=_cfg("JWT_COOKIE_SAMESITE", "Lax"))
    resp.delete_cookie(refresh_name, path=path, domain=domain, samesite=_cfg("JWT_COOKIE_SAMESITE", "Lax"))

def set_csrf_cookie(resp, csrf_token: str):
    """
    Define um cookie CSRF não-HttpOnly (para pegar no front e mandar em cabeçalho).
    """
    name    = _cfg("CSRF_COOKIE_NAME", "csrf_token")
    samesite = _cfg("JWT_COOKIE_SAMESITE", "Lax")
    secure   = bool(_cfg("JWT_COOKIE_SECURE", True))
    domain   = _cfg("JWT_COOKIE_DOMAIN")
    path     = "/"

    resp.set_cookie(
        name, csrf_token,
        httponly=False,  # necessário pro front ler
        secure=secure,
        samesite=samesite,
        domain=domain,
        path=path,
        max_age=int(_cfg("JWT_ACCESS_EXPIRES", 900)),
    )

# ---------- leitura dos cookies no request ----------
def get_access_from_request(req: Request) -> Optional[str]:
    """
    Lê o access_token dos cookies do request.
    """
    name = _cfg("JWT_ACCESS_COOKIE_NAME", "access_token")
    return req.cookies.get(name)

def get_refresh_from_request(req: Request) -> Optional[str]:
    """
    Lê o refresh_token dos cookies do request.
    """
    name = _cfg("JWT_REFRESH_COOKIE_NAME", "refresh_token")
    return req.cookies.get(name)
