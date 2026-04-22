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
 
 
class FaceLockApp:
 
    def __init__(self, root, role="user", username="unknown"):
        self.root     = root
        self.role     = role
        self.username = username
 
        self.root.title(f"FaceLock - {self.role}")
 
        self.detector = FaceDetector()
        self.auth     = FaceAuthenticator(threshold=0.8)
        self.system   = SystemController()
 
        self.cfg = load_config()
 
        self.auth.db.cleanup_old_data()
 
        self.running       = True
        self.current_frame = None
        self.status        = StatusIndicator(root)
        self.toast_shown   = False
 
        # ✅ Lock suspendu pendant enrollment
        self.enrolling = False
 
        # ✅ Période de grâce après enrollment (timestamp)
        #    pendant 8 secondes après fermeture de l'enrollment,
        #    un visage inconnu ne déclenche PAS le lock
        self.grace_until = 0.0
 
        self.lock_enabled = len(self.auth.known_faces) > 0
 
        tk.Button(root, text="Enrollment", command=self.open_enrollment).pack(pady=5)
        tk.Button(root, text="Paramètres", command=self.open_settings).pack(pady=5)
        tk.Button(root, text="Quitter",    command=self.quit_app).pack(pady=5)
 
        self.thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.thread.start()
 
        self.start_cleanup_scheduler()
 
        if not self.lock_enabled:
            self.root.after(500, self._auto_open_enrollment)
 
    # =========================
    def _auto_open_enrollment(self):
        messagebox.showinfo(
            "Bienvenue",
            "Aucun visage enregistré.\nVeuillez d'abord enrôler votre visage."
        )
        self.open_enrollment()
 
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
        self.enrolling   = True
        self.toast_shown = False
        ToastNotification.dismiss()
        self.system.update_activity()
 
        top = tk.Toplevel(self.root)
 
        def on_close():
            self.auth.reload_faces()
            if len(self.auth.known_faces) > 0:
                self.lock_enabled = True
 
            self.enrolling = False
 
            # ✅ Période de grâce : 8 secondes sans lock après enrollment
            self.grace_until = time.time() + 8
            self.system.update_activity()
            print("[FACELOCK] Enrollment fermé → grâce de 8s avant réactivation du lock")
 
            top.destroy()
 
        EnrollmentWindow(top, self.detector, self.auth, self.get_current_frame)
        top.protocol("WM_DELETE_WINDOW", on_close)
 
    # =========================
    def open_settings(self):
        top = tk.Toplevel(self.root)
 
        def on_save(new_cfg):
            self.cfg = new_cfg
            print(f"[SETTINGS] timeout={new_cfg['lock_timeout']}s  "
                  f"warn={new_cfg['warn_before']}s  "
                  f"show_score={new_cfg['show_score']}")
 
        SettingsWindow(top, on_save=on_save)
 
    # =========================
    def quit_app(self):
        self.running = False
        self.auth.db.close()
        self.root.destroy()
 
    def get_current_frame(self):
        return self.current_frame
 
    # =========================
    def _authenticate_with_score(self, face_image):
        """Retourne (nom, distance_L2) ou (None, distance)."""
        emb = self.auth.encoder.encode_face(face_image)
        if emb is None:
            return None, None
 
        emb = np.asarray(emb, dtype=np.float32).flatten()
 
        best_name     = None
        best_distance = float("inf")
        second_best   = float("inf")
 
        for name, known_emb in self.auth.known_faces:
            dist = float(np.linalg.norm(emb - known_emb))
            if dist < best_distance:
                second_best   = best_distance
                best_distance = dist
                best_name     = name
            elif dist < second_best:
                second_best = dist
 
        if len(self.auth.known_faces) <= 1:
            passes_gap = True
        else:
            passes_gap = (second_best - best_distance) >= 0.10
 
        if best_name and best_distance <= self.auth.distance_threshold and passes_gap:
            return best_name, best_distance
 
        return None, best_distance
 
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
 
            # ── Attente enrôlement initial ────────────
            if not self.lock_enabled:
                cv2.putText(frame, "En attente d'enrolement...",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 165, 255), 2)
                cv2.imshow("FaceLock", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.quit_app()
                    break
                continue
 
            # ── Détection + auth ──────────────────────
            boxes              = self.detector.detect_faces(frame)
            known_face_found   = False
            unknown_face_found = False
 
            for box in boxes:
                face_img   = self.detector.extract_face(frame, box)
                user, dist = self._authenticate_with_score(face_img)
 
                top_b, right_b, bottom_b, left_b = box
                color = (0, 255, 0) if user else (0, 0, 255)
                label = user if user else "Unknown"
 
                cv2.rectangle(frame,
                              (left_b, top_b), (right_b, bottom_b), color, 2)
                cv2.putText(frame, label,
                            (left_b, top_b - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
 
                # Score L2
                if dist is not None and self.cfg.get("show_score", True):
                    cv2.putText(frame, f"L2: {dist:.3f}",
                                (left_b, bottom_b + 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (255, 255, 0), 1)
 
                if user:
                    known_face_found = True
                else:
                    unknown_face_found = True
 
            # ── Lock logic ────────────────────────────
            timeout     = self.cfg.get("lock_timeout", 30)
            warn_before = self.cfg.get("warn_before",  10)
            idle        = self.system.get_idle_time()
            in_grace    = time.time() < self.grace_until
 
            if self.enrolling:
                # Enrollment ouvert → lock suspendu
                cv2.putText(frame, "Enrollment en cours...",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 165, 255), 2)
 
            elif in_grace:
                # ✅ Période de grâce après enrollment → pas de lock
                remaining = int(self.grace_until - time.time())
                cv2.putText(frame, f"Demarrage dans {remaining}s...",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 200, 255), 2)
                self.system.update_activity()
 
            elif known_face_found:
                self.system.update_activity()
                self.toast_shown = False
                ToastNotification.dismiss()
 
            elif unknown_face_found:
                ToastNotification.dismiss()
                self.toast_shown = False
                print("[FACELOCK] UNKNOWN FACE → LOCK IMMÉDIAT")
                self.system.lock_workstation()
                self.system.update_activity()
 
            else:
                time_left = timeout - idle
 
                if time_left <= warn_before and not self.toast_shown:
                    self.toast_shown = True
                    ToastNotification.show(
                        seconds=int(time_left),
                        on_cancel=self.system.update_activity
                    )
 
                if idle >= timeout:
                    ToastNotification.dismiss()
                    self.toast_shown = False
                    print("[FACELOCK] ABSENT → LOCK")
                    self.system.lock_workstation()
                    self.system.update_activity()
 
            self.status.update_status(active=known_face_found)
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