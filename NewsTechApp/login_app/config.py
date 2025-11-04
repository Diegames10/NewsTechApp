class Config:
    # chave secreta do Flask
    SECRET_KEY = "uma_chave_secreta_aqui"

    # banco principal (usuários, autenticação)
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/app.db"  # caminho absoluto no disco persistente

    # segundo banco (postagens)
    POSTS_DATABASE_URI = "sqlite:////data/posts.db"

    # dicionário de binds: o SQLAlchemy usa isso para identificar o segundo banco
    SQLALCHEMY_BINDS = {
        "posts": POSTS_DATABASE_URI
    }

    # configurações gerais
    SQLALCHEMY_TRACK_MODIFICATIONS = False
