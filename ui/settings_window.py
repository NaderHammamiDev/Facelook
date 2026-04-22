import tkinter as tk
from config import load_config, save_config
 
 
class SettingsWindow:
    """
    Fenêtre paramètres — à placer dans ui/settings_window.py
    Appelée depuis main.py :
        top = tk.Toplevel(self.root)
        SettingsWindow(top, on_save=callback)
    """
 
    def __init__(self, master, on_save=None):
        self.master  = master
        self.on_save = on_save
        self.cfg     = load_config()
 
        master.title("Paramètres FaceLock")
        master.resizable(False, False)
        master.configure(bg="#1a1a2e")
 
        self._build_ui()
 
    def _build_ui(self):
        BG   = "#1a1a2e"
        FG   = "#ffffff"
        ACC  = "#e94560"
        FONT = ("Consolas", 10)
        BOLD = ("Consolas", 10, "bold")
        PAD  = {"padx": 20, "pady": 8}
 
        tk.Label(self.master, text="⚙  Paramètres",
                 bg=BG, fg=ACC,
                 font=("Consolas", 14, "bold")).pack(pady=(16, 4))
 
        tk.Frame(self.master, bg=ACC, height=1).pack(fill="x", padx=20, pady=(0, 12))
 
        # ── Timeout verrouillage ──────────────────────
        tk.Label(self.master,
                 text="Verrouillage après absence (secondes)",
                 bg=BG, fg=FG, font=FONT, anchor="w").pack(fill="x", **PAD)
 
        self.timeout_var = tk.IntVar(value=self.cfg["lock_timeout"])
        f1 = tk.Frame(self.master, bg=BG)
        f1.pack(fill="x", padx=20, pady=(0, 8))
        tk.Scale(f1, variable=self.timeout_var, from_=10, to=120,
                 orient="horizontal", bg=BG, fg=FG,
                 highlightthickness=0, troughcolor="#16213e",
                 activebackground=ACC, length=220,
                 font=FONT).pack(side="left")
        tk.Label(f1, textvariable=self.timeout_var,
                 bg=BG, fg=ACC, font=BOLD, width=4).pack(side="left", padx=8)
        tk.Label(f1, text="sec", bg=BG, fg="#aaaaaa",
                 font=FONT).pack(side="left")
 
        # ── Toast avertissement ───────────────────────
        tk.Label(self.master,
                 text="Avertissement avant verrouillage (secondes)",
                 bg=BG, fg=FG, font=FONT, anchor="w").pack(fill="x", **PAD)
 
        self.warn_var = tk.IntVar(value=self.cfg["warn_before"])
        f2 = tk.Frame(self.master, bg=BG)
        f2.pack(fill="x", padx=20, pady=(0, 8))
        tk.Scale(f2, variable=self.warn_var, from_=5, to=30,
                 orient="horizontal", bg=BG, fg=FG,
                 highlightthickness=0, troughcolor="#16213e",
                 activebackground=ACC, length=220,
                 font=FONT).pack(side="left")
        tk.Label(f2, textvariable=self.warn_var,
                 bg=BG, fg=ACC, font=BOLD, width=4).pack(side="left", padx=8)
        tk.Label(f2, text="sec", bg=BG, fg="#aaaaaa",
                 font=FONT).pack(side="left")
 
        # ── Afficher score L2 ─────────────────────────
        tk.Frame(self.master, bg="#16213e", height=1).pack(fill="x",
                                                           padx=20, pady=8)
        self.score_var = tk.BooleanVar(value=self.cfg["show_score"])
        f3 = tk.Frame(self.master, bg=BG)
        f3.pack(fill="x", padx=20, pady=(0, 12))
        tk.Checkbutton(f3,
                       text="  Afficher la distance L2 sur la caméra",
                       variable=self.score_var,
                       bg=BG, fg=FG, selectcolor="#16213e",
                       activebackground=BG, activeforeground=ACC,
                       font=FONT, anchor="w").pack(side="left")
 
        # ── Boutons ───────────────────────────────────
        tk.Frame(self.master, bg=ACC, height=1).pack(fill="x",
                                                     padx=20, pady=(4, 12))
        fb = tk.Frame(self.master, bg=BG)
        fb.pack(pady=(0, 16))
        tk.Button(fb, text="Enregistrer",
                  bg=ACC, fg="white", font=BOLD, relief="flat",
                  cursor="hand2", padx=18, pady=6,
                  command=self._save).pack(side="left", padx=8)
        tk.Button(fb, text="Annuler",
                  bg="#16213e", fg="#aaaaaa", font=FONT, relief="flat",
                  cursor="hand2", padx=18, pady=6,
                  command=self.master.destroy).pack(side="left", padx=8)
 
    def _save(self):
        warn    = self.warn_var.get()
        timeout = self.timeout_var.get()
 
        if warn >= timeout:
            warn = max(5, timeout - 5)
            self.warn_var.set(warn)
 
        self.cfg["lock_timeout"] = timeout
        self.cfg["warn_before"]  = warn
        self.cfg["show_score"]   = self.score_var.get()
 
        save_config(self.cfg)
 
        if self.on_save:
            self.on_save(self.cfg)
 
        self.master.destroy()