import customtkinter as ctk
from tkinter import messagebox
from modules.security import hash_password, verify_password
from modules.database import DatabaseManager


class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.db = DatabaseManager()

        ctk.set_appearance_mode("dark")

        self.root.title("FaceLock Login")
        self.root.geometry("450x350")

        # ================= CENTER FRAME =================
        self.frame = ctk.CTkFrame(root, corner_radius=15)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # TITLE
        ctk.CTkLabel(
            self.frame,
            text="🔐 FaceLock System",
            font=("Arial", 22, "bold")
        ).pack(pady=15)

        # USERNAME
        self.username = ctk.CTkEntry(self.frame, placeholder_text="Username")
        self.username.pack(pady=10, padx=20, fill="x")

        # PASSWORD
        self.password = ctk.CTkEntry(self.frame, placeholder_text="Password", show="*")
        self.password.pack(pady=10, padx=20, fill="x")

        # STATUS
        self.status = ctk.CTkLabel(self.frame, text="")
        self.status.pack(pady=5)

        # BUTTON
        ctk.CTkButton(
            self.frame,
            text="Login",
            command=self.check_login,
            fg_color="#1f6aa5"
        ).pack(pady=20, fill="x", padx=20)

    def check_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        if user == "admin" and verify_password(pwd, hash_password("1234")):
            self.status.configure(text="✔ Admin access granted", text_color="green")
            self.on_success(role="admin", username=user)
            return

        role = self.db.get_user_role(user)

        if role is None:
            self.status.configure(text="✖ User not found", text_color="red")
            return

        self.status.configure(text=f"✔ Login success ({role})", text_color="green")
        self.on_success(role=role, username=user)