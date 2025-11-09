#!/bin/bash
set -e

echo "Iniciando aplicação NewsTechApp..."

# Garante diretórios persistentes
mkdir -p /data /data/uploads
chmod 755 /data

# Variáveis de ambiente para Flask CLI
export PYTHONPATH=/app
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# ===== Migrations seguras =====
echo "Aplicando migrations..."
if [ ! -d "/app/migrations" ]; then
  echo "migrations/ não existe. Inicializando..."
  flask db init
fi

# Tenta gerar migração (se não houver mudanças, ignora erro)
flask db migrate -m "auto" || true

# Tenta aplicar; se falhar por esquemas, fazemos fallback create_all()
if ! flask db upgrade; then
  echo "flask db upgrade falhou. Executando fallback db.create_all()..."
  python3 - <<'PY'
from login_app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("Fallback: db.create_all() executado.")
PY
fi

echo "Iniciando servidor Gunicorn..."
cd /app
exec gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 3 --timeout 120
