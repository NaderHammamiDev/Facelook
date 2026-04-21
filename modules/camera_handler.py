import cv2

class CameraHandler:
    def __init__(self, cam_index=0):
        self.cam_index = cam_index
        self.cap = None

    def initialize_camera(self):
        self.cap = cv2.VideoCapture(self.cam_index)
        if not self.cap.isOpened():
            raise RuntimeError("Impossible d'ouvrir la caméra")

    def capture_frame(self):
        if self.cap is None:
            raise RuntimeError("Caméra non initialisée")
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None