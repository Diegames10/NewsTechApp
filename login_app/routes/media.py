# login_app/routes/media.py
import os
from flask import Blueprint, current_app, send_from_directory, abort

media_bp = Blueprint("media", __name__)

@media_bp.route("/media/<path:filename>")
def media_file(filename):
    """Entrega segura de arquivos enviados para /data/uploads"""
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "/data/uploads")
    file_path = os.path.join(upload_dir, filename)

    if not os.path.isfile(file_path):
        abort(404)

    return send_from_directory(upload_dir, filename)
