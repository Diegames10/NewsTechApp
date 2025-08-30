from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from dotenv import load_dotenv
import os

from login_app import db, bcrypt
from login_app.models.user import User

load_dotenv()

auth_bp = Blueprint("auth", __name__)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="auth.google_login"
)

github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="auth.github_login"
)

# Página inicial -> manda para dashboard se logado, login caso contrário
@auth_bp.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))

# Login local
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Usuário ou senha inválidos", "danger")

    return render_template("login.html")

# Registro de novo usuário
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Verifica se já existe usuário
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Usuário já existe. Tente outro nome.", "warning")
            return redirect(url_for("auth.register"))

        # Cria novo usuário
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# Dashboard protegido
@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Faça login primeiro", "warning")
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html")

# Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta", "info")
    return redirect(url_for("auth.login"))
