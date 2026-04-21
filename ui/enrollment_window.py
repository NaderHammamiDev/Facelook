import customtkinter as ctk
from tkinter import messagebox


class EnrollmentWindow:
    def __init__(self, master, detector, auth, get_current_frame):
        self.master = master
        self.detector = detector
        self.auth = auth
        self.get_current_frame = get_current_frame

        self.frame = ctk.CTkFrame(master)
        self.frame.pack(padx=20, pady=20)

        # RGPD INFO
        policy = self.auth.db.get_privacy_policy()

        ctk.CTkLabel(
            self.frame,
            text="Finalité : authentification faciale sécurisée",
            text_color="gray"
        ).pack(pady=5)

        ctk.CTkLabel(
            self.frame,
            text=f"RGPD v{policy['version']} - {policy['date']}",
            text_color="gray"
        ).pack(pady=5)

        # USERNAME
        self.entry = ctk.CTkEntry(self.frame, placeholder_text="Nom utilisateur")
        self.entry.pack(pady=10)

        # ROLE
        self.role = ctk.CTkComboBox(self.frame, values=["user", "admin"])
        self.role.set("user")
        self.role.pack(pady=5)

        # CONSENT
        self.consent = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            self.frame,
            text="J'accepte les données biométriques",
            variable=self.consent
        ).pack(pady=10)

        # BUTTONS
        ctk.CTkButton(self.frame, text="Capturer visage",
                      command=self.capture_face).pack(pady=5)

        ctk.CTkButton(self.frame, text="Supprimer utilisateur",
                      fg_color="red",
                      command=self.delete_user).pack(pady=5)

        ctk.CTkButton(self.frame, text="Voir mes données",
                      command=self.view_data).pack(pady=5)

        ctk.CTkButton(self.frame, text="Exporter PDF",
                      command=self.export_pdf).pack(pady=5)

        ctk.CTkButton(self.frame, text="Exporter JSON",
                      command=self.export_json).pack(pady=5)

        ctk.CTkButton(self.frame, text="Exporter CSV",
                      command=self.export_csv).pack(pady=5)

    # =========================
    def _get_name(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Nom requis")
            return None
        return name

    # =========================
    def _check_identity(self, name):
        """
        🔐 Vérifie si le visage reconnu correspond à l'utilisateur
        """
        if not hasattr(self.auth, "current_user"):
            return False
        return self.auth.current_user == name

    # =========================
    def view_data(self):
        name = self._get_name()
        if not name:
            return

        data = self.auth.db.get_user_data(name)

        if not data:
            messagebox.showerror("Erreur", "Utilisateur introuvable")
            return

        messagebox.showinfo(
            "Données",
            "\n".join(f"{k}: {v}" for k, v in data.items())
        )

    # =========================
    # 🔐 EXPORTS SECURISÉS
    # =========================
    def export_pdf(self):
        name = self._get_name()
        if not name:
            return

        if not self._check_identity(name):
            messagebox.showerror("Erreur", "Visage non reconnu")
            return

        path = self.auth.export_user_pdf(name)
        messagebox.showinfo("Export PDF", path if path else "Échec export")

    def export_json(self):
        name = self._get_name()
        if not name:
            return

        if not self._check_identity(name):
            messagebox.showerror("Erreur", "Visage non reconnu")
            return

        path = self.auth.export_user_json(name)
        messagebox.showinfo("Export JSON", path if path else "Échec export")

    def export_csv(self):
        name = self._get_name()
        if not name:
            return

        if not self._check_identity(name):
            messagebox.showerror("Erreur", "Visage non reconnu")
            return

        path = self.auth.export_user_csv(name)
        messagebox.showinfo("Export CSV", path if path else "Échec export")

    # =========================
    # 📸 ENROLL FACE
    # =========================
    def capture_face(self):
        name = self._get_name()
        if not name:
            return

        if not self.consent.get():
            messagebox.showerror("Erreur", "Consentement requis")
            return

        frame = self.get_current_frame()

        if frame is None:
            messagebox.showerror("Erreur", "Caméra indisponible")
            return

        boxes = self.detector.detect_faces(frame)

        if not boxes:
            messagebox.showerror("Erreur", "Aucun visage détecté")
            return

        face = self.detector.extract_face(frame, boxes[0])
        role = self.role.get()

        success = self.auth.enroll_user(name, face, True, role)

        if success:
            messagebox.showinfo("OK", f"{name} ajouté ({role})")
        else:
            messagebox.showerror("Erreur", "Échec enregistrement")

    # =========================
    # 🗑 DELETE SECURISÉ
    # =========================
    def delete_user(self):
        name = self._get_name()
        if not name:
            return

        if not self._check_identity(name):
            messagebox.showerror("Erreur", "Visage non reconnu")
            return

        if self.auth.delete_user(name):
            messagebox.showinfo("OK", "Utilisateur supprimé")
        else:
            messagebox.showerror("Erreur", "Introuvable")