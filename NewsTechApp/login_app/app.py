from login_app import create_app

# Instância da app para WSGI/Gunicorn
app = create_app()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)


