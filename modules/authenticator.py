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
 
    def __init__(self, threshold=0.8, distance_threshold=0.60):  # ✅ 0.50 → 0.60 plus tolérant
        self.encoder = FaceEncoder()
        self.db = DatabaseManager()
        self.distance_threshold = distance_threshold
 
        self.current_user = None
        self.known_faces = []
 
        self.reload_faces()
        print("Loaded users:", len(self.known_faces))
 
    
    def audit(self, action, name):
        import datetime
        os.makedirs("logs", exist_ok=True)
        with open("logs/audit.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} | {action} | {name}\n")
 
    
    def _load_safe_faces(self):
        data = self.db.load_embeddings()
        safe = []
        seen_names = set()
 
        for name, emb in data:
            try:
                name_key = name.strip().lower()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)
 
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
 
    
    def log(self, action, name):
        print(f"[AUDIT] {action} - {name}")
        logging.info(f"{action} {name}")
 
    
    def authenticate(self, face_image):
 
        emb = self.encoder.encode_face(face_image)
 
        if emb is None:
            self.log("AUTH_FAIL_NO_FACE", "ANONYMOUS")
            return None
 
        emb = np.asarray(emb, dtype=np.float32).flatten()
 
        best_name     = None
        best_distance = float("inf")
        second_best   = float("inf")
 
        for name, known_emb in self.known_faces:
            dist = float(np.linalg.norm(emb - known_emb))
 
            if dist < best_distance:
                second_best   = best_distance
                best_distance = dist
                best_name     = name
            elif dist < second_best:
                second_best = dist
 
        
        if len(self.known_faces) <= 1:
            passes_gap = True
        else:
            passes_gap = (second_best - best_distance) >= 0.10
 
        print(f"[DEBUG] users={len(self.known_faces)} best={best_name} "
              f"dist={best_distance:.4f} threshold={self.distance_threshold} "
              f"passes_gap={passes_gap}")
 
        if (
            best_name is not None and
            best_distance <= self.distance_threshold and
            passes_gap
        ):
            self.current_user = best_name
            self.db.update_last_login(best_name)
            self.log("AUTH_SUCCESS", best_name)
            self.audit("AUTH_SUCCESS", best_name)
            return best_name
 
        self.current_user = None
        self.log("AUTH_FAIL", "UNKNOWN")
        self.audit("AUTH_FAIL", "UNKNOWN")
        return None
 
    
    def enroll_user(self, name, face_image, consent=False, role="user"):
 
        if not consent:
            self.log("ENROLL_DENIED", name)
            return False
 
        emb = self.encoder.encode_face(face_image)
 
        if emb is None:
            return False
 
        emb  = np.asarray(emb, dtype=np.float32).flatten()
        name = name.strip()
 
        self.db.store_embedding(name, emb, role=role, consent=1)
 
        self.audit("ENROLL", name)
        self.reload_faces()
 
        self.log("ENROLL_SUCCESS", name)
        return True
 
    def delete_user(self, name):
        ok = self.db.delete_user(name)
 
        if ok:
            self.reload_faces()
            self.log("DELETE_SUCCESS", name)
            self.audit("DELETE", name)
            return True
 
        return False
 
    # exportation des données   
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