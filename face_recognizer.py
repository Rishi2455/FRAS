
"""Simple attendance marker with simplified face detection"""
import os
import cv2
import numpy as np
import dlib

# Configure dlib's face detector
face_detector = dlib.get_frontal_face_detector()

class FaceRecognizer:
    def __init__(self, database):
        """Initialize the face recognizer with a database connection."""
        self.db = database
        self.face_detector = face_detector

        # Ensure student_images directory exists
        if not os.path.exists('student_images'):
            os.makedirs('student_images')

    def recognize_faces(self, frame):
        """Detect faces in the frame"""
        try:
            # Convert BGR to RGB as dlib expects RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces using dlib's frontal face detector
            faces = self.face_detector(rgb_frame)
            
            # Return face detections - one for each face found
            detected_faces = []
            for i, face in enumerate(faces):
                detected_faces.append((i + 1, "Face Detected"))
            
            return detected_faces
            
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []
