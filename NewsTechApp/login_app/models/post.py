from login_app import db

class Post(db.Model):
    __bind_key__  = "posts"
    __tablename__ = "posts"

    id            = db.Column(db.Integer, primary_key=True)
    titulo        = db.Column(db.String(200), nullable=False)
    conteudo      = db.Column(db.Text, nullable=False)
    autor         = db.Column(db.String(120), nullable=False)
    image_filename= db.Column(db.String(255), nullable=True)  # <- para salvar o nome do arquivo
    criado_em     = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)
    atualizado_em = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())

    def to_dict(self):
        # Evita importar url_for no model; a rota pode montar a URL pública se preferir
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "autor": self.autor,
            "image_filename": self.image_filename,
            # Deixe a URL “crua” para o frontend montar, ou use exatamente este prefixo se já tiver a rota /uploads/<filename>
            "image_url": f"/uploads/{self.image_filename}" if self.image_filename else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }

    def __repr__(self):
        return f"<Post {self.id} - {self.titulo[:30]!r}>"
