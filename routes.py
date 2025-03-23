import os
import csv
import base64
import uuid
from io import StringIO
from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import app, db
from models import Student, Attendance

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'student_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_file(file):
    """Save an uploaded file to the uploads directory"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add a UUID to make the filename unique
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        # Ensure the upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return unique_filename
    return None

def save_base64_image(base64_data):
    """Save a base64 encoded image to the uploads directory"""
    try:
        # Extract the base64 content from the data URL
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}_webcam.jpg"
        
        # Ensure the upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the image
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return unique_filename
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return None


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
        
        # Handle image upload
        image_filename = None
        
        # Check for webcam image (base64 data)
        webcam_image = request.form.get('webcam_image')
        if webcam_image:
            image_filename = save_base64_image(webcam_image)
        
        # Check for file upload
        elif 'student_image' in request.files:
            image_file = request.files['student_image']
            image_filename = save_image_file(image_file)
        
        if image_filename:
            new_student.image_path = image_filename
        
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
        
        # Handle image upload
        image_filename = None
        
        # Check for webcam image (base64 data)
        webcam_image = request.form.get('webcam_image')
        if webcam_image:
            image_filename = save_base64_image(webcam_image)
        
        # Check for file upload
        elif 'student_image' in request.files:
            image_file = request.files['student_image']
            if image_file.filename:  # Only update if a new file is selected
                image_filename = save_image_file(image_file)
        
        if image_filename:
            # Delete old image file if it exists
            if student.image_path:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], student.image_path)
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error removing old image: {e}")
            
            student.image_path = image_filename
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('view_student', id=student.id))
        
    return render_template('students/edit.html', student=student)


@app.route('/students/<int:id>/delete', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    
    # Delete student image if it exists
    if student.image_path:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], student.image_path)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error removing student image: {e}")
    
    # Delete the student and their attendance records
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

@app.route('/api/student_attendance')
def api_student_attendance():
    """API endpoint to get attendance data for a specific student in a date range"""
    student_id = request.args.get('student_id')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not student_id or not start_date_str or not end_date_str:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    # Query attendance records for this student in the date range
    attendance_records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    # Format the data for the response
    records = []
    for record in attendance_records:
        records.append({
            "date": record.date.strftime('%Y-%m-%d'),
            "status": record.status,
            "time_in": record.time_in.strftime('%H:%M:%S') if record.time_in else None
        })
    
    # Calculate summary stats
    present = sum(1 for record in attendance_records if record.status == 'Present')
    late = sum(1 for record in attendance_records if record.status == 'Late')
    absent = sum(1 for record in attendance_records if record.status == 'Absent')
    
    return jsonify({
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name
        },
        "attendance_records": records,
        "stats": {
            "present": present,
            "late": late,
            "absent": absent,
            "total": len(records)
        }
    })

@app.route('/api/date_attendance')
def api_date_attendance():
    """API endpoint to get attendance data for all students on a specific date"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({"error": "Missing date parameter"}), 400
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    # Get all students
    students = Student.query.all()
    
    # Get attendance records for the selected date
    attendance_records = {a.student_id: a for a in Attendance.query.filter_by(date=selected_date).all()}
    
    # Format the data for the response
    records = []
    for student in students:
        attendance = attendance_records.get(student.id)
        records.append({
            "student_id": student.id,
            "name": student.name,
            "display_id": student.student_id,
            "status": attendance.status if attendance else "Absent",
            "time_in": attendance.time_in.strftime('%H:%M:%S') if attendance and attendance.time_in else None
        })
    
    # Calculate summary stats
    present = sum(1 for record in records if record['status'] == 'Present')
    late = sum(1 for record in records if record['status'] == 'Late')
    absent = sum(1 for record in records if record['status'] == 'Absent')
    total = len(records)
    
    return jsonify({
        "date": date_str,
        "attendance_records": records,
        "stats": {
            "present": present,
            "late": late,
            "absent": absent,
            "total": total,
            "attendance_rate": ((present + late) / total * 100) if total > 0 else 0
        }
    })


@app.route('/attendance/export', methods=['GET', 'POST'])
def export_attendance():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        export_format = request.form.get('format', 'csv')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Please enter valid dates', 'danger')
            return redirect(url_for('export_attendance'))
        
        # Query attendance data for the date range
        attendances = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date).all()
        
        # Get all students
        students = {student.id: student for student in Student.query.all()}
        
        if export_format == 'csv':
            # Create CSV file in memory
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Date', 'Student ID', 'Student Name', 'Status', 'Time In', 'Time Out', 'Notes'])
            
            # Write data
            for attendance in attendances:
                student = students.get(attendance.student_id)
                if student:
                    writer.writerow([
                        attendance.date.strftime('%Y-%m-%d'),
                        student.student_id,
                        student.name,
                        attendance.status,
                        attendance.time_in.strftime('%H:%M:%S') if attendance.time_in else '',
                        attendance.time_out.strftime('%H:%M:%S') if attendance.time_out else '',
                        attendance.notes or ''
                    ])
            
            # Prepare response
            output.seek(0)
            filename = f"attendance_{start_date_str}_to_{end_date_str}.csv"
            return Response(
                output,
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
        else:
            flash('Only CSV export is currently supported', 'info')
            return redirect(url_for('export_attendance'))
    
    # Default dates: last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    return render_template(
        'attendance/export.html',
        start_date=start_date,
        end_date=end_date
    )


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