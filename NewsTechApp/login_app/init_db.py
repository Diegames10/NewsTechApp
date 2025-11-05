#!/usr/bin/env python3
"""
Script para inicializar o banco de dados no Render.
Este script deve ser executado uma vez para criar as tabelas necessárias.
"""
import os
from app import create_app, db
from login_app import create_app, db  # <-- corrigido

def init_database():
    """Inicializa o banco de dados criando todas as tabelas."""
    app = create_app()
    
    with app.app_context():
        # Criar o diretório /data se não existir
        data_dir = "/data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"Diretório {data_dir} criado.")
        
        # Criar todas as tabelas
        db.create_all()
        print("Banco de dados inicializado com sucesso!")
        print(f"Banco de dados criado em: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == "__main__":
    init_database()

