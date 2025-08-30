from login_app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default="local")

    def __repr__(self):
        return f'<User {self.username}>'
