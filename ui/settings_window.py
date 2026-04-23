import tkinter as tk
from config import load_config, save_config


class SettingsWindow:

    def __init__(self, master, on_save=None):
        self.master = master
        self.on_save = on_save
        self.cfg = load_config()

        master.title("Paramètres FaceLock")
        master.resizable(False, False)
        master.configure(bg="#1a1a2e")

        self._build_ui()

    def _build_ui(self):
        BG = "#1a1a2e"
        FG = "#ffffff"
        ACC = "#e94560"
        FONT = ("Consolas", 10)

        tk.Label(self.master, text="⚙ Paramètres",
                 bg=BG, fg=ACC,
                 font=("Consolas", 14, "bold")).pack(pady=12)

        # Timeout
        tk.Label(self.master, text="Timeout verrouillage (sec)",
                 bg=BG, fg=FG, font=FONT).pack()

        self.timeout_var = tk.IntVar(value=self.cfg.get("lock_timeout", 30))

        tk.Scale(self.master, variable=self.timeout_var,
                 from_=10, to=120,
                 orient="horizontal",
                 bg=BG, fg=FG).pack()

        # Warn
        tk.Label(self.master, text="Avertissement (sec)",
                 bg=BG, fg=FG, font=FONT).pack()

        self.warn_var = tk.IntVar(value=self.cfg.get("warn_before", 10))

        tk.Scale(self.master, variable=self.warn_var,
                 from_=5, to=30,
                 orient="horizontal",
                 bg=BG, fg=FG).pack()

        # ✅ CHECKBOX L2 FIX
        self.score_var = tk.BooleanVar()
        self.score_var.set(bool(self.cfg.get("show_score", True)))

        tk.Checkbutton(self.master,
                       text="Afficher distance L2",
                       variable=self.score_var,
                       bg=BG, fg=FG,
                       selectcolor="#16213e").pack(pady=10)

        # Buttons
        frame = tk.Frame(self.master, bg=BG)
        frame.pack(pady=10)

        tk.Button(frame, text="Enregistrer",
                  bg=ACC, fg="white",
                  command=self._save).pack(side="left", padx=5)

        tk.Button(frame, text="Annuler",
                  command=self.master.destroy).pack(side="left", padx=5)

    def _save(self):
        timeout = self.timeout_var.get()
        warn = self.warn_var.get()

        if warn >= timeout:
            warn = timeout - 5

        self.cfg["lock_timeout"] = timeout
        self.cfg["warn_before"] = warn
        self.cfg["show_score"] = self.score_var.get()

        save_config(self.cfg)

        if self.on_save:
            self.on_save(self.cfg)

        self.master.destroy()