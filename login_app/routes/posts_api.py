# login_app/routes/posts_api.py
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

# ✅ imports RELATIVOS (estamos dentro do pacote login_app)
from .. import db
from ..models.post import Post
from ..models.user import User

# Se você tem o utilitário de autenticação, importe relativo:
try:
    from ..utils.jwt_auth import login_required_api  # decorator esperado
except Exception:
    # Fallback seguro se util não existir ainda: passa direto (NÃO protege a rota)
    def login_required_api(fn):
        return fn

# Defina o blueprint com prefixo de API aqui (se no __init__.py você NÃO passou url_prefix)
posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")


@posts_api.get("/")
def list_posts():
    """Lista posts mais recentes (simples)."""
    posts = Post.query.order_by(Post.id.desc()).limit(50).all()
    return jsonify([
        {
            "id": p.id,
            "titulo": getattr(p, "titulo", None),
            "conteudo": getattr(p, "conteudo", None),
            "autor": getattr(p, "autor", None),
            "image_url": getattr(p, "image_url", None),
            "criado_em": getattr(p, "criado_em", None),
            "atualizado_em": getattr(p, "atualizado_em", None),
        } for p in posts
    ]), 200


@posts_api.get("/user/<int:user_id>")
def list_posts_by_user(user_id: int):
    """Lista posts de um usuário específico."""
    # ✅ agora User está importado
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    posts = Post.query.filter_by(autor=user.username).order_by(Post.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "titulo": getattr(p, "titulo", None),
            "conteudo": getattr(p, "conteudo", None),
            "autor": getattr(p, "autor", None),
            "image_url": getattr(p, "image_url", None),
            "criado_em": getattr(p, "criado_em", None),
            "atualizado_em": getattr(p, "atualizado_em", None),
        } for p in posts
    ]), 200


@posts_api.post("/")
@login_required_api
def create_post():
    """Cria um post simples (exemplo)."""
    data = request.get_json(silent=True) or {}
    titulo = (data.get("titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    autor = (data.get("autor") or "").strip()
    image_url = (data.get("image_url") or "").strip() or None

    if not titulo or not conteudo or not autor:
        return jsonify({"error": "Campos obrigatórios: titulo, conteudo, autor"}), 400

    post = Post(titulo=titulo, conteudo=conteudo, autor=autor, image_url=image_url)
    db.session.add(post)
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"DB error: {str(e)}"}), 500

    return jsonify({"ok": True, "id": post.id}), 201
