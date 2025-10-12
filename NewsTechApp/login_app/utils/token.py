import os
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(email):
    """Gera um token seguro baseado no e-mail do usuário."""
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset-salt")

def verify_reset_token(token, expiration=3600):
    """Verifica se o token é válido e retorna o e-mail."""
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None
    return email
