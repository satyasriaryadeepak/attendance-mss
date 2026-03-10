from flask import Blueprint, request, jsonify
from models import db, User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)


# -----------------------------
# Register User
# -----------------------------
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.json

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return jsonify({"message": "username, password, role required"}), 400

    existing = User.query.filter_by(username=username).first()

    if existing:
        return jsonify({"message": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)

    user = User(username=username, password=hashed_pw, role=role)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully"})

# -----------------------------
# Login User
# -----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid password"}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": token,
        "role": user.role
    })