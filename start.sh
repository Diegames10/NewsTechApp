#!/bin/bash
set -euo pipefail

echo "Iniciando aplicação NewsTechApp..."

# ===== Diretórios persistentes =====
mkdir -p /data /data/uploads
chmod 755 /data

# ===== Variáveis de ambiente para Flask CLI =====
# Usa a factory diretamente (login_app:create_app)
export PYTHONPATH=/app
export FLASK_APP='login_app:create_app'
export FLASK_ENV=production

echo "Aplicando migrations..."
# 1) Tenta aplicar direto (já cobre o caso comum)
if ! flask db upgrade; then
  echo "flask db upgrade falhou ou não há migrations ainda."

  # 2) Se não há pasta migrations/, inicializa
  if [ ! -d "/app/migrations" ]; then
    echo "migrations/ não existe. Inicializando..."
    flask db init
  fi

  # 3) Gera migração (se não houver mudanças, ignora erro)
  flask db migrate -m "auto" || true

  # 4) Tenta aplicar de novo
  if ! flask db upgrade; then
    echo "flask db upgrade ainda falhou. Fallback para db.create_all()..."
    python3 - <<'PY'
from login_app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("Fallback: db.create_all() executado com sucesso.")
PY
  fi
fi

echo "Iniciando servidor Gunicorn..."
cd /app
# Usa a factory do Flask direto no Gunicorn (não precisa de wsgi.py)

exec gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 3 --timeout 120
# export FLASK_APP='login_app:create_app'  # para o Flask-Migrate (mantém factory)
