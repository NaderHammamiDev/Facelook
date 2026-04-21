import os
from cryptography.fernet import Fernet
import stat

# 🔐 ISO / RGPD: clé hors dossier projet
KEY_FILE = os.path.expanduser("~/.facelock_key")


def load_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

    # =========================
    # 🔑 CREATE KEY IF NOT EXISTS
    # =========================
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as f:
            f.write(key)

        # 🔐 permissions sécurité
        try:
            os.chmod(KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except:
            pass

    # =========================
    # 📥 LOAD KEY
    # =========================
    with open(KEY_FILE, "rb") as f:
        key = f.read()

    return Fernet(key)


# =========================
# 🔐 ENCRYPTION
# =========================
def encrypt(data: bytes):
    return load_key().encrypt(data)


# =========================
# 🔐 DECRYPTION
# =========================
def decrypt(token: bytes):
    return load_key().decrypt(token)