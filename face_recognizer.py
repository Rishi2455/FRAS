"""
Module for face detection and recognition using OpenCV and face_recognition library.
"""
import os
import cv2
import numpy as np
import face_recognition
from database import Database

class FaceRecognizer:
    def __init__(self, database):
        """Initialize the face recognizer with a database connection."""
        self.db = database
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.processed_frame = None
        
        # Load known faces from database
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known face encodings from the database."""
        students = self.db.get_all_students()
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        for student in students:
            student_id = student['id']
            name = student['name']
            encoding = student['encoding']
            
            if encoding is not None:
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(name)
                self.known_face_ids.append(student_id)
    
    def detect_faces(self, frame):
        """Detect faces in the given frame."""
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations in the frame
        self.face_locations = face_recognition.face_locations(rgb_frame)
        
        return self.face_locations
    
    def recognize_faces(self, frame):
        """Recognize faces in the given frame and return list of (id, name) tuples."""
        # Detect faces
        self.detect_faces(frame)
        
        # If no faces are detected or no known faces to compare against
        if not self.face_locations or not self.known_face_encodings:
            return []
        
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Compute face encodings for each face found
        self.face_encodings = face_recognition.face_encodings(rgb_frame, self.face_locations)
        
        recognized_students = []
        
        # Compare each face encoding to known encodings
        for face_encoding in self.face_encodings:
            # Compare face encoding with all known face encodings
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            
            # Calculate face distance (lower = more similar)
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                # Get index of the closest matching face
                best_match_index = np.argmin(face_distances)
                
                # If there's a match and the confidence is high enough
                if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                    student_id = self.known_face_ids[best_match_index]
                    name = self.known_face_names[best_match_index]
                    recognized_students.append((student_id, name))
        
        return recognized_students
    
    def draw_face_locations(self, frame):
        """Draw rectangles around detected faces in the frame."""
        # Create a copy of the frame to avoid modifying the original
        display_frame = frame.copy()
        
        # Draw rectangles and names for each face
        for (top, right, bottom, left) in self.face_locations:
            # Draw rectangle around the face
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw label background
            cv2.rectangle(display_frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            
            # Draw name label
            cv2.putText(display_frame, "Face Detected", (left + 6, bottom - 6), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
        
        return display_frame
    
    def encode_face(self, frame):
        """Encode a face from a frame for storage in the database."""
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # If no face or multiple faces are detected
        if len(face_locations) != 1:
            return None
        
        # Compute face encoding
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(face_encodings) > 0:
            return face_encodings[0]
            
        return None
