from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(username="admin").first()

    user.password = generate_password_hash("admin123")

    db.session.commit()

    print("Admin password reset")