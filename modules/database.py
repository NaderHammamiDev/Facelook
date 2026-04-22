import sqlite3
import os
import numpy as np
import datetime
import json
import csv

from modules.encryption import encrypt, decrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


DB_PATH = os.path.join("data", "facelock.db")
RETENTION_DAYS = 30


class DatabaseManager:

    def __init__(self):
        os.makedirs("data", exist_ok=True)

        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)

        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA secure_delete=ON;")
        self.conn.execute("PRAGMA foreign_keys=ON;")

        self.create_tables()

    # =========================
    # TABLES
    # =========================
    def create_tables(self):

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            embedding BLOB,
            role TEXT DEFAULT 'user',
            consent INTEGER DEFAULT 0,
            consent_date TEXT,
            consent_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """)

        # POLICY TABLE
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS privacy_policy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT,
            date TEXT,
            text TEXT
        )
        """)

        # AUDIT TABLE
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            user TEXT,
            timestamp TEXT
        )
        """)

        self.conn.commit()
        self.init_privacy_policy()

    # =========================
    # POLICY INIT
    # =========================
    def init_privacy_policy(self):
        cursor = self.conn.execute("SELECT COUNT(*) FROM privacy_policy")
        if cursor.fetchone()[0] == 0:
            self.conn.execute("""
                INSERT INTO privacy_policy (version, date, text)
                VALUES (?, ?, ?)
            """, (
                "v1.0",
                "2026-04-17",
                "Biometric data used only for local authentication."
            ))
            self.conn.commit()

    # =========================
    # STORE
    # =========================
    def store_embedding(self, name, embedding, role="user", consent=1, consent_version="v1.0"):
        try:
            encrypted = encrypt(embedding.tobytes())
            now = datetime.datetime.utcnow().isoformat()

            self.conn.execute("""
                INSERT INTO users (
                    name, embedding, role,
                    consent, consent_date, consent_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    embedding=excluded.embedding,
                    role=excluded.role,
                    consent=excluded.consent,
                    consent_date=excluded.consent_date,
                    consent_version=excluded.consent_version
            """, (
                name, encrypted, role,
                consent, now, consent_version, now
            ))

            self.conn.commit()
            self.log_audit("ENROLL", name)

        except Exception as e:
            print("DB ERROR:", e)

    # =========================
    # LOAD
    # =========================
    def load_embeddings(self):
        cursor = self.conn.execute("""
            SELECT name, embedding FROM users WHERE consent=1
        """)

        data = []

        for name, enc in cursor:
            try:
                decrypted = decrypt(enc)
                emb = np.frombuffer(decrypted, dtype=np.float32).flatten()

                if emb.shape[0] != 128:
                    continue

                data.append((name, emb))

            except:
                continue

        return data

    # =========================
    # DELETE
    # =========================
    def delete_user(self, name):
        try:
            self.conn.execute("DELETE FROM users WHERE name=?", (name,))
            self.conn.commit()
            self.log_audit("DELETE", name)
            return True
        except:
            return False

    # =========================
    # UPDATE LOGIN
    # =========================
    def update_last_login(self, name):
        self.conn.execute("""
            UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE name=?
        """, (name,))
        self.conn.commit()

    # =========================
    # CLEANUP RGPD
    # =========================
    def cleanup_old_data(self):
        self.conn.execute("""
            DELETE FROM users
            WHERE julianday('now') - julianday(consent_date) > ?
        """, (RETENTION_DAYS,))
        self.conn.commit()

    # =========================
    # USER DATA
    # =========================
    def get_user_data(self, name):
        cursor = self.conn.execute("""
            SELECT name, consent, consent_date, consent_version,
                   created_at, last_login, role
            FROM users WHERE name=?
        """, (name,))

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "name": row[0],
            "consent": row[1],
            "consent_date": row[2],
            "consent_version": row[3],
            "created_at": row[4],
            "last_login": row[5],
            "role": row[6],
            "export_date": datetime.datetime.utcnow().isoformat()
        }

    # =========================
    # POLICY GET
    # =========================
    def get_privacy_policy(self):
        cursor = self.conn.execute("""
            SELECT version, date, text
            FROM privacy_policy
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            return {"version": "v0", "date": "", "text": ""}

        return {
            "version": row[0],
            "date": row[1],
            "text": row[2]
        }

    # =========================
    # AUDIT LOG
    # =========================
    def log_audit(self, action, user):
        self.conn.execute("""
            INSERT INTO audit_logs (action, user, timestamp)
            VALUES (?, ?, ?)
        """, (action, user, datetime.datetime.utcnow().isoformat()))

        self.conn.commit()

    # =========================
    # EXPORT USER
    # =========================
    def export_user_json(self, name):
        data = self.get_user_data(name)
        if not data:
            return None

        os.makedirs("exports", exist_ok=True)
        path = f"exports/{name}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.log_audit("EXPORT_JSON", name)
        return path

    def export_user_csv(self, name):
        data = self.get_user_data(name)
        if not data:
            return None

        os.makedirs("exports", exist_ok=True)
        path = f"exports/{name}.csv"

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(data.keys())
            writer.writerow(data.values())

        self.log_audit("EXPORT_CSV", name)
        return path

    def export_user_pdf(self, name):
        data = self.get_user_data(name)
        if not data:
            return None

        os.makedirs("exports", exist_ok=True)
        path = f"exports/{name}.pdf"

        doc = SimpleDocTemplate(path)
        styles = getSampleStyleSheet()

        content = [Paragraph("RGPD EXPORT", styles["Title"])]

        for k, v in data.items():
            content.append(Paragraph(f"{k}: {v}", styles["Normal"]))

        doc.build(content)

        self.log_audit("EXPORT_PDF", name)
        return path

    # =========================
    # EXPORT AUDIT
    # =========================
    def export_audit_json(self):
        cursor = self.conn.execute("SELECT action, user, timestamp FROM audit_logs")
        data = [{"action": a, "user": u, "timestamp": t} for a, u, t in cursor.fetchall()]

        os.makedirs("exports", exist_ok=True)
        path = "exports/audit.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return path

    def export_audit_csv(self):
        cursor = self.conn.execute("SELECT action, user, timestamp FROM audit_logs")

        os.makedirs("exports", exist_ok=True)
        path = "exports/audit.csv"

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["action", "user", "timestamp"])
            writer.writerows(cursor.fetchall())

        return path

    def export_audit_pdf(self):
        cursor = self.conn.execute("SELECT action, user, timestamp FROM audit_logs")

        os.makedirs("exports", exist_ok=True)
        path = "exports/audit.pdf"

        doc = SimpleDocTemplate(path)
        styles = getSampleStyleSheet()

        content = [Paragraph("AUDIT LOGS", styles["Title"])]

        for a, u, t in cursor.fetchall():
            content.append(Paragraph(f"{a} - {u} - {t}", styles["Normal"]))

        doc.build(content)

        return path

    # =========================
    # CLOSE
    # =========================
    def close(self):
        self.conn.close()
