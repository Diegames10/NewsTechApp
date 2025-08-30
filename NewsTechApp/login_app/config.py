import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")  # Defina uma chave secreta segura para produção
    SQLALCHEMY_DATABASE_URI = f"sqlite:////data/app.db"  # Caminho para o banco de dados
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
