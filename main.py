import cv2
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


class FaceLockApp:

    def __init__(self, root, role="user", username="unknown"):
        self.root = root
        self.role = role
        self.username = username

        self.root.title(f"FaceLock - {self.role}")

        self.detector = FaceDetector()
        self.auth = FaceAuthenticator(threshold=0.8)
        self.system = SystemController()

        self.auth.db.cleanup_old_data()

        self.running = True
        self.current_frame = None
        self.status = StatusIndicator(root)

        self.last_face_time = time.time()

        tk.Button(root, text="Enrollment", command=self.open_enrollment).pack(pady=5)

        if self.role == "admin":
            tk.Button(root, text="Settings (Admin)", command=self.open_settings).pack(pady=5)

        tk.Button(root, text="Quitter", command=self.quit_app).pack(pady=5)

        self.thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.thread.start()

        self.start_cleanup_scheduler()

    # =========================
    def start_cleanup_scheduler(self):
        def run():
            while self.running:
                try:
                    self.auth.db.cleanup_old_data()
                except Exception as e:
                    print("Cleanup error:", e)

                time.sleep(86400)

        threading.Thread(target=run, daemon=True).start()

    # =========================
    def open_enrollment(self):
        top = tk.Toplevel(self.root)
        EnrollmentWindow(top, self.detector, self.auth, self.get_current_frame)

    def open_settings(self):
        if self.role != "admin":
            messagebox.showerror("Access denied", "Admin only")
            return

        top = tk.Toplevel(self.root)
        SettingsWindow(top, threshold=self.auth.threshold)

    def quit_app(self):
        self.running = False
        self.auth.db.close()
        self.root.destroy()

    def get_current_frame(self):
        return self.current_frame

    # =========================
    def camera_loop(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d'ouvrir la caméra")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            self.current_frame = frame.copy()

            boxes = self.detector.detect_faces(frame)
            face_found = False

            for box in boxes:
                face_img = self.detector.extract_face(frame, box)
                user = self.auth.authenticate(face_img)

                top, right, bottom, left = box

                color = (0, 255, 0) if user else (0, 0, 255)
                label = user if user else "Unknown"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                if user:
                    face_found = True

            # =========================
            # 🔐 FACELOCK LOGIC FINAL
            # =========================
            if face_found:
                self.system.update_activity()
            else:
                self.system.check_and_lock(timeout=30)

            self.status.update_status(active=face_found)

            cv2.imshow("FaceLock", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.quit_app()
                break

        cap.release()
        cv2.destroyAllWindows()


# =========================
if __name__ == "__main__":
    root = tk.Tk()

    def start_app(role, username):
        root.destroy()
        main_root = tk.Tk()
        FaceLockApp(main_root, role=role, username=username)
        main_root.mainloop()

    LoginWindow(root, on_success=start_app)

    root.mainloop()