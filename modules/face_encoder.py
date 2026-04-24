import cv2
import numpy as np
import face_recognition
 
 
class FaceEncoder:
 
    def encode_face(self, face_image):
        if face_image is None:
            return None
 
        try:
            rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            rgb = np.ascontiguousarray(rgb)
 
            encodings = face_recognition.face_encodings(rgb)
 
            if len(encodings) == 0:
                return None
 
            emb = np.array(encodings[0], dtype=np.float32)
 
            if emb.shape != (128,):
                return None
 
            if not np.isfinite(emb).all():
                return None
            return emb
 
        except Exception as e:
            print("FaceEncoder error:", e)
            return None