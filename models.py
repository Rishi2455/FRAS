from datetime import datetime

from app import db
from utils import get_current_datetime


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=get_current_datetime)
    image_path = db.Column(db.String(255), nullable=True)
    
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: get_current_datetime().date())
    time_in = db.Column(db.Time, nullable=True)  # Changed to nullable=True to allow Absent status 
    time_out = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(20), default="Present")  # Present, Late, Absent
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Attendance {self.student_id} on {self.date}>'
