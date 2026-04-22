import tkinter as tk
import threading
 
 
class ToastNotification:
    """
    Toast Windows-style en bas à droite avec compte à rebours.
    Usage :
        ToastNotification.show(seconds=10, on_cancel=callback)
        ToastNotification.dismiss()
    """
 
    _instance = None
    _lock     = threading.Lock()
 
    @classmethod
    def show(cls, seconds: int, on_cancel=None):
        with cls._lock:
            if cls._instance and cls._instance.alive:
                cls._instance.reset(seconds)
                return
            t = cls(seconds, on_cancel)
            cls._instance = t
            t.start()
 
    @classmethod
    def dismiss(cls):
        with cls._lock:
            if cls._instance and cls._instance.alive:
                cls._instance._close()
 
    # ──────────────────────────────────────────────
    def __init__(self, seconds: int, on_cancel=None):
        self.seconds   = seconds
        self.remaining = seconds
        self.on_cancel = on_cancel
        self.alive     = False
        self.win       = None
 
    def start(self):
        threading.Thread(target=self._run, daemon=True).start()
 
    def reset(self, seconds: int):
        self.remaining = seconds
 
    def _run(self):
        self.alive = True
        root = tk.Tk()
        self.win = root
 
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)
        root.configure(bg="#1a1a2e")
 
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        w, h = 320, 90
        root.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 60}")
 
        tk.Label(root, text="🔒  FaceLock",
                 bg="#1a1a2e", fg="#e94560",
                 font=("Consolas", 11, "bold")).place(x=14, y=10)
 
        self.msg = tk.Label(root,
                            text=f"Verrouillage dans {self.remaining}s...",
                            bg="#1a1a2e", fg="#ffffff",
                            font=("Consolas", 10))
        self.msg.place(x=14, y=36)
 
        tk.Button(root, text="Annuler",
                  bg="#e94560", fg="white",
                  font=("Consolas", 9, "bold"),
                  relief="flat", cursor="hand2",
                  command=self._on_cancel).place(x=w - 90, y=30)
 
        self._tick(root)
        root.mainloop()
        self.alive = False
 
    def _tick(self, root):
        if not self.alive:
            return
        if self.remaining <= 0:
            self._close()
            return
        self.msg.config(text=f"Verrouillage dans {self.remaining}s...")
        self.remaining -= 1
        root.after(1000, lambda: self._tick(root))
 
    def _on_cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self._close()
 
    def _close(self):
        self.alive = False
        try:
            if self.win:
                self.win.destroy()
        except Exception:
            pass