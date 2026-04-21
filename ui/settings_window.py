class SettingsWindow:
    def __init__(self, master, threshold=0.6):
        self.master = master
        self.master.title("Paramètres")
        self.master.geometry("400x250")

        self.threshold = ctk.DoubleVar(value=threshold)

        self.frame = ctk.CTkFrame(master, corner_radius=15)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(self.frame, text="Seuil de reconnaissance", font=("Arial", 18)).pack(pady=10)

        self.slider = ctk.CTkSlider(self.frame, from_=0.3, to=1.0, variable=self.threshold)
        self.slider.pack(pady=15, padx=20)

        self.value_label = ctk.CTkLabel(self.frame, text=f"{self.threshold.get():.2f}")
        self.value_label.pack()

        self.slider.configure(command=self.update_label)

        ctk.CTkButton(self.frame, text="Sauvegarder", command=self.save).pack(pady=15)

    def update_label(self, value):
        self.value_label.configure(text=f"{float(value):.2f}")

    def save(self):
        print("Seuil mis à jour:", self.threshold.get())
        self.master.destroy()