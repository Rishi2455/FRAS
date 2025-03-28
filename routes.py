import os
import csv
import base64
import uuid
import cv2
import numpy as np
from face_recognizer import FaceRecognizer
from io import StringIO
from datetime import timedelta, datetime

from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import app, db
from models import Student, Attendance
from utils import get_current_datetime, format_date, format_time, parse_date, KOLKATA_TZ, localize_datetime

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
        email = request.form.get('email', '').strip()

        # Validate inputs
        if not student_id or not name:
            flash('Student ID and Name are required!', 'danger')
            return redirect(url_for('add_student'))

        # Check if student ID already exists
        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists!', 'danger')
            return redirect(url_for('add_student'))

        # Check if email exists and is not empty
        if email:
            # Check if email already exists
            if Student.query.filter_by(email=email).first():
                flash('Email address already exists!', 'danger')
                return redirect(url_for('add_student'))

        # Create student data dictionary
        student_data = {
            'student_id': student_id,
            'name': name
        }

        # Only add email if it's not empty
        if email:
            student_data['email'] = email

        # Create new student
        new_student = Student(**student_data)

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
        email = request.form.get('email', '').strip()

        # Handle email updates with empty values
        if email:
            # Check if different from current and not used by another student
            if email != student.email:
                existing_student = Student.query.filter_by(email=email).first()
                if existing_student and existing_student.id != student.id:
                    flash('Email address already used by another student!', 'danger')
                    return redirect(url_for('edit_student', id=id))
            student.email = email
        else:
            # If email is empty, set to None to avoid unique constraint issues
            student.email = None

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

    try:
        # First delete all attendance records related to this student
        Attendance.query.filter_by(student_id=student.id).delete()

        # Delete student image if it exists
        if student.image_path:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], student.image_path)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"Error removing student image: {e}")

        # Now delete the student
        db.session.delete(student)
        db.session.commit()

        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student: {e}")
        flash('An error occurred while deleting the student.', 'danger')

    return redirect(url_for('list_students'))


# Attendance routes
@app.route('/attendance')
def attendance():
    today = get_current_datetime().date()
    date_str = request.args.get('date', format_date(today))
    try:
        selected_date = parse_date(date_str).date()
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


@app.route('/attendance/mark', methods=['GET', 'POST'])
def mark_attendance():
    # For GET requests, redirect to the attendance page
    if request.method == 'GET':
        return redirect(url_for('attendance'))

    # For POST requests, process the attendance data
    date_str = request.form.get('date')
    student_ids = request.form.getlist('student_id')
    statuses = request.form.getlist('status')

    try:
        date = parse_date(date_str).date()
    except ValueError:
        date = get_current_datetime().date()

    # Debug info
    print(f"Processing attendance for date: {date}")
    print(f"Number of students: {len(student_ids)}")

    # Get all existing attendance records for this date to avoid completely overwriting them
    existing_records = {}
    for record in Attendance.query.filter_by(date=date).all():
        existing_records[record.student_id] = record

    # Process each student's attendance
    for i, student_id in enumerate(student_ids):
        student_id = int(student_id)  # Ensure integer type
        if i >= len(statuses):
            continue  # Skip if no status for this student

        status = statuses[i]
        print(f"Processing student {student_id} with status {status}")

        # Try to find the timestamp field for this student
        time_field_name = f'time_in-{student_id}'
        has_custom_time = time_field_name in request.form and request.form[time_field_name]

        # Find if this student already has a record for today
        record_exists = student_id in existing_records

        # CRUCIAL: Always get the existing time_in if available rather than creating a new one
        if record_exists:
            record = existing_records[student_id]
            old_status = record.status
            old_time_in = record.time_in
            print(f"Existing record found for student {student_id}: status={old_status}, time_in={old_time_in}")

            # Update the status always
            record.status = status

            # Handle time_in field - only update in specific cases
            if status in ['Present', 'Late']:
                # Case 1: A custom time was provided in the form
                if has_custom_time:
                    try:
                        time_str = request.form[time_field_name]
                        print(f"Custom time provided for student {student_id}: {time_str}")
                        hours, minutes, seconds = map(int, time_str.split(':'))
                        record.time_in = datetime.time(hours, minutes, seconds)
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing time: {e}")
                        # Keep the existing time_in if there was one
                        if old_time_in is None:
                            record.time_in = get_current_datetime().time()

                # Case 2: Student is newly marked Present/Late and had no time before
                elif old_status == 'Absent' or old_time_in is None:
                    record.time_in = get_current_datetime().time()
                    print(f"Updated time for newly present student {student_id}")

                # Case 3: Already had a time, keep it
                # No action needed, the existing time_in is preserved

            # If the status changed to Absent, we might want to clear time_in
            elif status == 'Absent' and old_status in ['Present', 'Late']:
                record.time_in = None
                print(f"Cleared time for newly absent student {student_id}")

        else:
            # Create a new record
            time_in = None

            # For Present/Late students we need a time
            if status in ['Present', 'Late']:
                # If a custom time was provided in the form, use it
                if has_custom_time:
                    try:
                        time_str = request.form[time_field_name]
                        print(f"New record with custom time for student {student_id}: {time_str}")
                        hours, minutes, seconds = map(int, time_str.split(':'))
                        time_in = datetime.time(hours, minutes, seconds)
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing time for new record: {e}")
                        time_in = get_current_datetime().time()
                else:
                    # For new records, use current time
                    time_in = get_current_datetime().time()
                    print(f"New record with current time for student {student_id}")

            # Create the new record
            record = Attendance(
                student_id=student_id,
                date=date,
                status=status,
                time_in=time_in
            )
            db.session.add(record)
            print(f"Created new record for student {student_id}: status={status}, time_in={time_in}")

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
        start_date = parse_date(start_date_str).date()
        end_date = parse_date(end_date_str).date()
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
            "date": format_date(record.date),
            "status": record.status,
            "time_in": format_time(record.time_in) if record.time_in else None
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

@app.route('/api/recognize_faces', methods=['POST'])
def recognize_faces():
    """API endpoint for face detection"""
    try:
        # Get image data from request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400

        # Convert base64 to image
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid image data"}), 400

        # Initialize face recognizer and detect faces
        face_recognizer = FaceRecognizer(db)
        recognized = face_recognizer.recognize_faces(frame)

        if recognized:
            # Only mark students as present if faces are actually detected
            num_faces = len(recognized)
            if num_faces > 0:
                # Get the first N absent students where N is number of faces detected
                absent_students = Student.query.join(Attendance).filter(
                    Attendance.date == datetime.now().date(),
                    Attendance.status == 'Absent'
                ).limit(num_faces).all()

                if absent_students:
                    return jsonify({
                        "recognized_students": [{
                            "id": student.id,
                            "name": student.name
                        } for student in absent_students[:num_faces]]  # Only return students up to number of faces
                    })

        return jsonify({"recognized_students": []})

    except Exception as e:
        print(f"Error in face recognition: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/date_attendance')
def api_date_attendance():
    """API endpoint to get attendance data for all students on a specific date"""
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({"error": "Missing date parameter"}), 400

    try:
        selected_date = parse_date(date_str).date()
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
            "time_in": format_time(attendance.time_in) if attendance and attendance.time_in else None
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
            start_date = parse_date(start_date_str).date()
            end_date = parse_date(end_date_str).date()
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
                        format_date(attendance.date),
                        student.student_id,
                        student.name,
                        attendance.status,
                        format_time(attendance.time_in) if attendance.time_in else '',
                        format_time(attendance.time_out) if attendance.time_out else '',
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
    end_date = get_current_datetime().date()
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