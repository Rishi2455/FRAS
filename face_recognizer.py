"""
Module for face detection and recognition using OpenCV and face_recognition library.
"""
import cv2
import face_recognition
import numpy as np


class FaceRecognizer:
    def __init__(self, database):
        """Initialize the face recognizer with a database connection."""
        self.database = database
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known face encodings from the database."""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        
        students = self.database.get_all_students()
        for student in students:
            if student.get('encoding'):
                self.known_face_encodings.append(student['encoding'])
                self.known_face_ids.append(student['id'])
                self.known_face_names.append(student['name'])
    
    def detect_faces(self, frame):
        """Detect faces in the given frame."""
        # Convert to RGB for face_recognition library
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.face_locations = face_recognition.face_locations(rgb_frame)
        return self.face_locations
    
    def recognize_faces(self, frame):
        """Recognize faces in the given frame and return list of (id, name) tuples."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in the frame
        self.face_locations = face_recognition.face_locations(rgb_frame)
        self.face_encodings = face_recognition.face_encodings(rgb_frame, self.face_locations)
        
        recognized_students = []
        
        for face_encoding in self.face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            
            # Find best match
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    student_id = self.known_face_ids[best_match_index]
                    student_name = self.known_face_names[best_match_index]
                    recognized_students.append((student_id, student_name))
        
        return recognized_students
    
    def draw_face_locations(self, frame):
        """Draw rectangles around detected faces in the frame."""
        for (top, right, bottom, left) in self.face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        return frame
    
    def encode_face(self, frame):
        """Encode a face from a frame for storage in the database."""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                # Use the first face found
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
                return face_encoding
            return None
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None