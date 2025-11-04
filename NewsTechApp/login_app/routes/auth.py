from login_app.utils.token import generate_reset_token, verify_reset_token
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_mail import Message
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer
from functools import wraps

# Extensões globais
from login_app import db, bcrypt, mail
from login_app.models.user import User

from flask import make_response
from login_app.utils.jwt_auth import (
    create_access_token, create_refresh_token,
    set_jwt_cookies, set_csrf_cookie,
    get_access_from_request, decode_token, clear_jwt_cookies
)

load_dotenv()

auth_bp = Blueprint("auth", __name__)

# ===============================
# 🔐 OAuth2: Google e GitHub
# ===============================
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="auth.google_authorized"
)

github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="auth.github_authorized"
)

# ===============================
# 🔒 Decorator para proteger views
# (redireciona para /login se não tiver sessão)
# ===============================
def login_required_view(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

# ===============================
# 🏠 Raiz → login
# ===============================
@auth_bp.route("/")
def root():
    return redirect(url_for("auth.login"))

# ===============================
# 👤 Login local
# ===============================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        user = User.query.filter_by(email=email, provider="local").first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            # mantém sessão para compatibilidade com seus decorators/base atual
            session["user_id"] = user.id
            session["username"] = user.username or user.email
        
            access = create_access_token(user.id)
            refresh = create_refresh_token(user.id)
            csrf_token = os.urandom(16).hex()
        
            flash(f"✅ Bem-vindo de volta, {session['username']}!", "success")
            resp = make_response(redirect(url_for("auth.home")))
            set_jwt_cookies(resp, access, refresh)
            set_csrf_cookie(resp, csrf_token)
            return resp
            return redirect(url_for("auth.home"))
        else:
            flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html")

# ===============================
# 🏡 Home (renderiza templates/index.html)
# protegida por sessão
# ===============================
@auth_bp.route("/home")
@login_required_view
def home():
    return render_template("postagem/index.html")

@auth_bp.route("/publicar")
@login_required_view
def publicar():
    # templates/postagem/publicar.html
    return render_template("postagem/publicar.html")

# ===============================
# 📊 Dashboard (opcional)
# ===============================
@auth_bp.route("/dashboard")
@login_required_view
def dashboard():
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

@auth_bp.route("/api/me")
def api_me():
    uid = session.get("user_id")
    if not uid:
        return {"logged": False}, 200

    user = User.query.get(uid)
    # fallback pro email se username estiver vazio
    username = (user.username or user.email or "Usuário").strip()
    return {
        "logged": True,
        "id": user.id,
        "username": username,
        "email": user.email
    }, 200

# ===============================
# 🚪 Logout
# ===============================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "success")
    resp = make_response(redirect(url_for("auth.login")))
    clear_jwt_cookies(resp)
    return resp
    return redirect(url_for("auth.login"))

# ===============================
# 🌐 Google OAuth
# ===============================
@auth_bp.route("/oauth2/login/google/authorized")
def google_authorized():
    if not google.authorized:
        flash("Autorização Google negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
        resp.raise_for_status()
        info = resp.json()
        email = info["email"]
        # você pode pegar nome exibível, se existir
        display_name = info.get("name") or email
    except Exception as e:
        flash(f"Erro ao obter informações do Google: {e}", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=email, provider="google").first()
    if not user:
        user = User(username=email, email=email, provider="google", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username or display_name
    flash(f"✅ Login Google bem-sucedido! Bem-vindo {session['username']}", "success")
    
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    csrf_token = os.urandom(16).hex()
    resp = make_response(redirect(url_for("auth.home")))
    set_jwt_cookies(resp, access, refresh)
    set_csrf_cookie(resp, csrf_token)
    return resp

    return redirect(url_for("auth.home"))

# ===============================
# 🐙 GitHub OAuth
# ===============================
@auth_bp.route("/oauth2/login/github/authorized")
def github_authorized():
    if not github.authorized:
        flash("Autorização GitHub negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = github.get("/user")
        resp.raise_for_status()
        info = resp.json()
        username = info["login"]
        email = info.get("email")  # pode vir None
    except Exception as e:
        flash(f"Erro ao obter informações do GitHub: {e}", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username, provider="github").first()
    if not user:
        user = User(username=username, email=email, provider="github", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username or (email or username)
    flash(f"✅ Login GitHub bem-sucedido! Bem-vindo {session['username']}", "success")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    csrf_token = os.urandom(16).hex()
    resp = make_response(redirect(url_for("auth.home")))
    set_jwt_cookies(resp, access, refresh)
    set_csrf_cookie(resp, csrf_token)
    return resp
    
    return redirect(url_for("auth.home"))

# ===============================
# 🆕 Registro local
# ===============================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("As senhas não coincidem. Tente novamente.", "danger")
            return redirect(url_for("auth.register"))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("E-mail já registrado. Faça login ou use outro endereço.", "danger")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(username=username, provider="local").first()
        if existing_user:
            flash("Nome de usuário já existe. Por favor, escolha outro.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email, password_hash=hashed_password, provider="local")
        db.session.add(new_user)
        db.session.commit()

        flash("✅ Conta criada com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# ===============================
# ✉️ Enviar e-mail de redefinição
# ===============================
def send_reset_email(user):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps(user.email, salt="password-reset-salt")

    reset_url = url_for("auth.reset_token", token=token, _external=True, _scheme="https")

    msg = Message(
        subject="🔑 Redefinição de Senha - NewsTechApp",
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        recipients=[user.email],
    )
    msg.body = f"""Olá {user.username},

Você solicitou a redefinição de senha da sua conta NewsTechApp.

Para redefinir sua senha, clique no link abaixo (válido por 30 minutos):

{reset_url}

Se você não solicitou esta redefinição, ignore este e-mail.
"""
    try:
        mail.send(msg)
        print(f"✅ E-mail de redefinição enviado para {user.email}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# ===============================
# 🔁 Solicitar redefinição
# ===============================
@auth_bp.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('E-mail não encontrado.', 'danger')
            return redirect(url_for('auth.reset_request'))

        if user.provider != "local":
            flash('Esta conta usa login via Google ou GitHub. Redefina a senha diretamente no provedor.', 'warning')
            return redirect(url_for('auth.login'))

        token = generate_reset_token(user.email)
        reset_link = url_for('auth.reset_token', token=token, _external=True)

        msg = Message('Redefinição de Senha - NewsTechApp', recipients=[email])
        msg.body = f'''Olá!

Para redefinir sua senha, acesse o link abaixo:

{reset_link}

O link expira em 1 hora.
Se você não solicitou, ignore este e-mail.
'''
        mail.send(msg)
        flash('Um e-mail foi enviado com instruções para redefinir sua senha.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('reset_request.html')

# ===============================
# 🔐 Redefinir senha via token
# ===============================
@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=1800)
    except Exception:
        flash("Token inválido ou expirado.", "danger")
        return redirect(url_for("auth.reset_request"))

    user = User.query.filter_by(email=email).first()
    if request.method == "POST":
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user.password_hash = hashed_password
        db.session.commit()
        flash("Senha redefinida com sucesso!", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")

# ===============================
# 🔐 Restaurar sessão automaticamente a partir do access_token
# ===============================

@auth_bp.before_app_request
def restore_session_from_jwt():
    if session.get("user_id"):
        return
    token = get_access_from_request()
    if not token:
        return
    data = decode_token(token, expected_type="access")
    if not data:
        return
    from login_app.models.user import User  # import local para evitar ciclos
    user = User.query.get(int(data["sub"]))
    if not user:
        return
    session["user_id"] = user.id
    session["username"] = user.username or user.email

# ===============================
# 🔐 Endpoint de refresh
# ===============================
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    refresh_token = get_refresh_from_request()
    if not refresh_token:
        return jsonify({"error": "missing refresh"}), 401

    data = decode_token(refresh_token, expected_type="refresh")
    if not data:
        return jsonify({"error": "invalid refresh"}), 401

    from login_app.models.user import User
    user = User.query.get(int(data["sub"]))
    if not user:
        return jsonify({"error": "user not found"}), 404

    new_access = create_access_token(user.id)
    csrf_token = os.urandom(16).hex()
    resp = jsonify({"message": "refreshed"})
    set_jwt_cookies(resp, new_access, refresh_token)  # mantém o mesmo refresh
    set_csrf_cookie(resp, csrf_token)
    return resp, 200


