from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Attendance
from werkzeug.security import generate_password_hash
from datetime import datetime
from calendar import monthrange

admin_bp = Blueprint("admin", __name__)


# -----------------------------
# Utility: Check Admin Access
# -----------------------------
def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == "admin"


# -----------------------------
# 1️⃣ List All Employees
# -----------------------------
@admin_bp.route("/employees", methods=["GET"])
@jwt_required()
def list_employees():

    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({"message": "Unauthorized"}), 403

    users = User.query.filter_by(role="employee").all()

    return jsonify([
        {
            "id": u.id,
            "username": u.username
        }
        for u in users
    ])


# -----------------------------
# 2️⃣ View All Attendance
# -----------------------------
@admin_bp.route("/all-attendance", methods=["GET"])
@jwt_required()
def all_attendance():

    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({"message": "Unauthorized"}), 403

    records = Attendance.query.all()

    data = []

    for r in records:

        employee = User.query.get(r.user_id)

        data.append({
            "attendance_id": r.id,
            "employee_id": employee.id,
            "employee_name": employee.username,
            "date": str(r.date),
            "status": r.status,
            "tap_in": str(r.tap_in) if r.tap_in else None,
            "break_start": str(r.break_start) if r.break_start else None,
            "break_end": str(r.break_end) if r.break_end else None,
            "tap_out": str(r.tap_out) if r.tap_out else None
        })

    return jsonify(data)


# -----------------------------
# 3️⃣ Create Employee
# -----------------------------
@admin_bp.route("/create-employee", methods=["POST"])
@jwt_required()
def create_employee():

    admin_id = int(get_jwt_identity())

    if not is_admin(admin_id):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    existing = User.query.filter_by(username=username).first()

    if existing:
        return jsonify({"message": "Employee already exists"}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        password=hashed_password,
        role="employee"
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Employee created successfully"
    })


# -----------------------------
# 4️⃣ Edit Attendance
# -----------------------------
@admin_bp.route("/edit-attendance", methods=["PUT"])
@jwt_required()
def edit_attendance():

    admin_id = int(get_jwt_identity())

    if not is_admin(admin_id):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()

    attendance_id = data.get("attendance_id")

    record = Attendance.query.get(attendance_id)

    if not record:
        return jsonify({"message": "Attendance record not found"}), 404

    record.status = data.get("status", record.status)
    record.tap_in = data.get("tap_in", record.tap_in)
    record.break_start = data.get("break_start", record.break_start)
    record.break_end = data.get("break_end", record.break_end)
    record.tap_out = data.get("tap_out", record.tap_out)

    db.session.commit()

    return jsonify({"message": "Attendance updated successfully"})


# -----------------------------
# 5️⃣ Delete Employee
# -----------------------------
@admin_bp.route("/delete-employee/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(user_id):

    admin_id = int(get_jwt_identity())

    if not is_admin(admin_id):
        return jsonify({"message": "Unauthorized"}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "Employee not found"}), 404

    Attendance.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Employee deleted successfully"})


# -----------------------------
# 6️⃣ Live Attendance Report
# -----------------------------
@admin_bp.route("/attendance-report", methods=["GET"])
@jwt_required()
def attendance_report():

    admin_id = int(get_jwt_identity())

    if not is_admin(admin_id):
        return jsonify({"message": "Unauthorized"}), 403

    today = datetime.now().date()

    total_employees = User.query.filter_by(role="employee").count()

    present_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == "Present"
    ).count()

    absent_today = total_employees - present_today

    return jsonify({
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today
    })