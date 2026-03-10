from functools import wraps
from flask import request, jsonify, g
from supabase_client import supabase

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing token"}), 401
        
        token = auth_header.split(" ")[1]
        try:
            res = supabase.auth.get_user(token)
            if not res or not res.user:
                return jsonify({"message": "Invalid token"}), 401
            
            # Store the Supabase string UUID in the Flask global object
            g.user_id = res.user.id
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"message": str(e)}), 401
            
    return decorated
