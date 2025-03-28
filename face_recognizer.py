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
            
            # Return a list of detected faces
            detected_faces = []
            for i, face in enumerate(faces):
                detected_faces.append((i + 1, f"Face {i + 1} Detected"))
            
            return detected_faces
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def encode_face(self, frame):
        """Simplified face detection for enrollment"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector(gray)
            return len(faces) > 0
        except Exception as e:
            print(f"Error encoding face: {e}")
            return False