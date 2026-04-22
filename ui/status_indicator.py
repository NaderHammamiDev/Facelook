import customtkinter as ctk


class StatusIndicator:
    def __init__(self, master):
        self.master = master
        self.master.title("FaceLock Status")
        self.master.geometry("300x150")

        ctk.set_appearance_mode("dark")

        self.frame = ctk.CTkFrame(master, corner_radius=15)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.status_label = ctk.CTkLabel(
            self.frame,
            text="🔴 Inactif",
            font=("Arial", 20, "bold"),
            text_color="red"
        )
        self.status_label.pack(pady=30)

    def update_status(self, active=True):
        if active:
            self.status_label.configure(text="🟢 Actif", text_color="green")
        else:
            self.status_label.configure(text="🔴 Inactif", text_color="red")