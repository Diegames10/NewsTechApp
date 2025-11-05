from login_app import db

class Post(db.Model):
    __bind_key__ = "posts"
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(120), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())
