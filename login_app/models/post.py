# login_app/models/post.py
from flask import url_for
from .. import db

class Post(db.Model):
    __tablename__  = "posts"
    __bind_key__   = "posts"

    id             = db.Column(db.Integer, primary_key=True)
    titulo         = db.Column(db.String(200),  nullable=False)
    conteudo       = db.Column(db.Text,        nullable=False)
    autor          = db.Column(db.String(120), nullable=False)
    criado_em      = db.Column(db.DateTime,    nullable=False, server_default=db.func.now())
    atualizado_em  = db.Column(db.DateTime,    nullable=True,  onupdate=db.func.now())
    image_filename = db.Column(db.String(255), nullable=True)

    def to_dict(self, external: bool = True):
        """
        external=True -> gera URL absoluta (https://.../uploads/arquivo.png)
        external=False -> gera URL relativa (/uploads/arquivo.png)
        """
        if self.image_filename:
            img = url_for(
                "uploads", filename=self.image_filename,
                _external=external, _scheme="https" if external else None
            )
        else:
            # compatibilidade: se por acaso existir um campo legado
            img = getattr(self, "image_url", None) or getattr(self, "image", None)

        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "autor": self.autor,
            "image_url": img,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
        }

    def __repr__(self):
        return f"<Post id={self.id} titulo={self.titulo!r}>"
