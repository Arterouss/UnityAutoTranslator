import os
import sys
import json

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "engine": "google",  # google, gemini, deepl, openai, custom
    "target_lang": "id",
    "threads": 5,
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash",
    "deepl_api_key": "",
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    "custom_endpoint": "http://localhost:11434/v1",
    "custom_model": "qwen2.5:latest"
}

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
