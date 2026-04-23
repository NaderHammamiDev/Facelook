import ctypes
import ctypes.wintypes
import time
 
 
class SystemController:
 
    def __init__(self):
        self.last_seen   = time.time()
        self._was_locked = False   # état précédent du verrou
 
    # =========================
    def lock_workstation(self):
        ctypes.windll.user32.LockWorkStation()
 
    def update_activity(self):
        self.last_seen = time.time()
 
    def get_idle_time(self):
        return time.time() - self.last_seen
 
    def is_user_absent(self, timeout=30):
        return self.get_idle_time() > timeout
 
    def check_and_lock(self, timeout=30):
        if self.is_user_absent(timeout):
            print("[FACELOCK] USER ABSENT → LOCK")
            self.lock_workstation()
            self.update_activity()
 
    # =========================
    # ✅ Détecte si Windows est actuellement verrouillé
    #    En essayant d'ouvrir le bureau interactif :
    #    - Si ça échoue  → session verrouillée
    #    - Si ça réussit → session active
    # =========================
    def is_workstation_locked(self) -> bool:
        try:
            user32 = ctypes.windll.user32
            # DESKTOP_SWITCHDESKTOP = 0x0100
            hDesk = user32.OpenInputDesktop(0, False, 0x0100)
            if hDesk == 0:
                return True   # bureau inaccessible → verrouillé
            user32.CloseDesktop(hDesk)
            return False
        except Exception:
            return False
 
    # =========================
    # ✅ Retourne True UNE SEULE FOIS au moment où Windows
    #    passe de "verrouillé" → "déverrouillé"
    #    (déclencheur pour demander la vérification faciale)
    # =========================
    def just_unlocked(self) -> bool:
        locked_now = self.is_workstation_locked()
 
        if self._was_locked and not locked_now:
            # Transition verrouillé → déverrouillé détectée
            self._was_locked = False
            print("[FACELOCK] Session déverrouillée → vérification faciale requise")
            return True
 
        self._was_locked = locked_now
        return False