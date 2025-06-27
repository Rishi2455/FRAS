"""
Main controller for the attendance system. Coordinates between
face recognition, database, and GUI components.
"""
import os
import datetime
import tkinter as tk
from tkinter import messagebox
import cv2
import pandas as pd

from face_recognizer import FaceRecognizer
from database import Database
from gui import AttendanceGUI
from utils import get_current_datetime, format_time

class AttendanceSystem:
    def __init__(self, root):
        """Initialize the attendance system with all components."""
        self.root = root
        self.db = Database()
        self.face_recognizer = FaceRecognizer(self.db)
        self.gui = AttendanceGUI(root, self)

        # Camera setup
        self.camera = None
        self.is_camera_running = False

        # Current session
        self.current_attendance = {}
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Initialize the system
        self.initialize_system()

    def initialize_system(self):
        """Initialize the system by loading student data."""
        # Load students from database
        students = self.db.get_all_students()
        if not students:
            messagebox.showinfo("System Initialization", "No students in database. Please add students.")

        # Check for today's attendance file
        today_file = f"attendance_logs/attendance_{self.current_date}.csv"
        if os.path.exists(today_file):
            # Load today's attendance
            try:
                self.current_attendance = self.load_today_attendance()
                self.gui.update_attendance_display(self.current_attendance)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load today's attendance: {str(e)}")

    def load_today_attendance(self):
        """Load today's attendance from CSV file."""
        today_file = f"attendance_logs/attendance_{self.current_date}.csv"
        if os.path.exists(today_file):
            df = pd.read_csv(today_file)
            attendance_dict = {}
            for _, row in df.iterrows():
                attendance_dict[row['Student ID']] = {
                    'name': row['Name'],
                    'time': row['Time'],
                    'date': row['Date']
                }
            return attendance_dict
        return {}

    def start_camera(self):
        """Start the webcam for face detection."""
        if self.is_camera_running:
            return

        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Failed to open webcam.")
                return

            self.is_camera_running = True
            self.update_camera()
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {str(e)}")

    def update_camera(self):
        """Update the camera feed and perform face recognition."""
        if not self.is_camera_running:
            return

        ret, frame = self.camera.read()
        if ret:
            # Perform face recognition
            recognized_faces = self.face_recognizer.recognize_faces(frame)

            # Mark attendance for recognized faces
            for student_id, student_name in recognized_faces:
                if student_id not in self.current_attendance:
                    current_time = get_current_datetime()
                    self.mark_attendance(student_id, student_name, current_time)

            # Draw rectangles around detected faces
            frame = self.face_recognizer.draw_face_locations(frame)

            # Display the frame
            self.gui.display_frame(frame)

            # Schedule the next update
            self.root.after(10, self.update_camera)
        else:
            messagebox.showerror("Error", "Failed to capture frame from webcam.")
            self.stop_camera()

    def stop_camera(self):
        """Stop the webcam."""
        self.is_camera_running = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None

        # Clear the camera display
        self.gui.clear_camera_display()

    def mark_attendance(self, student_id, student_name, timestamp):
        """Mark attendance for a recognized student."""
        # Add to current session
        self.current_attendance[student_id] = {
            'name': student_name,
            'time': timestamp.strftime("%H:%M:%S"),
            'date': timestamp.strftime("%Y-%m-%d")
        }

        # Update GUI
        self.gui.update_attendance_display(self.current_attendance)

        # Save to CSV
        self.save_attendance_to_csv()

        # Display notification
        self.gui.show_attendance_notification(student_name)

    def save_attendance_to_csv(self):
        """Save current attendance to CSV file."""
        filename = f"attendance_logs/attendance_{self.current_date}.csv"

        # Prepare data for DataFrame
        data = []
        for student_id, details in self.current_attendance.items():
            data.append({
                'Student ID': student_id,
                'Name': details['name'],
                'Date': details['date'],
                'Time': details['time']
            })

        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

    def add_new_student(self, student_id, name):
        """Capture and add a new student to the database."""
        if not self.is_camera_running:
            messagebox.showerror("Error", "Camera is not running. Start the camera first.")
            return False

        # Verify student ID format
        if not student_id.isdigit():
            messagebox.showerror("Error", "Student ID must be a number.")
            return False

        # Check if student ID already exists
        if self.db.student_exists(student_id):
            messagebox.showerror("Error", "Student ID already exists in the database.")
            return False

        # Capture image
        ret, frame = self.camera.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame from webcam.")
            return False

        # Detect faces in the frame
        face_locations = self.face_recognizer.detect_faces(frame)
        if not face_locations or len(face_locations) > 1:
            messagebox.showerror("Error",
                                "No face detected or multiple faces detected. Please ensure only one face is visible.")
            return False

        # Save student to database
        try:
            result = self.db.add_student(student_id, name, frame)
            if result:
                messagebox.showinfo("Success", f"Student {name} ({student_id}) added successfully.")
                return True
            else:
                messagebox.showerror("Error", "Failed to add student to database.")
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add student: {str(e)}")
            return False

    def view_attendance_history(self, date=None):
        """View attendance history for a specific date or range."""
        if date is None:
            date = self.current_date

        filename = f"attendance_logs/attendance_{date}.csv"
        if not os.path.exists(filename):
            messagebox.showinfo("Information", f"No attendance records found for {date}.")
            return None

        try:
            attendance_data = pd.read_csv(filename)
            return attendance_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load attendance data: {str(e)}")
            return None

    def delete_student(self, student_id):
        """Delete a student from the database."""
        if not self.db.student_exists(student_id):
            messagebox.showerror("Error", "Student ID does not exist in the database.")
            return False

        try:
            if self.db.delete_student(student_id):
                messagebox.showinfo("Success", f"Student with ID {student_id} deleted successfully.")
                return True
            else:
                messagebox.showerror("Error", "Failed to delete student.")
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete student: {str(e)}")
            return False

    def export_attendance(self, start_date, end_date):
        """Export attendance data for a date range to a CSV file."""
        try:
            # Convert string dates to datetime objects
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

            # Validate date range
            if start > end:
                messagebox.showerror("Error", "Start date cannot be after end date.")
                return False

            # Collect all attendance data in the range
            all_data = []
            current_date = start

            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")
                filename = f"attendance_logs/attendance_{date_str}.csv"

                if os.path.exists(filename):
                    df = pd.read_csv(filename)
                    all_data.append(df)

                current_date += datetime.timedelta(days=1)

            if not all_data:
                messagebox.showinfo("Information", "No attendance records found for the selected date range.")
                return False

            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)

            # Export to CSV
            export_filename = f"attendance_logs/export_{start_date}_to_{end_date}.csv"
            combined_df.to_csv(export_filename, index=False)

            messagebox.showinfo("Success", f"Attendance data exported to {export_filename}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export attendance data: {str(e)}")
            return False
