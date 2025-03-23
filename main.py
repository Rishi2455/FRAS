"""
Main entry point for the Face Recognition Attendance System.
"""
import os
import tkinter as tk
from attendance_system import AttendanceSystem

if __name__ == "__main__":
    # Create necessary directories if they don't exist
    os.makedirs("student_images", exist_ok=True)
    os.makedirs("attendance_logs", exist_ok=True)
    
    # Start the attendance system
    root = tk.Tk()
    root.title("Face Recognition Attendance System")
    app = AttendanceSystem(root)
    root.mainloop()
