# login_app/routes/posts_api.py
from flask import Blueprint, request, jsonify, abort, session
from functools import wraps
from login_app import db
from login_app.models.post import Post

# ======================================================
# 🔗 Blueprint da API de Postagens
# ======================================================
posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")

# ======================================================
# 🔒 Decorator de segurança — checa se o usuário está logado
# ======================================================
def login_required_api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)  # 401 = Unauthorized
        return fn(*args, **kwargs)
    return wrapper


# ======================================================
# 👤 Funções auxiliares de sessão e conversão
# ======================================================
def current_user():
    """Retorna o ID e nome do usuário logado."""
    uid = session.get("user_id")
    uname = session.get("username") or session.get("name") or session.get("email")
    return uid, uname or "Usuário"

def to_dict(post: Post):
    """Transforma objeto Post em dicionário JSON."""
    return {
        "id": post.id,
        "titulo": post.titulo,
        "conteudo": post.conteudo,
        "autor": post.autor,
        "user_id": post.user_id,
        "criado_em": post.criado_em.isoformat() if post.criado_em else None,
        "atualizado_em": post.atualizado_em.isoformat() if post.atualizado_em else None,
    }


# ======================================================
# 📜 Rotas da API — todas protegidas por login_required_api
# ======================================================

# 🔹 Listar postagens
@posts_api.route("", methods=["GET"])
@login_required_api
def list_posts():
    q = request.args.get("q", "").strip()
    uid, _ = current_user()

    query = Post.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Post.titulo.ilike(like),
                Post.conteudo.ilike(like),
                Post.autor.ilike(like)
            )
        )

    posts = query.order_by(Post.id.desc()).all()
    return jsonify([to_dict(p) for p in posts]), 200


# 🔹 Criar nova postagem
@posts_api.route("", methods=["POST"])
@login_required_api
def create_post():
    uid, uname = current_user()
    data = request.get_json() or {}

    titulo = data.get("titulo", "").strip()
    conteudo = data.get("conteudo", "").strip()

    if not titulo or not conteudo:
        abort(400, "Campos obrigatórios: título e conteúdo.")

    post = Post(titulo=titulo, conteudo=conteudo, user_id=uid, autor=uname)
    db.session.add(post)
    db.session.commit()

    return jsonify(to_dict(post)), 201


# 🔹 Atualizar postagem existente
@posts_api.route("/<int:pid>", methods=["PUT"])
@login_required_api
def update_post(pid):
    uid, _ = current_user()
    post = Post.query.get_or_404(pid)

    # Segurança: só o dono pode editar
    if post.user_id != uid:
        abort(403, "Você não tem permissão para editar esta postagem.")

    data = request.get_json() or {}
    post.titulo = data.get("titulo", post.titulo)
    post.conteudo = data.get("conteudo", post.conteudo)

    db.session.commit()
    return jsonify(to_dict(post)), 200


# 🔹 Deletar postagem
@posts_api.route("/<int:pid>", methods=["DELETE"])
@login_required_api
def delete_post(pid):
    uid, _ = current_user()
    post = Post.query.get_or_404(pid)

    # Segurança: só o dono pode deletar
    if post.user_id != uid:
        abort(403, "Você não tem permissão para excluir esta postagem.")

    db.session.delete(post)
    db.session.commit()
    return "", 204
