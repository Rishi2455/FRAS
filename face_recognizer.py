"""Face recognition implementation with dlib"""
import os
import cv2
import numpy as np
import dlib
from datetime import datetime
from models import Student

# Configure dlib's face detector
face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat') if os.path.exists('shape_predictor_68_face_landmarks.dat') else None
face_rec = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat') if os.path.exists('dlib_face_recognition_resnet_model_v1.dat') else None

class FaceRecognizer:
    def __init__(self, database):
        """Initialize the face recognizer with a database connection."""
        self.db = database
        self.face_detector = face_detector
        self.shape_predictor = shape_predictor
        self.face_rec = face_rec

        # Ensure student_images directory exists
        if not os.path.exists('student_images'):
            os.makedirs('student_images')

    def load_student_image(self, image_path):
        """Load and preprocess a student's image"""
        if not os.path.exists(image_path):
            return None
        return cv2.imread(image_path)

    def get_face_encoding(self, image):
        """Get face encoding from image"""
        try:
            if self.shape_predictor and self.face_rec:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                faces = self.face_detector(rgb_image)
                if len(faces) > 0:
                    shape = self.shape_predictor(rgb_image, faces[0])
                    return np.array(self.face_rec.compute_face_descriptor(rgb_image, shape))
        except Exception as e:
            print(f"Error getting face encoding: {e}")
        return None

    def recognize_faces(self, frame):
        """Detect and recognize faces in the frame"""
        try:
            # Convert BGR to RGB for dlib
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces using dlib
            faces = self.face_detector(rgb_frame)
            
            if not faces:
                return []

            # Get all students from database
            students = Student.query.all()
            recognized_students = []

            # Process each detected face
            for face in faces:
                try:
                    if self.shape_predictor and self.face_rec:
                        # Get face encoding for detected face
                        shape = self.shape_predictor(rgb_frame, face)
                        face_encoding = np.array(self.face_rec.compute_face_descriptor(rgb_frame, shape))

                        # Compare with student images
                        for student in students:
                            try:
                                if student.image_path:
                                    student_img_path = os.path.join('student_images', student.image_path)
                                    if not os.path.exists(student_img_path):
                                        continue
                                        
                                    student_img = self.load_student_image(student_img_path)
                                    if student_img is None:
                                        continue

                                    student_encoding = self.get_face_encoding(student_img)
                                    if student_encoding is not None:
                                        # Compare face encodings
                                        distance = np.linalg.norm(face_encoding - student_encoding)
                                        if distance < 0.4:  # Threshold for face matching
                                            recognized_students.append({
                                                'student_id': student.id,
                                                'name': student.name,
                                                'confidence': 1.0 - distance,
                                                'detection_time': datetime.now().strftime('%H:%M:%S')
                                            })
                                            break
                            except Exception as e:
                                print(f"Error processing student {student.id}: {e}")
                                continue
                except Exception as e:
                    print(f"Error processing face: {e}")
                    continue

            return recognized_students

        except Exception as e:
            print(f"Error in face recognition: {e}")
            return []
