from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))
    device_info = db.Column(db.String(300))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    date = db.Column(db.Date)
    tap_in = db.Column(db.DateTime)
    break_start = db.Column(db.DateTime)
    break_end = db.Column(db.DateTime)
    tap_out = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # Present / Half Day / Leave