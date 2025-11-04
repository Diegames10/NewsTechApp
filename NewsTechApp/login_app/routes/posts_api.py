from flask import Blueprint, request, jsonify, abort, session
from functools import wraps
from login_app import db
from login_app.models.post import Post

# ======================================================
# 🔗 Blueprint da API de Postagens
# ======================================================
posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")

# ======================================================
# 🔒 Decorator: exige login ativo
# ======================================================
def login_required_api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)  # 401 Unauthorized
        return fn(*args, **kwargs)
    return wrapper

# ======================================================
# 👤 Função auxiliar: retorna dados do usuário logado
# ======================================================
def current_user():
    uid = session.get("user_id")
    uname = (
        session.get("username")
        or session.get("name")
        or session.get("email")
        or "Usuário"
    )
    return uid, uname

# ======================================================
# 🔧 Helper: converter objeto em dicionário JSON
# ======================================================
def to_dict(post: Post):
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
# 📜 Rotas
# ======================================================

# 🔹 Listar todas as postagens
@posts_api.route("", methods=["GET"])
@login_required_api
def list_posts():
    q = request.args.get("q", "").strip()
    query = Post.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Post.titulo.ilike(like),
                Post.conteudo.ilike(like),
                Post.autor.ilike(like),
            )
        )
    posts = query.order_by(Post.id.desc()).all()
    return jsonify([to_dict(p) for p in posts]), 200


# 🔹 Criar nova postagem (autor = usuário logado)
@posts_api.route("", methods=["POST"])
@login_required_api
def create_post():
    uid, uname = current_user()
    data = request.get_json() or {}

    titulo = data.get("titulo", "").strip()
    conteudo = data.get("conteudo", "").strip()
    if not titulo or not conteudo:
        abort(400, "Campos obrigatórios: título e conteúdo.")

    # 🔸 Define automaticamente o autor
    post = Post(
        titulo=titulo,
        conteudo=conteudo,
        autor=uname,   # <— nome do usuário logado
        user_id=uid    # <— ID do usuário logado
    )

    db.session.add(post)
    db.session.commit()
    return jsonify(to_dict(post)), 201


# 🔹 Atualizar postagem (apenas o dono pode)
@posts_api.route("/<int:pid>", methods=["PUT"])
@login_required_api
def update_post(pid):
    uid, _ = current_user()
    post = Post.query.get_or_404(pid)
    if post.user_id != uid:
        abort(403, "Você não tem permissão para editar esta postagem.")

    data = request.get_json() or {}
    if "titulo" in data:
        post.titulo = data["titulo"].strip()
    if "conteudo" in data:
        post.conteudo = data["conteudo"].strip()

    db.session.commit()
    return jsonify(to_dict(post)), 200


# 🔹 Excluir postagem (apenas o dono pode)
@posts_api.route("/<int:pid>", methods=["DELETE"])
@login_required_api
def delete_post(pid):
    uid, _ = current_user()
    post = Post.query.get_or_404(pid)
    if post.user_id != uid:
        abort(403, "Você não tem permissão para excluir esta postagem.")
    db.session.delete(post)
    db.session.commit()
    return "", 204
