"""
Module for managing student database and face encodings.
"""
import os
import pickle
import cv2
import numpy as np
from datetime import datetime


class Database:
    def __init__(self):
        """Initialize the database manager."""
        self.students = {}
        self.data_file = 'student_data.pkl'
        self.load_students()
    
    def load_students(self):
        """Load student data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    self.students = pickle.load(f)
            except Exception as e:
                print(f"Error loading student data: {e}")
                self.students = {}
    
    def save_students(self):
        """Save student data to file."""
        try:
            with open(self.data_file, 'wb') as f:
                pickle.dump(self.students, f)
        except Exception as e:
            print(f"Error saving student data: {e}")
    
    def add_student(self, student_id, name, image_frame):
        """Add a new student to the database."""
        if student_id in self.students:
            return False
        
        # Store the face encoding if an image is provided
        encoding = None
        if image_frame is not None:
            from face_recognizer import FaceRecognizer
            recognizer = FaceRecognizer(self)
            encoding = recognizer.encode_face(image_frame)
        
        self.students[student_id] = {
            'id': student_id,
            'name': name,
            'encoding': encoding,
            'added_date': datetime.now()
        }
        
        self.save_students()
        return True
    
    def get_student(self, student_id):
        """Get a student by ID."""
        return self.students.get(student_id)
    
    def get_all_students(self):
        """Get all students."""
        return [student for student in self.students.values()]
    
    def update_student(self, student_id, name=None, image_frame=None):
        """Update a student's information."""
        if student_id not in self.students:
            return False
        
        student = self.students[student_id]
        
        if name:
            student['name'] = name
        
        if image_frame is not None:
            from face_recognizer import FaceRecognizer
            recognizer = FaceRecognizer(self)
            encoding = recognizer.encode_face(image_frame)
            student['encoding'] = encoding
        
        self.save_students()
        return True
    
    def delete_student(self, student_id):
        """Delete a student from the database."""
        if student_id in self.students:
            del self.students[student_id]
            self.save_students()
            return True
        return False
    
    def student_exists(self, student_id):
        """Check if a student exists in the database."""
        return student_id in self.students