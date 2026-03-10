from flask import Blueprint, request, jsonify
from supabase_client import supabase

auth_bp = Blueprint("auth", __name__)

# Utility to convert username to a valid email format for Supabase Auth
def make_email(username):
    return f"{username}@mss.com"

# -----------------------------
# Register User (Optional, if needed directly)
# -----------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return jsonify({"message": "username, password, role required"}), 400

    email = make_email(username)

    try:
        # Create user in Supabase Auth
        res = supabase.auth.sign_up({"email": email, "password": password})
        if not res.user:
            return jsonify({"message": "User creation failed"}), 400
        
        # Save user to public.users table
        supabase.table("users").insert({
            "id": res.user.id,
            "username": username,
            "role": role
        }).execute()
        
        return jsonify({"message": "User created successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400

# -----------------------------
# Login User
# -----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    email = make_email(username)

    try:
        # Authenticate with Supabase Auth
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if not res.session:
            return jsonify({"message": "Invalid credentials"}), 401
            
        # Get user role from public.users table
        user_record = supabase.table("users").select("role").eq("id", res.user.id).single().execute()
        role = user_record.data.get("role") if user_record.data else "employee"

        return jsonify({
            "access_token": res.session.access_token,
            "role": role
        })
    except Exception as e:
        return jsonify({"message": "Invalid password or username. " + str(e)}), 401