from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from dotenv import load_dotenv
import os
from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message
from login_app.app import mail, db, bcrypt
from utils.token import generate_reset_token, verify_reset_token
from models.user import User

load_dotenv()

from login_app.app import db, bcrypt
from login_app.models.user import User

auth_bp = Blueprint("auth", __name__)

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

# Página inicial
@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))
    
# Login local
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, provider="local").first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Credenciais inválidas.", "danger")

    return render_template("login.html")

# Dashboard
@auth_bp.route("/dashboard")
def dashboard():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("auth.login"))

# Login Google
@auth_bp.route("/oauth2/login/google/authorized")
def google_authorized():
    if not google.authorized:
        flash("Autorização Google negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
        resp.raise_for_status()  # Levanta exceção para erros HTTP
        info = resp.json()
        email = info["email"]
    except Exception as e:
        flash(f"Erro ao obter informações do Google: {e}", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=email, provider="google").first()
    if not user:
        user = User(username=email, provider="google", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    flash(f"✅ Login Google bem-sucedido! Bem-vindo {email}", "success")
    return redirect(url_for("auth.dashboard"))

@auth_bp.route("/oauth2/login/github/authorized")
def github_authorized():
    if not github.authorized:
        flash("Autorização GitHub negada.", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = github.get("/user")
        resp.raise_for_status()  # Levanta exceção para erros HTTP
        info = resp.json()
        username = info["login"]
    except Exception as e:
        flash(f"Erro ao obter informações do GitHub: {e}", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username, provider="github").first()
    if not user:
        user = User(username=username, provider="github", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    flash(f"✅ Login GitHub bem-sucedido! Bem-vindo {username}", "success")
    return redirect(url_for("auth.dashboard"))

# Registro de usuário local
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username, provider="local").first()
        if existing_user:
            flash("Nome de usuário já existe. Por favor, escolha outro.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password_hash=hashed_password, provider="local")
        db.session.add(new_user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# --- Solicitar redefinição de senha ---
@auth_bp.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_link = url_for('reset_token', token=token, _external=True)

            msg = Message('Redefinição de Senha - NewsTechApp', recipients=[email])
            msg.body = f'''Olá!

            Para redefinir sua senha, acesse o link abaixo:

            {reset_link}

            O link expira em 1 hora.
            Se você não solicitou, ignore este e-mail.
            '''
            
            mail.send(msg)
            flash('Um e-mail foi enviado com instruções para redefinir sua senha.', 'info')
            return redirect(url_for('login'))

        flash('E-mail não encontrado.', 'danger')
    return render_template('reset_request.html')


# --- Redefinir senha via token ---
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    email = verify_reset_token(token)
    if not email:
        flash('Link inválido ou expirado.', 'danger')
        return redirect(url_for('reset_request'))

    if request.method == 'POST':
        password = request.form['password']
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User.query.filter_by(email=email).first()
        user.password = hashed
        db.session.commit()
        flash('Senha atualizada com sucesso! Faça login novamente.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')
