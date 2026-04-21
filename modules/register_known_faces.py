import os
import cv2
import numpy as np
from modules.face_encoder import FaceEncoder
from modules.database import DatabaseManager

KNOWN_FACES_DIR = "known_faces"

def register_faces():
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    encoder = FaceEncoder()
    db = DatabaseManager()

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            name = os.path.splitext(filename)[0]  # nom sans extension
            image = cv2.imread(path)
            if image is None:
                print(f"[ERREUR] Impossible de lire {filename}")
                continue

            embedding = encoder.encode_face(image)
            if embedding is None:
                print(f"[ERREUR] Aucun visage détecté dans {filename}")
                continue

            try:
                db.store_embedding(name, embedding)
                print(f"[OK] {name} enregistré.")
            except Exception as e:
                print(f"[ERREUR] {filename} : {e}")

    db.close()
    print("✅ Tous les visages connus ont été enregistrés dans la base.")

if __name__ == "__main__":
    register_faces()