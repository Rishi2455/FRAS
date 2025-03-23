import os
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from sqlalchemy import func

from app import app, db
from models import Student, Attendance


# Home route
@app.route('/')
def index():
    return render_template('index.html')


# Student routes
@app.route('/students')
def list_students():
    students = Student.query.all()
    return render_template('students/list.html', students=students)


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        email = request.form.get('email')

        # Validate inputs
        if not student_id or not name:
            flash('Student ID and Name are required!', 'danger')
            return redirect(url_for('add_student'))

        # Check if student ID already exists
        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists!', 'danger')
            return redirect(url_for('add_student'))

        # Create new student
        new_student = Student(
            student_id=student_id,
            name=name,
            email=email
        )
        
        # Handle image upload later
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('list_students'))
        
    return render_template('students/add.html')


@app.route('/students/<int:id>')
def view_student(id):
    student = Student.query.get_or_404(id)
    attendances = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
    return render_template('students/view.html', student=student, attendances=attendances)


@app.route('/students/<int:id>/edit', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        student.student_id = request.form.get('student_id')
        student.name = request.form.get('name')
        student.email = request.form.get('email')
        
        # Handle image upload later
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('list_students'))
        
    return render_template('students/edit.html', student=student)


@app.route('/students/<int:id>/delete', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('list_students'))


# Attendance routes
@app.route('/attendance')
def attendance():
    today = datetime.now().date()
    date_str = request.args.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today
    
    # Get all students
    students = Student.query.all()
    
    # Get attendance for selected date
    attendances = {a.student_id: a for a in Attendance.query.filter_by(date=selected_date).all()}
    
    return render_template('attendance/mark.html', 
                          students=students, 
                          attendances=attendances, 
                          selected_date=selected_date)


@app.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    date_str = request.form.get('date')
    student_ids = request.form.getlist('student_id')
    statuses = request.form.getlist('status')
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date = datetime.now().date()
    
    # Delete existing attendance records for this date
    Attendance.query.filter_by(date=date).delete()
    
    # Add new attendance records
    for i, student_id in enumerate(student_ids):
        if i < len(statuses):
            status = statuses[i]
            attendance = Attendance(
                student_id=student_id,
                date=date,
                time_in=datetime.now().time(),
                status=status
            )
            db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('attendance', date=date_str))


@app.route('/attendance/report')
def attendance_report():
    students = Student.query.all()
    
    # Calculate attendance statistics for each student
    stats = []
    for student in students:
        total = Attendance.query.filter_by(student_id=student.id).count()
        present = Attendance.query.filter_by(student_id=student.id, status='Present').count()
        late = Attendance.query.filter_by(student_id=student.id, status='Late').count()
        absent = Attendance.query.filter_by(student_id=student.id, status='Absent').count()
        
        stats.append({
            'student': student,
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_rate': (present + late) / total * 100 if total > 0 else 0
        })
    
    return render_template('attendance/report.html', stats=stats)


@app.route('/attendance/export')
def export_attendance():
    # This will be implemented later
    flash('Export feature is not yet implemented', 'info')
    return redirect(url_for('attendance_report'))


# Create static folder for student images
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config.get('UPLOAD_FOLDER', 'student_images'), filename)


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500