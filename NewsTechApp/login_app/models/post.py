# login_app/models/post.py
from login_app import db

class Post(db.Model):
    __tablename__ = "posts"
    __bind_key__  = "posts"  # usa /data/posts.db (via SQLALCHEMY_BINDS)

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200),  nullable=False)  # VARCHAR(200)
    conteudo  = db.Column(db.Text,        nullable=False)   # TEXT
    autor = db.Column(db.String(120), nullable=False)   # VARCHAR(120)
    criado_em = db.Column(db.DateTime,    nullable=False,   server_default=db.func.now())  # DATETIME NOT NULL
    atualizado_em = db.Column(db.DateTime,    nullable=True,    onupdate=db.func.now())        # DATETIME (nullable)
    image_filename = db.Column(db.String(255), nullable=True)    # VARCHAR(255)

    def __repr__(self):
        return f"<Post id={self.id} titulo={self.titulo!r}>"
