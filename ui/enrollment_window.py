import customtkinter as ctk
from tkinter import messagebox


class EnrollmentWindow:
    def __init__(self, master, detector, auth, get_current_frame):
        self.master = master
        self.detector = detector
        self.auth = auth
        self.get_current_frame = get_current_frame

        ctk.set_appearance_mode("dark")

        # ================= MAIN FRAME =================
        self.frame = ctk.CTkFrame(master, corner_radius=15)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # ================= HEADER =================
        ctk.CTkLabel(
            self.frame,
            text="🧠 FaceLock Enrollment",
            font=("Arial", 22, "bold")
        ).pack(pady=10)

        # ================= RGPD INFO =================
        policy = self.auth.db.get_privacy_policy()

        info = ctk.CTkFrame(self.frame, fg_color="transparent")
        info.pack(pady=5)

        ctk.CTkLabel(info, text="Finalité : authentification biométrique").pack()
        ctk.CTkLabel(info, text=f"RGPD v{policy['version']} - {policy['date']}").pack()

        # ================= FORM =================
        form = ctk.CTkFrame(self.frame, corner_radius=10)
        form.pack(pady=10, padx=10, fill="x")

        self.entry = ctk.CTkEntry(form, placeholder_text="Nom utilisateur")
        self.entry.pack(pady=8, padx=10, fill="x")

        self.consent = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            form,
            text="Consentement biométrique RGPD",
            variable=self.consent
        ).pack(pady=10)

        # ================= STATUS =================
        self.status = ctk.CTkLabel(self.frame, text="")
        self.status.pack(pady=5)

        # ================= ACTIONS =================
        actions = ctk.CTkFrame(self.frame, fg_color="transparent")
        actions.pack(pady=10, fill="x")

        ctk.CTkButton(actions, text="📸 Capturer visage", command=self.capture_face).pack(pady=5, fill="x")
        ctk.CTkButton(actions, text="🗑 Supprimer utilisateur", fg_color="red", command=self.delete_user).pack(pady=5, fill="x")
        ctk.CTkButton(actions, text="📄 Export PDF", command=self.export_pdf).pack(pady=5, fill="x")
        ctk.CTkButton(actions, text="📊 Export JSON", command=self.export_json).pack(pady=5, fill="x")
        ctk.CTkButton(actions, text="📁 Export CSV", command=self.export_csv).pack(pady=5, fill="x")

    # ================= GET NAME =================
    def _get_name(self):
        name = self.entry.get().strip()
        if not name:
            self.status.configure(text="✖ Nom requis", text_color="red")
            return None
        return name

    # ================= 🔐 VERIFY FACE =================
    def _verify_face(self, name):
        frame = self.get_current_frame()

        if frame is None:
            self.status.configure(text="✖ Caméra indisponible", text_color="red")
            return False

        boxes = self.detector.detect_faces(frame)

        if not boxes:
            self.status.configure(text="✖ Aucun visage détecté", text_color="red")
            return False

        face = self.detector.extract_face(frame, boxes[0])

        user = self.auth.authenticate(face)

        if user != name:
            return False

        return True

    # ================= 📸 CAPTURE FACE =================
    def capture_face(self):
        name = self._get_name()
        if not name:
            return

        if not self.consent.get():
            self.status.configure(text="✖ Consentement requis", text_color="red")
            return

        frame = self.get_current_frame()

        if frame is None:
            self.status.configure(text="✖ Caméra indisponible", text_color="red")
            return

        boxes = self.detector.detect_faces(frame)

        if not boxes:
            self.status.configure(text="✖ Aucun visage détecté", text_color="red")
            return

        face = self.detector.extract_face(frame, boxes[0])

        role = "user"

        success = self.auth.enroll_user(name, face, True, role)

        if success:
            self.status.configure(
                text=f"✔ {name} enregistré avec succès",
                text_color="green"
            )
        else:
            self.status.configure(
                text="✖ Échec enregistrement",
                text_color="red"
            )

    # ================= DELETE USER =================
    def delete_user(self):
        name = self._get_name()
        if not name:
            return

        if not self._verify_face(name):
            self.status.configure(text="✖ Visage non reconnu", text_color="red")
            return

        if self.auth.delete_user(name):
            self.status.configure(text="✔ Utilisateur supprimé", text_color="green")
        else:
            self.status.configure(text="✖ Introuvable", text_color="red")

    # ================= EXPORT PDF =================
    def export_pdf(self):
        name = self._get_name()
        if not name:
            return

        if not self._verify_face(name):
            self.status.configure(text="✖ Visage non reconnu", text_color="red")
            return

        self.auth.export_user_pdf(name)
        self.status.configure(text="✔ PDF exporté", text_color="green")

    # ================= EXPORT JSON =================
    def export_json(self):
        name = self._get_name()
        if not name:
            return

        if not self._verify_face(name):
            self.status.configure(text="✖ Visage non reconnu", text_color="red")
            return

        self.auth.export_user_json(name)
        self.status.configure(text="✔ JSON exporté", text_color="green")

    # ================= EXPORT CSV =================
    def export_csv(self):
        name = self._get_name()
        if not name:
            return

        if not self._verify_face(name):
            self.status.configure(text="✖ Visage non reconnu", text_color="red")
            return

        self.auth.export_user_csv(name)
        self.status.configure(text="✔ CSV exporté", text_color="green")