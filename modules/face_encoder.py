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
 
            # vérification shape
            if emb.shape != (128,):
                return None
 
            # vérification NaN / inf
            if not np.isfinite(emb).all():
                return None
 
            # ✅ PAS de normalisation :
            #    face_recognition est conçu pour la distance L2 sur vecteurs bruts.
            #    Normaliser détruit la métrique et rend tous les visages similaires.
            return emb
 
        except Exception as e:
            print("FaceEncoder error:", e)
            return None