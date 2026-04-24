import cv2
import face_recognition
import numpy as np

class FaceDetector:
    def __init__(self):
        pass

    def detect_faces(self, frame):
        if frame is None:
            return []

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        try:
            boxes = face_recognition.face_locations(rgb)

            scaled_boxes = []
            for top, right, bottom, left in boxes:
                scaled_boxes.append((
                    top*4, right*4, bottom*4, left*4
                ))
            return scaled_boxes
        except Exception as e:
            print("Erreur face_recognition:", e)
            return []

    def extract_face(self, frame, box):
        top, right, bottom, left = box
        return frame[top:bottom, left:right]