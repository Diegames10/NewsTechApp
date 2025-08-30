from login_app.app import db
from flask_bcrypt import generate_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default="local")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')
