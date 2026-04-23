import json
import os

DB_PATH = "data/facelock.db"
KNOWN_FACES_DIR = "known_faces"
THRESHOLD = 0.6

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "lock_timeout": 20,
    "warn_before": 10,
    "show_score": True
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)

    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = value

    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)