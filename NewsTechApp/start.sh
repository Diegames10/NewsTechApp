#!/bin/bash

# Script de inicialização para o container no Render
echo "Iniciando aplicação NewsTechApp..."

# Verificar se o diretório /data existe, se não, criar
if [ ! -d "/data" ]; then
    echo "Criando diretório /data..."
    mkdir -p /data
    chmod 755 /data
fi

# Verificar se o banco de dados existe, se não, inicializar
if [ ! -f "/data/app.db" ]; then
    echo "Banco de dados não encontrado. Inicializando..."
    PYTHONPATH=/app python3 -c "
from login_app.app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Banco de dados inicializado com sucesso!')
"
else
    echo "Banco de dados já existe em /data/app.db"
fi

# Iniciar a aplicação com Gunicorn
echo "Iniciando servidor Gunicorn..."
cd /app && PYTHONPATH=/app exec gunicorn login_app.app:app --bind 0.0.0.0:8080 --workers 3 --timeout 120

