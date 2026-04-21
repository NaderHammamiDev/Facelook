import customtkinter as ctk
from tkinter import messagebox
from modules.security import hash_password, verify_password
from modules.database import DatabaseManager


class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.db = DatabaseManager()

        self.root.title("FaceLock Login")
        self.root.geometry("400x300")

        frame = ctk.CTkFrame(root)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(frame, text="🔐 FaceLock Login", font=("Arial", 18)).pack(pady=20)

        self.username = ctk.CTkEntry(frame, placeholder_text="Username")
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(frame, placeholder_text="Password", show="*")
        self.password.pack(pady=10)

        ctk.CTkButton(frame, text="Login", command=self.check_login).pack(pady=20)

    def check_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()

        # =========================
        # 🔥 ADMIN CHECK (STATIC)
        # =========================
        if user == "admin" and verify_password(pwd, hash_password("1234")):
            messagebox.showinfo("OK", "Admin login success")
            self.on_success(role="admin", username=user)
            return

        # =========================
        # 🔥 USER CHECK (DATABASE ROLE)
        # =========================
        role = self.db.get_user_role(user)

        if role is None:
            messagebox.showerror("Error", "User not found")
            return

        if role == "user":
            messagebox.showinfo("OK", "User login success")
            self.on_success(role="user", username=user)
            return

        if role == "admin":
            messagebox.showinfo("OK", "Admin login success")
            self.on_success(role="admin", username=user)
            return

        messagebox.showerror("Error", "Access denied")