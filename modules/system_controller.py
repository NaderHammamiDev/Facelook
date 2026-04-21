import ctypes
import time


class SystemController:

    def __init__(self):
        self.last_seen = time.time()

    # 🔐 LOCK WINDOWS SESSION
    def lock_workstation(self):
        ctypes.windll.user32.LockWorkStation()

    # 👁 update activity when face detected
    def update_activity(self):
        self.last_seen = time.time()

    # ⏱ idle time (cahier des charges OK)
    def get_idle_time(self):
        return time.time() - self.last_seen

    # ❌ check inactivity
    def is_user_absent(self, timeout=30):
        return self.get_idle_time() > timeout

    # 🔥 AUTO LOCK SYSTEM
    def check_and_lock(self, timeout=30):
        if self.is_user_absent(timeout):
            print("[FACELOCK] USER ABSENT → LOCK")
            self.lock_workstation()
            self.update_activity()