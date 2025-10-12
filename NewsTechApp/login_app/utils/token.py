import os
from itsdangerous import URLSafeTimedSerializer

# Gera um token seguro com base no SECRET_KEY do app
def generate_reset_token(email):
    from flask import current_app
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt="password-reset-salt")

# Verifica o token e retorna o e-mail se válido
def verify_reset_token(token, expiration=3600):
    from flask import current_app
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None
    return email
