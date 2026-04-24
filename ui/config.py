import json
import os


CONFIG_PATH = os.path.join("data", "config.json")

DEFAULTS = {
    "lock_timeout": 30,       
    "warn_before":  10,       
    "show_score":   True,   
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return DEFAULTS.copy()


def save_config(cfg: dict):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)
print("CONFIG LOADED")        
