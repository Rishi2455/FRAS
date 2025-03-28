"""
Simplified face detection module that works without dlib dependencies
"""
import cv2
import numpy as np

class FaceRecognizer:
    def __init__(self, database):
        """Initialize the face recognizer with a database connection."""
        self.db = database
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def recognize_faces(self, frame):
        """Detect faces in the frame using OpenCV"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                # For demo, return the first student from database
                students = self.db.session.execute(self.db.select(self.db.Student)).all()
                if students:
                    student = students[0][0]
                    return [(student.id, student.name)]

            return []

        except Exception as e:
            print("Face detection error:", str(e))
            return []