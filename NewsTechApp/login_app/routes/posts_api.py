from flask import Blueprint, request, jsonify, abort, session
from functools import wraps
from login_app import db
from login_app.models.post import Post
from login_app.models.user import User

# ======================================================
# 🔗 Blueprint da API de Postagens
# ======================================================
posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")

# ======================================================
# 🔒 Decorator: exige login ativo
# ======================================================
def login_required_api(fn):
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
    user = User.query.get(uid) if uid else None
    display = (user.username or user.email or "Usuário") if user else "Usuário"
    return user, display
    
# ======================================================
# 🔧 Helper: converter objeto em dicionário JSON
# ======================================================
def to_dict(post: Post):
    return {
        "id": post.id,
        "titulo": post.titulo,
        "conteudo": post.conteudo,
        "autor": post.autor,
        "criado_em": post.criado_em.isoformat() if getattr(post, "criado_em", None) else None,
        "atualizado_em": post.atualizado_em.isoformat() if getattr(post, "atualizado_em", None) else None,
        # ❌ sem user_id porque o modelo não tem essa coluna
    }

# ======================================================
# 📜 Rotas
# ======================================================

# 🔹 Listar todas as postagens
@posts_api.route("", methods=["GET"])
@login_required_api
def list_posts():
    q = (request.args.get("q") or "").strip()
    query = Post.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Post.titulo.ilike(like),
            Post.conteudo.ilike(like),
            Post.autor.ilike(like),
        ))
    posts = query.order_by(Post.id.desc()).all()
    return jsonify([to_dict(p) for p in posts]), 200


# 🔹 Criar nova postagem (autor = usuário logado)
@posts_api.route("", methods=["POST"])
@login_required_api
def create_post():
    data = request.get_json(force=True) or {}
    titulo = (data.get("titulo") or "").strip()
    conteudo = (data.get("conteudo") or "").strip()
    imagem = data.get("imagemDataURL")  # só usa se seu modelo tiver coluna 'imagem'

    if not titulo or not conteudo:
        return jsonify({"error": "Título e conteúdo são obrigatórios"}), 400

    user, autor_nome = current_user()
    post = Post(titulo=titulo, conteudo=conteudo, autor=autor_nome)
    if hasattr(Post, "imagem"):
        post.imagem = imagem

    db.session.add(post)
    db.session.commit()

    return jsonify(to_dict(post)), 201


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
    user, display = current_user()
    post = Post.query.get_or_404(pid)
    if (post.autor or "").strip().lower() != (display or "").strip().lower():
        abort(403, "Você não tem permissão para editar esta postagem.")
    data = request.get_json(force=True) or {}
    if "titulo" in data and data["titulo"] is not None:
        post.titulo = data["titulo"].strip()
    if "conteudo" in data and data["conteudo"] is not None:
        post.conteudo = data["conteudo"].strip()
    if hasattr(Post, "imagem") and "imagemDataURL" in data:
        post.imagem = data["imagemDataURL"]
    db.session.commit()
    return jsonify(to_dict(post)), 200


# 🔹 Excluir postagem (apenas o dono pode)
@posts_api.route("/<int:pid>", methods=["DELETE"])
@login_required_api
def delete_post(pid):
    user, display = current_user()
    post = Post.query.get_or_404(pid)
    if (post.autor or "").strip().lower() != (display or "").strip().lower():
        abort(403, "Você não tem permissão para excluir esta postagem.")
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Postagem excluída com sucesso."}), 200
