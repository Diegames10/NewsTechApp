# login_app/routes/posts_api.py
from flask import Blueprint, request, jsonify, abort
from login_app import db
from login_app.models.post import Post

posts_api = Blueprint("posts_api", __name__, url_prefix="/api/posts")

def to_dict(p: Post):
    return {
        "id": p.id,
        "titulo": p.titulo,
        "conteudo": p.conteudo,
        "autor": p.autor,
        "criado_em": p.criado_em.isoformat() if p.criado_em else None,
        "atualizado_em": p.atualizado_em.isoformat() if p.atualizado_em else None,
    }

@posts_api.get("")
def list_posts():
    q = request.args.get("q", "").strip()
    qry = Post.query
    if q:
        like = f"%{q}%"
        qry = qry.filter(
            db.or_(Post.titulo.ilike(like), Post.conteudo.ilike(like), Post.autor.ilike(like))
        )
    items = qry.order_by(Post.id.desc()).all()
    return jsonify([to_dict(p) for p in items])

@posts_api.get("/<int:pid>")
def get_post(pid):
    p = Post.query.get_or_404(pid)
    return jsonify(to_dict(p))

@posts_api.post("")
def create_post():
    data = request.get_json(force=True, silent=True) or {}
    for k in ("titulo", "conteudo", "autor"):
        if not data.get(k):
            abort(400, f"Campo obrigatório: {k}")
    p = Post(titulo=data["titulo"], conteudo=data["conteudo"], autor=data["autor"])
    db.session.add(p)
    db.session.commit()
    return jsonify(to_dict(p)), 201

@posts_api.put("/<int:pid>")
def update_post(pid):
    p = Post.query.get_or_404(pid)
    data = request.get_json(force=True, silent=True) or {}
    p.titulo = data.get("titulo", p.titulo)
    p.conteudo = data.get("conteudo", p.conteudo)
    p.autor = data.get("autor", p.autor)
    db.session.commit()
    return jsonify(to_dict(p))

@posts_api.delete("/<int:pid>")
def delete_post(pid):
    p = Post.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return "", 204
