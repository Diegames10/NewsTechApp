#!/usr/bin/env python3
"""
Script para inicializar o banco de dados no Render.
Este script deve ser executado uma vez para criar as tabelas necessárias.
"""
import os
from login_app import create_app, db  # <-- corrigido

def init_database():
    app = create_app()
    with app.app_context():
        os.makedirs("/data", exist_ok=True)
        from login_app.models.user import User
        from login_app.models.post import Post
        db.create_all()
        print("Banco de dados inicializado:", app.config['SQLALCHEMY_DATABASE_URI'])

if __name__ == "__main__":
    init_database()
