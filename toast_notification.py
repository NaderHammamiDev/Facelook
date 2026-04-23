import tkinter as tk
import threading


class ToastNotification:

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def show(cls, seconds: int, on_cancel=None, parent=None):
        with cls._lock:
            if cls._instance and cls._instance.alive:
                cls._instance.reset(seconds)
                return

            t = cls(seconds, on_cancel, parent)
            cls._instance = t
            t.start()

    @classmethod
    def dismiss(cls):
        with cls._lock:
            if cls._instance and cls._instance.alive:
                cls._instance._close()

    def __init__(self, seconds, on_cancel=None, parent=None):
        self.seconds = seconds
        self.remaining = seconds
        self.on_cancel = on_cancel
        self.parent = parent
        self.alive = False
        self.win = None

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def reset(self, seconds):
        self.remaining = seconds

    def _run(self):
        self.alive = True

        root = self.parent if self.parent else tk._default_root
        if root is None:
            return

        self.win = tk.Toplevel(root)

        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.92)
        self.win.configure(bg="#1a1a2e")

        self.win.update_idletasks()

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 320, 90

        self.win.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 60}")

        tk.Label(self.win, text="🔒 FaceLock",
                 bg="#1a1a2e", fg="#e94560",
                 font=("Consolas", 11, "bold")).place(x=14, y=10)

        self.msg = tk.Label(self.win,
                            text=f"Verrouillage dans {self.remaining}s...",
                            bg="#1a1a2e", fg="white",
                            font=("Consolas", 10))
        self.msg.place(x=14, y=36)

        tk.Button(self.win, text="Annuler",
                  bg="#e94560", fg="white",
                  font=("Consolas", 9, "bold"),
                  relief="flat",
                  command=self._on_cancel).place(x=w - 90, y=30)

        self._tick()

    def _tick(self):
        if not self.alive:
            return

        if self.remaining <= 0:
            self._close()
            return

        self.msg.config(text=f"Verrouillage dans {self.remaining}s...")
        self.remaining -= 1

        self.win.after(1000, self._tick)

    def _on_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self._close()

    def _close(self):
        self.alive = False
        try:
            if self.win:
                self.win.destroy()
        except:
            pass