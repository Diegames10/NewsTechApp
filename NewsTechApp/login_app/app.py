import os
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session
)
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from werkzeug.security import generate_password_hash, check_password_hash
from login_app import db
from login_app.models.user import User


# =====================================================
# 🔹 IMPORTS DO NEWSAPI
# =====================================================

from flask_cors import CORS
import re
from chat_api import bp_chat   # importa o blueprint do chat
from rss_client import fetch_category_sub, list_subkeys
from flask import Flask, render_template, request, jsonify
from markupsafe import escape

# =====================================================
# 🔹 Blueprint principal
# =====================================================
auth_bp = Blueprint("auth", __name__)


# =====================================================
# 🔹 Rotas locais
# =====================================================

@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username, provider="local").first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Usuário ou senha inválidos!", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já existe!", "warning")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw, provider="local")
        db.session.add(new_user)
        db.session.commit()
        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Faça login para acessar o painel.", "warning")
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", username=session.get("username"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("auth.login"))


# =====================================================
# 🔹 Recuperar senha
# =====================================================
@auth_bp.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email, provider="local").first()

        if user:
            flash("Link de redefinição enviado (simulado).", "info")
        else:
            flash("Email não encontrado.", "warning")

        return redirect(url_for("auth.login"))

    return render_template("reset_request.html")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    # Placeholder: aqui ficaria a validação real de token
    if request.method == "POST":
        new_pw = request.form.get("password")
        email = request.form.get("email")

        user = User.query.filter_by(email=email, provider="local").first()
        if user:
            user.password_hash = generate_password_hash(new_pw)
            db.session.commit()
            flash("Senha atualizada com sucesso!", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Usuário não encontrado.", "danger")

    return render_template("reset_password.html", token=token)

from login_app import create_app

CORS(app, resources={r"/*": {"origins": "*"}})

# Configurações
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["JSON_AS_ASCII"] = False

# 🔗 registra o blueprint do chat (endpoints /api/chat)
app.register_blueprint(bp_chat)

# ==========================================================
# 🔍 ROTA PRINCIPAL — Página inicial de busca
# ==========================================================
@app.route("/", methods=["GET"])
def home():
    """Página inicial — formulário de busca"""
    return render_template(
        "news.html",
        articles=[],
        error="",
        q="",
        lang="pt,en",
        mode="AND",
        scope="title",
        exact="1",
        sort="publishedAt",
    )


# ==========================================================
# 🔎 ROTA DE BUSCA — NewsAPI (segura e filtrada)
# ==========================================================
@app.route("/buscar-chat", methods=["GET"])
def buscar():
    """Busca segura de notícias com sanitização, validação e fallback robusto."""

    # 🔹 Sanitiza a query
    raw_q = request.args.get("q", "", type=str).strip()
    safe_q = escape(raw_q)  # evita XSS no template

    # 🔹 Parâmetros default e validação defensiva
    lang = request.args.get("lang", "pt,en").lower()
    langs = [s.strip() for s in lang.split(",") if s.strip() in ("pt", "en")]
    if not langs:
        langs = ["pt"]

    mode = request.args.get("mode", "AND").upper()
    if mode not in ("AND", "OR"):
        mode = "AND"

    scope = request.args.get("scope", "title")
    if scope not in ("title", "title+desc"):
        scope = "title"

    sort = request.args.get("sort", "publishedAt")
    if sort not in ("publishedAt", "relevancy", "popularity"):
        sort = "publishedAt"

    exact = request.args.get("exact", "1").lower() in ("1", "true", "on", "yes")

    # 🔹 Se o campo de busca estiver vazio
    if not safe_q:
        return render_template(
            "news.html",
            articles=[],
            error="Digite algo para pesquisar.",
            q="",
            lang=",".join(langs),
            mode=mode,
            scope=scope,
            exact="1" if exact else "0",
            sort=sort,
        )

    # 🔹 Divide e normaliza termos da busca
    import re
    parts = re.split(r"[|,;]+", raw_q)
    keywords = [
        p.strip() for p in parts
        if p.strip() and 2 <= len(p.strip()) <= 64
    ][:10]  # máximo de 10 palavras

    if not keywords:
        return render_template(
            "news.html",
            articles=[],
            error="Nenhum termo de busca válido encontrado.",
            q=safe_q,
            lang=",".join(langs),
            mode=mode,
            scope=scope,
            exact="1" if exact else "0",
            sort=sort,
        )

    # 🔹 Busca via NewsAPI (função importada de news_client.py)
    articles, error = [], None
    try:
        articles, error = fetch_by_keywords_strict(
            keywords=keywords,
            languages=langs,
            hours_back=168,   # busca últimos 7 dias
            page_size=24,
            page=1,
            mode=mode,
            exact=exact,
            scope=scope,
            sort_by=sort,
        )
    except TimeoutError:
        error = "Tempo de resposta excedido. Tente novamente em alguns segundos."
    except ConnectionError:
        error = "Falha de conexão com o provedor de notícias."
    except Exception as e:
        error = f"Ocorreu um erro inesperado: {escape(str(e))}"

    # 🔹 Garante que error seja string
    if not isinstance(error, str):
        error = None

    # 🔹 Renderiza o resultado
    return render_template(
        "news.html",
        articles=articles or [],
        error=error,
        q=safe_q,
        lang=",".join(langs),
        mode=mode,
        scope=scope,
        exact="1" if exact else "0",
        sort=sort,
    )


# =========================
# 📊 DASHBOARD / RSS (HTML)
# =========================

@app.route("/dashboard-rss", methods=["GET"])
def rss_dashboard_page():
    """Página do dashboard de categorias/subcategorias (HTML)."""
    return render_template("dashboard-rss.html")

@app.route("/rss/<cat>/<sub>", methods=["GET"])
def rss_items_page(cat: str, sub: str):
    """
    Lista itens RSS de uma subcategoria (HTML).
    Usa o template rss_list.html para renderizar os cards.
    """
    items, err = fetch_category_sub(cat, sub, limit=24)
    return render_template(
        "rss_list.html",
        cat=cat,
        sub=sub,
        articles=items or [],
        error=err or "",
    )
    
 # =========================
# 🧩 RSS (API JSON)
# =========================

@app.route("/api/rss/subs/<category>", methods=["GET"])
def rss_list_subs_api(category: str):
    """
    Retorna as subcategorias disponíveis de uma categoria RSS (JSON).
    Ex.: GET /api/rss/subs/hardware
    """
    return jsonify({
        "category": category,
        "subkeys": list_subkeys(category)
    })

@app.route("/api/rss/items/<category>/<subkey>", methods=["GET"])
def rss_fetch_items_api(category: str, subkey: str):
    """
    Retorna os itens RSS de uma subcategoria (JSON).
    Ex.: GET /api/rss/items/hardware/gpus
    """
    items, err = fetch_category_sub(category, subkey, limit=12)
    return jsonify({
        "category": category,
        "subkey": subkey,
        "error": err or "",
        "items": items or [],
    })
    
    
@app.route("/rss/<cat>/<sub>/<region>")
def rss_page_region(cat, sub, region):
    # exemplo: /rss/tecnologia/gadgets/nacional
    from rss_client import FEEDS, _parse_one

    if cat not in FEEDS or sub not in FEEDS[cat]:
        return f"Subcategoria '{sub}' inválida para '{cat}'", 404

    region = region.lower()
    urls = FEEDS[cat][sub].get(region)
    if not urls:
        return f"Região '{region}' não encontrada em {cat}/{sub}", 404

    all_items = []
    for u in urls:
        all_items.extend(_parse_one(u, limit=24))

    return render_template(
        "rss_list.html",
        cat=cat,
        sub=f"{sub} ({region})",
        articles=all_items,
        error=None,
    )
   
@app.route("/assistente")
def assistente_page():
    return render_template("assistente.html")

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

