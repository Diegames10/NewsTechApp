# login_app/routes/news.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, g

news_bp = Blueprint("news", __name__, template_folder="../templates")

@news_bp.route("/")
def index():
    # Renderiza a página inicial do portal (listagem de posts)
    # Se você já tem um index.html específico, ajuste o caminho abaixo
    return render_template("postagem/index.html")

@news_bp.route("/publicar", methods=["GET"])
def publicar():
    # Apenas renderiza o formulário (POST vai para a API /api/posts/)
    # Proteção de login pode ser feita aqui se necessário:
    # if not g.get("user"): return redirect(url_for("auth.login", next=request.path))
    return render_template("postagem/publicar.html")
