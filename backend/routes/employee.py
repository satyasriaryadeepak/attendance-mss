from flask import Blueprint, jsonify, request, render_template, g
from utils import token_required
from supabase_client import supabase
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
    start_date = str(datetime(now.year, now.month, 1).date())
    try:
        supabase.table("attendance").delete().eq("user_id", user_id).lt("date", start_date).execute()
    except Exception:
        pass


# -----------------------------------
# AUTO SUNDAY ATTENDANCE
# -----------------------------------
def auto_mark_sunday(user_id):
    today = datetime.now().date()
    today_str = str(today)
    
    if today.weekday() == 6:
        try:
            res = supabase.table("attendance").select("id").eq("user_id", user_id).eq("date", today_str).execute()
            if not res.data:
                supabase.table("attendance").insert({
                    "user_id": user_id,
                    "date": today_str,
                    "tap_in": str(datetime.combine(today, time(9,0))),
                    "break_start": str(datetime.combine(today, time(13,0))),
                    "break_end": str(datetime.combine(today, time(14,0))),
                    "tap_out": str(datetime.combine(today, time(18,0))),
                    "status": "Present"
                }).execute()
        except Exception:
            pass


# -----------------------------------
# EMPLOYEE DASHBOARD
# -----------------------------------
@employee_bp.route('/employee')
def employee_dashboard():
    return render_template('employee.html')

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
@token_required
def login():
    user_id = g.user_id
    
    auto_delete_previous_month(user_id)
    auto_mark_sunday(user_id)

    today = str(datetime.now().date())
    now = datetime.now()

    if not check_office_network():
        return jsonify({"message": "Access allowed only from office WiFi"}), 403

    device = request.headers.get("User-Agent")
    
    try:
        user_res = supabase.table("users").select("device_info").eq("id", user_id).single().execute()
        db_device = user_res.data.get("device_info") if user_res.data else None
    except Exception:
        return jsonify({"message": "Failed to fetch user data"}), 500

    if db_device and db_device != device:
        return jsonify({"message": "Login allowed only from registered device"}), 403

    if not db_device:
        supabase.table("users").update({"device_info": device}).eq("id", user_id).execute()

    try:
        existing = supabase.table("attendance").select("id").eq("user_id", user_id).eq("date", today).execute()
        if existing.data:
            return jsonify({"message": "Already tapped in today"}), 400
    except Exception:
        pass

    status = "Present"
    if now.time() > time(10,10):
        status = "Half Day"

    try:
        supabase.table("attendance").insert({
            "user_id": user_id,
            "date": today,
            "tap_in": str(now),
            "status": status
        }).execute()
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": status})


# -----------------------------------
# AFTERNOON BREAK END
# -----------------------------------
@employee_bp.route("/break-end", methods=["POST"])
@token_required
def break_end():
    user_id = g.user_id
    today = str(datetime.now().date())
    now = datetime.now()

    try:
        res = supabase.table("attendance").select("*").eq("user_id", user_id).eq("date", today).execute()
        
        if not res.data:
            supabase.table("attendance").insert({
                "user_id": user_id,
                "date": today,
                "break_end": str(now),
                "status": "Half Day"
            }).execute()
            return jsonify({"message": "Half day recorded"})
            
        record = res.data[0]
        attendance_id = record.get("id")
        current_status = record.get("status")
        
        new_status = current_status
        if now.time() > time(14,10):
            new_status = "Absent" if current_status == "Half Day" else "Half Day"
            
        supabase.table("attendance").update({
            "break_end": str(now),
            "status": new_status
        }).eq("id", attendance_id).execute()
        
        return jsonify({"message": "Break end recorded"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400


# -----------------------------------
# TAP OUT
# -----------------------------------
@employee_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    user_id = g.user_id
    today = str(datetime.now().date())

    if not check_office_network():
        return jsonify({"message": "Access allowed only from office WiFi"}), 403

    try:
        res = supabase.table("attendance").select("id, tap_out").eq("user_id", user_id).eq("date", today).execute()
        if not res.data or res.data[0].get("tap_out"):
            return jsonify({"message": "Cannot logout"}), 400
            
        attendance_id = res.data[0].get("id")
        supabase.table("attendance").update({"tap_out": str(datetime.now())}).eq("id", attendance_id).execute()
        return jsonify({"message": "Logout successful"})
    except Exception as e:
        return jsonify({"message": str(e)}), 400


# -----------------------------------
# MONTHLY SUMMARY (FOR PROFILE)
# -----------------------------------
@employee_bp.route("/summary", methods=["GET"])
@token_required
def monthly_summary():
    user_id = g.user_id
    now = datetime.now()
    month = now.month
    year = now.year

    start_date = str(datetime(year, month, 1).date())
    end_date = str(datetime(year, month, monthrange(year, month)[1]).date())

    try:
        res = supabase.table("attendance").select("status").eq("user_id", user_id).gte("date", start_date).lte("date", end_date).execute()
        records = res.data
    except Exception:
        records = []

    present = 0
    half = 0

    for r in records:
        if r.get("status") == "Present":
            present += 1
        elif r.get("status") == "Half Day":
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
@token_required
def attendance_percentage():
    user_id = g.user_id
    now = datetime.now()
    month = now.month
    year = now.year
    total_days = monthrange(year, month)[1]

    start_date = str(datetime(year, month, 1).date())
    end_date = str(datetime(year, month, total_days).date())

    try:
        res = supabase.table("attendance").select("status").eq("user_id", user_id).gte("date", start_date).lte("date", end_date).execute()
        records = res.data
    except Exception:
        records = []

    present = 0
    half = 0

    for r in records:
        if r.get("status") == "Present":
            present += 1
        elif r.get("status") == "Half Day":
            half += 1

    score = present + (half * 0.5)
    percentage = (score / total_days) * 100 if total_days else 0

    return jsonify({
        "attendance_percentage": round(percentage, 2)
    })


# -----------------------------------
# PROFILE
# -----------------------------------
@employee_bp.route("/profile", methods=["GET"])
@token_required
def profile():
    user_id = g.user_id
    try:
        res = supabase.table("users").select("id, username, role").eq("id", user_id).single().execute()
        return jsonify(res.data) if res.data else jsonify({"message": "User not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 400


# -----------------------------------
# MY ATTENDANCE HISTORY
# -----------------------------------
@employee_bp.route("/my-attendance", methods=["GET"])
@token_required
def my_attendance():
    user_id = g.user_id
    
    try:
        res = supabase.table("attendance").select("*").eq("user_id", user_id).order("date", desc=True).execute()
        records = res.data
        
        data = []
        for r in records:
            data.append({
                "date": r.get('date'),
                "tap_in": r.get('tap_in'),
                "break_start": r.get('break_start'),
                "break_end": r.get('break_end'),
                "tap_out": r.get('tap_out'),
                "status": r.get('status')
            })
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"message": str(e)}), 400