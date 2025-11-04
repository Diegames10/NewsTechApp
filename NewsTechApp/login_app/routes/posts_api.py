from flask import Blueprint, request, jsonify, abort, session
from functools import wraps
from login_app import db
from login_app.models.post import Post

# ======================================================
# 🔗 Blueprint da API de Postagens
# ======================================================
#posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")
posts_api = Blueprint("posts_api", __name__)

# ======================================================
# 🔒 Decorator: exige login ativo
# ======================================================
def login_required_api(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("user_id"):
            return jsonify({"error": "unauthorized"}), 401
        return fn(*a, **kw)
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
@posts_api.route("/api/posts", methods=["POST"])
@login_required_api
def create_post():
    data = request.get_json(force=True) or {}
    titulo = (data.get("titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    imagem = data.get("imagemDataURL")  # opcional (dataURL)

    if not titulo or not conteudo:
        return jsonify({"error": "Título e conteúdo são obrigatórios"}), 400

    # busca usuário logado
    user = User.query.get(session["user_id"])
    autor_nome = user.username or user.email or "Usuário"

    # cria o post conforme seu modelo
    post = Post(
        titulo=titulo,
        conteudo=conteudo,
        autor=autor_nome
    )

    # se quiser armazenar imagem no campo 'conteudo' ou criar coluna depois:
    if hasattr(Post, "imagem"):
        post.imagem = imagem

    db.session.add(post)
    db.session.commit()

    return jsonify({
        "id": post.id,
        "titulo": post.titulo,
        "conteudo": post.conteudo,
        "autor": post.autor,
        "criado_em": post.criado_em.isoformat()
    }), 201
    
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
