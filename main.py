import cv2
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import messagebox

from modules.system_controller import SystemController
from ui.login_window import LoginWindow
from modules.face_detector import FaceDetector
from modules.authenticator import FaceAuthenticator
from ui.enrollment_window import EnrollmentWindow
from ui.settings_window import SettingsWindow
from ui.status_indicator import StatusIndicator
from toast_notification import ToastNotification
from config import load_config


CAMERA_WARMUP = 1


class FaceLockApp:

    def __init__(self, root, role="user", username="unknown"):
        self.root = root
        self.role = role
        self.username = username

        self.root.title(f"FaceLock - {self.role}")

        self.detector = FaceDetector()
        self.auth = FaceAuthenticator(threshold=0.8)
        self.system = SystemController()

        self.cfg = load_config()

        self.running = True
        self.current_frame = None
        self.status = StatusIndicator(root)

        self.toast_shown = False
        self.enrolling = False
        self.face_verify_start = None

        self.lock_enabled = len(self.auth.known_faces) > 0

        tk.Button(root, text="Enrollment", command=self.open_enrollment).pack(pady=5)
        tk.Button(root, text="Paramètres", command=self.open_settings).pack(pady=5)
        tk.Button(root, text="Quitter", command=self.quit_app).pack(pady=5)

        self.thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.thread.start()

        if not self.lock_enabled:
            self.root.after(500, self._auto_open_enrollment)

    # =========================
    def _auto_open_enrollment(self):
        messagebox.showinfo(
            "Bienvenue",
            "Aucun visage enregistré.\nVeuillez enrôler un visage."
        )
        self.open_enrollment()

    # =========================
    def open_enrollment(self):
        self.enrolling = True
        self.toast_shown = False
        ToastNotification.dismiss()
        self.system.update_activity()

        top = tk.Toplevel(self.root)

        def on_close():
            self.auth.reload_faces()
            self.lock_enabled = len(self.auth.known_faces) > 0
            self.enrolling = False
            self.system.update_activity()
            top.destroy()

        EnrollmentWindow(top, self.detector, self.auth, self.get_current_frame)
        top.protocol("WM_DELETE_WINDOW", on_close)

    # =========================
    def open_settings(self):
        top = tk.Toplevel(self.root)
        SettingsWindow(top, on_save=lambda cfg: setattr(self, "cfg", cfg))

    # =========================
    def quit_app(self):
        self.running = False
        self.auth.db.close()
        self.root.destroy()

    # =========================
    def get_current_frame(self):
        return self.current_frame

    # =========================
    def _authenticate_with_score(self, face_image):
        emb = self.auth.encoder.encode_face(face_image)
        if emb is None:
            return None

        emb = np.asarray(emb, dtype=np.float32).flatten()

        for name, known_emb in self.auth.known_faces:
            dist = np.linalg.norm(emb - known_emb)
            if dist <= self.auth.distance_threshold:
                return name

        return None

    # =========================
    def camera_loop(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Erreur caméra")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            self.current_frame = frame.copy()
            now = time.time()

            # reload config (IMPORTANT)
            self.cfg = load_config()

            # unlock event
            if self.system.just_unlocked() and not self.enrolling:
                self.face_verify_start = now

            boxes = self.detector.detect_faces(frame)
            known_face_found = False

            for box in boxes:
                face_img = self.detector.extract_face(frame, box)
                user = self._authenticate_with_score(face_img)

                (top, right, bottom, left) = box

                color = (0, 255, 0) if user else (0, 0, 255)
                label = user if user else "Unknown"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                
                # L2 DISPLAY FIX
                if self.cfg.get("show_score", True):

                    text = "L2: OK" if user else "L2: Unknown"
                    color2 = (0, 255, 0) if user else (0, 0, 255)

                    cv2.putText(frame,
                                text,
                                (left, bottom + 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                color2,
                                2)

                if user:
                    known_face_found = True

            
            # SECURITY LOGIC

            if self.face_verify_start is not None:
                elapsed = now - self.face_verify_start

                if elapsed < CAMERA_WARMUP:
                    cv2.putText(frame,
                                "Preparation camera...",
                                (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 165, 255), 2)

                elif known_face_found:
                    self.face_verify_start = None
                    self.system.update_activity()

                else:
                    self.face_verify_start = None
                    self.system.lock_workstation()
                    self.system.update_activity()

            elif known_face_found:
                self.system.update_activity()
                ToastNotification.dismiss()

            else:
                idle = self.system.get_idle_time()
                timeout = self.cfg.get("lock_timeout", 20)
                warn = self.cfg.get("warn_before", 10)

                time_left = int(timeout - idle)

                if time_left <= warn and not self.toast_shown:
                    self.toast_shown = True
                    ToastNotification.show(
                        seconds=max(time_left, 1),
                        on_cancel=self.system.update_activity,
                        parent=self.root
                    )

                if idle >= timeout:
                    self.toast_shown = False
                    ToastNotification.dismiss()
                    self.system.lock_workstation()
                    self.system.update_activity()

            self.status.update_status(active=known_face_found)
            cv2.imshow("FaceLock", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


# ========= main
if __name__ == "__main__":
    root = tk.Tk()

    def start_app(role, username):
        root.destroy()
        main_root = tk.Tk()
        FaceLockApp(main_root, role=role, username=username)
        main_root.mainloop()

    LoginWindow(root, on_success=start_app)
    root.mainloop()