"""
GUI module for the face recognition attendance system.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk
import datetime

from utils import get_current_datetime, format_time, format_date


class AttendanceGUI:
    def __init__(self, root, controller):
        """Initialize the GUI components."""
        self.root = root
        self.controller = controller
        
        # Set window size
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # Variables
        self.camera_frame = None
        self.notification_label = None
        self.notification_after_id = None
        
        # Create the GUI
        self.create_gui()
    
    def create_gui(self):
        """Create the main GUI elements."""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.attendance_tab = ttk.Frame(self.notebook)
        self.manage_students_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.attendance_tab, text="Take Attendance")
        self.notebook.add(self.manage_students_tab, text="Manage Students")
        self.notebook.add(self.history_tab, text="Attendance History")
        
        # Set up each tab
        self.setup_attendance_tab()
        self.setup_manage_students_tab()
        self.setup_history_tab()
    
    def setup_attendance_tab(self):
        """Set up the attendance tab with camera feed and current attendance."""
        # Create frames
        camera_controls_frame = ttk.Frame(self.attendance_tab)
        camera_controls_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        main_frame = ttk.Frame(self.attendance_tab)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        camera_frame = ttk.LabelFrame(main_frame, text="Camera Feed")
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        attendance_frame = ttk.LabelFrame(main_frame, text="Today's Attendance")
        attendance_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Camera controls
        start_camera_btn = ttk.Button(camera_controls_frame, text="Start Camera", 
                                      command=self.controller.start_camera)
        start_camera_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        stop_camera_btn = ttk.Button(camera_controls_frame, text="Stop Camera", 
                                     command=self.controller.stop_camera)
        stop_camera_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Camera display
        self.camera_display = ttk.Label(camera_frame)
        self.camera_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Notification area
        notification_frame = ttk.Frame(camera_frame)
        notification_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        self.notification_label = ttk.Label(notification_frame, text="", font=("Arial", 12))
        self.notification_label.pack(side=tk.LEFT)
        
        # Attendance display
        attendance_scroll = ttk.Scrollbar(attendance_frame)
        attendance_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.attendance_tree = ttk.Treeview(attendance_frame, 
                                            columns=("ID", "Name", "Time"),
                                            show="headings",
                                            yscrollcommand=attendance_scroll.set)
        
        self.attendance_tree.heading("ID", text="Student ID")
        self.attendance_tree.heading("Name", text="Name")
        self.attendance_tree.heading("Time", text="Check-in Time")
        
        self.attendance_tree.column("ID", width=100)
        self.attendance_tree.column("Name", width=200)
        self.attendance_tree.column("Time", width=100)
        
        self.attendance_tree.pack(fill=tk.BOTH, expand=True)
        attendance_scroll.config(command=self.attendance_tree.yview)
    
    def setup_manage_students_tab(self):
        """Set up the tab for managing students."""
        # Create frames
        top_frame = ttk.Frame(self.manage_students_tab)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        bottom_frame = ttk.Frame(self.manage_students_tab)
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        add_student_frame = ttk.LabelFrame(top_frame, text="Add New Student")
        add_student_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        students_frame = ttk.LabelFrame(bottom_frame, text="Student Database")
        students_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add student form
        form_frame = ttk.Frame(add_student_frame)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(form_frame, text="Student ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.student_id_entry = ttk.Entry(form_frame)
        self.student_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Name:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.student_name_entry = ttk.Entry(form_frame)
        self.student_name_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        add_btn = ttk.Button(form_frame, text="Capture & Add Student", 
                             command=self.add_student)
        add_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Student list
        scroll = ttk.Scrollbar(students_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.students_tree = ttk.Treeview(students_frame, 
                                          columns=("ID", "Name"),
                                          show="headings",
                                          yscrollcommand=scroll.set)
        
        self.students_tree.heading("ID", text="Student ID")
        self.students_tree.heading("Name", text="Name")
        
        self.students_tree.column("ID", width=150)
        self.students_tree.column("Name", width=300)
        
        self.students_tree.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.students_tree.yview)
        
        # Buttons for managing students
        btn_frame = ttk.Frame(students_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        delete_btn = ttk.Button(btn_frame, text="Delete Selected Student", 
                                command=self.delete_student)
        delete_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        refresh_btn = ttk.Button(btn_frame, text="Refresh List", 
                                 command=self.refresh_student_list)
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Initial population of student list
        self.refresh_student_list()
    
    def setup_history_tab(self):
        """Set up the tab for viewing attendance history."""
        # Create frames
        controls_frame = ttk.Frame(self.history_tab)
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        view_frame = ttk.LabelFrame(self.history_tab, text="Attendance Records")
        view_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        export_frame = ttk.LabelFrame(self.history_tab, text="Export Attendance")
        export_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Date selector
        ttk.Label(controls_frame, text="Select Date:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(controls_frame, textvariable=self.date_var)
        date_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        view_btn = ttk.Button(controls_frame, text="View Attendance", 
                              command=self.view_attendance)
        view_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Attendance view
        scroll = ttk.Scrollbar(view_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree = ttk.Treeview(view_frame, 
                                         columns=("ID", "Name", "Date", "Time"),
                                         show="headings",
                                         yscrollcommand=scroll.set)
        
        self.history_tree.heading("ID", text="Student ID")
        self.history_tree.heading("Name", text="Name")
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Time", text="Time")
        
        self.history_tree.column("ID", width=100)
        self.history_tree.column("Name", width=200)
        self.history_tree.column("Date", width=100)
        self.history_tree.column("Time", width=100)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.history_tree.yview)
        
        # Export controls
        export_controls = ttk.Frame(export_frame)
        export_controls.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(export_controls, text="Start Date:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        start_date_entry = ttk.Entry(export_controls, textvariable=self.start_date_var)
        start_date_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(export_controls, text="End Date:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.end_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(export_controls, textvariable=self.end_date_var)
        end_date_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        export_btn = ttk.Button(export_controls, text="Export to CSV", 
                                command=self.export_attendance)
        export_btn.grid(row=0, column=4, padx=5, pady=5)
    
    def display_frame(self, frame):
        """Display a frame from OpenCV in the GUI."""
        # Convert frame from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL format
        pil_image = Image.fromarray(rgb_frame)
        
        # Resize to fit the display
        width, height = 640, 480
        pil_image = pil_image.resize((width, height), Image.LANCZOS)
        
        # Convert to ImageTk format
        self.camera_frame = ImageTk.PhotoImage(image=pil_image)
        
        # Update the label
        self.camera_display.config(image=self.camera_frame)
    
    def clear_camera_display(self):
        """Clear the camera display."""
        self.camera_display.config(image="")
        self.camera_frame = None
    
    def show_attendance_notification(self, student_name):
        """Show a notification when attendance is marked."""
        # Cancel previous notification if it exists
        if self.notification_after_id:
            self.root.after_cancel(self.notification_after_id)
        
        # Show notification
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.notification_label.config(
            text=f"✓ Attendance marked for {student_name} at {current_time}",
            foreground="green"
        )
        
        # Schedule notification to disappear after 3 seconds
        self.notification_after_id = self.root.after(3000, self.clear_notification)
    
    def clear_notification(self):
        """Clear the notification text."""
        self.notification_label.config(text="")
        self.notification_after_id = None
    
    def update_attendance_display(self, attendance_dict):
        """Update the attendance display with current data."""
        # Clear existing items
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        # Add new items
        for student_id, details in attendance_dict.items():
            self.attendance_tree.insert("", tk.END, values=(
                student_id,
                details['name'],
                details['time']
            ))
    
    def add_student(self):
        """Add a new student via the GUI."""
        student_id = self.student_id_entry.get().strip()
        name = self.student_name_entry.get().strip()
        
        if not student_id or not name:
            messagebox.showerror("Error", "Student ID and Name are required.")
            return
        
        success = self.controller.add_new_student(student_id, name)
        
        if success:
            # Clear form
            self.student_id_entry.delete(0, tk.END)
            self.student_name_entry.delete(0, tk.END)
            
            # Refresh the student list
            self.refresh_student_list()
    
    def delete_student(self):
        """Delete a selected student."""
        # Get selected item
        selected_item = self.students_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a student to delete.")
            return
        
        # Get student ID from selected item
        student_id = self.students_tree.item(selected_item[0], 'values')[0]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm", 
                                      f"Are you sure you want to delete student with ID {student_id}?")
        if not confirm:
            return
        
        # Delete student
        success = self.controller.delete_student(student_id)
        
        if success:
            # Refresh the student list
            self.refresh_student_list()
    
    def refresh_student_list(self):
        """Refresh the student list display."""
        # Clear existing items
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
        
        # Get students from database
        students = self.controller.db.get_all_students()
        
        # Add students to tree view
        for student in students:
            self.students_tree.insert("", tk.END, values=(
                student['id'],
                student['name']
            ))
    
    def view_attendance(self):
        """View attendance for a selected date."""
        selected_date = self.date_var.get()
        
        try:
            # Validate date format
            datetime.datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return
        
        # Get attendance data
        attendance_data = self.controller.view_attendance_history(selected_date)
        
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        if attendance_data is not None:
            # Add data to tree view
            for _, row in attendance_data.iterrows():
                self.history_tree.insert("", tk.END, values=(
                    row['Student ID'],
                    row['Name'],
                    row['Date'],
                    row['Time']
                ))
    
    def export_attendance(self):
        """Export attendance data for a date range."""
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        try:
            # Validate date format
            datetime.datetime.strptime(start_date, "%Y-%m-%d")
            datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return
        
        # Export attendance
        self.controller.export_attendance(start_date, end_date)
