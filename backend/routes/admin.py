from flask import Blueprint, jsonify, request, g
from utils import token_required
from supabase_client import supabase
from datetime import datetime
from routes.auth import make_email

admin_bp = Blueprint("admin", __name__)

def is_admin(user_id):
    try:
        res = supabase.table("users").select("role").eq("id", user_id).single().execute()
        return res.data and res.data.get("role") == "admin"
    except:
        return False

@admin_bp.route("/employees", methods=["GET"])
@token_required
def list_employees():
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
    res = supabase.table("users").select("id, username").eq("role", "employee").execute()
    return jsonify(res.data)

@admin_bp.route("/all-attendance", methods=["GET"])
@token_required
def all_attendance():
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
    
    res = supabase.table("attendance").select("*, users(username)").execute()
    data = []
    for r in res.data:
        data.append({
            "attendance_id": r.get('id'),
            "employee_id": r.get('user_id'),
            "employee_name": r.get('users', {}).get('username', 'Unknown'),
            "date": r.get('date'),
            "status": r.get('status'),
            "tap_in": r.get('tap_in'),
            "break_start": r.get('break_start'),
            "break_end": r.get('break_end'),
            "tap_out": r.get('tap_out')
        })
    return jsonify(data)

@admin_bp.route("/create-employee", methods=["POST"])
@token_required
def create_employee():
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400
        
    email = make_email(username)
    try:
        # Use auth.admin to create user without logging them in or requiring email confirmation
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        supabase.table("users").insert({
            "id": res.user.id,
            "username": username,
            "role": "employee"
        }).execute()
        
        return jsonify({"message": "Employee created successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@admin_bp.route("/edit-attendance", methods=["PUT"])
@token_required
def edit_attendance():
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
        
    data = request.get_json()
    attendance_id = data.get("attendance_id")
    update_data = {k: v for k, v in data.items() if k != "attendance_id"}
    
    try:
        supabase.table("attendance").update(update_data).eq("id", attendance_id).execute()
        return jsonify({"message": "Attendance updated successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@admin_bp.route("/delete-employee/<string:user_id>", methods=["DELETE"])
@token_required
def delete_employee(user_id):
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
        
    try:
        supabase.table("attendance").delete().eq("user_id", user_id).execute()
        supabase.table("users").delete().eq("id", user_id).execute()
        supabase.auth.admin.delete_user(user_id)
        return jsonify({"message": "Employee deleted successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@admin_bp.route("/attendance-report", methods=["GET"])
@token_required
def attendance_report():
    if not is_admin(g.user_id):
        return jsonify({"message": "Unauthorized"}), 403
        
    today = str(datetime.now().date())
    try:
        # Get count of total employees
        total_res = supabase.table("users").select("id", count="exact").eq("role", "employee").execute()
        total_employees = total_res.count if total_res.count else 0
        
        # Get count of present employees today
        present_res = supabase.table("attendance").select("id", count="exact").eq("date", today).eq("status", "Present").execute()
        present_today = present_res.count if present_res.count else 0
        
        absent_today = total_employees - present_today
        return jsonify({
            "total_employees": total_employees,
            "present_today": present_today,
            "absent_today": absent_today
        })
    except Exception as e:
        return jsonify({"message": str(e)}), 400