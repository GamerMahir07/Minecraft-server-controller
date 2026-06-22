"""core/settings.py"""
import json, threading, os
from .constants import SETTINGS_FILE

_cache: dict | None = None
_lock = threading.Lock()


def load_settings() -> dict:
    global _cache
    with _lock:
        if _cache is not None:
            return dict(_cache)
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
        return dict(_cache)


def save_settings(data: dict):
    global _cache
    with _lock:
        _cache = dict(data)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def update_setting(key: str, value):
    global _cache
    with _lock:
        if _cache is None:
            _cache = {}
        _cache[key] = value
        snap = dict(_cache)
    def _w():
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(snap, f, indent=2)
        except Exception:
            pass
    threading.Thread(target=_w, daemon=True).start()


def load_presets() -> dict:
    return load_settings().get("server_presets", {})


def save_preset(name: str, path: str, java: str | None = None, ram_gb: int = 2):
    s = load_settings()
    presets = s.get("server_presets", {})
    presets[name] = {
        "path": path,
        "java": java or s.get("java_path", "java"),
        "ram_gb": ram_gb,
    }
    update_setting("server_presets", presets)


def delete_preset(name: str):
    s = load_settings()
    presets = s.get("server_presets", {})
    presets.pop(name, None)
    update_setting("server_presets", presets)
