import time, jwt
from flask import current_app, request, g, jsonify
from functools import wraps

def _now():
    return int(time.time())

def create_access_token(sub: str | int):
    payload = {
        "sub": str(sub),
        "type": "access",
        "iat": _now(),
        "exp": _now() + current_app.config["JWT_ACCESS_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm=current_app.config["JWT_ALG"])

def create_refresh_token(sub: str | int):
    payload = {
        "sub": str(sub),
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + current_app.config["JWT_REFRESH_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm=current_app.config["JWT_ALG"])

def decode_token(token: str):
    return jwt.decode(token,
                      current_app.config["JWT_SECRET"],
                      algorithms=[current_app.config["JWT_ALG"]])

def set_jwt_cookies(resp, access_token: str, refresh_token: str | None = None):
    # ACCESS
    resp.set_cookie(
        "access_token",
        access_token,
        max_age=current_app.config["JWT_ACCESS_EXPIRES"],
        httponly=True,
        secure=current_app.config["COOKIE_SECURE"],
        samesite=current_app.config["COOKIE_SAMESITE"],
        path="/",  # acessível no site todo
    )
    # REFRESH
    if refresh_token:
        resp.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=current_app.config["JWT_REFRESH_EXPIRES"],
            httponly=True,
            secure=current_app.config["COOKIE_SECURE"],
            samesite=current_app.config["COOKIE_SAMESITE"],
            path="/auth/refresh",  # escopo reduzido
        )
    return resp

def clear_jwt_cookies(resp):
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/auth/refresh")
    return resp

# ----- CSRF (double-submit): cookie não-HttpOnly + header -----
def set_csrf_cookie(resp, token: str):
    resp.set_cookie(
        "csrf_token",
        token,
        max_age=current_app.config["JWT_REFRESH_EXPIRES"],
        httponly=False,  # cliente precisa ler e mandar no header
        secure=current_app.config["COOKIE_SECURE"],
        samesite=current_app.config["COOKIE_SAMESITE"],
        path="/",
    )
    return resp

def csrf_protect(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            cookie = request.cookies.get("csrf_token")
            header = request.headers.get("X-CSRF-Token")
            if not cookie or not header or cookie != header:
                return jsonify({"error": "CSRF token inválido"}), 403
        return fn(*a, **kw)
    return wrapper

# ----- Guard: exige JWT de access no cookie -----
def jwt_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        token = request.cookies.get("access_token")
        if not token:
            return jsonify({"error": "missing access token"}), 401
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                return jsonify({"error": "invalid token type"}), 401
            g.current_user_id = payload["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "access token expired"}), 401
        except Exception:
            return jsonify({"error": "invalid token"}), 401
        return fn(*a, **kw)
    return wrapper
