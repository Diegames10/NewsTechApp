# wsgi.py (raiz do repo)
from login_app import create_app
app = create_app()
# exec gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 3 --timeout 120
