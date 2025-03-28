"""
Module for face detection and recognition using OpenCV and face_recognition library.
"""
import os
import cv2
import numpy as np
import face_recognition
from models import Student

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
        try:
            students = Student.query.all()

            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_ids = []

            for student in students:
                if student.image_path:
                    try:
                        image_path = os.path.join('student_images', student.image_path)
                        if os.path.exists(image_path):
                            image = face_recognition.load_image_file(image_path)
                            encoding = face_recognition.face_encodings(image)

                            if len(encoding) > 0:
                                self.known_face_encodings.append(encoding[0])
                                self.known_face_names.append(student.name)
                                self.known_face_ids.append(student.id)
                    except Exception as e:
                        print(f"Error loading face for student {student.name}: {e}")
                        continue
        except Exception as e:
            print(f"Error loading faces from database: {e}")

    def detect_faces(self, frame):
        """Detect faces in the given frame."""
        try:
            # Convert BGR to RGB (face_recognition uses RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find all face locations in the frame
            self.face_locations = face_recognition.face_locations(rgb_frame)

            return self.face_locations
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def recognize_faces(self, frame):
        """Recognize faces in the given frame and return list of (id, name) tuples."""
        try:
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

                if True in matches:
                    best_match_index = matches.index(True)
                    student_id = self.known_face_ids[best_match_index]
                    name = self.known_face_names[best_match_index]
                    recognized_students.append((student_id, name))

            return recognized_students
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []

    def encode_face(self, frame):
        """Encode a face from a frame for storage in the database."""
        try:
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
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None