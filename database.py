"""
Module for managing student database and face encodings.
"""
import os
import pickle
import json
import numpy as np
import cv2
import face_recognition

class Database:
    def __init__(self):
        """Initialize the database manager."""
        self.students_dir = "student_images"
        self.students_data_file = os.path.join(self.students_dir, "students.json")
        self.students = self.load_students()
    
    def load_students(self):
        """Load student data from file."""
        if not os.path.exists(self.students_data_file):
            return {}
        
        try:
            with open(self.students_data_file, 'r') as f:
                students = json.load(f)
            
            # Convert encodings from list back to numpy arrays
            for student_id, student_data in students.items():
                if 'encoding' in student_data and student_data['encoding']:
                    encoding_path = os.path.join(self.students_dir, f"{student_id}_encoding.pkl")
                    if os.path.exists(encoding_path):
                        with open(encoding_path, 'rb') as f:
                            student_data['encoding'] = pickle.load(f)
                    else:
                        student_data['encoding'] = None
            
            return students
        except Exception as e:
            print(f"Error loading students data: {str(e)}")
            return {}
    
    def save_students(self):
        """Save student data to file."""
        try:
            # Create a copy of the students dictionary without numpy arrays
            students_copy = {}
            for student_id, student_data in self.students.items():
                students_copy[student_id] = student_data.copy()
                
                # Save encoding separately as pickle file
                if 'encoding' in student_data and student_data['encoding'] is not None:
                    encoding_path = os.path.join(self.students_dir, f"{student_id}_encoding.pkl")
                    with open(encoding_path, 'wb') as f:
                        pickle.dump(student_data['encoding'], f)
                    
                    # Set encoding to True in JSON to indicate it exists
                    students_copy[student_id]['encoding'] = True
            
            # Save the student data to JSON
            with open(self.students_data_file, 'w') as f:
                json.dump(students_copy, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error saving students data: {str(e)}")
            return False
    
    def add_student(self, student_id, name, image_frame):
        """Add a new student to the database."""
        # Check if student already exists
        if student_id in self.students:
            return False
        
        # Encode the face
        from face_recognizer import FaceRecognizer
        face_rec = FaceRecognizer(self)
        encoding = face_rec.encode_face(image_frame)
        
        if encoding is None:
            return False
        
        # Save the student image
        image_path = os.path.join(self.students_dir, f"{student_id}.jpg")
        cv2.imwrite(image_path, image_frame)
        
        # Add student to database
        self.students[student_id] = {
            'id': student_id,
            'name': name,
            'image_path': image_path,
            'encoding': encoding
        }
        
        # Save the database
        return self.save_students()
    
    def get_student(self, student_id):
        """Get a student by ID."""
        return self.students.get(student_id)
    
    def get_all_students(self):
        """Get all students."""
        return list(self.students.values())
    
    def update_student(self, student_id, name=None, image_frame=None):
        """Update a student's information."""
        if student_id not in self.students:
            return False
        
        student = self.students[student_id]
        
        if name:
            student['name'] = name
        
        if image_frame is not None:
            # Update the student image
            image_path = os.path.join(self.students_dir, f"{student_id}.jpg")
            cv2.imwrite(image_path, image_frame)
            student['image_path'] = image_path
            
            # Update face encoding
            from face_recognizer import FaceRecognizer
            face_rec = FaceRecognizer(self)
            encoding = face_rec.encode_face(image_frame)
            
            if encoding is not None:
                student['encoding'] = encoding
        
        return self.save_students()
    
    def delete_student(self, student_id):
        """Delete a student from the database."""
        if student_id not in self.students:
            return False
        
        # Remove student image if it exists
        image_path = os.path.join(self.students_dir, f"{student_id}.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Remove encoding file if it exists
        encoding_path = os.path.join(self.students_dir, f"{student_id}_encoding.pkl")
        if os.path.exists(encoding_path):
            os.remove(encoding_path)
        
        # Remove student from database
        del self.students[student_id]
        
        return self.save_students()
    
    def student_exists(self, student_id):
        """Check if a student exists in the database."""
        return student_id in self.students
