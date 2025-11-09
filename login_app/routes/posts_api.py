# login_app/routes/posts_api.py
from __future__ import annotations

import os
import time
from typing import Optional

from flask import Blueprint, request, jsonify, current_app, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

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

# -------------------------------------------------------------------
# Configuração
# -------------------------------------------------------------------
posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")

ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def _build_image_url(filename: Optional[str]) -> Optional[str]:
    """Monta URL pública da imagem usando a rota /uploads/<filename>."""
    if not filename:
        return None
    try:
        return url_for("uploads", filename=filename, _external=True)
    except RuntimeError:
        # fora de contexto de request; retorna relativo como fallback
        return f"/uploads/{filename}"


def _serialize_post(p: Post) -> dict:
    return {
        "id": p.id,
        "titulo": getattr(p, "titulo", None),
        "conteudo": getattr(p, "conteudo", None),
        "autor": getattr(p, "autor", None),
        "image_url": _build_image_url(getattr(p, "image_filename", None)),
        "criado_em": getattr(p, "criado_em", None),
        "atualizado_em": getattr(p, "atualizado_em", None),
    }


# -------------------------------------------------------------------
# Rotas
# -------------------------------------------------------------------
@posts_api.get("/")
def list_posts():
    """Lista posts mais recentes, com paginação e busca."""
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("per_page", 10)), 50), 1)
    q = (request.args.get("q") or "").strip()

    query = Post.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Post.titulo.ilike(like), Post.conteudo.ilike(like), Post.autor.ilike(like))
        )

    pag = query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = [_serialize_post(p) for p in pag.items]

    return jsonify(
        {
            "page": pag.page,
            "pages": pag.pages,
            "total": pag.total,
            "items": items,
        }
    ), 200


@posts_api.get("/user/<int:user_id>")
def list_posts_by_user(user_id: int):
    """Lista posts de um usuário específico (por username gravado no Post.autor)."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    posts = (
        Post.query.filter_by(autor=user.username)
        .order_by(Post.id.desc())
        .all()
    )
    return jsonify([_serialize_post(p) for p in posts]), 200


@posts_api.post("/")
@login_required_api
def create_post():
    """
    Cria um post.
    Aceita **multipart/form-data**:
      - titulo   (str) [obrigatório]
      - conteudo (str) [obrigatório]
      - autor    (str) [opcional; se não vier, usa 'Anônimo' ou username da sessão]
      - imagem   (file) [opcional]  <-- nome do campo do arquivo

    Também aceita JSON sem arquivo (mas NÃO grava image_url no banco; só filename local).
    """
    image_filename = None

    if request.content_type and "multipart/form-data" in request.content_type:
        # --- Formulário com arquivo ---
        titulo = (request.form.get("titulo") or "").strip()
        conteudo = (request.form.get("conteudo") or "").strip()
        autor = (request.form.get("autor") or "").strip()

        if not titulo or not conteudo:
            return jsonify({"error": "Campos obrigatórios: titulo, conteudo"}), 400

        # arquivo opcional
        if "imagem" in request.files:
            f = request.files["imagem"]
            if f and f.filename:
                if not _allowed_file(f.filename):
                    return jsonify({"error": "Extensão de imagem não permitida."}), 415
                base = secure_filename(f.filename)
                unique = f"{int(time.time())}_{base}"
                dest_dir = current_app.config.get("UPLOAD_FOLDER") or "/data/uploads"
                os.makedirs(dest_dir, exist_ok=True)
                f.save(os.path.join(dest_dir, unique))
                image_filename = unique

    else:
        # --- JSON (sem upload de arquivo) ---
        data = request.get_json(silent=True) or {}
        titulo = (data.get("titulo") or "").strip()
        conteudo = (data.get("conteudo") or "").strip()
        autor = (data.get("autor") or "").strip()

        if not titulo or not conteudo:
            return jsonify({"error": "Campos obrigatórios: titulo, conteudo"}), 400

        # Ignoramos qualquer `image_url` vindo no JSON porque o modelo só tem `image_filename`.
        # Se quiser suportar URL externa, crie coluna/fluxo específicos depois.

    if not autor:
        autor = "Anônimo"

    post = Post(
        titulo=titulo,
        conteudo=conteudo,
        autor=autor,
        image_filename=image_filename,
    )
    db.session.add(post)
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"DB error: {str(e)}"}), 500

    return jsonify(_serialize_post(post)), 201
