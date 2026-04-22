import ctypes
import time
 
 
class SystemController:
 
    def __init__(self):
        self.last_seen = time.time()
 
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