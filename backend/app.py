from flask import Flask, jsonify
from config import Config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.employee import employee_bp
from flask import render_template





app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db.init_app(app)
jwt = JWTManager(app)




app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(employee_bp, url_prefix="/api/employee")



@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/home")
def home_page():
    return render_template("home.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")

@app.route("/employee")
def employee_page():
    return render_template("employee.html")

@app.route("/myprofile")
def myprofile_page():
    return render_template("myprofile.html")

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok"})

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    
    
    
