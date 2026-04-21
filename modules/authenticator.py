import numpy as np
import logging
import os
from modules.face_encoder import FaceEncoder
from modules.database import DatabaseManager

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class FaceAuthenticator:

    def __init__(self, threshold=0.6):
        self.encoder = FaceEncoder()
        self.db = DatabaseManager()
        self.threshold = threshold

        self.current_user = None
        self.known_faces = []

        self.reload_faces()

        print("Loaded users:", len(self.known_faces))

    # =========================
    def audit(self, action, name):
        import datetime
        os.makedirs("logs", exist_ok=True)

        with open("logs/audit.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} | {action} | {name}\n")

    # =========================
    def _load_safe_faces(self):
        data = self.db.load_embeddings()
        safe = []

        for name, emb in data:
            try:
                emb = np.asarray(emb, dtype=np.float32).flatten()

                if emb.shape != (128,):
                    continue

                if not np.isfinite(emb).all():
                    continue

                safe.append((name, emb))

            except:
                continue

        return safe

    def reload_faces(self):
        self.known_faces = self._load_safe_faces()

    # =========================
    def log(self, action, name):
        print(f"[AUDIT] {action} - {name}")
        logging.info(f"{action} {name}")

    # =========================
    def authenticate(self, face_image):

        emb = self.encoder.encode_face(face_image)

        if emb is None:
            self.log("AUTH_FAIL_NO_FACE", "ANONYMOUS")
            return None

        emb = np.asarray(emb, dtype=np.float32).flatten()

        for name, known_emb in self.known_faces:

            distance = np.linalg.norm(emb - known_emb)

            if distance < self.threshold:
                self.current_user = name
                self.db.update_last_login(name)
                self.log("AUTH_SUCCESS", name)
                self.audit("AUTH_SUCCESS", name)
                return name

        self.current_user = None
        self.log("AUTH_FAIL", "ANONYMOUS")
        self.audit("AUTH_FAIL", "UNKNOWN")
        return None

    # =========================
    def enroll_user(self, name, face_image, consent=False, role="user"):

        if not consent:
            self.log("ENROLL_DENIED", name)
            return False

        emb = self.encoder.encode_face(face_image)

        if emb is None:
            return False

        emb = np.asarray(emb, dtype=np.float32).flatten()

        self.db.store_embedding(name, emb, role=role, consent=1)

        self.audit("ENROLL", name)
        self.reload_faces()

        self.log("ENROLL_SUCCESS", name)
        return True

    # =========================
    def delete_user(self, name):
        ok = self.db.delete_user(name)

        if ok:
            self.reload_faces()
            self.log("DELETE_SUCCESS", name)
            self.audit("DELETE", name)
            return True

        return False

    # =========================
    def get_user_data(self, name):
        return self.db.get_user_data(name)

    def export_user_json(self, name):
        result = self.db.export_user_json(name)
        if result:
            self.audit("EXPORT_JSON", name)
        return result

    def export_user_csv(self, name):
        result = self.db.export_user_csv(name)
        if result:
            self.audit("EXPORT_CSV", name)
        return result

    def export_user_pdf(self, name):
        result = self.db.export_user_pdf(name)
        if result:
            self.audit("EXPORT_PDF", name)
        return result