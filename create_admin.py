import argparse
from werkzeug.security import generate_password_hash
from app import app
from models import db, User


def create_or_update_admin(username, password, role="admin"):
    with app.app_context():
        existing = User.query.filter_by(username=username).first()
        hashed = generate_password_hash(password)
        if existing:
            existing.password = hashed
            existing.role = role
            db.session.commit()
            print(f"Updated user '{username}' with role '{role}'.")
        else:
            user = User(username=username, password=hashed, role=role)
            db.session.add(user)
            db.session.commit()
            print(f"Created user '{username}' with role '{role}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create or update an admin user')
    parser.add_argument('username', help='Admin username')
    parser.add_argument('password', help='Admin password')
    parser.add_argument('--role', default='admin', help='Role to assign (default: admin)')
    args = parser.parse_args()
    create_or_update_admin(args.username, args.password, args.role)
