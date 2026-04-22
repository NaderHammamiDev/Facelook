import json
import os


CONFIG_PATH = os.path.join("data", "config.json")

DEFAULTS = {
    "lock_timeout": 30,       # secondes avant verrouillage si absent
    "warn_before":  10,       # secondes avant le lock → toast affiché
    "show_score":   True,     # afficher la distance L2 sur la caméra
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge avec les defaults pour les clés manquantes
        return {**DEFAULTS, **data}
    except Exception:
        return DEFAULTS.copy()


def save_config(cfg: dict):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)
print("CONFIG LOADED")        
