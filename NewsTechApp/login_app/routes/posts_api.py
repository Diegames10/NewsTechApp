# login_app/routes/posts_api.py
from flask import Blueprint, request, jsonify, abort, session, current_app, url_for
from functools import wraps
from sqlalchemy import or_
from login_app import db
from login_app.models.post import Post
from login_app.models.user import User
from uuid import uuid4
import os
from werkzeug.utils import secure_filename
from login_app.utils.jwt_auth import login_required_api


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
# 👤 Util: usuário logado
# ======================================================
def current_user():
    uid = session.get("user_id")
    user = User.query.get(uid) if uid else None
    display = (user.username or user.email or "Usuário") if user else "Usuário"
    return user, display

# ======================================================
# 🧰 Util: salvar imagem no UPLOAD_FOLDER
# ======================================================
def _save_image(file):
    if not file or not getattr(file, "filename", ""):
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
        return None, "Formato de imagem não permitido"
    filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename, None

# ======================================================
# 🧱 Serializer
# ======================================================
def to_dict(post: Post):
    return {
        "id": post.id,
        "titulo": post.titulo,
        "conteudo": post.conteudo,
        "autor": post.autor,
        "criado_em": post.criado_em.isoformat() if getattr(post, "criado_em", None) else None,
        "atualizado_em": post.atualizado_em.isoformat() if getattr(post, "atualizado_em", None) else None,
        "image_url": (
            url_for("uploads", filename=post.image_filename, _external=True)
            if getattr(post, "image_filename", None) else None
        ),
    }

# ======================================================
# 📜 Rotas
# ======================================================

# 🔹 Listar (com busca opcional ?q=)
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

# 🔹 Criar (suporta multipart OU JSON)
@posts_api.route("", methods=["POST"])
@login_required_api
def create_post():
    # multipart (form + arquivo) ou JSON puro
    if request.content_type and "multipart/form-data" in request.content_type:
        titulo   = (request.form.get("titulo") or "").strip()
        autor    = (request.form.get("autor") or "").strip()
        conteudo = (request.form.get("conteudo") or "").strip()
        image    = request.files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        titulo   = (data.get("titulo") or "").strip()
        autor    = (data.get("autor") or "").strip()
        conteudo = (data.get("conteudo") or "").strip()
        image    = None  # JSON não traz arquivo

    if not titulo or not conteudo:
        return jsonify({"error": "Título e conteúdo são obrigatórios"}), 400

    # se não veio autor no form, usa o nome do usuário logado
    _, autor_display = current_user()
    autor_final = autor or autor_display

    post = Post(titulo=titulo, conteudo=conteudo, autor=autor_final)

    # trata imagem se houver
    if image and image.filename:
        fname, err = _save_image(image)
        if err:
            return jsonify({"error": err}), 400
        # exige que o modelo Post tenha a coluna image_filename
        post.image_filename = fname

    db.session.add(post)
    db.session.commit()
    return jsonify(to_dict(post)), 201

# 🔹 Atualizar (PUT; aceita trocar texto e opcionalmente a imagem)
@posts_api.route("/<int:pid>", methods=["PUT"])
@login_required_api
def update_post(pid):
    # quem está logado (para validar autoria)
    user, display = current_user()

    post = Post.query.get_or_404(pid)

    # regra simples: só o autor (mesmo nome exibido) pode editar
    if (post.autor or "").strip().lower() != (display or "").strip().lower():
        abort(403, "Você não tem permissão para editar esta postagem.")

    # ler dados (multipart ou JSON)
    if request.mimetype and "multipart/form-data" in request.mimetype:
        titulo   = (request.form.get("titulo") or "").strip()
        autor    = (request.form.get("autor") or "").strip()
        conteudo = (request.form.get("conteudo") or "").strip()
        image    = request.files.get("image")
    else:
        data     = request.get_json(silent=True) or {}
        titulo   = (data.get("titulo") or "").strip()
        autor    = (data.get("autor") or "").strip()
        conteudo = (data.get("conteudo") or "").strip()
        image    = None

    # aplicar alterações se vieram
    if titulo:   post.titulo   = titulo
    if autor:    post.autor    = autor
    if conteudo: post.conteudo = conteudo

    # tratar upload de imagem (opcional)
    if image and getattr(image, "filename", ""):
        fname, err = _save_image(image)
        if err:
            return jsonify({"error": err}), 400
        post.image_filename = fname

    db.session.commit()
    return jsonify(to_dict(post)), 200

# 🔹 Excluir
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
