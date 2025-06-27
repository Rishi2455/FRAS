"""Face recognition implementation with dlib"""
import os
import cv2
import numpy as np
import dlib
from datetime import datetime
from models import Student
import torch
from torchvision import models, transforms
from PIL import Image

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

        # ——— New: load Torchvision ResNet-50 for face embeddings ———
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _resnet = models.resnet50(pretrained=True).to(self.device)
        _resnet.eval()
        # strip off the final classifier layer
        self.feature_extractor = torch.nn.Sequential(*list(_resnet.children())[:-1]).to(self.device)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def load_student_image(self, image_path):
        """Load and preprocess a student's image"""
        if not os.path.exists(image_path):
            return None
        return cv2.imread(image_path)

    def get_face_encoding(self, image):
        """Get face encoding from image"""
        # ——— Try Torch-based embedding first ———
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = self.face_detector(rgb_image)
        if faces:
            # crop out the first face
            f = faces[0]
            x1, y1, x2, y2 = f.left(), f.top(), f.right(), f.bottom()
            face_img = rgb_image[y1:y2, x1:x2]
            pil_img = Image.fromarray(face_img)
            tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                feat = self.feature_extractor(tensor)
            return feat.squeeze().cpu().numpy()

        # ——— Fallback to your existing dlib pipeline ———
        if self.shape_predictor and self.face_rec:
            faces = self.face_detector(rgb_image)
            if len(faces) > 0:
                shape = self.shape_predictor(rgb_image, faces[0])
                return np.array(self.face_rec.compute_face_descriptor(rgb_image, shape))
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
                    # Crop and embed the detected face via ResNet50 (or fallback)
                    x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                    face_crop = rgb_frame[y1:y2, x1:x2]
                    face_encoding = self.get_face_encoding(face_crop)
                    if face_encoding is None:
                        continue

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
