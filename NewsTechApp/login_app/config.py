import os

class Config:
    SECRET_KEY = "uma_chave_secreta_aqui"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/app.db"  # caminho absoluto no disco persistente

    # Novo bind para postagens
    POSTS_DATABASE_URI = os.environ.get(
        "POSTS_DATABASE_URI", "sqlite:////data/posts.db"
    )
    SQLALCHEMY_BINDS = {
        "posts": POSTS_DATABASE_URI,
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
