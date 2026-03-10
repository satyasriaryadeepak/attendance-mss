from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Attendance, User
from datetime import datetime, time
from calendar import monthrange

employee_bp = Blueprint("employee", __name__)

OFFICE_IP_PREFIX = "192.168.1."


# -----------------------------------
# CHECK ADMIN DEVICE / WIFI
# -----------------------------------
def check_office_network():

    client_ip = request.remote_addr

    if not (
        (client_ip and client_ip.startswith(OFFICE_IP_PREFIX))
        or client_ip.startswith("127.")
        or client_ip == "127.0.0.1"
        or client_ip == "::1"
    ):
        return False

    return True


# -----------------------------------
# DELETE PREVIOUS MONTH DATA
# -----------------------------------
def auto_delete_previous_month(user_id):

    now = datetime.now()
    start_date = datetime(now.year, now.month, 1).date()

    Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date < start_date
    ).delete()

    db.session.commit()


# -----------------------------------
# AUTO SUNDAY ATTENDANCE
# -----------------------------------
def auto_mark_sunday(user_id):

    today = datetime.now().date()

    if today.weekday() == 6:

        existing = Attendance.query.filter_by(
            user_id=user_id,
            date=today
        ).first()

        if not existing:

            attendance = Attendance(
                user_id=user_id,
                date=today,
                tap_in=datetime.combine(today, time(9,0)),
                break_start=datetime.combine(today, time(13,0)),
                break_end=datetime.combine(today, time(14,0)),
                tap_out=datetime.combine(today, time(18,0)),
                status="Present"
            )

            db.session.add(attendance)
            db.session.commit()


# -----------------------------------
# EMPLOYEE DASHBOARD
# -----------------------------------
@employee_bp.route('/employee')
def employee_dashboard():
    return render_template('employee.html')
#
@employee_bp.route("/myprofile")
def myprofile_page():
    return render_template("myprofile.html")

# -----------------------------------
# ABOUT PAGE
# -----------------------------------

@employee_bp.route("/about")
def about_page():
    return render_template("about.html")
# -----------------------------------
# LOGIN (MORNING ATTENDANCE)
# -----------------------------------
@employee_bp.route("/login", methods=["POST"])
@jwt_required()
def login():

    user_id = int(get_jwt_identity())

    auto_delete_previous_month(user_id)
    auto_mark_sunday(user_id)

    today = datetime.now().date()
    now = datetime.now()

    if not check_office_network():
        return jsonify({"message": "Access allowed only from office WiFi"}), 403


    device = request.headers.get("User-Agent")
    user = User.query.get(user_id)

    if user.device_info and user.device_info != device:
        return jsonify({"message": "Login allowed only from registered device"}), 403

    if not user.device_info:
        user.device_info = device
        db.session.commit()


    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if existing:
        return jsonify({"message": "Already tapped in today"}), 400


    status = "Present"

    if now.time() > time(10,10):
        status = "Half Day"


    attendance = Attendance(
        user_id=user_id,
        date=today,
        tap_in=now,
        status=status
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({"message": status})


# -----------------------------------
# AFTERNOON BREAK END
# -----------------------------------
@employee_bp.route("/break-end", methods=["POST"])
@jwt_required()
def break_end():

    user_id = int(get_jwt_identity())

    today = datetime.now().date()
    now = datetime.now()

    record = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not record:

        record = Attendance(
            user_id=user_id,
            date=today,
            break_end=now,
            status="Half Day"
        )

        db.session.add(record)
        db.session.commit()

        return jsonify({"message": "Half day recorded"})


    record.break_end = now

    if now.time() > time(14,10):

        if record.status == "Half Day":
            record.status = "Absent"
        else:
            record.status = "Half Day"

    db.session.commit()

    return jsonify({"message": "Break end recorded"})


# -----------------------------------
# TAP OUT
# -----------------------------------
@employee_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    user_id = int(get_jwt_identity())
    today = datetime.now().date()

    if not check_office_network():
        return jsonify({"message": "Access allowed only from office WiFi"}), 403


    attendance = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not attendance or attendance.tap_out:
        return jsonify({"message": "Cannot logout"}), 400

    attendance.tap_out = datetime.now()
    db.session.commit()

    return jsonify({"message": "Logout successful"})


# -----------------------------------
# MONTHLY SUMMARY (FOR PROFILE)
# -----------------------------------
@employee_bp.route("/summary", methods=["GET"])
@jwt_required()
def monthly_summary():

    user_id = int(get_jwt_identity())

    now = datetime.now()
    month = now.month
    year = now.year

    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, monthrange(year, month)[1]).date()

    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    present = 0
    half = 0

    for r in records:

        if r.status == "Present":
            present += 1
        elif r.status == "Half Day":
            half += 1

    return jsonify({
        "total_days": len(records),
        "present_days": present,
        "half_days": half
    })


# -----------------------------------
# ATTENDANCE PERCENTAGE
# -----------------------------------
@employee_bp.route("/percentage", methods=["GET"])
@jwt_required()
def attendance_percentage():

    user_id = int(get_jwt_identity())

    now = datetime.now()
    month = now.month
    year = now.year

    total_days = monthrange(year, month)[1]

    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, total_days).date()

    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    present = 0
    half = 0

    for r in records:

        if r.status == "Present":
            present += 1
        elif r.status == "Half Day":
            half += 1

    score = present + (half * 0.5)

    percentage = (score / total_days) * 100 if total_days else 0

    return jsonify({
        "attendance_percentage": round(percentage,2)
    })


# -----------------------------------
# PROFILE
# -----------------------------------
@employee_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role
    })


# -----------------------------------
# MY ATTENDANCE HISTORY
# -----------------------------------
@employee_bp.route("/my-attendance", methods=["GET"])
@jwt_required()
def my_attendance():

    user_id = int(get_jwt_identity())

    records = Attendance.query.filter_by(user_id=user_id)\
        .order_by(Attendance.date.desc()).all()

    data = []

    for r in records:

        data.append({
            "date": str(r.date),
            "tap_in": str(r.tap_in) if r.tap_in else None,
            "break_start": str(r.break_start) if r.break_start else None,
            "break_end": str(r.break_end) if r.break_end else None,
            "tap_out": str(r.tap_out) if r.tap_out else None,
            "status": r.status
        })

    return jsonify(data)