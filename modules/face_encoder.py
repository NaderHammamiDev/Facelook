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

            # sécurité shape
            if emb.shape != (128,):
                return None

            # remove NaN / inf
            if not np.isfinite(emb).all():
                return None

            # normalisation
            norm = np.linalg.norm(emb)
            if norm == 0:
                return None

            emb = emb / norm

            return emb.astype(np.float32)

        except Exception as e:
            print("FaceEncoder error:", e)
            return None

    def compare_embeddings(self, emb1, emb2, threshold=0.6):
        if emb1 is None or emb2 is None:
            return False

        emb1 = np.array(emb1, dtype=np.float32)
        emb2 = np.array(emb2, dtype=np.float32)

        if emb1.shape != (128,) or emb2.shape != (128,):
            return False

        distance = np.linalg.norm(emb1 - emb2)

        return distance < threshold