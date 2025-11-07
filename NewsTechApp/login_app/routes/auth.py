from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, current_app, jsonify, make_response
)
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
import os
from functools import wraps

# Extensões globais
from login_app import db, bcrypt, mail
from login_app.models.user import User

# Tokens / JWT helpers
from login_app.utils.token import generate_reset_token, verify_reset_token
from login_app.utils.jwt_auth import (
    create_access_token, create_refresh_token,
    set_jwt_cookies, set_csrf_cookie, clear_jwt_cookies,
    get_access_from_request, get_refresh_from_request,
    decode_token,
)

load_dotenv()

auth_bp = Blueprint("auth", __name__)

# ===============================
# 🔐 OAuth2: Google e GitHub (sem colisão)
#  - Mantemos o callback interno do Flask-Dance em:
#    /oauth2/login/google/authorized
#    /oauth2/login/github/authorized
#  - E redirecionamos DEPOIS para os SEUS endpoints finais:
#    /login/google/callback
#    /login/github/callback
# ===============================
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "email", "profile"],
    redirect_to="auth.google_callback",
)

github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    scope="user:email",
    redirect_to="auth.github_callback",
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
    # 1) Se já há sessão ativa → home
    if session.get("user_id"):
        return redirect(url_for("auth.home"))

    # 2) Tenta SSO silencioso via cookie (JWT)
    token = get_access_from_request(request)
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            uid = int(payload.get("sub"))
            user = User.query.get(uid)
            if user:
                session["user_id"] = user.id
                session["username"] = user.username or user.email
                return redirect(url_for("auth.home"))
        except Exception:
            # token inválido/expirado → segue para tela de login
            pass

    # 3) POST: valida credenciais
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # Se sua tabela tem coluna 'provider', mantém; senão, remove o provider="local"
        try:
            user = User.query.filter_by(email=email, provider="local").first()
        except Exception:
            user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            # mantém sessão
            session["user_id"] = user.id
            session["username"] = user.username or user.email

            # emite JWTs e seta cookies
            access = create_access_token(user.id)
            refresh = create_refresh_token(user.id)
            csrf_token = os.urandom(16).hex()

            resp = make_response(redirect(url_for("auth.home")))
            set_jwt_cookies(resp, access, refresh)
            set_csrf_cookie(resp, csrf_token)

            flash(f"✅ Bem-vindo de volta, {session['username']}!", "success")
            return resp

        # credenciais inválidas
        flash("E-mail ou senha inválidos.", "danger")
        return render_template("login.html"), 401

    # 4) GET sem sessão/JWT → renderiza form
    return render_template("login.html")

# ===============================
# 🏡 Home (renderiza templates/postagem/index.html)
# protegida por sessão/JWT
# ===============================
@auth_bp.route("/home")
def home():
    if not session.get("user_id"):
        token = get_access_from_request(request)
        if not token:
            return redirect(url_for("auth.login"))
        try:
            payload = decode_token(token, expected_type="access")
            session["user_id"] = int(payload["sub"])
            u = User.query.get(session["user_id"])
            if u:
                session["username"] = u.username or u.email
        except Exception:
            return redirect(url_for("auth.login"))

    return render_template("postagem/index.html")

# ===============================
# 📝 Publicar (protegida)
# ===============================
@auth_bp.route("/publicar", methods=["GET"], endpoint="publicar")
def publicar():
    if not session.get("user_id"):
        token = get_access_from_request(request)
        if not token:
            return redirect(url_for("auth.login"))
        try:
            payload = decode_token(token, expected_type="access")
            session["user_id"] = int(payload["sub"])
            u = User.query.get(session["user_id"])
            if u:
                session["username"] = u.username or u.email
        except Exception:
            return redirect(url_for("auth.login"))

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

# =========================================================
# 🌐 ENDPOINTS FINAIS SEUS (pós-OAuth) — sem /authorized
#  - O Flask-Dance processa /authorized e redireciona pra cá
# =========================================================
@auth_bp.route("/login/google/callback")
def google_callback():
    if not google.authorized:
        flash("Autorização Google negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
        resp.raise_for_status()
        info = resp.json()
        email = info.get("email")
        display_name = info.get("name") or (email.split("@")[0] if email else "Usuário")
        if not email:
            raise ValueError("Google não retornou e-mail")
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

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    csrf_token = os.urandom(16).hex()
    resp = make_response(redirect(url_for("auth.home")))
    set_jwt_cookies(resp, access, refresh)
    set_csrf_cookie(resp, csrf_token)
    flash(f"✅ Login Google bem-sucedido! Bem-vindo {session['username']}", "success")
    return resp

@auth_bp.route("/login/github/callback")
def github_callback():
    if not github.authorized:
        flash("Autorização GitHub negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        # 1) Tenta e-mails (requer scope user:email)
        emails_resp = github.get("/user/emails")
        primary_email = None
        if emails_resp.ok:
            for item in emails_resp.json():
                if item.get("primary") and item.get("verified"):
                    primary_email = item.get("email")
                    break
            if not primary_email and emails_resp.json():
                primary_email = emails_resp.json()[0].get("email")

        # 2) /user para username e fallback de e-mail
        user_resp = github.get("/user")
        user_resp.raise_for_status()
        info = user_resp.json()
        username = info.get("login")
        email = primary_email or info.get("email")
        if not username and not email:
            raise ValueError("GitHub não retornou username/email")

        effective_username = username or (email.split("@")[0] if email else "usuario_github")
    except Exception as e:
        flash(f"Erro ao obter informações do GitHub: {e}", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=effective_username, provider="github").first()
    if not user:
        user = User(username=effective_username, email=email, provider="github", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username or (email or effective_username)

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    csrf_token = os.urandom(16).hex()
    resp = make_response(redirect(url_for("auth.home")))
    set_jwt_cookies(resp, access, refresh)
    set_csrf_cookie(resp, csrf_token)
    flash(f"✅ Login GitHub bem-sucedido! Bem-vindo {session['username']}", "success")
    return resp

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

        if getattr(user, "provider", "local") != "local":
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
# 🔐 Restaura sessão pelo access_token (antes de cada request)
# ===============================
@auth_bp.before_app_request
def restore_session_from_jwt():
    if session.get("user_id"):
        return  # já autenticado

    token = get_access_from_request(request)
    if not token:
        return

    data = decode_token(token, expected_type="access")
    if not data:
        return

    user = User.query.get(int(data["sub"]))
    if not user:
        return

    session["user_id"] = user.id
    session["username"] = user.username or user.email

# ===============================
# 🔁 Endpoint de refresh do access token
# ===============================
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    try:
        refresh_token = get_refresh_from_request(request)
        if not refresh_token:
            return jsonify({"error": "missing refresh"}), 401

        data = decode_token(refresh_token, expected_type="refresh")
        if not data:
            return jsonify({"error": "invalid refresh"}), 401

        user = User.query.get(int(data["sub"]))
        if not user:
            return jsonify({"error": "user not found"}), 404

        new_access = create_access_token(user.id)
        csrf_token = os.urandom(16).hex()

        resp = jsonify({"message": "refreshed"})
        # mantém o mesmo refresh, apenas renova o access
        set_jwt_cookies(resp, new_access, refresh_token)
        set_csrf_cookie(resp, csrf_token)
        return resp, 200
    except Exception:
        return jsonify({"error": "refresh failed"}), 400
