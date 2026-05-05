import time
import shutil
import tkinter as tk
import tkinter.filedialog as _tk_fd
# matplotlib removed (unused) — was causing slow startup
import customtkinter as ctk
import subprocess
import threading
import json
import os
import ctypes
import re
import urllib.request
import urllib.error
import importlib.util
import sys
from datetime import datetime
try:
    import tkinterdnd2 as dnd
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

CREATE_NO_WINDOW = 0x08000000

# ── playit.gg globals ─────────────────────────────────────
playit_proc      = None
playit_tunnel    = None
playit_log_lines = []
_playit_addr_re  = re.compile(
    r'((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg|joinmc\.link|plymc\.link|mc\.gg)(?::\d+)?)',
    re.IGNORECASE)
# Also match the "hostname => ip:port" arrow format playit uses in its TUI
_playit_arrow_re = re.compile(
    r'([\w][\w\-.]+\.[a-z]{2,})\s*=>\s*[\d.]+:\d+', re.IGNORECASE)
_playit_claim_re = re.compile(
    r'(https?://[^\s]+(?:playit|claim|tunnel)[^\s]*)', re.IGNORECASE)

# ── App addon globals ──────────────────────────────────────
_loaded_addons   = {}   # name -> module

SRV_PATH  = r"C:\Users\DigitalComputer\Desktop\mc"
JAVA_PATH = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe"
REPO_URL  = "https://github.com/GamerMahir07/minecraft-server.git"

THEMES = {
    # ── Default ───────────────────────────────────────────
    "Dark (Default)":            {"appearance":"dark", "bg":"#0d0d0d","card":"#1a1a1a","border":"#2a2a2a","text":"#e0e0e0","muted":"#555555","start":"#22c55e","stop":"#ef4444","sync":"#60a5fa","handoff":"#f59e0b"},
    "Light (Default)":           {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#e0e0e0","text":"#1a1a1a","muted":"#888888","start":"#16a34a","stop":"#dc2626","sync":"#2563eb","handoff":"#d97706"},
    # ── Midnight Blue ─────────────────────────────────────
    "Midnight Blue Dark":        {"appearance":"dark", "bg":"#0a0f1e","card":"#111827","border":"#1e3a5f","text":"#e2e8f0","muted":"#4a6080","start":"#34d399","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Midnight Blue Light":       {"appearance":"light","bg":"#e8eeff","card":"#ffffff","border":"#7a9fd4","text":"#0a0f2e","muted":"#5570a0","start":"#059669","stop":"#dc2626","sync":"#4f46e5","handoff":"#d97706"},
    # ── Creeper Green ─────────────────────────────────────
    "Creeper Green Dark":        {"appearance":"dark", "bg":"#0a1a0a","card":"#0f2a0f","border":"#1a4a1a","text":"#c8f0c8","muted":"#3a6a3a","start":"#4ade80","stop":"#f87171","sync":"#86efac","handoff":"#fde047"},
    "Creeper Green Light":       {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#86efac","text":"#052e16","muted":"#3a7a3a","start":"#16a34a","stop":"#dc2626","sync":"#059669","handoff":"#ca8a04"},
    # ── Nether Red ────────────────────────────────────────
    "Nether Red Dark":           {"appearance":"dark", "bg":"#000000","card":"#1a0000","border":"#6a0000","text":"#ff4444","muted":"#8b0000","start":"#ff6b6b","stop":"#ff0000","sync":"#ff8c8c","handoff":"#ffd700"},
    "Nether Red Light":          {"appearance":"light","bg":"#fff5f5","card":"#ffffff","border":"#fca5a5","text":"#3a0000","muted":"#b06060","start":"#b91c1c","stop":"#7f1d1d","sync":"#dc2626","handoff":"#c2410c"},
    # ── Ocean ─────────────────────────────────────────────
    "Ocean Dark":                {"appearance":"dark", "bg":"#01131e","card":"#021f30","border":"#0e4a6e","text":"#bae6fd","muted":"#2a6a8a","start":"#22d3ee","stop":"#f87171","sync":"#38bdf8","handoff":"#fbbf24"},
    "Ocean Light":               {"appearance":"light","bg":"#e0f7ff","card":"#ffffff","border":"#7dd3f0","text":"#003a52","muted":"#4a8fa8","start":"#0284c7","stop":"#e11d48","sync":"#0ea5e9","handoff":"#f59e0b"},
    # ── Sunset ────────────────────────────────────────────
    "Sunset Dark":               {"appearance":"dark", "bg":"#1a0a00","card":"#2a1200","border":"#7c3a10","text":"#ffe4c4","muted":"#8a5030","start":"#4ade80","stop":"#f87171","sync":"#c084fc","handoff":"#fb923c"},
    "Sunset Light":              {"appearance":"light","bg":"#fff7ed","card":"#ffffff","border":"#fed7aa","text":"#1c0a00","muted":"#9a6030","start":"#16a34a","stop":"#e11d48","sync":"#7c3aed","handoff":"#ea580c"},
    # ── Obsidian ──────────────────────────────────────────
    "Obsidian Dark":             {"appearance":"dark", "bg":"#080808","card":"#101010","border":"#1e1e2e","text":"#cdd6f4","muted":"#45475a","start":"#a6e3a1","stop":"#f38ba8","sync":"#89b4fa","handoff":"#fab387"},
    "Obsidian Light":            {"appearance":"light","bg":"#f0f0f8","card":"#ffffff","border":"#c5c5e0","text":"#1e1e2e","muted":"#6e7090","start":"#40a02b","stop":"#d20f39","sync":"#1e66f5","handoff":"#e49320"},
    # ── Ender Night ───────────────────────────────────────
    "Ender Night Dark":          {"appearance":"dark", "bg":"#000000","card":"#0d0010","border":"#3b0060","text":"#e8b4ff","muted":"#6a2a8a","start":"#bf7fff","stop":"#ff5f87","sync":"#d68fff","handoff":"#ffb347"},
    "Ender Night Light":         {"appearance":"light","bg":"#f8f0ff","card":"#ffffff","border":"#d4b0ff","text":"#200040","muted":"#7a40a0","start":"#7c3aed","stop":"#db2777","sync":"#6d28d9","handoff":"#c2410c"},
    # ── Arctic ────────────────────────────────────────────
    "Arctic Light":              {"appearance":"light","bg":"#eef4fb","card":"#ffffff","border":"#b8d4f0","text":"#0d2137","muted":"#6a90b0","start":"#0ea5e9","stop":"#e11d48","sync":"#6366f1","handoff":"#f59e0b"},
    "Arctic Dark":               {"appearance":"dark", "bg":"#071520","card":"#0d2035","border":"#1a4060","text":"#dbeafe","muted":"#3a6080","start":"#38bdf8","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    # ── Forest ────────────────────────────────────────────
    "Forest Dark":               {"appearance":"dark", "bg":"#0d1a0d","card":"#142414","border":"#254025","text":"#d4edda","muted":"#4a7a4a","start":"#86efac","stop":"#fca5a5","sync":"#6ee7b7","handoff":"#fde68a"},
    "Forest Light":              {"appearance":"light","bg":"#f0faf0","card":"#ffffff","border":"#a7d7a7","text":"#0a2010","muted":"#4a7a4a","start":"#16a34a","stop":"#dc2626","sync":"#0d9488","handoff":"#ca8a04"},
    # ── Rose Gold ─────────────────────────────────────────
    "Rose Gold Dark":            {"appearance":"dark", "bg":"#1a0008","card":"#2a0010","border":"#7a2040","text":"#ffd6e0","muted":"#8a4060","start":"#fb7185","stop":"#f43f5e","sync":"#f472b6","handoff":"#fb923c"},
    "Rose Gold Light":           {"appearance":"light","bg":"#fff0f3","card":"#ffffff","border":"#f4c2cb","text":"#3a0a14","muted":"#b06070","start":"#e11d48","stop":"#9f1239","sync":"#db2777","handoff":"#c2410c"},
    # ── Dracula ───────────────────────────────────────────
    "Dracula Dark":              {"appearance":"dark", "bg":"#282a36","card":"#313442","border":"#44475a","text":"#f8f8f2","muted":"#6272a4","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Dracula Light":             {"appearance":"light","bg":"#f8f8f5","card":"#ffffff","border":"#bdbdcc","text":"#282a36","muted":"#6272a4","start":"#2da44e","stop":"#d0333e","sync":"#0087cc","handoff":"#c47900"},
    # ── Lava ──────────────────────────────────────────────
    "Lava Dark":                 {"appearance":"dark", "bg":"#120500","card":"#1e0a00","border":"#5a1a00","text":"#ffe8d0","muted":"#7a3a10","start":"#ff7c00","stop":"#ff3300","sync":"#ffaa00","handoff":"#ffdd00"},
    "Lava Light":                {"appearance":"light","bg":"#fff8f0","card":"#ffffff","border":"#ffc080","text":"#2a0a00","muted":"#a05020","start":"#c2410c","stop":"#b91c1c","sync":"#ea580c","handoff":"#b45309"},
    # ── Sand ──────────────────────────────────────────────
    "Sand Light":                {"appearance":"light","bg":"#f5e6c8","card":"#fdf3e0","border":"#c8a96e","text":"#3d2b00","muted":"#8a6a30","start":"#5a8a00","stop":"#c0392b","sync":"#1a6b8a","handoff":"#c07000"},
    "Sand Dark":                 {"appearance":"dark", "bg":"#1a1200","card":"#2a1e00","border":"#7a5a20","text":"#f0dcb0","muted":"#7a6030","start":"#a0c040","stop":"#e05030","sync":"#40a0c0","handoff":"#e0a000"},
    # ── Void ──────────────────────────────────────────────
    "Void Dark":                 {"appearance":"dark", "bg":"#000000","card":"#0a0a0a","border":"#1a1a1a","text":"#aaaaaa","muted":"#333333","start":"#444444","stop":"#666666","sync":"#555555","handoff":"#777777"},
    "Void Light":                {"appearance":"light","bg":"#f0f0f0","card":"#ffffff","border":"#cccccc","text":"#222222","muted":"#999999","start":"#444444","stop":"#888888","sync":"#666666","handoff":"#777777"},
    # ── Carbon ────────────────────────────────────────────
    "Carbon Dark":               {"appearance":"dark", "bg":"#1a1a2e","card":"#16213e","border":"#0f3460","text":"#e0e0e0","muted":"#4a4a6a","start":"#00c896","stop":"#e94560","sync":"#4d9fff","handoff":"#f5a623"},
    "Carbon Light":              {"appearance":"light","bg":"#eef0ff","card":"#ffffff","border":"#8090cc","text":"#0a0a20","muted":"#5060a0","start":"#009966","stop":"#cc2244","sync":"#2266cc","handoff":"#c07000"},
    # ── Lavender ──────────────────────────────────────────
    "Lavender Light":            {"appearance":"light","bg":"#f0eeff","card":"#ffffff","border":"#c5b8ff","text":"#1a0050","muted":"#7060a0","start":"#5b21b6","stop":"#db2777","sync":"#4f46e5","handoff":"#d97706"},
    "Lavender Dark":             {"appearance":"dark", "bg":"#0f0820","card":"#1a1035","border":"#3d2a7a","text":"#e8dfff","muted":"#6050a0","start":"#a78bfa","stop":"#f472b6","sync":"#818cf8","handoff":"#fbbf24"},
    # ── Mocha ─────────────────────────────────────────────
    "Mocha Dark":                {"appearance":"dark", "bg":"#1c1410","card":"#2a1f18","border":"#4a3428","text":"#f0dece","muted":"#7a5a48","start":"#c8a86e","stop":"#e05050","sync":"#90b8d0","handoff":"#e8c060"},
    "Mocha Light":               {"appearance":"light","bg":"#fdf6ee","card":"#ffffff","border":"#d4b896","text":"#2a1a0a","muted":"#9a7a60","start":"#7a5a28","stop":"#c0392b","sync":"#2a6080","handoff":"#c07020"},
    # ── Sakura ────────────────────────────────────────────
    "Sakura Light":              {"appearance":"light","bg":"#fff0f5","card":"#ffffff","border":"#ffb8cc","text":"#3a0020","muted":"#c06080","start":"#be185d","stop":"#e11d48","sync":"#9d174d","handoff":"#f59e0b"},
    "Sakura Dark":               {"appearance":"dark", "bg":"#1a0010","card":"#2a0018","border":"#7a2050","text":"#ffd6e8","muted":"#8a4068","start":"#f472b6","stop":"#fb7185","sync":"#e879f9","handoff":"#fbbf24"},
    # ── Matrix ────────────────────────────────────────────
    "Matrix Dark":               {"appearance":"dark", "bg":"#000000","card":"#001400","border":"#004400","text":"#00ff41","muted":"#006600","start":"#00ff41","stop":"#ff0000","sync":"#00cc33","handoff":"#ffff00"},
    "Matrix Light":              {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#80cc80","text":"#002200","muted":"#408040","start":"#166534","stop":"#b91c1c","sync":"#14532d","handoff":"#713f12"},
    # ── Nord ──────────────────────────────────────────────
    "Nord Dark":                 {"appearance":"dark", "bg":"#2e3440","card":"#3b4252","border":"#434c5e","text":"#eceff4","muted":"#4c566a","start":"#a3be8c","stop":"#bf616a","sync":"#88c0d0","handoff":"#ebcb8b"},
    "Nord Light":                {"appearance":"light","bg":"#eceff4","card":"#ffffff","border":"#d8dee9","text":"#2e3440","muted":"#7a8898","start":"#4c9a2a","stop":"#bf616a","sync":"#5e81ac","handoff":"#d08770"},
    # ── Solarized ─────────────────────────────────────────
    "Solarized Light":           {"appearance":"light","bg":"#fdf6e3","card":"#eee8d5","border":"#93a1a1","text":"#073642","muted":"#657b83","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Solarized Dark":            {"appearance":"dark", "bg":"#002b36","card":"#073642","border":"#586e75","text":"#fdf6e3","muted":"#839496","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    # ── Gruvbox ───────────────────────────────────────────
    "Gruvbox Dark":              {"appearance":"dark", "bg":"#282828","card":"#3c3836","border":"#504945","text":"#ebdbb2","muted":"#7c6f64","start":"#b8bb26","stop":"#fb4934","sync":"#83a598","handoff":"#fabd2f"},
    "Gruvbox Light":             {"appearance":"light","bg":"#fbf1c7","card":"#f9f5d7","border":"#d5c4a1","text":"#3c3836","muted":"#928374","start":"#79740e","stop":"#9d0006","sync":"#076678","handoff":"#b57614"},
    # ── Cyberpunk ─────────────────────────────────────────
    "Cyberpunk Dark":            {"appearance":"dark", "bg":"#0a0014","card":"#110022","border":"#ff00ff","text":"#00ffff","muted":"#8800aa","start":"#00ffff","stop":"#ff0088","sync":"#ff00ff","handoff":"#ffff00"},
    "Cyberpunk Light":           {"appearance":"light","bg":"#f0e8ff","card":"#ffffff","border":"#cc44ff","text":"#1a0030","muted":"#8840aa","start":"#0088cc","stop":"#cc0066","sync":"#8800ff","handoff":"#cc8800"},
    # ── Slate ─────────────────────────────────────────────
    "Slate Dark":                {"appearance":"dark", "bg":"#0f172a","card":"#1e293b","border":"#334155","text":"#f1f5f9","muted":"#64748b","start":"#22d3ee","stop":"#f43f5e","sync":"#818cf8","handoff":"#fb923c"},
    "Slate Light":               {"appearance":"light","bg":"#f1f5f9","card":"#ffffff","border":"#cbd5e1","text":"#0f172a","muted":"#64748b","start":"#0891b2","stop":"#e11d48","sync":"#4f46e5","handoff":"#ea580c"},
    # ── Amber ─────────────────────────────────────────────
    "Amber Dark":                {"appearance":"dark", "bg":"#1a1000","card":"#2a1a00","border":"#7a5500","text":"#ffe88a","muted":"#7a6020","start":"#fbbf24","stop":"#ef4444","sync":"#f59e0b","handoff":"#84cc16"},
    "Amber Light":               {"appearance":"light","bg":"#fffbeb","card":"#ffffff","border":"#fde68a","text":"#1c1400","muted":"#9a7a00","start":"#b45309","stop":"#dc2626","sync":"#d97706","handoff":"#65a30d"},
    # ── Copper ────────────────────────────────────────────
    "Copper Dark":               {"appearance":"dark", "bg":"#150900","card":"#221200","border":"#7a3a10","text":"#ffcc99","muted":"#7a4a20","start":"#f97316","stop":"#ef4444","sync":"#fb923c","handoff":"#fbbf24"},
    "Copper Light":              {"appearance":"light","bg":"#fff8f0","card":"#ffffff","border":"#e0a060","text":"#1a0800","muted":"#a06030","start":"#c2410c","stop":"#b91c1c","sync":"#d97706","handoff":"#65a30d"},
    # ── CB: Blue & Orange ─────────────────────────────────
    "CB: Blue & Orange Light":   {"appearance":"light","bg":"#f7f7f7","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#0072b2","stop":"#d55e00","sync":"#56b4e9","handoff":"#e69f00"},
    "CB: Blue & Orange Dark":    {"appearance":"dark", "bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#ffffff","muted":"#888888","start":"#56b4e9","stop":"#d55e00","sync":"#0072b2","handoff":"#e69f00"},
    # ── CB: Green & Purple ────────────────────────────────
    "CB: Green & Purple Light":  {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#009e73","stop":"#cc79a7","sync":"#0072b2","handoff":"#f0e442"},
    "CB: Green & Purple Dark":   {"appearance":"dark", "bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#eeeeee","muted":"#888888","start":"#009e73","stop":"#cc79a7","sync":"#56b4e9","handoff":"#f0e442"},
    # ── CB: High Contrast ─────────────────────────────────
    "CB: High Contrast Light":   {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#000000","text":"#000000","muted":"#444444","start":"#0000ff","stop":"#ff0000","sync":"#007700","handoff":"#ff8800"},
    "CB: High Contrast Dark":    {"appearance":"dark", "bg":"#000000","card":"#1a1a1a","border":"#ffffff","text":"#ffffff","muted":"#aaaaaa","start":"#ffff00","stop":"#ff6600","sync":"#00ffff","handoff":"#ff99ff"},
    # ── CB: Tol Muted ─────────────────────────────────────
    "CB: Tol Muted Light":       {"appearance":"light","bg":"#f8f4f0","card":"#ffffff","border":"#bbaabb","text":"#221122","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    "CB: Tol Muted Dark":        {"appearance":"dark", "bg":"#221122","card":"#332244","border":"#554466","text":"#eeddff","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    # ── CB: Monochrome ────────────────────────────────────
    "CB: Monochrome Light":      {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#999999","text":"#000000","muted":"#666666","start":"#222222","stop":"#777777","sync":"#444444","handoff":"#555555"},
    "CB: Monochrome Dark":       {"appearance":"dark", "bg":"#111111","card":"#1e1e1e","border":"#555555","text":"#eeeeee","muted":"#888888","start":"#cccccc","stop":"#888888","sync":"#aaaaaa","handoff":"#bbbbbb"},
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# ── Settings helpers (cached — avoids disk read on every widget event) ────────
_settings_cache = None
_settings_lock  = threading.Lock()

def load_settings():
    global _settings_cache
    with _settings_lock:
        if _settings_cache is not None:
            return dict(_settings_cache)
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                _settings_cache = json.load(f)
        except Exception:
            _settings_cache = {}
        return dict(_settings_cache)

def save_settings(data):
    global _settings_cache
    with _settings_lock:
        _settings_cache = dict(data)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def update_setting(key, value):
    global _settings_cache
    with _settings_lock:
        if _settings_cache is None:
            _settings_cache = {}
        _settings_cache[key] = value
    # Write in a background thread so the UI never blocks on disk I/O
    def _write():
        try:
            with _settings_lock:
                snap = dict(_settings_cache)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(snap, f, indent=2)
        except Exception:
            pass
    threading.Thread(target=_write, daemon=True).start()

settings           = load_settings()
is_first_launch    = "theme" not in settings
current_theme_name = settings.get("theme", "Dark (Default)")
show_chat          = settings.get("show_chat", True)
log_left           = settings.get("log_left", False)
show_perf          = settings.get("show_perf", True)
fullscreen         = settings.get("fullscreen", False)
auto_upload        = settings.get("auto_upload", False)
backup_upload_on   = settings.get("backup_upload_on", True)   # new switch
auto_upload_mins   = settings.get("auto_upload_mins", 10)
upload_on_stop     = settings.get("upload_on_stop", True)
ram_display_mode   = settings.get("ram_display_mode", "percent")
# Migrate old theme names that were renamed
_THEME_ALIASES = {
    "Obsidian":          "Obsidian Dark",
    "Midnight Blue":     "Midnight Blue Dark",
    "Creeper Green":     "Creeper Green Dark",
    "Nether Red":        "Nether Red Dark",
    "Ender Night":       "Ender Night Dark",
    "Ocean Light":       "Ocean Light",
    "Ocean Dark":        "Ocean Dark",
}
if current_theme_name not in THEMES:
    current_theme_name = _THEME_ALIASES.get(current_theme_name, "Dark (Default)")
T                  = THEMES[current_theme_name]

ctk.set_appearance_mode(T["appearance"])
ctk.set_default_color_theme("dark-blue")

server_proc       = None
server_stdin      = None
server_pid        = None
perf_running      = False
server_ready      = False
player_count      = 0
online_players    = {}   # name -> join_time string
auto_upload_timer = None
log_history       = ""
chat_history      = ""
_players_refresh_id = None   # after() id for live players panel

perf = {
    "ram_used":"--","ram_pct":"--","ram_srv":"--",
    "cpu_sys":"--","cpu_srv":"--",
    "tps":"--","latency":"--","players":"0",
    "uptime":"--","threads":"--",
}
server_start_time = None

# ── Regex ─────────────────────────────────────────────────
CHAT_RE         = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE         = re.compile(r'^(\w+) joined the game', re.IGNORECASE)
LEAVE_RE        = re.compile(r'^(\w+) (?:lost connection|left the game)', re.IGNORECASE)
DEATH_RE        = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.IGNORECASE)
STRIP_RE        = re.compile(r'^\[[\d:]+\]\s*\[.*?(?:INFO|WARN|ERROR).*?\]:\s*', re.IGNORECASE)
DONE_RE         = re.compile(r'Done \([\d.]+s\)!', re.IGNORECASE)
SPARK_TPS       = re.compile(r'TPS from last 1m[^:]*:\s*([\d.]+)', re.IGNORECASE)
TPS_RE2         = re.compile(r'Current TPS[:\s]+([\d.]+)', re.IGNORECASE)
PLAYER_RE       = re.compile(r'There are (\d+) of a max of \d+ players', re.IGNORECASE)
LIST_NAMES_RE   = re.compile(r'There are \d+[^:]*:\s*(.+)', re.IGNORECASE)
# Multiple latency formats: "Steve has 42ms", "Steve has a ping of 42ms", "Steve (42ms)"
LATENCY_RE      = re.compile(r'(\w+)\s+has\s+(?:a\s+ping\s+of\s+)?(\d+)\s*ms', re.IGNORECASE)
LATENCY_RE2     = re.compile(r'(\w+)\s*\((\d+)\s*ms\)', re.IGNORECASE)
LATENCY_RE3     = re.compile(r'ping\[(\w+)\]\s*=\s*(\d+)', re.IGNORECASE)

def parse_server_line(raw):
    global player_count, server_ready
    clean = STRIP_RE.sub('', raw).strip()
    if not clean:
        return None

    # ── Fast string pre-checks before any regex ──────────────
    # Server ready
    if "Done (" in clean:
        if DONE_RE.search(clean):
            server_ready = True
            app.after(0, show_toast, "Server is ready!", T["start"])
            return ('log', clean)

    # TPS — only run regex if keywords present
    if "TPS" in clean or "tps" in clean:
        tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
        if tps:
            perf["tps"] = tps.group(1)
            return None

    # Latency — only run if "ms" in line
    if "ms" in clean:
        lat = LATENCY_RE.search(clean) or LATENCY_RE2.search(clean) or LATENCY_RE3.search(clean)
        if lat:
            try:
                pings = [int(m[1]) for m in
                         (LATENCY_RE.findall(clean) or
                          LATENCY_RE2.findall(clean) or
                          LATENCY_RE3.findall(clean))]
                if pings:
                    perf["latency"] = f"{sum(pings) // len(pings)} ms"
            except: pass
            return None

    # Player list — only if "There are" in line
    if "There are" in clean:
        pl = PLAYER_RE.search(clean)
        if pl:
            player_count = int(pl.group(1))
            perf["players"] = str(player_count)
            nm = LIST_NAMES_RE.search(clean)
            if nm:
                raw_names = nm.group(1).strip()
                if raw_names and raw_names not in ("", "online:"):
                    names = [n.strip() for n in raw_names.split(",") if n.strip()]
                    now = datetime.now().strftime("%H:%M")
                    for n in names:
                        if n not in online_players:
                            online_players[n] = now
                    for gone in [k for k in online_players if k not in names]:
                        online_players.pop(gone, None)
            return None

    # Chat — only if line contains '<'
    if '<' in clean:
        chat = CHAT_RE.search(clean)
        if chat:
            return ('chat', f"[CHAT] {chat.group(1)}: {chat.group(2)}")

    # Join/Leave — only if "joined" or "left"/"lost" in line
    if "joined the game" in clean:
        join = JOIN_RE.search(clean)
        if join:
            name = join.group(1)
            player_count += 1
            perf["players"] = str(player_count)
            online_players[name] = datetime.now().strftime("%H:%M")
            return ('event', f">> {name} joined")

    if "left the game" in clean or "lost connection" in clean:
        leave = LEAVE_RE.search(clean)
        if leave:
            name = leave.group(1)
            player_count = max(0, player_count - 1)
            perf["players"] = str(player_count)
            online_players.pop(name, None)
            return ('event', f"<< {name} left")

    # Death — only if common death keywords present
    if any(w in clean for w in ("was slain","died","fell","drowned","burned","blew up","suffocated","starved","withered")):
        if DEATH_RE.search(clean):
            return ('event', f"[DEATH] {clean}")

    return ('log', clean)

# ── Pre-warm settings cache in background ─────────────────
threading.Thread(target=load_settings, daemon=True).start()

# ── App window ────────────────────────────────────────────
app = ctk.CTk()
app.title("MC CTRL")
app.geometry("1020x720")
app.resizable(True, True)
app.configure(fg_color=T["bg"])

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gamermahir07.mcserver.launcher.1')
try:
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    app.iconbitmap(ico)
except:
    pass

if fullscreen:
    app.after(100, lambda: app.attributes("-fullscreen", True))

# ── Core helpers ──────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        log_box.configure(state="normal")
        log_box.insert("end", f"[{ts}]  {msg}\n")
        log_box.configure(state="disabled")
        log_box.see("end")
    except:
        pass

def log_chat(msg):
    if not show_chat:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        chat_box.configure(state="normal")
        chat_box.insert("end", f"[{ts}]  {msg}\n")
        chat_box.configure(state="disabled")
        chat_box.see("end")
    except:
        pass

def set_status(txt, color):
    try:
        status_lbl.configure(text=txt)
        status_dot.configure(text_color=color)
    except:
        pass

def send_command():
    cmd = cmd_entry.get().strip()
    if not cmd:
        return
    cmd_entry.delete(0, "end")
    send_server_cmd(cmd)

def send_server_cmd(cmd):
    global server_stdin
    if server_stdin is None:
        show_toast("Server is not running!", T["stop"])
        return
    try:
        server_stdin.write(cmd + "\n")
        server_stdin.flush()
        log(f">> {cmd}")
    except BrokenPipeError:
        server_stdin = None
        show_toast("Lost connection to server!", T["stop"])
    except Exception as ex:
        log(f"Command failed: {ex}")

def run_cmd(cmd, cwd=None):
    log(f"$ {cmd}")
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                           text=True, creationflags=CREATE_NO_WINDOW)
        for line in p.stdout.strip().splitlines():
            log(f"  {line}")
        if p.returncode != 0:
            for line in p.stderr.strip().splitlines():
                log(f"  {line}")
        return p.returncode == 0
    except Exception as ex:
        log(str(ex)); return False

def set_all_buttons(state):
    for b in [btn_start, btn_stop, btn_sync]:
        try: b.configure(state=state)
        except: pass

def copy_log_to_clipboard():
    try:
        content = log_box.get("1.0", "end")
        app.clipboard_clear(); app.clipboard_append(content)
        show_toast("Log copied to clipboard!", T["sync"])
    except: pass

def read_server_output(proc):
    for raw in iter(proc.stdout.readline, ''):
        if not raw: break
        parsed = parse_server_line(raw)
        if parsed is None: continue
        cat, text = parsed
        if cat in ('chat', 'event'):
            app.after(0, log_chat, text)
        else:
            app.after(0, log, text)

# ── Toast notification ────────────────────────────────────
_toast_win = None

def show_toast(msg, color=None, duration_ms=3000):
    global _toast_win
    if color is None: color = T["sync"]
    try:
        if _toast_win and _toast_win.winfo_exists(): _toast_win.destroy()
    except: pass
    toast = ctk.CTkToplevel(app)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(fg_color=T["card"])
    _toast_win = toast
    frame = ctk.CTkFrame(toast, fg_color=T["card"],
                         border_color=color, border_width=2, corner_radius=10)
    frame.pack(padx=2, pady=2)
    ctk.CTkLabel(frame, text=msg,
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=color).pack(padx=18, pady=12)
    def _place():
        try:
            ax = app.winfo_x() + app.winfo_width() - 360
            ay = app.winfo_y() + app.winfo_height() - 80
            toast.geometry(f"+{ax}+{ay}")
        except: pass
    app.after(10, _place)
    app.after(duration_ms, lambda: toast.destroy() if toast.winfo_exists() else None)

# ── Auto upload ───────────────────────────────────────────
def toggle_auto_upload():
    global auto_upload
    auto_upload = not auto_upload
    update_setting("auto_upload", auto_upload)
    if auto_upload: schedule_auto_upload()
    else:
        if auto_upload_timer:
            try: auto_upload_timer.cancel()
            except: pass

def schedule_auto_upload():
    global auto_upload_timer
    if auto_upload_timer:
        try: auto_upload_timer.cancel()
        except: pass
    if not auto_upload: return
    auto_upload_timer = threading.Timer(auto_upload_mins * 60, _do_auto_upload)
    auto_upload_timer.daemon = True
    auto_upload_timer.start()

def _do_auto_upload():
    if not auto_upload: return
    if not backup_upload_on:
        schedule_auto_upload()  # reschedule but skip
        return
    s = load_settings()
    path = s.get("srv_path", SRV_PATH)
    repo = s.get("repo_url", REPO_URL)
    def _work():
        app.after(0, log, "-- Auto-upload -------------------")
        try:
            subprocess.run(f'git remote set-url origin {repo}', shell=True, cwd=path,
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run('git add .', shell=True, cwd=path,
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
            r = subprocess.run(
                f'git commit -m "Auto-upload {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                shell=True, cwd=path, capture_output=True, text=True,
                creationflags=CREATE_NO_WINDOW)
            if "nothing to commit" in r.stdout or r.returncode != 0:
                app.after(0, log, "  Nothing new to commit.")
            else:
                push = subprocess.run('git push origin main', shell=True, cwd=path,
                                      capture_output=True, text=True,
                                      creationflags=CREATE_NO_WINDOW)
                if push.returncode == 0:
                    app.after(0, log, "  Auto-upload complete.")
                    app.after(0, show_toast, "Auto-upload complete!", T["sync"])
                else:
                    app.after(0, log, f"  Push failed: {push.stderr.strip()}")
        except Exception as ex:
            app.after(0, log, f"  Error: {ex}")
        schedule_auto_upload()
    threading.Thread(target=_work, daemon=True).start()

# ── Perf polling ──────────────────────────────────────────
perf_labels = {}

def find_java_proc():
    """Use the captured server_pid directly — no full process scan."""
    import psutil
    if server_pid:
        try:
            return psutil.Process(server_pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    # Fallback: scan only if PID not captured yet (e.g. external server)
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'java' in p.info['name'].lower():
                if 'server.jar' in ' '.join(p.info['cmdline'] or []):
                    return p
        except: pass
    return None

def perf_loop():
    import psutil  # lazy
    global perf_running
    perf_running = True
    java_proc = None; tick = 0
    while perf_running:
        try:
            vm = psutil.virtual_memory()
            if ram_display_mode == "fraction":
                perf["ram_used"] = f"{vm.used/1024**3:.1f}/{vm.total/1024**3:.0f}GB"
            else:
                perf["ram_used"] = f"{vm.used/1024**3:.1f} GB"
            perf["ram_pct"] = f"{vm.percent:.0f}%"
            perf["cpu_sys"] = f"{psutil.cpu_percent(interval=None):.0f}%"
            if java_proc is None: java_proc = find_java_proc()
            if java_proc:
                try:
                    perf["ram_srv"] = f"{java_proc.memory_info().rss/1024**2:.0f} MB"
                    perf["cpu_srv"] = f"{java_proc.cpu_percent(interval=None):.0f}%"
                    perf["threads"] = str(java_proc.num_threads())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    java_proc = None
                    perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            else:
                perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            if server_start_time:
                elapsed = int((datetime.now() - server_start_time).total_seconds())
                h, r = divmod(elapsed, 3600); m, sc = divmod(r, 60)
                perf["uptime"] = f"{h:02d}:{m:02d}:{sc:02d}"
            else:
                perf["uptime"] = "--"
            if server_ready and server_stdin:
                try:
                    if tick % 5  == 0: server_stdin.write("tps\n");  server_stdin.flush()
                    if tick % 10 == 0: server_stdin.write("list\n"); server_stdin.flush()
                    # Spark ping gives per-player latency
                    if tick % 30 == 0 and online_players:
                        server_stdin.write("spark ping\n"); server_stdin.flush()
                except: pass
            tick += 1
            app.after(0, update_perf_labels)
        except: pass
        time.sleep(2)

def update_perf_labels():
    for key, lbl in perf_labels.items():
        try:
            val = perf[key]
            if key == "tps":
                try: t=float(val); c=T["start"] if t>=18 else T["handoff"] if t>=15 else T["stop"]
                except: c=T["text"]
                lbl.configure(text=val, text_color=c)
            elif key in ("cpu_sys","cpu_srv","ram_pct"):
                try: n=float(str(val).replace("%","")); c=T["start"] if n<60 else T["handoff"] if n<85 else T["stop"]
                except: c=T["text"]
                lbl.configure(text=val, text_color=c)
            elif key == "latency":
                try: n=float(str(val).replace("ms","").strip()); c=T["start"] if n<60 else T["handoff"] if n<120 else T["stop"]
                except: c=T["text"]
                lbl.configure(text=val, text_color=c)
            else:
                lbl.configure(text=val, text_color=T["text"])
        except: pass

# ── Theme / layout ────────────────────────────────────────
def apply_theme(name):
    global T, current_theme_name
    current_theme_name = name; T = THEMES[name]
    update_setting("theme", name)
    ctk.set_appearance_mode(T["appearance"])
    app.configure(fg_color=T["bg"])
    _recolor_all(app)

def _recolor_all(widget):
    """Recursively recolor every widget to match the new theme — no rebuild."""
    COLOR_MAP = {
        # Maps widget fg_color values to new theme equivalents
        # We walk the tree and update anything that holds a theme color.
    }
    try:
        # CTkTextbox, CTkFrame, CTkScrollableFrame — update fg_color
        wtype = type(widget).__name__
        if wtype in ("CTkFrame", "CTkScrollableFrame"):
            try:
                cur = widget.cget("fg_color")
                if cur not in ("transparent", "#00000000"):
                    widget.configure(fg_color=T["bg"])
            except: pass
        if wtype == "CTkTextbox":
            try: widget.configure(fg_color=T["bg"], text_color=T["text"])
            except: pass
        if wtype == "CTkLabel":
            try:
                cur = widget.cget("text_color")
                # Only recolor if it was set to a theme colour (not a status colour)
                widget.configure(text_color=T["text"])
            except: pass
        if wtype == "CTkButton":
            try: widget.configure(border_color=T["border"])
            except: pass
        if wtype == "CTkEntry":
            try: widget.configure(fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
            except: pass
        if wtype in ("CTkCanvas", "Canvas"):
            try: widget.configure(bg=T["bg"])
            except: pass
    except: pass
    try:
        for child in widget.winfo_children():
            _recolor_all(child)
    except: pass

def rebuild_ui():
    global log_history, chat_history
    try: log_history  = log_box.get("1.0","end")
    except: pass
    try: chat_history = chat_box.get("1.0","end")
    except: pass
    for w in app.winfo_children(): w.destroy()
    build_ui()
    # Restore playit log — if the playit tab was already built, repopulate it
    if playit_log_lines:
        def _restore_ptlog():
            try:
                from itertools import islice
                # find pt_log widget by scanning all Text widgets in the app
                def _find_text(w):
                    results = []
                    for child in w.winfo_children():
                        if isinstance(child, ctk.CTkTextbox):
                            results.append(child)
                        results.extend(_find_text(child))
                    return results
                # Just trigger the playit tab to build, then repopulate
                # The playit_log_lines global is preserved — _append_ptlog uses it
                pass  # log lines are re-added when tab is first opened via _built_tabs
            except Exception:
                pass
        app.after(100, _restore_ptlog)

def swap_layout():
    global log_left
    log_left = not log_left
    update_setting("log_left", log_left)
    rebuild_ui()

def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    update_setting("fullscreen", fullscreen)
    app.attributes("-fullscreen", fullscreen)
    if not fullscreen: app.geometry("1020x720")
    rebuild_ui()

def toggle_perf():
    global show_perf
    show_perf = not show_perf
    update_setting("show_perf", show_perf)
    rebuild_ui()

def toggle_chat():
    global show_chat
    show_chat = not show_chat
    update_setting("show_chat", show_chat)
    chat_toggle_btn.configure(text="Hide" if show_chat else "Show")
    if show_chat:
        chat_box.configure(height=110)
        chat_box.pack(fill="x", padx=8, pady=(4,8))
    else:
        chat_box.pack_forget(); chat_box.configure(height=0)

# ── First-Launch Onboarding Dialog ────────────────────────
def show_first_launch_dialog():
    global auto_upload, upload_on_stop, current_theme_name, T

    dlg = ctk.CTkToplevel(app)
    dlg.title("Welcome - First-Launch Setup")
    dlg.geometry("640x700"); dlg.resizable(False, False)
    dlg.configure(fg_color="#0d0d0d")
    dlg.grab_set(); dlg.attributes("-topmost", True)

    def _center():
        try:
            ax = app.winfo_x() + (app.winfo_width()  - 640) // 2
            ay = app.winfo_y() + (app.winfo_height() - 700) // 2
            dlg.geometry(f"640x700+{ax}+{ay}")
        except: pass
    app.after(50, _center)

    outer = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
    outer.pack(fill="both", expand=True)

    banner = ctk.CTkFrame(outer, fg_color="#1a0000", corner_radius=0)
    banner.pack(fill="x")
    ctk.CTkLabel(banner, text="READ ME!",
                 font=ctk.CTkFont(size=40, weight="bold"),
                 text_color="#ff3333").pack(pady=(22,2))
    ctk.CTkLabel(banner, text="First-time setup  |  takes about 30 seconds",
                 font=ctk.CTkFont(size=13), text_color="#ff8888").pack(pady=(0,22))

    def card(title, icon=""):
        f = ctk.CTkFrame(outer, fg_color="#1a1a1a",
                         border_color="#2a2a2a", border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(12,0))
        ctk.CTkLabel(f, text=f"{icon}  {title}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e0e0e0").pack(anchor="w", padx=16, pady=(14,6))
        ctk.CTkFrame(f, height=1, fg_color="#333333").pack(fill="x", padx=16)
        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(10,14))
        return body

    b1 = card("Choose Your Theme", "Appearance")
    ctk.CTkLabel(b1, text="Pick a colour scheme. You can change it any time in the top bar or Settings.",
                 font=ctk.CTkFont(size=12), text_color="#888888",
                 wraplength=560, justify="left").pack(anchor="w")
    theme_var = ctk.StringVar(value=current_theme_name)
    def _preview(name):
        global T, current_theme_name
        current_theme_name = name; T = THEMES[name]
        ctk.set_appearance_mode(T["appearance"])
    ctk.CTkOptionMenu(b1, values=list(THEMES.keys()), variable=theme_var, command=_preview,
                      font=ctk.CTkFont(size=12), width=300,
                      fg_color="#111111", button_color="#333333",
                      button_hover_color="#444444", text_color="#e0e0e0",
                      dropdown_fg_color="#1a1a1a", dropdown_text_color="#e0e0e0",
                      dropdown_hover_color="#2a2a2a").pack(anchor="w", pady=(10,0))

    b2 = card("GitHub World Backup", "Cloud")
    ctk.CTkLabel(b2, text=(
        "This launcher can automatically back up your Minecraft world\n"
        "to a GitHub repository so it is never lost.\n\n"
        "  Upload on Stop  ->  pushes world/ folders to GitHub when you Stop the server.\n"
        "  Auto-Upload  ->  background timer pushes every N minutes while running.\n"
        "  Manual Sync  ->  the Sync & Upload button pushes on demand.\n\n"
        "  If you do NOT want any files sent to GitHub or any other website,\n"
        "  leave BOTH toggles OFF. Nothing is ever pushed unless you allow it."
    ), font=ctk.CTkFont(size=12), text_color="#aaaaaa",
       wraplength=560, justify="left").pack(anchor="w")
    ctk.CTkFrame(b2, height=10, fg_color="transparent").pack()

    up_stop_var = ctk.BooleanVar(value=upload_on_stop)
    up_auto_var = ctk.BooleanVar(value=auto_upload)
    def toggle_row(parent, label, var):
        r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", pady=4)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color="#dddddd").pack(side="left")
        ctk.CTkSwitch(r, text="", variable=var,
                      button_color="#60a5fa", progress_color="#60a5fa").pack(side="right")
    toggle_row(b2, "Upload world to GitHub when server stops", up_stop_var)
    toggle_row(b2, "Enable timed auto-upload while server is running", up_auto_var)
    ctk.CTkLabel(b2, text="Repo URL, Java path, and upload interval can be configured in Settings.",
                 font=ctk.CTkFont(size=10), text_color="#555555").pack(anchor="w", pady=(8,0))

    ctk.CTkFrame(outer, height=12, fg_color="transparent").pack()

    def _confirm():
        global auto_upload, upload_on_stop, current_theme_name, T
        chosen = theme_var.get()
        current_theme_name = chosen; T = THEMES[chosen]
        auto_upload = up_auto_var.get(); upload_on_stop = up_stop_var.get()
        s = load_settings()
        s["theme"] = chosen; s["auto_upload"] = auto_upload
        s["upload_on_stop"] = upload_on_stop; s["first_launch_done"] = True
        save_settings(s)
        ctk.set_appearance_mode(T["appearance"])
        dlg.destroy(); rebuild_ui()
        if auto_upload: schedule_auto_upload()

    ctk.CTkButton(outer, text="Got it - Let's go!",
                  font=ctk.CTkFont(size=15, weight="bold"),
                  height=48, corner_radius=10,
                  fg_color="#22c55e", hover_color="#16a34a", text_color="#000000",
                  command=_confirm).pack(padx=20, pady=(0,24), fill="x")

# ── Smooth scrollable frame (replaces CTkScrollableFrame) ─
def make_scroll_frame(parent, **kwargs):
    """Canvas scroll area — atomic redraw, no flicker on fast scroll."""
    fg = kwargs.pop("fg_color", "transparent")
    bg = T["bg"] if fg == "transparent" else (fg[1] if isinstance(fg, (list,tuple)) else fg)

    outer = ctk.CTkFrame(parent, fg_color=fg, **kwargs)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    vbar   = ctk.CTkScrollbar(outer, orientation="vertical",
                               command=canvas.yview,
                               button_color=T["border"],
                               button_hover_color=T["muted"])
    vbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=vbar.set)

    inner = ctk.CTkFrame(canvas, fg_color=fg)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _resize_inner(e): canvas.itemconfig(win_id, width=e.width)
    def _update_region(e): canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.bind("<Configure>", _resize_inner)
    inner.bind("<Configure>", _update_region)

    def _scroll(e): canvas.yview_scroll(int(-e.delta / 60), "units")
    def _bind_tree(w):
        try:
            w.bind("<MouseWheel>", _scroll)
            for c in w.winfo_children(): _bind_tree(c)
        except Exception: pass
    canvas.bind("<MouseWheel>", _scroll)
    inner.bind("<MouseWheel>", _scroll)
    inner.bind("<Map>", lambda e: _bind_tree(inner))
    return inner

# ── UI ────────────────────────────────────────────────────
def build_ui():
    global status_dot, status_lbl, e_path, e_repo, e_java
    global btn_start, btn_stop, btn_sync

    is_fs = app.attributes("-fullscreen")

    # ── Top bar ───────────────────────────────────────────
    top = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0)
    top.pack(fill="x")
    ctk.CTkLabel(top, text="MC CTRL",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=16, pady=10)

    # Theme picker button → opens search/filter window
    def open_theme_picker():
        win = ctk.CTkToplevel(app)
        win.title("Theme Search")
        win.geometry("780x620")
        win.resizable(True, True)
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        try:
            ax = app.winfo_x() + (app.winfo_width()  - 780) // 2
            ay = app.winfo_y() + (app.winfo_height() - 620) // 2
            win.geometry(f"780x620+{ax}+{ay}")
        except: pass

        # ── colour-role filter state ───────────────────────
        # Each role has a list of hue-bucket buttons the user can toggle
        # Hue buckets: red orange yellow green cyan blue purple pink white grey black
        HUE_LABELS = ["red","orange","yellow","green","cyan","blue","purple","pink","white","grey","black"]
        HUE_RANGES = {          # hue in [0,360), s/v in [0,1]
            "red":    (lambda h,s,v: (h<20 or h>=340) and s>0.35 and v>0.15),
            "orange": (lambda h,s,v: 20<=h<45          and s>0.35 and v>0.15),
            "yellow": (lambda h,s,v: 45<=h<70          and s>0.35 and v>0.3),
            "green":  (lambda h,s,v: 70<=h<165         and s>0.25 and v>0.1),
            "cyan":   (lambda h,s,v: 165<=h<200        and s>0.25 and v>0.2),
            "blue":   (lambda h,s,v: 200<=h<265        and s>0.25 and v>0.1),
            "purple": (lambda h,s,v: 265<=h<310        and s>0.25 and v>0.1),
            "pink":   (lambda h,s,v: 310<=h<340        and s>0.25 and v>0.3),
            "white":  (lambda h,s,v: s<0.12 and v>0.85),
            "grey":   (lambda h,s,v: s<0.18 and 0.2<v<=0.85),
            "black":  (lambda h,s,v: v<=0.2),
        }
        ROLE_LABELS = ["bg","card","text","start","stop","sync"]

        import colorsys
        def hex_to_hsv(hx):
            hx = hx.lstrip("#")
            if len(hx)==3: hx = "".join(c*2 for c in hx)
            r,g,b = int(hx[0:2],16)/255, int(hx[2:4],16)/255, int(hx[4:6],16)/255
            h,s,v = colorsys.rgb_to_hsv(r,g,b)
            return h*360, s, v

        # Pre-compute HSV for every theme colour role once
        _hsv_cache = {}
        for _tn, _td in THEMES.items():
            for _role in ROLE_LABELS:
                _hx = _td.get(_role, "#000000")
                try: _hsv_cache[(_tn,_role)] = hex_to_hsv(_hx)
                except: _hsv_cache[(_tn,_role)] = (0,0,0)

        def colour_matches_bucket(theme_name, role, bucket):
            h,s,v = _hsv_cache.get((theme_name,role),(0,0,0))
            return HUE_RANGES[bucket](h,s,v)

        # Debounce timer
        _rebuild_timer = [None]

        # filters[role] = set of active hue buckets (empty = any)
        filters = {r: set() for r in ROLE_LABELS}
        mode_filter = tk.StringVar(value="any")   # "any" | "dark" | "light"
        text_filter = tk.StringVar(value="")

        # ── header ────────────────────────────────────────
        hdr = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Theme Search",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(hdr, text=f"64 themes",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")

        # mode toggle
        mr = ctk.CTkFrame(hdr, fg_color="transparent"); mr.pack(side="right", padx=12, pady=8)
        ctk.CTkLabel(mr, text="Mode:", font=ctk.CTkFont(size=11),
                     text_color=T["muted"]).pack(side="left", padx=(0,6))
        for mv, ml in [("any","Any"),("dark","Dark"),("light","Light")]:
            ctk.CTkRadioButton(mr, text=ml, variable=mode_filter, value=mv,
                               font=ctk.CTkFont(size=11), text_color=T["text"],
                               fg_color=T["sync"], border_color=T["border"],
                               command=lambda: win.after(0, _rebuild_grid)
                               ).pack(side="left", padx=(0,8))

        # search box
        sr = ctk.CTkFrame(win, fg_color=T["bg"]); sr.pack(fill="x", padx=14, pady=(8,0))
        ctk.CTkLabel(sr, text="🔍  Name:", font=ctk.CTkFont(size=11),
                     text_color=T["muted"]).pack(side="left")
        se = ctk.CTkEntry(sr, textvariable=text_filter, height=28,
                          font=ctk.CTkFont(size=12), fg_color=T["card"],
                          border_color=T["border"], text_color=T["text"],
                          placeholder_text="type to filter…")
        se.pack(side="left", fill="x", expand=True, padx=(6,10))
        def _debounced_rebuild(*_):
            if _rebuild_timer[0]: win.after_cancel(_rebuild_timer[0])
            _rebuild_timer[0] = win.after(120, _rebuild_grid)
        text_filter.trace_add("write", _debounced_rebuild)

        # colour filter rows — collapsed by default, shown when user clicks "Colour Filters"
        cf_visible = [False]
        cf_toggle_btn = ctk.CTkButton(win, text="▶  Colour Filters", height=26, width=150,
                                      font=ctk.CTkFont(size=11), corner_radius=6,
                                      fg_color="transparent", border_width=1,
                                      border_color=T["border"], text_color=T["muted"],
                                      hover_color=T["border"])
        cf_toggle_btn.pack(anchor="w", padx=14, pady=(4,0))

        cf = ctk.CTkFrame(win, fg_color=T["bg"])
        # NOT packed yet — shown on demand

        def _toggle_cf():
            cf_visible[0] = not cf_visible[0]
            if cf_visible[0]:
                cf.pack(fill="x", padx=14, pady=(2,0))
                cf_toggle_btn.configure(text="▼  Colour Filters")
            else:
                cf.pack_forget()
                cf_toggle_btn.configure(text="▶  Colour Filters")
        cf_toggle_btn.configure(command=_toggle_cf)

        # Also open colour filters when search entry is focused
        se.bind("<FocusIn>", lambda e: (_toggle_cf() if not cf_visible[0] else None))

        # hue swatch colours for buttons
        HUE_SWATCHES = {
            "red":"#ef4444","orange":"#f97316","yellow":"#eab308","green":"#22c55e",
            "cyan":"#06b6d4","blue":"#3b82f6","purple":"#8b5cf6","pink":"#ec4899",
            "white":"#f5f5f5","grey":"#888888","black":"#222222",
        }
        hue_btn_refs = {}  # (role, hue) -> button widget

        def _toggle_hue(role, hue):
            if hue in filters[role]: filters[role].discard(hue)
            else: filters[role].add(hue)
            _update_hue_btn(role, hue)
            _rebuild_grid()

        def _update_hue_btn(role, hue):
            btn = hue_btn_refs.get((role, hue))
            if not btn: return
            active = hue in filters[role]
            btn.configure(
                fg_color=HUE_SWATCHES[hue] if active else T["bg"],
                border_color=HUE_SWATCHES[hue],
                text_color="#000000" if active else T["muted"],
            )

        for ri, role in enumerate(ROLE_LABELS):
            rr = ctk.CTkFrame(cf, fg_color="transparent"); rr.pack(fill="x", pady=1)
            ctk.CTkLabel(rr, text=role.capitalize()+":", font=ctk.CTkFont(size=10),
                         text_color=T["muted"], width=44, anchor="e").pack(side="left", padx=(0,4))
            for hue in HUE_LABELS:
                b = ctk.CTkButton(rr, text=hue, width=52, height=20,
                                  font=ctk.CTkFont(size=9), corner_radius=4,
                                  fg_color=T["bg"], border_width=2,
                                  border_color=HUE_SWATCHES[hue],
                                  text_color=T["muted"], hover_color=T["border"],
                                  command=lambda r=role, h=hue: _toggle_hue(r, h))
                b.pack(side="left", padx=2)
                hue_btn_refs[(role, hue)] = b

        def _clear_filters():
            for r in ROLE_LABELS: filters[r].clear()
            mode_filter.set("any"); text_filter.set("")
            for (r,h),btn in hue_btn_refs.items(): _update_hue_btn(r,h)
            _rebuild_grid()

        clr_btn_row = ctk.CTkFrame(win, fg_color="transparent"); clr_btn_row.pack(fill="x", padx=14, pady=(4,0))
        ctk.CTkButton(clr_btn_row, text="Clear filters", height=22, width=90,
                      font=ctk.CTkFont(size=10), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=_clear_filters).pack(side="left")
        result_lbl = ctk.CTkLabel(clr_btn_row, text="", font=ctk.CTkFont(size=10),
                                   text_color=T["muted"])
        result_lbl.pack(side="left", padx=10)

        ctk.CTkFrame(win, height=1, fg_color=T["border"]).pack(fill="x", padx=14, pady=(6,0))

        # ── scrollable grid ───────────────────────────────
        grid_outer = ctk.CTkScrollableFrame(win, fg_color="transparent")
        grid_outer.pack(fill="both", expand=True, padx=10, pady=6)

        _card_widgets = []

        def _theme_matches(name, tdata):
            # mode
            m = mode_filter.get()
            if m != "any" and tdata["appearance"] != m: return False
            # text search
            q = text_filter.get().strip().lower()
            if q and q not in name.lower(): return False
            # colour filters
            for role in ROLE_LABELS:
                if not filters[role]: continue  # no filter on this role = any
                if not any(colour_matches_bucket(name, role, h) for h in filters[role]):
                    return False
            return True

        def _pick(name):
            apply_theme(name)
            try: win.destroy()
            except: pass

        def _rebuild_grid():
            for w in _card_widgets: 
                try: w.destroy()
                except: pass
            _card_widgets.clear()

            matching = [(n,t) for n,t in THEMES.items() if _theme_matches(n,t)]
            result_lbl.configure(text=f"{len(matching)} / {len(THEMES)} themes")

            COLS = 3
            for i, (name, tdata) in enumerate(matching):
                col = i % COLS
                row = i // COLS

                card = ctk.CTkFrame(grid_outer,
                                    fg_color=tdata["card"],
                                    border_color=tdata["border"],
                                    border_width=2, corner_radius=10)
                card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")
                grid_outer.columnconfigure(col, weight=1)
                _card_widgets.append(card)

                # colour swatches row
                sw_row = ctk.CTkFrame(card, fg_color="transparent"); sw_row.pack(fill="x", padx=8, pady=(8,2))
                for role in ["bg","card","border","start","stop","sync"]:
                    swatch = ctk.CTkFrame(sw_row, width=16, height=16, corner_radius=3,
                                          fg_color=tdata.get(role,"#888888"))
                    swatch.pack(side="left", padx=2)
                    swatch.pack_propagate(False)

                # dark/light badge
                badge_col = "#334155" if tdata["appearance"]=="dark" else "#e2e8f0"
                badge_tc  = "#e2e8f0" if tdata["appearance"]=="dark" else "#334155"
                badge = ctk.CTkLabel(sw_row, text="🌙" if tdata["appearance"]=="dark" else "☀",
                                     font=ctk.CTkFont(size=11),
                                     fg_color=badge_col, text_color=badge_tc,
                                     corner_radius=4, width=22, height=18)
                badge.pack(side="right", padx=(0,2))

                # name + select button
                nl = ctk.CTkLabel(card, text=name,
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color=tdata["text"],
                                  wraplength=180, justify="left")
                nl.pack(anchor="w", padx=10, pady=(2,0))

                # mini preview bar
                prev = ctk.CTkFrame(card, height=8, fg_color=tdata["bg"],
                                    corner_radius=0)
                prev.pack(fill="x", pady=(3,0))

                is_current = (name == current_theme_name)
                btn = ctk.CTkButton(card,
                                    text="✓ Active" if is_current else "Apply",
                                    height=26, corner_radius=6,
                                    font=ctk.CTkFont(size=11),
                                    fg_color=tdata["start"] if is_current else tdata["sync"],
                                    hover_color=tdata["start"],
                                    text_color="#000000",
                                    command=lambda n=name: _pick(n))
                btn.pack(fill="x", padx=8, pady=(4,8))

        _rebuild_grid()

    theme_btn = ctk.CTkButton(top, text=f"🎨  {current_theme_name}", width=180, height=28,
                               font=ctk.CTkFont(size=11), corner_radius=6,
                               fg_color=T["bg"], border_width=1, border_color=T["border"],
                               text_color=T["text"], hover_color=T["border"],
                               command=open_theme_picker)
    theme_btn.pack(side="left", padx=(0,6), pady=8)

    # keep theme button label in sync when theme changes via settings
    _orig_apply = apply_theme
    def _apply_and_sync(name):
        _orig_apply(name)
        try: theme_btn.configure(text=f"🎨  {name}")
        except: pass
    # monkey-patch the local reference the Settings option-menu will call
    globals()["apply_theme"] = _apply_and_sync

    # ⚙ Settings button — opens floating window
    def open_settings_window():
        win = ctk.CTkToplevel(app)
        win.title("Settings — MC CTRL")
        win.geometry("700x700")
        win.resizable(True, True)
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        try:
            ax = app.winfo_x() + (app.winfo_width()  - 700) // 2
            ay = app.winfo_y() + (app.winfo_height() - 700) // 2
            win.geometry(f"700x700+{ax}+{ay}")
        except: pass
        build_settings_tab(win)

    ctk.CTkButton(top, text="⚙  Settings", width=100, height=28,
                  font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=open_settings_window).pack(side="left", padx=(0,8), pady=8)

    status_dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=13), text_color=T["stop"])
    status_dot.pack(side="right", padx=(0,14), pady=10)
    status_lbl = ctk.CTkLabel(top, text="Stopped", font=ctk.CTkFont(size=12), text_color=T["muted"])
    status_lbl.pack(side="right", padx=(0,4), pady=10)

    # ── Tab bar ───────────────────────────────────────────
    tab_bar = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0,
                           border_color=T["border"], border_width=1)
    tab_bar.pack(fill="x")

    tab_content = ctk.CTkFrame(app, fg_color="transparent")
    tab_content.pack(fill="both", expand=True)

    dashboard_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")
    network_frame    = ctk.CTkFrame(tab_content, fg_color="transparent")
    serverinfo_frame = ctk.CTkFrame(tab_content, fg_color="transparent")
    playit_frame     = ctk.CTkFrame(tab_content, fg_color="transparent")

    tab_btns = {}

    multictrl_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")

    all_frames = {
        "dashboard":  dashboard_frame,
        "network":    network_frame,
        "serverinfo": serverinfo_frame,
        "playit":     playit_frame,
        "multictrl":  multictrl_frame,
    }
    _built_tabs = set()   # lazy: only build when first visited

    def show_tab(name):
        for f in all_frames.values():
            f.pack_forget()
        for n, b in tab_btns.items():
            b.configure(fg_color="transparent", text_color=T["muted"])
        # Lazy build on first visit
        if name not in _built_tabs:
            _built_tabs.add(name)
            builders = {
                "dashboard":  lambda: build_dashboard(dashboard_frame, is_fs),
                "network":    lambda: build_network_tab(network_frame),
                "serverinfo": lambda: build_server_info_tab(serverinfo_frame),
                "playit":     lambda: build_playit_tab(playit_frame),
                "multictrl":  lambda: build_multictrl_tab(multictrl_frame),
            }
            if name in builders:
                builders[name]()
        all_frames[name].pack(fill="both", expand=True)
        tab_btns[name].configure(fg_color=T["sync"], text_color="#000")

    TAB_DEFS = [
        ("dashboard",  "Dashboard"),
        ("playit",     "playit.gg"),
        ("serverinfo", "Server Info"),
        ("network",    "Network & IPs"),
        ("multictrl",  "⊞ MULTI CTRL"),
    ]
    for key, label in TAB_DEFS:
        is_multi = key == "multictrl"
        b = ctk.CTkButton(tab_bar, text=label,
                          width=130 if is_multi else 120, height=30,
                          font=ctk.CTkFont(size=12, weight="bold" if is_multi else "normal"),
                          corner_radius=6,
                          fg_color=T["handoff"] if is_multi else "transparent",
                          text_color="#000" if is_multi else T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=(8 if key=="dashboard" else 2, 2), pady=6)
        tab_btns[key] = b

    show_tab("dashboard")   # only dashboard is built at startup

# ── Dashboard ─────────────────────────────────────────────
def build_dashboard(parent, is_fs):
    global btn_start, btn_stop, btn_sync
    global log_box, chat_box, cmd_entry, chat_toggle_btn

    if not is_fs:
        scroll = make_scroll_frame(parent, fg_color="transparent")
        container = scroll
    else:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True)

    body = ctk.CTkFrame(container, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=12)
    ctrl_col = 1 if log_left else 0
    log_col  = 0 if log_left else 1
    body.columnconfigure(ctrl_col, weight=0, minsize=340)
    body.columnconfigure(log_col, weight=1)
    body.rowconfigure(0, weight=1)

    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=ctrl_col, sticky="nsew",
              padx=(10,0) if log_left else (0,10))

    def make_btn(parent, text, desc, color, cmd):
        f = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        top_r = ctk.CTkFrame(inner, fg_color="transparent"); top_r.pack(fill="x")
        ctk.CTkLabel(top_r, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=color, anchor="w").pack(side="left")
        b = ctk.CTkButton(top_r, text="Run", width=64, height=26,
                          font=ctk.CTkFont(size=11), fg_color=color,
                          hover_color=color, text_color="#000", command=cmd)
        b.pack(side="right")
        ctk.CTkLabel(inner, text=desc, font=ctk.CTkFont(size=10),
                     text_color=T["muted"], anchor="w",
                     wraplength=280, justify="left").pack(anchor="w", pady=(2,0))
        return b

    btn_start = make_btn(left, "Start Server",  "Git pull then launch with Aikar JVM flags", T["start"], lambda: threading.Thread(target=start_server, daemon=True).start())
    btn_stop  = make_btn(left, "Stop Server",   "Kill Java process then push world to GitHub", T["stop"],  lambda: threading.Thread(target=stop_server,  daemon=True).start())
    btn_sync  = make_btn(left, "Sync & Upload", "Git add all, commit Manual Sync, push",      T["sync"],  lambda: threading.Thread(target=sync_git,     daemon=True).start())

    # Quick Commands
    qf = ctk.CTkFrame(left, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    qf.pack(fill="x", pady=(8,3))
    ctk.CTkLabel(qf, text="QUICK COMMANDS",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,4))
    ctk.CTkFrame(qf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    qgrid = ctk.CTkFrame(qf, fg_color="transparent")
    qgrid.pack(fill="x", padx=10, pady=8)

    QUICK_CMDS = [
        ("Save World",    "save-all",           T["sync"]),
        ("Player List",   "list",                T["sync"]),
        ("Check TPS",     "tps",                 T["sync"]),
        ("Set Day",       "time set day",        T["handoff"]),
        ("Set Night",     "time set night",      T["handoff"]),
        ("Clear Weather", "weather clear",       T["handoff"]),
        ("Hard Mode",     "difficulty hard",     T["stop"]),
        ("Peaceful",      "difficulty peaceful", T["start"]),
        ("Safe Stop",     "stop",                T["stop"]),
        ("Reload",        "reload",              T["muted"]),
    ]
    cols = 2
    for i, (label, cmd_txt, color) in enumerate(QUICK_CMDS):
        ri = i // cols; ci = i % cols
        ctk.CTkButton(qgrid, text=label, width=140, height=26,
                      font=ctk.CTkFont(size=10), corner_radius=6,
                      fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=color,
                      hover_color=T["border"],
                      command=lambda c=cmd_txt: send_server_cmd(c)
                      ).grid(row=ri, column=ci, padx=3, pady=2, sticky="ew")
        qgrid.columnconfigure(ci, weight=1)

    # Right log panel
    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=log_col, sticky="nsew")
    right.rowconfigure(0, weight=1); right.rowconfigure(1, weight=0); right.rowconfigure(2, weight=0)
    right.columnconfigure(0, weight=1)

    lf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    lf.grid(row=0, column=0, sticky="nsew", pady=(0,6))
    lt = ctk.CTkFrame(lf, fg_color="transparent"); lt.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left")
    ctk.CTkButton(lt, text="Swap", width=40, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=swap_layout).pack(side="right", padx=(4,0))
    ctk.CTkButton(lt, text="Copy", width=44, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=copy_log_to_clipboard).pack(side="right", padx=(0,4))
    ctk.CTkButton(lt, text="Clear", width=44, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: (log_box.configure(state="normal"),
                                   log_box.delete("1.0","end"),
                                   log_box.configure(state="disabled"))
                  ).pack(side="right")

    log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),
                             wrap="word", state="disabled",
                             fg_color="transparent", text_color=T["text"])
    log_box.pack(fill="both", expand=True, padx=8, pady=(4,8))
    if log_history.strip():
        log_box.configure(state="normal"); log_box.insert("1.0", log_history)
        log_box.configure(state="disabled"); log_box.see("end")

    cf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    cf.grid(row=1, column=0, sticky="ew", pady=(0,6))
    ct = ctk.CTkFrame(cf, fg_color="transparent"); ct.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(ct, text="SERVER CHAT & EVENTS", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left")
    chat_toggle_btn = ctk.CTkButton(ct, text="Hide" if show_chat else "Show",
                                    width=44, height=20, font=ctk.CTkFont(size=10),
                                    fg_color="transparent", border_width=1,
                                    border_color=T["border"], text_color=T["muted"],
                                    hover_color=T["border"], command=toggle_chat)
    chat_toggle_btn.pack(side="right")
    ctk.CTkButton(ct, text="Clear", width=44, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: (chat_box.configure(state="normal"),
                                   chat_box.delete("1.0","end"),
                                   chat_box.configure(state="disabled"))
                  ).pack(side="right", padx=(0,4))
    chat_box = ctk.CTkTextbox(cf, font=ctk.CTkFont(size=11, family="Consolas"),
                              wrap="word", state="disabled", fg_color="transparent",
                              text_color=T["text"], height=110 if show_chat else 0)
    if show_chat: chat_box.pack(fill="x", padx=8, pady=(4,8))
    if chat_history.strip():
        chat_box.configure(state="normal"); chat_box.insert("1.0", chat_history)
        chat_box.configure(state="disabled"); chat_box.see("end")

    cmdf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=10)
    cmdf.grid(row=2, column=0, sticky="ew")
    ci = ctk.CTkFrame(cmdf, fg_color="transparent"); ci.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(ci, text="/", font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=T["muted"], width=14).pack(side="left")
    cmd_entry = ctk.CTkEntry(ci, font=ctk.CTkFont(size=12, family="Consolas"),
                             fg_color=T["bg"], border_color=T["border"],
                             text_color=T["text"],
                             placeholder_text="command or chat message...", height=32)
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(4,8))
    cmd_entry.bind("<Return>", lambda e: send_command())
    ctk.CTkButton(ci, text="Send", width=60, height=32,
                  font=ctk.CTkFont(size=12), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=send_command).pack(side="left")

    if show_perf: build_perf_panel(container)

# ── Perf panel ────────────────────────────────────────────
def build_perf_panel(parent):
    global perf_labels
    perf_labels = {}
    pf = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    pf.pack(fill="x", padx=20, pady=(0,10))
    ph = ctk.CTkFrame(pf, fg_color="transparent"); ph.pack(fill="x", padx=12, pady=(8,4))
    ctk.CTkLabel(ph, text="SERVER PERFORMANCE", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left")
    ctk.CTkLabel(ph, text="refresh 2s", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="right")
    grid = ctk.CTkFrame(pf, fg_color="transparent")
    grid.pack(fill="x", padx=12, pady=(0,10))
    stats = [("TPS","tps"),("Players","players"),("Latency","latency"),
             ("Uptime","uptime"),("RAM Total","ram_used"),("RAM %","ram_pct"),
             ("RAM Server","ram_srv"),("CPU Sys","cpu_sys"),("CPU Srv","cpu_srv"),("Threads","threads")]
    for i, (label, key) in enumerate(stats):
        col = i % 5; row = i // 5
        cell = ctk.CTkFrame(grid, fg_color=T["bg"], border_color=T["border"],
                            border_width=1, corner_radius=8)
        cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        grid.columnconfigure(col, weight=1)
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=9),
                     text_color=T["muted"]).pack(pady=(6,0))
        lbl = ctk.CTkLabel(cell, text=perf[key],
                           font=ctk.CTkFont(size=13, weight="bold"), text_color=T["text"])
        lbl.pack(pady=(0,6))
        perf_labels[key] = lbl

# ── Network tab ───────────────────────────────────────────
def build_network_tab(parent):
    import socket, urllib.request

    scroll = make_scroll_frame(parent, fg_color="transparent")

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
        except: return "127.0.0.1"

    local_ip = get_local_ip()
    port_val = load_settings().get("server_port", "25565")
    port_var = ctk.StringVar(value=port_val)
    ext_ip_var = ctk.StringVar(value="Fetching...")

    def save_port(*_): update_setting("server_port", port_var.get())
    port_var.trace_add("write", save_port)

    # Header
    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    hf.pack(fill="x", padx=20, pady=(12,0))
    hi = ctk.CTkFrame(hf, fg_color="transparent"); hi.pack(fill="x", padx=16, pady=14)
    ctk.CTkLabel(hi, text="SERVER CONNECTION INFO",
                 font=ctk.CTkFont(size=14, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkLabel(hi, text="Share these IPs with players to connect",
                 font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left", padx=12)

    def copy_to_clip(val):
        app.clipboard_clear(); app.clipboard_append(val)
        show_toast(f"Copied: {val}", T["sync"])

    def ip_card(parent, row, col, title, subtitle, get_val_fn, highlight_color, extra_widget_fn=None):
        c = ctk.CTkFrame(parent, fg_color=T["card"], border_color=highlight_color,
                         border_width=2, corner_radius=12)
        c.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=highlight_color).pack(anchor="w", padx=14, pady=(12,2))
        ctk.CTkLabel(c, text=subtitle, font=ctk.CTkFont(size=9),
                     text_color=T["muted"]).pack(anchor="w", padx=14)
        ctk.CTkFrame(c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
        if extra_widget_fn:
            extra_widget_fn(c)
        else:
            val_lbl = ctk.CTkLabel(c, text=get_val_fn(),
                                   font=ctk.CTkFont(size=13, weight="bold", family="Consolas"),
                                   text_color=T["text"])
            val_lbl.pack(padx=14, pady=(2,6))
        ctk.CTkButton(c, text="Copy IP",
                      font=ctk.CTkFont(size=11), height=30, corner_radius=6,
                      fg_color=highlight_color, hover_color=highlight_color, text_color="#000",
                      command=lambda: copy_to_clip(get_val_fn())
                      ).pack(padx=14, pady=(0,12), fill="x")
        return c

    grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    grid_frame.pack(fill="x", padx=20, pady=10)
    grid_frame.columnconfigure((0,1,2), weight=1)

    # Port editor
    def port_widget(p):
        pf = ctk.CTkFrame(p, fg_color="transparent"); pf.pack(fill="x", padx=14, pady=(2,6))
        e = ctk.CTkEntry(pf, textvariable=port_var, height=32,
                         font=ctk.CTkFont(size=13, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
        e.pack(fill="x")

    port_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["border"],
                          border_width=2, corner_radius=12)
    port_c.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(port_c, text="PORT", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkLabel(port_c, text="Edit to change port", font=ctk.CTkFont(size=9),
                 text_color=T["muted"]).pack(anchor="w", padx=14)
    ctk.CTkFrame(port_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    port_widget(port_c)

    # Local / LAN IP
    def get_local(): return f"{local_ip}:{port_var.get()}"
    local_c = ip_card(grid_frame, 0, 1, "LOCAL (LAN)",
                      "For players on your WiFi/network",
                      get_local, T["start"])
    # live-update LAN label when port changes
    try:
        llan = [w for w in local_c.winfo_children()
                if isinstance(w, ctk.CTkLabel) and ":" in w.cget("text")]
        if llan:
            def _upd_lan(*_): llan[0].configure(text=get_local())
            port_var.trace_add("write", _upd_lan)
    except: pass

    # External IP
    ext_disp = ctk.CTkLabel(grid_frame, text="", fg_color="transparent")  # placeholder

    def get_ext():
        v = ext_ip_var.get()
        return v if "fetching" not in v.lower() else "unavailable"

    ext_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["sync"],
                         border_width=2, corner_radius=12)
    ext_c.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(ext_c, text="EXTERNAL (INTERNET)",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=T["sync"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkLabel(ext_c, text="For players outside your network",
                 font=ctk.CTkFont(size=9), text_color=T["muted"]).pack(anchor="w", padx=14)
    ctk.CTkFrame(ext_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    ext_val_lbl = ctk.CTkLabel(ext_c, textvariable=ext_ip_var,
                               font=ctk.CTkFont(size=13, weight="bold", family="Consolas"),
                               text_color=T["sync"])
    ext_val_lbl.pack(padx=14, pady=(2,6))
    ctk.CTkButton(ext_c, text="Copy IP",
                  font=ctk.CTkFont(size=11), height=30, corner_radius=6,
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=lambda: copy_to_clip(ext_ip_var.get())).pack(padx=14, pady=(0,12), fill="x")

    # Row 2: localhost + custom domain
    grid_frame.columnconfigure((0,1,2), weight=1)

    def get_localhost(): return f"localhost:{port_var.get()}"
    ip_card(grid_frame, 1, 0, "LOCALHOST",
            "For testing on this PC",
            get_localhost, T["handoff"])

    # Custom domain card
    custom_var = ctk.StringVar(value=load_settings().get("custom_ip",""))
    cust_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["border"],
                          border_width=2, corner_radius=12)
    cust_c.grid(row=1, column=1, padx=6, pady=6, sticky="nsew", columnspan=2)
    ctk.CTkLabel(cust_c, text="CUSTOM DOMAIN / PROXY",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkLabel(cust_c, text="e.g. play.yourserver.net  —  set if you have a domain or proxy",
                 font=ctk.CTkFont(size=9), text_color=T["muted"]).pack(anchor="w", padx=14)
    ctk.CTkFrame(cust_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    cust_row = ctk.CTkFrame(cust_c, fg_color="transparent"); cust_row.pack(fill="x", padx=14, pady=(0,6))
    cust_entry = ctk.CTkEntry(cust_row, textvariable=custom_var, height=30,
                              font=ctk.CTkFont(size=12, family="Consolas"),
                              fg_color=T["bg"], border_color=T["border"],
                              text_color=T["text"], placeholder_text="play.example.net")
    cust_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
    def set_custom():
        v = custom_var.get().strip()
        if v:
            full = f"{v}:{port_var.get()}"
            ext_ip_var.set(full); update_setting("custom_ip", v)
            show_toast(f"Custom domain set to {v}", T["sync"])
    ctk.CTkButton(cust_row, text="Set", width=60, height=30,
                  font=ctk.CTkFont(size=11), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=set_custom).pack(side="left")
    ctk.CTkButton(cust_c, text="Copy Custom Domain",
                  font=ctk.CTkFont(size=11), height=30, corner_radius=6,
                  fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"],
                  hover_color=T["border"],
                  command=lambda: copy_to_clip(f"{custom_var.get()}:{port_var.get()}")
                  ).pack(padx=14, pady=(0,12))

    # Connection guide
    guide = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
    guide.pack(fill="x", padx=20, pady=(0,12))
    ctk.CTkLabel(guide, text="CONNECTION GUIDE",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10,6))
    ctk.CTkFrame(guide, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    ctk.CTkLabel(guide, text=(
        "1. Same house / WiFi  →  share the LOCAL (LAN) address.\n"
        "2. Friends over the internet  →  share the EXTERNAL address. Your router must port-forward port 25565 (TCP) to this PC.\n"
        "3. If you have a domain or reverse-proxy  →  set the CUSTOM DOMAIN above and share that instead.\n"
        "4. Just testing yourself  →  use localhost:25565 or 127.0.0.1:25565."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       justify="left", wraplength=900).pack(anchor="w", padx=14, pady=(8,12))

    # ── Quick World Switcher (in Network tab) ─────────────
    wqf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                       border_width=1, corner_radius=10)
    wqf.pack(fill="x", padx=20, pady=(0,12))
    wqh = ctk.CTkFrame(wqf, fg_color="transparent"); wqh.pack(fill="x", padx=14, pady=(10,4))
    ctk.CTkLabel(wqh, text="ACTIVE SERVER",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")
    ctk.CTkFrame(wqf, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    wqb = ctk.CTkFrame(wqf, fg_color="transparent"); wqb.pack(fill="x", padx=14, pady=(6, 10))
    ctk.CTkLabel(wqb, text="Select which server folder to load when the server starts (updates level-name in server.properties).",
                 font=ctk.CTkFont(size=11), text_color=T["muted"], wraplength=820,
                 justify="left").pack(anchor="w", pady=(0, 6))

    wq_inner = ctk.CTkFrame(wqb, fg_color=T["bg"], border_color=T["border"],
                             border_width=1, corner_radius=8)
    wq_inner.pack(fill="x")

    def _net_get_worlds():
        path = load_settings().get("srv_path", SRV_PATH)
        try:
            folders = []
            for e in sorted(os.listdir(path)):
                full = os.path.join(path, e)
                if not os.path.isdir(full) or e.startswith("."):
                    continue
                # Only treat as a server instance if it has server.properties
                if os.path.exists(os.path.join(full, "server.properties")):
                    folders.append(e)
            return folders if folders else []
        except: return []

    def _net_read_active():
        path = load_settings().get("srv_path", SRV_PATH)
        try:
            with open(os.path.join(path, "server.properties"), encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("level-name") and "=" in line:
                        return line.split("=", 1)[1].strip()
        except: pass
        return "world"

    def _net_set_world(name):
        path = load_settings().get("srv_path", SRV_PATH)
        props = os.path.join(path, "server.properties")
        try:
            if os.path.exists(props):
                with open(props, encoding="utf-8", errors="ignore") as f: lines = f.readlines()
                new_lines = []; found = False
                for line in lines:
                    if line.strip().startswith("level-name") and "=" in line:
                        new_lines.append(f"level-name={name}\n"); found = True
                    else: new_lines.append(line)
                if not found: new_lines.append(f"level-name={name}\n")
                with open(props, "w", encoding="utf-8") as f: f.writelines(new_lines)
            show_toast(f"Active server → {name}", T["start"])
            _net_refresh_worlds()
        except Exception as ex: show_toast(f"Error: {ex}", T["stop"])

    def _net_refresh_worlds():
        for w in wq_inner.winfo_children(): w.destroy()
        worlds = _net_get_worlds()
        active = _net_read_active()
        # Header row with count
        row_top = ctk.CTkFrame(wq_inner, fg_color="transparent")
        row_top.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(row_top,
                     text=f"Found {len(worlds)} server instance{'s' if len(worlds)!=1 else ''} (subfolders with server.properties):",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")
        if not worlds or worlds == ["world"]:
            ctk.CTkLabel(wq_inner, text="No sub-servers found.\nEach must be a subfolder containing server.properties.",
                         font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(padx=10, pady=(0,8))
        for wname in worlds:
            wr = ctk.CTkFrame(wq_inner,
                              fg_color=T["card"] if wname==active else "transparent",
                              corner_radius=6)
            wr.pack(fill="x", padx=10, pady=2)
            is_active = (wname == active)
            dot = ctk.CTkLabel(wr, text="●" if is_active else "○", width=20,
                               font=ctk.CTkFont(size=14),
                               text_color=T["start"] if is_active else T["muted"])
            dot.pack(side="left", padx=(8,4), pady=6)
            ctk.CTkLabel(wr, text=wname,
                         font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                         text_color=T["start"] if is_active else T["text"]).pack(side="left")
            if is_active:
                ctk.CTkLabel(wr, text="  ← active", font=ctk.CTkFont(size=10),
                             text_color=T["start"]).pack(side="left")
            else:
                ctk.CTkButton(wr, text="Switch to This", width=110, height=26,
                              font=ctk.CTkFont(size=11), fg_color=T["sync"],
                              hover_color=T["border"], text_color="#000",
                              command=lambda n=wname: _net_set_world(n)).pack(side="right", padx=6, pady=4)
        # Manual / browse entry
        ctk.CTkFrame(wq_inner, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=(6, 0))
        man = ctk.CTkFrame(wq_inner, fg_color="transparent"); man.pack(fill="x", padx=10, pady=(6, 10))
        ctk.CTkLabel(man, text="Or type:", font=ctk.CTkFont(size=11),
                     text_color=T["muted"]).pack(side="left", padx=(0, 6))
        _mwv = ctk.StringVar()
        ctk.CTkEntry(man, textvariable=_mwv, width=150, height=28,
                     font=ctk.CTkFont(size=12, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                     placeholder_text="server_folder_name").pack(side="left", padx=(0, 6))
        ctk.CTkButton(man, text="Set", width=50, height=28,
                      font=ctk.CTkFont(size=11), fg_color=T["start"],
                      hover_color=T["start"], text_color="#000",
                      command=lambda: _mwv.get().strip() and _net_set_world(_mwv.get().strip())
                      ).pack(side="left", padx=(0, 6))
        def _browse_srv():
            import tkinter.filedialog as _fd
            p = load_settings().get("srv_path", SRV_PATH)
            chosen = _fd.askdirectory(title="Select server folder", initialdir=p)
            if chosen:
                folder = os.path.basename(chosen)
                _net_set_world(folder)
        ctk.CTkButton(man, text="Browse…", width=72, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=_browse_srv).pack(side="left")

    _net_refresh_worlds()
    ctk.CTkButton(wqh, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_net_refresh_worlds).pack(side="right")

    def fetch_ext():
        try:
            ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
            saved = load_settings().get("custom_ip","")
            app.after(0, lambda: ext_ip_var.set(
                f"{saved}:{port_var.get()}" if saved else f"{ip}:{port_var.get()}"))
        except: app.after(0, lambda: ext_ip_var.set("unavailable"))
    threading.Thread(target=fetch_ext, daemon=True).start()

# ── Server Info tab ───────────────────────────────────────
def build_server_info_tab(parent):
    scroll = make_scroll_frame(parent, fg_color="transparent")

    def section_card(title):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10,0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(6,12))
        return body, h

    # ── Online Players ────────────────────────────────────
    pb, ph = section_card("Online Players")
    players_frame = ctk.CTkFrame(pb, fg_color=T["bg"], border_color=T["border"],
                                 border_width=1, corner_radius=8)
    players_frame.pack(fill="x")

    def refresh_players_now():
        for w in players_frame.winfo_children(): w.destroy()
        names = list(online_players.keys())
        if not names:
            ctk.CTkLabel(players_frame, text="No players online.",
                         font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(padx=14, pady=10)
        else:
            for name in sorted(names):
                joined = online_players.get(name, "?")
                r = ctk.CTkFrame(players_frame, fg_color="transparent")
                r.pack(fill="x", padx=10, pady=3)
                ctk.CTkLabel(r, text="●", font=ctk.CTkFont(size=12),
                             text_color=T["start"]).pack(side="left", padx=(0,8))
                ctk.CTkLabel(r, text=name,
                             font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=T["text"]).pack(side="left")
                ctk.CTkLabel(r, text=f"joined {joined}",
                             font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left", padx=8)
                # Copy player name
                ctk.CTkButton(r, text="Copy Name", width=80, height=22,
                              font=ctk.CTkFont(size=10), fg_color="transparent",
                              border_width=1, border_color=T["border"],
                              text_color=T["muted"], hover_color=T["border"],
                              command=lambda n=name: (app.clipboard_clear(),
                                                       app.clipboard_append(n),
                                                       show_toast(f"Copied: {n}", T["sync"]))
                              ).pack(side="right", padx=(4,0))
                ctk.CTkButton(r, text="Kick", width=50, height=22,
                              font=ctk.CTkFont(size=10), fg_color="transparent",
                              border_width=1, border_color=T["stop"],
                              text_color=T["stop"], hover_color=T["border"],
                              command=lambda n=name: send_server_cmd(f"kick {n}")
                              ).pack(side="right")

    def _auto_refresh_players():
        global _players_refresh_id
        try: refresh_players_now()
        except: pass
        _players_refresh_id = app.after(2000, _auto_refresh_players)

    _auto_refresh_players()

    ctk.CTkButton(ph, text="Force Refresh", width=90, height=22,
                  font=ctk.CTkFont(size=10), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=lambda: (send_server_cmd("list"), refresh_players_now())
                  ).pack(side="right")

    # ── Active Server Selector ────────────────────────────────
    wb, wh = section_card("Active Server")
    ctk.CTkLabel(wb, text=(
        "Select which server folder loads when the server starts. "
        "This updates level-name in server.properties."
    ), font=ctk.CTkFont(size=11), text_color=T["muted"], wraplength=820,
       justify="left").pack(anchor="w", pady=(0, 6))

    world_sel_frame = ctk.CTkFrame(wb, fg_color=T["bg"], border_color=T["border"],
                                   border_width=1, corner_radius=8)
    world_sel_frame.pack(fill="x")

    _active_world_var = ctk.StringVar(value="world")

    def _get_world_folders():
        path = load_settings().get("srv_path", SRV_PATH)
        try:
            folders = []
            for entry in sorted(os.listdir(path)):
                full = os.path.join(path, entry)
                if not os.path.isdir(full) or entry.startswith("."):
                    continue
                # Only treat as a server instance if it has server.properties
                if os.path.exists(os.path.join(full, "server.properties")):
                    folders.append(entry)
            return folders if folders else []
        except:
            return []

    def _read_active_world():
        path = load_settings().get("srv_path", SRV_PATH)
        try:
            with open(os.path.join(path, "server.properties"), encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("level-name") and "=" in line:
                        return line.split("=", 1)[1].strip()
        except:
            pass
        return "world"

    def _set_active_world(name):
        path = load_settings().get("srv_path", SRV_PATH)
        props_path = os.path.join(path, "server.properties")
        try:
            if os.path.exists(props_path):
                with open(props_path, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                new_lines = []
                found = False
                for line in lines:
                    if line.strip().startswith("level-name") and "=" in line:
                        new_lines.append(f"level-name={name}\n")
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    new_lines.append(f"level-name={name}\n")
                with open(props_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            _active_world_var.set(name)
            show_toast(f"Active server set to: {name}", T["start"])
        except Exception as ex:
            show_toast(f"Error updating world: {ex}", T["stop"])

    def _refresh_world_list():
        for w in world_sel_frame.winfo_children():
            w.destroy()
        worlds = _get_world_folders()
        active = _read_active_world()
        _active_world_var.set(active)

        row_top = ctk.CTkFrame(world_sel_frame, fg_color="transparent")
        row_top.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(row_top,
                     text=f"Found {len(worlds)} server instance{'s' if len(worlds)!=1 else ''} (subfolders with server.properties):",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")

        if not worlds:
            ctk.CTkLabel(world_sel_frame, text="No sub-servers found. Each server must have its own subfolder\ncontaining server.properties.",
                         font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(padx=14, pady=(0,8))
        for wname in worlds:
            wr = ctk.CTkFrame(world_sel_frame,
                              fg_color=T["card"] if wname==active else "transparent",
                              corner_radius=6)
            wr.pack(fill="x", padx=10, pady=2)
            is_active = (wname == active)
            ctk.CTkLabel(wr, text="●" if is_active else "○", width=20,
                         font=ctk.CTkFont(size=14),
                         text_color=T["start"] if is_active else T["muted"]).pack(side="left", padx=(8,4), pady=6)
            ctk.CTkLabel(wr, text=wname,
                         font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                         text_color=T["start"] if is_active else T["text"]).pack(side="left")
            if is_active:
                ctk.CTkLabel(wr, text="  ← active", font=ctk.CTkFont(size=10),
                             text_color=T["start"]).pack(side="left")
            else:
                ctk.CTkButton(wr, text="Switch to This", width=110, height=26,
                              font=ctk.CTkFont(size=11),
                              fg_color=T["sync"], hover_color=T["border"], text_color="#000",
                              command=lambda n=wname: (_set_active_world(n), _refresh_world_list())
                              ).pack(side="right", padx=6, pady=4)

        # Manual / browse row
        ctk.CTkFrame(world_sel_frame, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=(6, 0))
        man_row = ctk.CTkFrame(world_sel_frame, fg_color="transparent")
        man_row.pack(fill="x", padx=10, pady=(6, 10))
        ctk.CTkLabel(man_row, text="Or type:",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left", padx=(0, 6))
        _manual_world_var = ctk.StringVar()
        ctk.CTkEntry(man_row, textvariable=_manual_world_var, width=150, height=28,
                     font=ctk.CTkFont(size=12, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                     placeholder_text="server_folder_name").pack(side="left", padx=(0, 6))
        ctk.CTkButton(man_row, text="Set", width=50, height=28,
                      font=ctk.CTkFont(size=11), fg_color=T["start"],
                      hover_color=T["start"], text_color="#000",
                      command=lambda: (
                          _manual_world_var.get().strip() and
                          _set_active_world(_manual_world_var.get().strip()) and
                          _refresh_world_list()
                      )).pack(side="left", padx=(0, 6))
        def _browse_srv_info():
            import tkinter.filedialog as _fd
            p = load_settings().get("srv_path", SRV_PATH)
            chosen = _fd.askdirectory(title="Select server folder", initialdir=p)
            if chosen:
                _set_active_world(os.path.basename(chosen))
                _refresh_world_list()
        ctk.CTkButton(man_row, text="Browse…", width=72, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=_browse_srv_info).pack(side="left")

    _refresh_world_list()
    ctk.CTkButton(wh, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_refresh_world_list).pack(side="right")

    # ── Plugins ───────────────────────────────────────────
    plb, plh = section_card("Plugins")
    plugins_frame = ctk.CTkFrame(plb, fg_color=T["bg"], border_color=T["border"],
                                 border_width=1, corner_radius=8)
    plugins_frame.pack(fill="x")

    def refresh_plugins():
        for w in plugins_frame.winfo_children(): w.destroy()
        path = load_settings().get("srv_path", SRV_PATH)
        try:
            jars = sorted([x for x in os.listdir(os.path.join(path, "plugins"))
                           if x.endswith(".jar")])
            if not jars:
                ctk.CTkLabel(plugins_frame, text="No plugins found.",
                             font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(padx=14, pady=10)
            else:
                grid = ctk.CTkFrame(plugins_frame, fg_color="transparent")
                grid.pack(fill="x", padx=8, pady=8)
                cols = 3
                for i, j in enumerate(jars):
                    c = ctk.CTkFrame(grid, fg_color=T["card"], border_color=T["border"],
                                     border_width=1, corner_radius=6)
                    c.grid(row=i//cols, column=i%cols, padx=3, pady=3, sticky="ew")
                    grid.columnconfigure(i%cols, weight=1)
                    ctk.CTkLabel(c, text=j.replace(".jar",""),
                                 font=ctk.CTkFont(size=11), text_color=T["text"]).pack(padx=8, pady=6)
        except Exception as ex:
            ctk.CTkLabel(plugins_frame, text=f"Error: {ex}",
                         font=ctk.CTkFont(size=11), text_color=T["stop"]).pack(padx=14, pady=10)

    refresh_plugins()
    ctk.CTkButton(plh, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=refresh_plugins).pack(side="right")

    # ── Resource Packs ────────────────────────────────────
    rpb, rph = section_card("Resource Packs")
    rp_list_frame = ctk.CTkFrame(rpb, fg_color=T["bg"], border_color=T["border"],
                                  border_width=1, corner_radius=8)
    rp_list_frame.pack(fill="x")

    def get_rp_dir():
        path = load_settings().get("srv_path", SRV_PATH)
        for d in ["resource-packs", "resourcepacks", "resources"]:
            dp = os.path.join(path, d)
            if os.path.isdir(dp): return dp
        # Default: resource-packs folder
        rp = os.path.join(path, "resource-packs")
        os.makedirs(rp, exist_ok=True)
        return rp

    def refresh_respacks():
        for w in rp_list_frame.winfo_children(): w.destroy()
        found = []
        path = load_settings().get("srv_path", SRV_PATH)
        for d in ["resource-packs","resourcepacks","resources"]:
            dp = os.path.join(path, d)
            if os.path.isdir(dp):
                for x in os.listdir(dp):
                    if x.endswith((".zip",".jar")): found.append((dp, x))
        if not found:
            drop_hint = " | Drag & drop .zip files here" if _DND_AVAILABLE else ""
            ctk.CTkLabel(rp_list_frame,
                         text=f"No resource packs found.{drop_hint}",
                         font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(padx=14, pady=10)
        else:
            for dp, rp in sorted(found, key=lambda x: x[1]):
                r = ctk.CTkFrame(rp_list_frame, fg_color="transparent")
                r.pack(fill="x", padx=10, pady=3)
                size_kb = os.path.getsize(os.path.join(dp, rp)) // 1024
                ctk.CTkLabel(r, text=rp, font=ctk.CTkFont(size=12), text_color=T["text"]).pack(side="left")
                ctk.CTkLabel(r, text=f"{size_kb} KB", font=ctk.CTkFont(size=10),
                             text_color=T["muted"]).pack(side="left", padx=8)
                ctk.CTkButton(r, text="Remove", width=60, height=22,
                              font=ctk.CTkFont(size=10), fg_color="transparent",
                              border_width=1, border_color=T["stop"],
                              text_color=T["stop"], hover_color=T["border"],
                              command=lambda p=dp, n=rp: _remove_rp(p, n, refresh_respacks)
                              ).pack(side="right")

        # Drop zone
        dz_color = T["border"]
        dz = ctk.CTkFrame(rp_list_frame, fg_color="transparent",
                          border_color=dz_color, border_width=2, corner_radius=8)
        dz.pack(fill="x", padx=10, pady=(6,10))
        dz_hint = "Drop .zip / .jar here  OR  click Browse to add a resource pack"
        if not _DND_AVAILABLE:
            dz_hint = "Click Browse to add a resource pack  (install tkinterdnd2 for drag-and-drop)"
        ctk.CTkLabel(dz, text=dz_hint, font=ctk.CTkFont(size=11),
                     text_color=T["muted"]).pack(pady=8)
        ctk.CTkButton(dz, text="Browse & Install", height=30,
                      font=ctk.CTkFont(size=11), fg_color=T["sync"],
                      hover_color=T["sync"], text_color="#000",
                      command=lambda: _browse_rp(get_rp_dir, refresh_respacks)
                      ).pack(pady=(0,10))

        # Enable drag-and-drop if tkinterdnd2 is available
        if _DND_AVAILABLE:
            try:
                dz.drop_target_register(dnd.DND_FILES)
                dz.dnd_bind("<<Drop>>", lambda e: _handle_rp_drop(e.data, get_rp_dir(), refresh_respacks))
            except: pass

    def _remove_rp(folder, name, refresh_fn):
        try:
            os.remove(os.path.join(folder, name))
            show_toast(f"Removed {name}", T["stop"])
            refresh_fn()
        except Exception as ex:
            show_toast(f"Error: {ex}", T["stop"])

    def _browse_rp(get_dir_fn, refresh_fn):
        import tkinter.filedialog as fd
        files = fd.askopenfilenames(
            title="Select Resource Pack(s)",
            filetypes=[("Resource Packs", "*.zip *.jar"), ("All files", "*.*")])
        if not files: return
        dest = get_dir_fn()
        for src in files:
            try:
                shutil.copy2(src, os.path.join(dest, os.path.basename(src)))
            except Exception as ex:
                log(f"Copy failed: {ex}")
        show_toast(f"Installed {len(files)} pack(s)", T["start"])
        refresh_fn()

    def _handle_rp_drop(data, dest_dir, refresh_fn):
        # tkinterdnd2 gives paths wrapped in braces or space-separated
        paths = re.findall(r'\{([^}]+)\}|(\S+)', data)
        paths = [p[0] or p[1] for p in paths]
        count = 0
        for src in paths:
            if src.endswith((".zip",".jar")):
                try:
                    shutil.copy2(src, os.path.join(dest_dir, os.path.basename(src)))
                    count += 1
                except Exception as ex:
                    log(f"Drop copy failed: {ex}")
        if count: show_toast(f"Installed {count} pack(s)", T["start"])
        refresh_fn()

    refresh_respacks()
    ctk.CTkButton(rph, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=refresh_respacks).pack(side="right")

    # ── Server Properties ─────────────────────────────────
    spb, sph = section_card("Server Properties")

    ALL_PROPS = [
        ("gamemode",             "Game Mode",              "survival"),
        ("difficulty",           "Difficulty",             "easy"),
        ("max-players",          "Max Players",            "20"),
        ("view-distance",        "View Distance",          "10"),
        ("simulation-distance",  "Simulation Distance",    "10"),
        ("server-port",          "Port",                   "25565"),
        ("online-mode",          "Online Mode",            "true"),
        ("pvp",                  "PvP",                    "true"),
        ("spawn-monsters",       "Spawn Monsters",         "true"),
        ("spawn-animals",        "Spawn Animals",          "true"),
        ("allow-flight",         "Allow Flight",           "false"),
        ("white-list",           "Whitelist",              "false"),
        ("enforce-whitelist",    "Enforce Whitelist",      "false"),
        ("level-name",           "World Name",             "world"),
        ("motd",                 "MOTD",                   "A Minecraft Server"),
        ("spawn-protection",     "Spawn Protection Radius","16"),
        ("level-seed",           "World Seed",             ""),
        ("max-world-size",       "Max World Size",         "29999984"),
        ("allow-nether",         "Allow Nether",           "true"),
        ("enable-command-block", "Command Blocks",         "false"),
        ("enable-rcon",          "Enable RCON",            "false"),
        ("rcon.password",        "RCON Password",          ""),
        ("rcon.port",            "RCON Port",              "25575"),
    ]

    props_vars = {}   # key -> StringVar

    def load_props():
        path = load_settings().get("srv_path", SRV_PATH)
        kv = {}
        try:
            with open(os.path.join(path, "server.properties"), "r",
                      encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("="); kv[k.strip()] = v.strip()
        except: pass
        return kv

    def save_props():
        path = load_settings().get("srv_path", SRV_PATH)
        prop_file = os.path.join(path, "server.properties")
        try:
            with open(prop_file, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
            updated = set()
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k, _, _ = stripped.partition("="); k = k.strip()
                    if k in props_vars:
                        new_lines.append(f"{k}={props_vars[k].get()}\n")
                        updated.add(k)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            # Add new keys not already in file
            for k in props_vars:
                if k not in updated:
                    new_lines.append(f"{k}={props_vars[k].get()}\n")
            with open(prop_file, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)
            show_toast("server.properties saved!", T["start"])
        except Exception as ex:
            show_toast(f"Save failed: {ex}", T["stop"])

    kv = load_props()
    pg = ctk.CTkScrollableFrame(spb, fg_color=T["bg"], border_color=T["border"],
                                 border_width=1, corner_radius=8, height=320)
    pg.pack(fill="x")
    pg.columnconfigure((0,1,2), weight=1)
    for i, (key, label, default) in enumerate(ALL_PROPS):
        val = kv.get(key, default)
        var = ctk.StringVar(value=val)
        props_vars[key] = var
        cell = ctk.CTkFrame(pg, fg_color="transparent")
        cell.grid(row=i//3, column=i%3, padx=4, pady=3, sticky="ew")
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=10),
                     text_color=T["muted"], anchor="w").pack(anchor="w")
        e = ctk.CTkEntry(cell, textvariable=var, height=28,
                         font=ctk.CTkFont(size=11, family="Consolas"),
                         fg_color=T["card"], border_color=T["border"],
                         text_color=T["text"])
        e.pack(fill="x")

    ctk.CTkButton(spb, text="Save server.properties", height=36, corner_radius=8,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=save_props).pack(pady=(8,0), fill="x")
    ctk.CTkLabel(spb, text="Server must be restarted for changes to take effect.",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(4,0))
    ctk.CTkButton(sph, text="Reload File", width=80, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: [var.set(load_props().get(k, d))
                                   for k, _, d in ALL_PROPS
                                   if (var := props_vars.get(k)) is not None]
                  ).pack(side="right")


    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

    # World Creation
    _build_world_creation_section(scroll)
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

# ── World Creation ─────────────────────────────────────────
def _build_world_creation_section(scroll):
    def _card(title):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10,0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(6,12))
        return body, h

    wcb, wch = _card("World Creation & Server Setup")
    ctk.CTkLabel(wcb, text=(
        "Pick server software — Paper/Purpur/Vanilla are auto-downloaded.\n"
        "Existing world folders are backed up with a timestamp before any changes."
    ), font=ctk.CTkFont(size=11), text_color=T["muted"], wraplength=780, justify="left"
    ).pack(anchor="w", pady=(0,8))

    r0 = ctk.CTkFrame(wcb, fg_color="transparent"); r0.pack(fill="x", pady=(0,6))
    ctk.CTkLabel(r0, text="Server Software", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=140, anchor="w").pack(side="left")
    software_var = ctk.StringVar(value="Paper")
    ctk.CTkOptionMenu(r0, values=["Paper","Purpur","Vanilla","Fabric (manual)"],
                      variable=software_var, font=ctk.CTkFont(size=12), width=200,
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"], dropdown_hover_color=T["border"]
                      ).pack(side="left", padx=(0,20))
    ctk.CTkLabel(r0, text="MC Version", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=90, anchor="w").pack(side="left")
    MC_VERSIONS = [
        "latest",
        "1.21.4", "1.21.3", "1.21.1", "1.21",
        "1.20.6", "1.20.4", "1.20.2", "1.20.1", "1.20",
        "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
        "1.18.2", "1.18.1", "1.18",
        "1.17.1", "1.17",
        "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
        "1.15.2", "1.15.1", "1.15",
        "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
        "1.13.2", "1.13.1", "1.13",
        "1.12.2", "1.12.1", "1.12",
        "1.8.9", "1.8",
    ]
    _s_mc = load_settings()
    mc_ver_var = ctk.StringVar(value=_s_mc.get("mc_version", "latest"))
    def _save_mc_ver(v): update_setting("mc_version", v)
    ctk.CTkOptionMenu(r0, values=MC_VERSIONS, variable=mc_ver_var,
                      command=_save_mc_ver,
                      font=ctk.CTkFont(size=12), width=140, height=30,
                      fg_color=T["bg"], button_color=T["border"],
                      button_hover_color=T["muted"], text_color=T["text"],
                      dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"]).pack(side="left")

    r1 = ctk.CTkFrame(wcb, fg_color="transparent"); r1.pack(fill="x", pady=(4,0))
    ctk.CTkLabel(r1, text="World Name", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=140, anchor="w").pack(side="left")
    world_name_var = ctk.StringVar(value="world")
    ctk.CTkEntry(r1, textvariable=world_name_var, width=160, height=30,
                 font=ctk.CTkFont(size=12, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]
                 ).pack(side="left", padx=(0,20))
    ctk.CTkLabel(r1, text="Seed (blank=random)", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=160, anchor="w").pack(side="left")
    seed_var = ctk.StringVar(value="")
    ctk.CTkEntry(r1, textvariable=seed_var, width=160, height=30,
                 font=ctk.CTkFont(size=12, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="e.g. 123456789").pack(side="left")

    r2 = ctk.CTkFrame(wcb, fg_color="transparent"); r2.pack(fill="x", pady=(6,0))
    ctk.CTkLabel(r2, text="Level Type", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=140, anchor="w").pack(side="left")
    level_type_var = ctk.StringVar(value="minecraft:normal")
    ctk.CTkOptionMenu(r2, values=["minecraft:normal","minecraft:flat","minecraft:large_biomes",
                                   "minecraft:amplified","minecraft:single_biome_surface"],
                      variable=level_type_var, font=ctk.CTkFont(size=12), width=210,
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"], dropdown_hover_color=T["border"]
                      ).pack(side="left", padx=(0,16))
    ctk.CTkLabel(r2, text="Game Mode", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=90, anchor="w").pack(side="left")
    gamemode_var = ctk.StringVar(value="survival")
    ctk.CTkOptionMenu(r2, values=["survival","creative","adventure","spectator"],
                      variable=gamemode_var, font=ctk.CTkFont(size=12), width=120,
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"], dropdown_hover_color=T["border"]
                      ).pack(side="left", padx=(0,16))
    ctk.CTkLabel(r2, text="Difficulty", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=70, anchor="w").pack(side="left")
    diff_var = ctk.StringVar(value="normal")
    ctk.CTkOptionMenu(r2, values=["peaceful","easy","normal","hard"],
                      variable=diff_var, font=ctk.CTkFont(size=12), width=110,
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"], dropdown_hover_color=T["border"]
                      ).pack(side="left")

    r3 = ctk.CTkFrame(wcb, fg_color="transparent"); r3.pack(fill="x", pady=(6,0))
    hardcore_var   = ctk.BooleanVar(value=False)
    structures_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(r3, text="Hardcore", variable=hardcore_var,
                    font=ctk.CTkFont(size=12), text_color=T["text"],
                    checkmark_color="#000", fg_color=T["stop"],
                    border_color=T["border"]).pack(side="left", padx=(0,20))
    ctk.CTkCheckBox(r3, text="Generate Structures", variable=structures_var,
                    font=ctk.CTkFont(size=12), text_color=T["text"],
                    checkmark_color="#000", fg_color=T["sync"],
                    border_color=T["border"]).pack(side="left")

    wc_status_lbl = ctk.CTkLabel(wcb, text="", font=ctk.CTkFont(size=11), text_color=T["muted"])
    wc_status_lbl.pack(anchor="w", pady=(8,0))
    wc_prog = ctk.CTkProgressBar(wcb, height=6); wc_prog.set(0)

    def _set_st(msg, color=None, prog=None):
        try:
            wc_status_lbl.configure(text=msg, text_color=color or T["muted"])
            if prog is not None:
                wc_prog.set(prog)
                if prog > 0: wc_prog.pack(fill="x", pady=(4,0))
                else: wc_prog.pack_forget()
        except: pass

    def _dl(url, dest, label):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"MC-CTRL/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                total = int(r.headers.get("Content-Length", 0))
                done = 0
                with open(dest, "wb") as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk: break
                        f.write(chunk); done += len(chunk)
                        if total:
                            p = done/total
                            app.after(0, lambda p=p,d=done,t=total: _set_st(
                                f"{label}... {d//1048576}/{t//1048576} MB", T["sync"], p))
            return True
        except Exception as ex:
            app.after(0, _set_st, f"Download failed: {ex}", T["stop"], 0)
            return False

    def _paper_url(ver):
        # PaperMC fill.papermc.io v3 API
        # GET /v3/projects/paper           → {"versions": ["1.21.1", ...], ...}
        # GET /v3/projects/paper/versions/{ver}/builds
        #   → {"builds": [{"channel":"STABLE","downloads":{"server:default":{"url":"..."}}},...]}
        base = "https://fill.papermc.io/v3/projects/paper"
        hdrs = {"User-Agent": "MC-CTRL/1.0 (github.com/GamerMahir07)"}
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(base, headers=hdrs), timeout=15) as r:
                data = json.loads(r.read())
            # v3 returns a flat "versions" list
            versions = data.get("versions", [])
            if not versions:
                return None, "No versions returned by PaperMC API"
            if ver == "latest":
                ver = versions[-1]
            elif ver not in versions:
                return None, f"Version {ver} not found. Available: {', '.join(versions[-5:])}"
            builds_url = f"{base}/versions/{ver}/builds"
            with urllib.request.urlopen(
                    urllib.request.Request(builds_url, headers=hdrs), timeout=15) as r2:
                bdata = json.loads(r2.read())
            # builds is nested under "builds" key in v3
            builds = bdata.get("builds", bdata) if isinstance(bdata, dict) else bdata
            if not builds:
                return None, f"No builds found for Paper {ver}"
            stable = [b for b in builds if b.get("channel","").upper() == "STABLE"]
            chosen = stable[-1] if stable else builds[-1]
            dl_url = chosen["downloads"]["server:default"]["url"]
            return dl_url, ver
        except Exception as ex:
            return None, str(ex)

    def _purpur_url(ver):
        # Purpur API: https://api.purpurmc.org/v2/purpur
        # → {"versions": [...]}  latest is last
        # Download: https://api.purpurmc.org/v2/purpur/{ver}/latest/download
        try:
            with urllib.request.urlopen(
                    urllib.request.Request("https://api.purpurmc.org/v2/purpur",
                                           headers={"User-Agent":"MC-CTRL/1.0"}),
                    timeout=15) as r:
                data = json.loads(r.read())
            versions = data.get("versions", [])
            if not versions:
                return None, "No Purpur versions returned"
            if ver == "latest":
                ver = versions[-1]
            elif ver not in versions:
                return None, f"Purpur {ver} not found. Available: {', '.join(versions[-5:])}"
            return f"https://api.purpurmc.org/v2/purpur/{ver}/latest/download", ver
        except Exception as ex:
            return None, str(ex)

    def _vanilla_url(ver):
        # Mojang version manifest
        MF = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
        try:
            with urllib.request.urlopen(MF, timeout=15) as r:
                mf = json.loads(r.read())
            if ver == "latest":
                ver = mf["latest"]["release"]
            vi = next((v for v in mf["versions"]
                        if v["id"] == ver and v["type"] == "release"), None)
            if not vi:
                return None, f"Vanilla release {ver} not found"
            with urllib.request.urlopen(vi["url"], timeout=15) as r2:
                vd = json.loads(r2.read())
            srv = vd.get("downloads", {}).get("server")
            if not srv:
                return None, f"No server download for {ver}"
            return srv["url"], ver
        except Exception as ex:
            return None, str(ex)

    def _do_create():
        s = load_settings(); path = s.get("srv_path", SRV_PATH)
        wname = world_name_var.get().strip() or "world"
        seed  = seed_var.get().strip()
        sw    = software_var.get()
        mc_v  = mc_ver_var.get().strip() or "latest"
        if server_proc and server_proc.poll() is None:
            app.after(0, show_toast, "Stop the server first!", T["stop"])
            app.after(0, _set_st, "Stop the server first.", T["stop"], 0); return
        app.after(0, _set_st, "Resolving download URL...", T["sync"], 0.05)
        if sw != "Fabric (manual)":
            if sw == "Paper":    url, resolved = _paper_url(mc_v)
            elif sw == "Purpur": url, resolved = _purpur_url(mc_v)
            else:                url, resolved = _vanilla_url(mc_v)
            if not url:
                app.after(0, _set_st, f"Could not resolve: {resolved}", T["stop"], 0)
                app.after(0, show_toast, "URL fetch failed.", T["stop"]); return
            app.after(0, log, f"  Downloading {sw} {resolved}...")
            jar_dest = os.path.join(path, "server.jar")
            if not _dl(url, jar_dest, f"{sw} {resolved}"):
                app.after(0, show_toast, "Download failed.", T["stop"]); return
            app.after(0, log, f"  JAR saved -> {jar_dest}")
        else:
            app.after(0, _set_st, "Fabric: install manually.", T["muted"], 0)
        try:
            with open(os.path.join(path,"eula.txt"),"w") as ef: ef.write("eula=true\n")
            app.after(0, log, "  eula.txt accepted.")
        except: pass
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        for fld in [wname,f"{wname}_nether",f"{wname}_the_end","world","world_nether","world_the_end"]:
            fp = os.path.join(path, fld)
            if os.path.isdir(fp):
                try: shutil.copytree(fp,f"{fp}_bak_{ts}"); app.after(0,log,f"  Backed up: {fld}")
                except Exception as ex: app.after(0,log,f"  Backup err {fld}: {ex}")
        for fld in [wname,f"{wname}_nether",f"{wname}_the_end"]:
            fp = os.path.join(path, fld)
            if os.path.isdir(fp):
                try: shutil.rmtree(fp); app.after(0,log,f"  Deleted old: {fld}")
                except Exception as ex: app.after(0,log,f"  Delete err: {ex}")
        prop_file = os.path.join(path,"server.properties")
        patches = {"level-name":wname,"level-seed":seed,"level-type":level_type_var.get(),
                   "gamemode":gamemode_var.get(),"difficulty":diff_var.get(),
                   "hardcore":str(hardcore_var.get()).lower(),
                   "generate-structures":str(structures_var.get()).lower()}
        try:
            lines_in = open(prop_file,encoding="utf-8").readlines() if os.path.exists(prop_file) else []
            new_lines=[]; written=set()
            for line in lines_in:
                s2=line.strip()
                if s2.startswith("#") or "=" not in s2: new_lines.append(line); continue
                k=s2.split("=",1)[0].strip()
                if k in patches: new_lines.append(f"{k}={patches[k]}\n"); written.add(k)
                else: new_lines.append(line)
            for k,v in patches.items():
                if k not in written: new_lines.append(f"{k}={v}\n")
            open(prop_file,"w",encoding="utf-8").writelines(new_lines)
            app.after(0,log,"  server.properties updated.")
        except Exception as ex:
            app.after(0,_set_st,f"Properties error: {ex}",T["stop"],0); return
        app.after(0,_set_st,f"Done! Start the server to generate world '{wname}'.",T["start"],1.0)
        app.after(0,show_toast,f"World '{wname}' configured!",T["start"])
        app.after(0,log,f"-- World creation done: {sw} '{wname}' seed='{seed or 'random'}' --")

    ctk.CTkButton(wch, text="Download & Create World", height=28, corner_radius=6,
                  font=ctk.CTkFont(size=11, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=lambda: threading.Thread(target=_do_create, daemon=True).start()
                  ).pack(side="right")

# ── Addon loader ───────────────────────────────────────────
def _load_addon(path):
    global _loaded_addons
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "setup"):
            ctx = {"app":app,"T":T,"log":log,"show_toast":show_toast,
                   "send_server_cmd":send_server_cmd,"load_settings":load_settings}
            mod.setup(ctx)
        _loaded_addons[name] = mod
        log(f"  Addon loaded: {name}")
    except Exception as ex:
        log(f"  Addon error [{name}]: {ex}")
        show_toast(f"Addon '{name}' failed: {ex}", T["stop"])

def _load_all_addons():
    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)
    readme = os.path.join(addon_dir, "README.md")
    if not os.path.exists(readme):
        open(readme,"w").write("""# MC CTRL Addon API

Addons are .py files in this folder, loaded at startup.

## Minimal addon

```python
def setup(ctx):
    ctx["log"]("Hello from my addon!")
```

## Context keys
- ctx["app"]              — CTk root window
- ctx["T"]               — theme colour dict
- ctx["log"](msg)        — write to server log
- ctx["show_toast"](m,c) — show a toast notification
- ctx["send_server_cmd"] — send command to running MC server
- ctx["load_settings"]   — returns settings dict
""")
    try:
        for s in sorted(os.listdir(addon_dir)):
            if s.endswith(".py"):
                _load_addon(os.path.join(addon_dir, s))
    except: pass

# ── playit.gg tab ──────────────────────────────────────────
def build_playit_tab(parent):
    global playit_proc, playit_tunnel, playit_log_lines

    scroll = make_scroll_frame(parent, fg_color="transparent")

    def _card(title, subtitle=None):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10,0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8,12))
        return body, h

    ab, _ = _card("What is playit.gg?")
    ctk.CTkLabel(ab, text=(
        "playit.gg is a free tunnel that gives your server a public address without port forwarding\n"
        "or exposing your home IP. Friends connect via a .ply.gg address.\n\n"
        "Free: up to 3 tunnels  |  Premium ~$3/mo: regional routing & custom domains."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=840, justify="left"
    ).pack(anchor="w")

    sb, sh = _card("Setup", "one-time")
    s = load_settings()
    playit_path_var = ctk.StringVar(value=s.get("playit_path",""))
    def _save_pt(*_): update_setting("playit_path", playit_path_var.get())
    playit_path_var.trace_add("write", _save_pt)

    pt_status_lbl = ctk.CTkLabel(sb, text="", font=ctk.CTkFont(size=11), text_color=T["muted"])
    def _set_pt_st(msg, color):
        try: pt_status_lbl.configure(text=msg, text_color=color)
        except: pass

    def _browse_pt():
        p = _tk_fd.askopenfilename(title="Select playit.exe",
                                   filetypes=[("Executables","*.exe"),("All","*.*")])
        if p: playit_path_var.set(p)

    def _dl_playit():
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),"playit.exe")
        _set_pt_st("Downloading playit.exe...", T["sync"])
        def _do():
            url = "https://github.com/playit-cloud/playit-agent/releases/latest/download/playit-windows.exe"
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"MC-CTRL/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    with open(dest,"wb") as f: f.write(r.read())
                playit_path_var.set(dest)
                update_setting("playit_path", dest)
                app.after(0, _set_pt_st, "Downloaded!", T["start"])
                app.after(0, show_toast, "playit.exe downloaded!", T["start"])
            except Exception as ex:
                app.after(0, _set_pt_st, f"Failed: {ex}", T["stop"])
        threading.Thread(target=_do, daemon=True).start()

    pr = ctk.CTkFrame(sb, fg_color="transparent"); pr.pack(fill="x", pady=(0,6))
    ctk.CTkLabel(pr, text="playit.exe", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=100, anchor="w").pack(side="left")
    ctk.CTkEntry(pr, textvariable=playit_path_var, height=30,
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="path\\to\\playit.exe"
                 ).pack(side="left", fill="x", expand=True, padx=(0,8))
    ctk.CTkButton(pr, text="Browse", width=70, height=30, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_browse_pt).pack(side="left", padx=(0,6))
    ctk.CTkButton(pr, text="Auto-Download", height=30, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_dl_playit).pack(side="left")
    pt_status_lbl.pack(anchor="w", pady=(4,0))

    # Agent secret key (for users who already have an account)
    ctk.CTkFrame(sb, height=1, fg_color=T["border"]).pack(fill="x", pady=(8,6))
    ctk.CTkLabel(sb, text="Already have a playit.gg account?",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=T["text"]).pack(anchor="w")
    ctk.CTkLabel(sb, text=(
        "If you've already set up the agent and have your secret key, paste it below.\n"
        "The agent will use it automatically on next start — no browser claim needed."
    ), font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(2,4))

    key_row = ctk.CTkFrame(sb, fg_color="transparent"); key_row.pack(fill="x", pady=(0,4))
    ctk.CTkLabel(key_row, text="Secret Key", font=ctk.CTkFont(size=11),
                 text_color=T["text"], width=90, anchor="w").pack(side="left")
    _s = load_settings()
    playit_key_var = ctk.StringVar(value=_s.get("playit_secret_key",""))
    key_entry = ctk.CTkEntry(key_row, textvariable=playit_key_var, height=28,
                              font=ctk.CTkFont(size=11, family="Consolas"),
                              fg_color=T["bg"], border_color=T["border"],
                              text_color=T["text"], show="•",
                              placeholder_text="paste your secret key here")
    key_entry.pack(side="left", fill="x", expand=True, padx=(0,8))

    def _toggle_key_vis():
        cur = key_entry.cget("show")
        key_entry.configure(show="" if cur == "•" else "•")
        vis_btn.configure(text="Hide" if cur == "•" else "Show")
    vis_btn = ctk.CTkButton(key_row, text="Show", width=52, height=28,
                             font=ctk.CTkFont(size=10), fg_color="transparent",
                             border_width=1, border_color=T["border"],
                             text_color=T["muted"], hover_color=T["border"],
                             command=_toggle_key_vis)
    vis_btn.pack(side="left")

    def _save_key(*_):
        update_setting("playit_secret_key", playit_key_var.get().strip())
    playit_key_var.trace_add("write", _save_key)

    def _open_claim_link():
        import webbrowser
        webbrowser.open("https://playit.gg/login")
    ctk.CTkButton(sb, text="Open playit.gg to get your key →", height=26,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=_open_claim_link).pack(anchor="w", pady=(0,4))

    ctk.CTkLabel(sb, text="First run without a key: a claim URL appears in the agent log below.",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w")

    cb, ch = _card("Tunnel Control")
    tun_st = ctk.CTkLabel(cb, text="● Stopped", font=ctk.CTkFont(size=13, weight="bold"),
                           text_color=T["stop"]); tun_st.pack(side="left")
    tun_addr = ctk.CTkLabel(cb, text="", font=ctk.CTkFont(size=13, family="Consolas"),
                             text_color=T["start"]); tun_addr.pack(side="left", padx=(14,0))

    def _set_tst(msg, col):
        try: tun_st.configure(text=msg, text_color=col)
        except: pass
    def _set_addr(addr):
        global playit_tunnel; playit_tunnel = addr
        try:
            tun_addr.configure(text=addr or "")
            if addr: show_toast(f"Tunnel: {addr}", T["start"])
        except: pass
    # ── Batched, throttled log writer ─────────────────────────────
    # Lines from background threads accumulate in _PT_LOG_QUEUE.
    # A single recurring app.after() drains them at most every 120ms,
    # so fast bursts never schedule hundreds of individual UI updates.
    _PT_LOG_QUEUE    = []
    _PT_LOG_MAXLINES = 300
    _PT_FLUSH_MS     = 120
    _pt_flush_pending = [False]

    _ansi_re  = re.compile(r'\x1b(?:\[[0-9;]*[mABCDEFGHJKSTfhilmnprsuu]|\][^\x07]*\x07|[()][AB012]|[=>])')
    _coord_re = re.compile(r'\x1b\[\d+;\d+H')

    def _flush_ptlog():
        _pt_flush_pending[0] = False
        if not _PT_LOG_QUEUE:
            return
        batch = _PT_LOG_QUEUE[:]
        _PT_LOG_QUEUE.clear()
        try:
            pt_log.configure(state="normal")
            pt_log.insert("end", "\n".join(batch) + "\n")
            # Keep widget trimmed — one bulk delete instead of per-line
            total = int(pt_log.index("end-1c").split(".")[0])
            if total > _PT_LOG_MAXLINES:
                pt_log.delete("1.0", f"{total - _PT_LOG_MAXLINES}.0")
            pt_log.configure(state="disabled")
            pt_log.see("end")
        except Exception:
            pass

    def _append_ptlog(line):
        _PT_LOG_QUEUE.append(line)
        if not _pt_flush_pending[0]:
            _pt_flush_pending[0] = True
            app.after(_PT_FLUSH_MS, _flush_ptlog)

    def _handle_line(raw_bytes, prefix=""):
        try:
            line = raw_bytes.decode("utf-8", errors="replace").rstrip()
        except Exception:
            line = repr(raw_bytes)
        clean = _ansi_re.sub("", _coord_re.sub(" ", line)).strip()
        if not clean:
            return
        tagged = f"{prefix}{clean}" if prefix else clean
        playit_log_lines.append(tagged)
        if len(playit_log_lines) > 300:
            del playit_log_lines[:150]   # drop oldest half in one shot
        m = _playit_addr_re.search(clean) or _playit_arrow_re.search(clean)
        if m:
            app.after(0, _set_addr, m.group(1))
        cm = _playit_claim_re.search(clean)
        if cm:
            url = cm.group(1)
            _append_ptlog(f"[MC CTRL] >>> CLAIM URL: {url} <<<")
            app.after(0, show_toast, "Open claim URL in browser!", T["handoff"], 8000)
        _append_ptlog(tagged)

    def _read_stream_bytes(stream, prefix=""):
        try:
            for raw in iter(stream.readline, b""):
                if not raw:
                    break
                _handle_line(raw, prefix)
        except Exception:
            pass

    def _read_pt(proc):
        _read_stream_bytes(proc.stdout, "")
        code = proc.wait()
        if code == 0:
            msg = "[MC CTRL] Agent exited cleanly."
        else:
            msg = (f"[MC CTRL] Agent exited with code {code}. "
                   "If your secret key is wrong, clear it and restart — "
                   "a claim URL will appear for first-time setup.")
        app.after(0, _append_ptlog, msg)
        app.after(0, _set_tst, "● Stopped", T["stop"])

    def _read_stderr_pt(proc):
        """Read stderr separately — playit prints errors here."""
        _read_stream_bytes(proc.stderr, "[stderr] ")

    def _watch_tunnel_toml(exe_path):
        """
        Fallback: poll TOML files and recent log lines for tunnel address.
        playit writes %APPDATA%/playit/*.toml or next to the exe.
        """
        import glob, time as _time
        appdata = os.environ.get("APPDATA", "")
        exe_dir = os.path.dirname(exe_path)
        # Broader address pattern for TOML values
        toml_addr_re = re.compile(
            r'(?:address|host|tunnel|alloc)\s*=\s*["\']?((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg)(?::\d+)?)',
            re.IGNORECASE)
        seen = set()

        def _scan_toml(path):
            try:
                txt = open(path, encoding="utf-8", errors="ignore").read()
                for m in toml_addr_re.finditer(txt):
                    addr = m.group(1)
                    if addr not in seen:
                        seen.add(addr)
                        app.after(0, _set_addr, addr)
                        app.after(0, _append_ptlog,
                                  f"[MC CTRL] Tunnel address from config: {addr}")
            except Exception:
                pass

        def _scan_log_lines():
            for line in list(playit_log_lines):
                m = _playit_addr_re.search(line)
                if m:
                    addr = m.group(1)
                    if addr not in seen:
                        seen.add(addr)
                        app.after(0, _set_addr, addr)

        for _ in range(120):   # poll for up to 6 minutes
            if not (playit_proc and playit_proc.poll() is None):
                break
            # Dynamically discover TOML files (playit may create them after start)
            toml_files = []
            if appdata:
                toml_files += glob.glob(os.path.join(appdata, "playit", "*.toml"))
                toml_files += glob.glob(os.path.join(appdata, "playit", "**", "*.toml"), recursive=True)
            toml_files += glob.glob(os.path.join(exe_dir, "*.toml"))
            for p in toml_files:
                _scan_toml(p)
            _scan_log_lines()
            _time.sleep(3)

    def _start_pt():
        global playit_proc
        exe = playit_path_var.get().strip()
        if not exe or not os.path.exists(exe):
            show_toast("Set playit.exe path first!", T["stop"]); return
        if playit_proc and playit_proc.poll() is None:
            show_toast("Already running.", T["muted"]); return

        # Inject secret key into playit's TOML config (the only reliable method).
        # playit reads %APPDATA%\playit\playit.toml  →  secret_key = "..."
        # We patch that file before launching so no CLI flags are needed.
        saved_key = load_settings().get("playit_secret_key", "").strip()
        cmd = [exe]
        env = os.environ.copy()
        if saved_key:
            _injected_path = None
            try:
                appdata = os.environ.get("APPDATA", "")
                if appdata:
                    pt_dir = os.path.join(appdata, "playit")
                    os.makedirs(pt_dir, exist_ok=True)
                    toml_path = os.path.join(pt_dir, "playit.toml")
                    if os.path.exists(toml_path):
                        with open(toml_path, encoding="utf-8", errors="ignore") as _tf:
                            toml_lines = _tf.readlines()
                        new_toml = []
                        found_key = False
                        for _tl in toml_lines:
                            if _tl.strip().startswith("secret_key"):
                                new_toml.append('secret_key = "' + saved_key + '"\n')
                                found_key = True
                            else:
                                new_toml.append(_tl)
                        if not found_key:
                            new_toml.insert(0, 'secret_key = "' + saved_key + '"\n')
                    else:
                        new_toml = ['secret_key = "' + saved_key + '"\n']
                    with open(toml_path, "w", encoding="utf-8") as _tf:
                        _tf.writelines(new_toml)
                    _injected_path = toml_path
            except Exception:
                pass
            # Also write next to the exe as a fallback for portable installs
            try:
                exe_toml = os.path.join(os.path.dirname(exe), "playit.toml")
                with open(exe_toml, "w") as _tf2:
                    _tf2.write('secret_key = "' + saved_key + '"\n')
                if not _injected_path:
                    _injected_path = exe_toml
            except Exception:
                pass
            # Show what we actually wrote so user can verify
            try:
                _toml_preview = open(_injected_path, encoding="utf-8").read().strip()
            except Exception:
                _toml_preview = "(could not read)"
            app.after(0, _append_ptlog,
                      f"[MC CTRL] Secret key written to: {_injected_path}")
            app.after(0, _append_ptlog,
                      f"[MC CTRL] TOML contents: {_toml_preview}")

        try:
            # Hide console window; use unbuffered binary pipes so we get
            # output immediately even though playit is not a tty.
            _si = subprocess.STARTUPINFO()
            _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            _si.wShowWindow = 0   # SW_HIDE
            playit_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,     # separate so we capture both
                stdin=subprocess.DEVNULL,
                text=False,                 # binary — we decode per-line ourselves
                bufsize=0,                  # unbuffered — get lines immediately
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                startupinfo=_si,
                env=env,
            )
            _set_tst("● Running", T["start"])
            log("-- playit.gg started --")
            app.after(0, _append_ptlog,
                      "[MC CTRL] Agent started. Waiting for tunnel address...")
            # Read stdout and stderr on separate threads so neither blocks
            threading.Thread(target=_read_pt,        args=(playit_proc,), daemon=True).start()
            threading.Thread(target=_read_stderr_pt, args=(playit_proc,), daemon=True).start()
            threading.Thread(target=_watch_tunnel_toml, args=(exe,),     daemon=True).start()
        except Exception as ex:
            show_toast(f"Failed to start playit: {ex}", T["stop"])
            _set_tst("● Error", T["stop"])
    def _stop_pt():
        global playit_proc, playit_tunnel
        if playit_proc:
            try: playit_proc.terminate()
            except: pass
            playit_proc = None
        playit_tunnel = None; _set_addr(""); _set_tst("● Stopped", T["stop"])
        log("-- playit.gg stopped --")
    def _copy_addr():
        addr = tun_addr.cget("text")
        if addr: app.clipboard_clear(); app.clipboard_append(addr); show_toast(f"Copied: {addr}",T["sync"])
        else: show_toast("No address yet.",T["muted"])

    br = ctk.CTkFrame(ch, fg_color="transparent"); br.pack(side="right")
    ctk.CTkButton(br,text="▶ Start",width=74,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["start"],hover_color=T["start"],text_color="#000",
                  command=_start_pt).pack(side="left",padx=(0,4))
    ctk.CTkButton(br,text="■ Stop",width=74,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["stop"],hover_color=T["stop"],text_color="#fff",
                  command=_stop_pt).pack(side="left",padx=(0,4))
    ctk.CTkButton(br,text="Copy Address",width=100,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["sync"],hover_color=T["sync"],text_color="#000",
                  command=_copy_addr).pack(side="left")

    lb, lh = _card("Agent Log")
    pt_log = ctk.CTkTextbox(lb, font=ctk.CTkFont(size=11,family="Consolas"),
                             wrap="word", state="disabled", height=220,
                             fg_color=T["bg"], text_color=T["text"]); pt_log.pack(fill="x")
    # Restore log lines saved from before a theme rebuild
    if playit_log_lines:
        pt_log.configure(state="normal")
        for _saved_line in playit_log_lines:
            pt_log.insert("end", _saved_line + "\n")
        pt_log.configure(state="disabled")
        pt_log.see("end")
    # If tunnel address already known, restore it
    if playit_tunnel:
        _set_addr(playit_tunnel)
    def _clear_ptlog():
        global playit_log_lines
        playit_log_lines.clear()
        pt_log.configure(state="normal")
        pt_log.delete("1.0","end")
        pt_log.configure(state="disabled")
    ctk.CTkButton(lh,text="Clear",width=58,height=22,font=ctk.CTkFont(size=10),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],
                  command=_clear_ptlog).pack(side="right")
    def _copy_ptlog():
        try:
            txt = pt_log.get("1.0","end").strip()
            app.clipboard_clear(); app.clipboard_append(txt)
            show_toast("Agent log copied!", T["sync"])
        except: pass
    ctk.CTkButton(lh,text="Copy Log",width=72,height=22,font=ctk.CTkFont(size=10),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],
                  command=_copy_ptlog).pack(side="right", padx=(0,4))

    gb, _ = _card("Setup Guide")

    def _step(parent, num, title, body, tip=None):
        sf = ctk.CTkFrame(parent, fg_color=T["bg"], border_color=T["border"],
                          border_width=1, corner_radius=8)
        sf.pack(fill="x", pady=(0, 8))
        nb = ctk.CTkFrame(sf, fg_color=T["sync"], width=28, height=28, corner_radius=14)
        nb.pack(side="left", anchor="n", padx=(12, 10), pady=12)
        nb.pack_propagate(False)
        ctk.CTkLabel(nb, text=str(num), font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#000000").place(relx=0.5, rely=0.5, anchor="center")
        tb = ctk.CTkFrame(sf, fg_color="transparent")
        tb.pack(side="left", fill="x", expand=True, pady=10, padx=(0, 12))
        ctk.CTkLabel(tb, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tb, text=body, font=ctk.CTkFont(size=11),
                     text_color=T["muted"], justify="left",
                     wraplength=680, anchor="w").pack(anchor="w", pady=(2, 0))
        if tip:
            tf = ctk.CTkFrame(tb, fg_color=T["card"], corner_radius=6)
            tf.pack(anchor="w", fill="x", pady=(6, 0))
            ctk.CTkLabel(tf, text=f"\U0001f4a1  {tip}", font=ctk.CTkFont(size=10),
                         text_color=T["sync"], justify="left",
                         wraplength=660, anchor="w").pack(padx=10, pady=6)

    _step(gb, 1,
          "Download the playit agent",
          "Click the  \u2b07 Auto-Download  button in the Setup card above. It fetches the latest\n"
          "playit-windows.exe directly from GitHub and saves it next to launcher.pyw.\n"
          "You can also point to an existing playit.exe using Browse.",
          "Only do this once \u2014 the same exe works forever, it updates itself automatically.")

    _step(gb, 2,
          "Start the agent",
          "Click  \u25b6 Start  in the Tunnel Control card. The status dot turns green\n"
          "and the Agent Log starts filling with output from playit.",
          "Start the agent before or at the same time as your Minecraft server.")

    _step(gb, 3,
          "Claim your account (first run only)",
          "On the very first run playit doesn't know who you are yet. Look in the Agent Log\n"
          "for a line like:\n\n"
          "      visit https://playit.gg/claim/xxxxxxxxxxxxxxxx to setup your agent\n\n"
          "Open that URL in your browser, sign in or create a free account, and click\n"
          "Continue. This links the agent on your PC to your playit.gg account.\n"
          "You only ever need to do this once.",
          "The claim URL is unique to this installation. Don't share it with anyone.")

    _step(gb, 4,
          "Wait for the tunnel address",
          "After claiming, playit.gg automatically creates a Minecraft tunnel.\n"
          "Within a few seconds the address (something like  xxxxx.at.ply.gg) appears\n"
          "in big text next to the status dot.\n"
          "Click  Copy Address  to copy it to your clipboard.",
          "If the address doesn't appear after 30 seconds, stop and restart the agent.")

    _step(gb, 5,
          "Share with your friends",
          "Give the address to your friends. They open Minecraft \u2192\n"
          "Multiplayer \u2192 Add Server (or Direct Connect) and paste it exactly as shown.\n"
          "No port number is needed \u2014 playit routes port 25565 automatically.",
          "Friends don't need a playit account. Only you (the host) need one.")

    _step(gb, 6,
          "Stop the tunnel when done",
          "Click  \u25a0 Stop  when you're finished. The tunnel goes offline immediately.\n"
          "Next session, click  \u25b6 Start  again \u2014 the same address comes back.",
          None)

    faq_f = ctk.CTkFrame(gb, fg_color=T["card"], border_color=T["border"],
                          border_width=1, corner_radius=8)
    faq_f.pack(fill="x", pady=(4, 0))
    ctk.CTkLabel(faq_f, text="Troubleshooting",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=T["text"]).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(faq_f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    ctk.CTkLabel(faq_f, text=(
        "Friends can't connect?   \u2192   Make sure your MC server is running AND \u25b6 Start is active.\n"
        "No address appears?      \u2192   Check the Agent Log for errors; try Stop then Start again.\n"
        "Claim URL missing?       \u2192   The agent may already be claimed. Check playit.gg \u2192 Agents.\n"
        "Address keeps changing?  \u2192   Free plan addresses are persistent \u2014 they don't change.\n"
        "Lag / high ping?         \u2192   Upgrade to Premium ($3/mo) to pick a nearby server region.\n"
        "Port already in use?     \u2192   Make sure no other playit instance is already running."
    ), font=ctk.CTkFont(size=11), text_color=T["muted"],
       justify="left", wraplength=820).pack(anchor="w", padx=14, pady=(8, 12))

    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

# ── MULTI CTRL tab ────────────────────────────────────────
# Up to 3 independent server columns, each with its own
# path input, log, start/stop buttons.
# A shared chat bar at the bottom sends to whichever server
# is selected.

_mc_servers = {}   # slot (0,1,2) -> {proc, stdin, pid, log_box, path_var, ...}

def build_multictrl_tab(parent):
    global _mc_servers

    MAX_SLOTS = 3
    # Slot state
    slots = {}
    for i in range(MAX_SLOTS):
        slots[i] = {
            "proc":     None,
            "stdin":    None,
            "path_var": ctk.StringVar(value=""),
            "log_box":  None,
            "status":   None,   # label widget
            "running":  False,
        }
    _mc_servers = slots

    # ── Layout: top toolbar + columns + shared chat ────────
    parent.rowconfigure(0, weight=0)
    parent.rowconfigure(1, weight=1)
    parent.rowconfigure(2, weight=0)
    parent.columnconfigure(0, weight=1)

    # ── Top toolbar ────────────────────────────────────────
    toolbar = ctk.CTkFrame(parent, fg_color=T["card"],
                            border_color=T["border"], border_width=1,
                            corner_radius=0)
    toolbar.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(toolbar, text="⊞  MULTI CTRL",
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["handoff"]).pack(side="left", padx=14, pady=8)
    ctk.CTkLabel(toolbar, text="— control up to 3 servers simultaneously",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

    # ── Column area ────────────────────────────────────────
    col_area = ctk.CTkFrame(parent, fg_color="transparent")
    col_area.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
    for i in range(MAX_SLOTS):
        col_area.columnconfigure(i, weight=1, uniform="col")
    col_area.rowconfigure(0, weight=1)

    def _mc_log(slot, msg):
        """Append msg to slot's log box (call from any thread via app.after)."""
        lb = slots[slot]["log_box"]
        if lb is None: return
        try:
            lb.configure(state="normal")
            lb.insert("end", msg + "\n")
            lb.configure(state="disabled")
            lb.see("end")
        except: pass

    def _mc_set_status(slot, txt, color):
        lbl = slots[slot]["status"]
        if lbl:
            try: lbl.configure(text=txt, text_color=color)
            except: pass

    def _mc_read_output(slot, proc):
        for raw in iter(proc.stdout.readline, ""):
            if not raw: break
            app.after(0, _mc_log, slot, raw.rstrip())
        app.after(0, _mc_set_status, slot, "● Stopped", T["stop"])
        slots[slot]["running"] = False
        slots[slot]["proc"]    = None
        slots[slot]["stdin"]   = None

    def _mc_start(slot):
        path = slots[slot]["path_var"].get().strip()
        if not path or not os.path.isdir(path):
            show_toast(f"Server {slot+1}: set a valid world/server folder first.", T["stop"])
            return
        if slots[slot]["running"]:
            show_toast(f"Server {slot+1} is already running.", T["muted"]); return
        s = load_settings()
        java = s.get("java_path", JAVA_PATH)
        jar  = os.path.join(path, "server.jar")
        if not os.path.exists(jar):
            show_toast(f"Server {slot+1}: no server.jar found in that folder.", T["stop"])
            return
        # EULA check
        if not _check_eula(path): return
        try:
            cmd = [java,
                   "-Xms512M", "-Xmx2G",
                   "-XX:+UseG1GC",
                   "-jar", jar, "--nogui"]
            proc = subprocess.Popen(
                cmd, cwd=path,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=CREATE_NO_WINDOW)
            slots[slot]["proc"]    = proc
            slots[slot]["stdin"]   = proc.stdin
            slots[slot]["running"] = True
            _mc_set_status(slot, "● Running", T["start"])
            app.after(0, _mc_log, slot, f"-- Server {slot+1} started --")
            threading.Thread(target=_mc_read_output, args=(slot, proc),
                             daemon=True).start()
        except Exception as ex:
            show_toast(f"Server {slot+1} failed: {ex}", T["stop"])

    def _mc_stop(slot):
        proc = slots[slot]["proc"]
        if proc:
            try:
                slots[slot]["stdin"].write("stop\n")
                slots[slot]["stdin"].flush()
            except: pass
            app.after(3000, lambda p=proc: p.terminate() if p.poll() is None else None)
        slots[slot]["running"] = False
        slots[slot]["proc"]    = None
        slots[slot]["stdin"]   = None
        _mc_set_status(slot, "● Stopped", T["stop"])
        app.after(0, _mc_log, slot, f"-- Server {slot+1} stopped --")

    # ── Build each column ──────────────────────────────────
    for i in range(MAX_SLOTS):
        col = ctk.CTkFrame(col_area, fg_color=T["card"],
                           border_color=T["border"], border_width=1,
                           corner_radius=10)
        col.grid(row=0, column=i, sticky="nsew", padx=4, pady=0)
        col.rowconfigure(2, weight=1)
        col.columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────
        hdr = ctk.CTkFrame(col, fg_color=T["bg"], corner_radius=8)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))

        ctk.CTkLabel(hdr, text=f"Server {i+1}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=10, pady=6)
        st_lbl = ctk.CTkLabel(hdr, text="● Stopped",
                               font=ctk.CTkFont(size=11, weight="bold"),
                               text_color=T["stop"])
        st_lbl.pack(side="right", padx=10)
        slots[i]["status"] = st_lbl

        # ── Path input ────────────────────────────────────
        path_frame = ctk.CTkFrame(col, fg_color="transparent")
        path_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,4))
        path_frame.columnconfigure(0, weight=1)

        path_entry = ctk.CTkEntry(path_frame,
                                   textvariable=slots[i]["path_var"],
                                   height=28,
                                   font=ctk.CTkFont(size=10, family="Consolas"),
                                   fg_color=T["bg"], border_color=T["border"],
                                   text_color=T["text"],
                                   placeholder_text=f"Server {i+1} folder path…")
        path_entry.grid(row=0, column=0, sticky="ew", padx=(0,4))

        def _browse_mc(slot=i):
            import tkinter.filedialog as fd
            p = fd.askdirectory(title=f"Select Server {slot+1} Folder")
            if p: slots[slot]["path_var"].set(p)

        ctk.CTkButton(path_frame, text="…", width=28, height=28,
                      font=ctk.CTkFont(size=11), corner_radius=6,
                      fg_color=T["bg"], border_width=1,
                      border_color=T["border"], text_color=T["muted"],
                      hover_color=T["border"],
                      command=lambda s=i: _browse_mc(s)
                      ).grid(row=0, column=1)

        # ── Start / Stop buttons ──────────────────────────
        btn_row = ctk.CTkFrame(path_frame, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4,0))
        ctk.CTkButton(btn_row, text="▶ Start", height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color=T["start"], hover_color=T["start"],
                      text_color="#000",
                      command=lambda s=i: threading.Thread(
                          target=_mc_start, args=(s,), daemon=True).start()
                      ).pack(side="left", expand=True, fill="x", padx=(0,3))
        ctk.CTkButton(btn_row, text="■ Stop", height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color=T["stop"], hover_color=T["stop"],
                      text_color="#fff",
                      command=lambda s=i: _mc_stop(s)
                      ).pack(side="left", expand=True, fill="x", padx=(3,0))

        # ── Log box ───────────────────────────────────────
        lb = ctk.CTkTextbox(col,
                             font=ctk.CTkFont(size=10, family="Consolas"),
                             wrap="word", state="disabled",
                             fg_color=T["bg"], text_color=T["text"])
        lb.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0,8))
        slots[i]["log_box"] = lb

    # ── Shared chat bar ────────────────────────────────────
    chat_bar = ctk.CTkFrame(parent, fg_color=T["card"],
                             border_color=T["border"], border_width=1,
                             corner_radius=0)
    chat_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
    chat_bar.columnconfigure(1, weight=1)

    # Target selector
    target_var = ctk.StringVar(value="Server 1")
    ctk.CTkLabel(chat_bar, text="Send to:",
                 font=ctk.CTkFont(size=11), text_color=T["muted"]
                 ).grid(row=0, column=0, padx=(10,4), pady=8)
    target_menu = ctk.CTkOptionMenu(
        chat_bar,
        values=["Server 1", "Server 2", "Server 3", "All Servers"],
        variable=target_var,
        font=ctk.CTkFont(size=11), width=120, height=30,
        fg_color=T["bg"], button_color=T["border"],
        button_hover_color=T["muted"], text_color=T["text"],
        dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
        dropdown_hover_color=T["border"])
    target_menu.grid(row=0, column=1, padx=(0,6), pady=8, sticky="w")

    cmd_entry = ctk.CTkEntry(chat_bar, height=30,
                              font=ctk.CTkFont(size=12),
                              fg_color=T["bg"], border_color=T["border"],
                              text_color=T["text"],
                              placeholder_text="command or chat…")
    cmd_entry.grid(row=0, column=2, sticky="ew", padx=(0,6), pady=8)
    chat_bar.columnconfigure(2, weight=1)

    def _mc_send(_event=None):
        cmd = cmd_entry.get().strip()
        if not cmd: return
        target = target_var.get()
        targets = list(range(MAX_SLOTS)) if target == "All Servers"                   else [int(target.split()[-1]) - 1]
        for s in targets:
            stdin = slots[s]["stdin"]
            if stdin:
                try:
                    stdin.write(cmd + "\n"); stdin.flush()
                    app.after(0, _mc_log, s, f">> {cmd}")
                except Exception as ex:
                    app.after(0, _mc_log, s, f"[error] {ex}")
            else:
                app.after(0, _mc_log, s,
                          f"[Server {s+1} not running — command not sent]")
        cmd_entry.delete(0, "end")

    cmd_entry.bind("<Return>", _mc_send)
    ctk.CTkButton(chat_bar, text="Send", width=70, height=30,
                  font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"],
                  text_color="#000", command=_mc_send
                  ).grid(row=0, column=3, padx=(0,10), pady=8)

# ── Settings tab ─────────────────────────────────────────def build_settings_tab(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=20, pady=12)

    def section(title):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["text"]).pack(anchor="w", padx=14, pady=(10,4))
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        b = ctk.CTkFrame(f, fg_color="transparent"); b.pack(fill="x", padx=14, pady=(6,10))
        return b

    def row(parent, label, fn):
        r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", pady=5)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color=T["text"], width=240, anchor="w").pack(side="left")
        fn(r)

    def sw(parent, get_val, on_change):
        var = ctk.BooleanVar(value=get_val())
        ctk.CTkSwitch(parent, text="", variable=var,
                      command=lambda: on_change(var.get()),
                      button_color=T["sync"], progress_color=T["sync"]).pack(side="right")

    # Appearance
    b = section("Appearance")
    def theme_fn(p):
        tm = ctk.CTkOptionMenu(p, values=list(THEMES.keys()), command=apply_theme,
                               font=ctk.CTkFont(size=12), width=200,
                               fg_color=T["bg"], button_color=T["border"],
                               button_hover_color=T["muted"], text_color=T["text"],
                               dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                               dropdown_hover_color=T["border"])
        tm.set(current_theme_name); tm.pack(side="right")
    row(b, "Theme", theme_fn)
    row(b, "Fullscreen", lambda p: sw(p, lambda: fullscreen, lambda v: toggle_fullscreen()))
    def ram_fn(p):
        def toggle():
            global ram_display_mode
            ram_display_mode = "fraction" if ram_display_mode=="percent" else "percent"
            update_setting("ram_display_mode", ram_display_mode)
        sw(p, lambda: ram_display_mode=="fraction", lambda v: toggle())
    row(b, "Show RAM as x/y GB (instead of %)", ram_fn)

    # Layout
    b = section("Layout")
    row(b, "Log panel on left side",   lambda p: sw(p, lambda: log_left,  lambda v: swap_layout()))
    row(b, "Show performance panel",   lambda p: sw(p, lambda: show_perf, lambda v: toggle_perf()))
    row(b, "Show chat & events panel", lambda p: sw(p, lambda: show_chat, lambda v: toggle_chat()))

    # Server paths
    b = section("Server")
    def srv_e(label, key, default):
        r = ctk.CTkFrame(b, fg_color="transparent"); r.pack(fill="x", pady=4)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color=T["text"], width=240, anchor="w").pack(side="left")
        e = ctk.CTkEntry(r, font=ctk.CTkFont(size=11, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"],
                         text_color=T["text"], height=28)
        e.insert(0, load_settings().get(key, default)); e.pack(side="left", fill="x", expand=True)
        def save(*_): update_setting(key, e.get())
        e.bind("<FocusOut>", save); e.bind("<Return>", save)
        return e
    global e_path, e_repo, e_java
    e_path = srv_e("Server path",     "srv_path",  SRV_PATH)
    e_repo = srv_e("GitHub repo URL", "repo_url",  REPO_URL)
    e_java = srv_e("Java path",       "java_path", JAVA_PATH)

    # Auto Upload
    b = section("Auto Upload")
    row(b, "Enable auto upload",
        lambda p: sw(p, lambda: auto_upload, lambda v: toggle_auto_upload()))
    def _toggle_backup_upload(v):
        global backup_upload_on
        backup_upload_on = v
        update_setting("backup_upload_on", v)
    row(b, "Backup upload  (ON = uploads to GitHub, OFF = skips all uploads)",
        lambda p: sw(p, lambda: backup_upload_on, _toggle_backup_upload))
    def mins_fn(p):
        var = ctk.StringVar(value=str(auto_upload_mins))
        e = ctk.CTkEntry(p, textvariable=var, width=60, height=28,
                         font=ctk.CTkFont(size=12, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
        e.pack(side="right")
        def save(*_):
            global auto_upload_mins
            try:
                auto_upload_mins = max(1, int(float(var.get())))
                update_setting("auto_upload_mins", auto_upload_mins)
                if auto_upload: schedule_auto_upload()
            except: pass
        e.bind("<FocusOut>", save); e.bind("<Return>", save)
    row(b, "Upload interval (minutes)", mins_fn)
    row(b, "Upload world to GitHub on server stop",
        lambda p: sw(p, lambda: upload_on_stop, lambda v: _set_upload_on_stop(v)))

    # ── Server Plugins Manager ────────────────────────────
    b = section("Server Plugins Manager")
    def _get_pd(): return os.path.join(load_settings().get("srv_path",SRV_PATH),"plugins")
    plf = ctk.CTkFrame(b, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8)
    plf.pack(fill="x", pady=(0,6))
    def _ref_plug():
        for w in plf.winfo_children(): w.destroy()
        pd = _get_pd()
        try: jars = sorted([x for x in os.listdir(pd) if x.endswith(".jar")])
        except: jars = []
        if not jars:
            ctk.CTkLabel(plf,text="No server plugins installed.",font=ctk.CTkFont(size=11),text_color=T["muted"]).pack(padx=14,pady=8)
        else:
            for j in jars:
                pr=ctk.CTkFrame(plf,fg_color="transparent"); pr.pack(fill="x",padx=10,pady=3)
                ctk.CTkLabel(pr,text=j.replace(".jar",""),font=ctk.CTkFont(size=12),text_color=T["text"]).pack(side="left")
                def _rem(n=j):
                    try: os.remove(os.path.join(_get_pd(),n)); show_toast(f"Removed {n}",T["stop"]); _ref_plug()
                    except Exception as ex: show_toast(f"Error: {ex}",T["stop"])
                ctk.CTkButton(pr,text="Remove",width=64,height=22,font=ctk.CTkFont(size=10),fg_color="transparent",
                              border_width=1,border_color=T["stop"],text_color=T["stop"],hover_color=T["border"],
                              command=_rem).pack(side="right")
    def _add_plug():
        pd=_get_pd(); os.makedirs(pd,exist_ok=True)
        paths=_tk_fd.askopenfilenames(title="Select plugin JAR(s)",filetypes=[("JAR","*.jar"),("All","*.*")])
        if not paths: return
        for p in paths:
            try: shutil.copy2(p,os.path.join(pd,os.path.basename(p)))
            except Exception as ex: show_toast(f"Failed: {ex}",T["stop"])
        show_toast(f"{len(paths)} plugin(s) added!",T["start"]); _ref_plug()
    _ref_plug()
    plr=ctk.CTkFrame(b,fg_color="transparent"); plr.pack(fill="x",pady=(4,0))
    ctk.CTkButton(plr,text="+ Add Plugin JAR(s)",height=30,corner_radius=6,font=ctk.CTkFont(size=12),
                  fg_color=T["start"],hover_color=T["start"],text_color="#000",command=_add_plug).pack(side="left")
    ctk.CTkButton(plr,text="Refresh",height=30,corner_radius=6,font=ctk.CTkFont(size=12),fg_color="transparent",
                  border_width=1,border_color=T["border"],text_color=T["muted"],hover_color=T["border"],
                  command=_ref_plug).pack(side="left",padx=(8,0))
    ctk.CTkLabel(b,text="Restart the server after adding/removing plugins.",
                 font=ctk.CTkFont(size=10),text_color=T["muted"]).pack(anchor="w",pady=(4,0))

    # ── MC CTRL App Addons ─────────────────────────────────
    b = section("MC CTRL App Addons")
    ctk.CTkLabel(b,text=(
        "Addons are custom Python (.py) scripts anyone can write to extend MC CTRL.\n"
        "They are loaded at startup and can add new UI, commands, or automations."
    ),font=ctk.CTkFont(size=11),text_color=T["muted"],wraplength=560,justify="left").pack(anchor="w",pady=(0,6))
    addon_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)),"addons")
    os.makedirs(addon_dir,exist_ok=True)
    alf=ctk.CTkFrame(b,fg_color=T["bg"],border_color=T["border"],border_width=1,corner_radius=8)
    alf.pack(fill="x",pady=(0,6))
    def _ref_addons():
        for w in alf.winfo_children(): w.destroy()
        try: scripts=sorted([x for x in os.listdir(addon_dir) if x.endswith(".py")])
        except: scripts=[]
        if not scripts:
            ctk.CTkLabel(alf,text="No addons installed. Drop .py files in the addons/ folder.",
                         font=ctk.CTkFont(size=11),text_color=T["muted"]).pack(padx=14,pady=8)
        else:
            for s in scripts:
                ar=ctk.CTkFrame(alf,fg_color="transparent"); ar.pack(fill="x",padx=10,pady=3)
                loaded=s.replace(".py","") in _loaded_addons
                ctk.CTkLabel(ar,text="●",font=ctk.CTkFont(size=11),
                             text_color=T["start"] if loaded else T["muted"]).pack(side="left",padx=(0,6))
                ctk.CTkLabel(ar,text=s,font=ctk.CTkFont(size=12),text_color=T["text"]).pack(side="left")
                ctk.CTkLabel(ar,text="loaded" if loaded else "not loaded",font=ctk.CTkFont(size=10),
                             text_color=T["start"] if loaded else T["muted"]).pack(side="left",padx=8)
                def _rel(n=s): _load_addon(os.path.join(addon_dir,n)); _ref_addons()
                def _rem2(n=s):
                    try:
                        os.remove(os.path.join(addon_dir,n)); _loaded_addons.pop(n.replace(".py",""),None)
                        show_toast(f"Removed {n}",T["stop"]); _ref_addons()
                    except Exception as ex: show_toast(f"Error: {ex}",T["stop"])
                ctk.CTkButton(ar,text="Reload",width=64,height=22,font=ctk.CTkFont(size=10),
                              fg_color="transparent",border_width=1,border_color=T["sync"],
                              text_color=T["sync"],hover_color=T["border"],command=_rel).pack(side="right",padx=(4,0))
                ctk.CTkButton(ar,text="Remove",width=64,height=22,font=ctk.CTkFont(size=10),
                              fg_color="transparent",border_width=1,border_color=T["stop"],
                              text_color=T["stop"],hover_color=T["border"],command=_rem2).pack(side="right")
    def _inst_addon():
        paths=_tk_fd.askopenfilenames(title="Select MC CTRL Addon (.py)",filetypes=[("Python","*.py"),("All","*.*")])
        if not paths: return
        for p in paths:
            dest=os.path.join(addon_dir,os.path.basename(p))
            try: shutil.copy2(p,dest); _load_addon(dest)
            except Exception as ex: show_toast(f"Failed: {ex}",T["stop"])
        show_toast(f"{len(paths)} addon(s) installed!",T["start"]); _ref_addons()
    _ref_addons()
    alr=ctk.CTkFrame(b,fg_color="transparent"); alr.pack(fill="x",pady=(4,0))
    ctk.CTkButton(alr,text="+ Install Addon (.py)",height=30,corner_radius=6,font=ctk.CTkFont(size=12),
                  fg_color=T["sync"],hover_color=T["sync"],text_color="#000",command=_inst_addon).pack(side="left")
    ctk.CTkButton(alr,text="Open Addons Folder",height=30,corner_radius=6,font=ctk.CTkFont(size=12),
                  fg_color="transparent",border_width=1,border_color=T["border"],text_color=T["muted"],
                  hover_color=T["border"],command=lambda:os.startfile(addon_dir)).pack(side="left",padx=(8,0))
    ctk.CTkButton(alr,text="Refresh",height=30,corner_radius=6,font=ctk.CTkFont(size=12),
                  fg_color="transparent",border_width=1,border_color=T["border"],text_color=T["muted"],
                  hover_color=T["border"],command=_ref_addons).pack(side="left",padx=(8,0))
    ctk.CTkLabel(b,text="Addon API: your script's setup(ctx) receives app, T, log, show_toast, send_server_cmd, load_settings.",
                 font=ctk.CTkFont(size=10),text_color=T["muted"],wraplength=560,justify="left").pack(anchor="w",pady=(6,0))

    # About
    b = section("Setup & About")
    def reopen_fn(p):
        ctk.CTkButton(p, text="Re-open First-Launch Setup",
                      font=ctk.CTkFont(size=11), height=28,
                      fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                      command=show_first_launch_dialog).pack(side="right")
    row(b, "Re-read README / change initial settings", reopen_fn)

    ctk.CTkLabel(scroll, text=f"Settings file: {SETTINGS_FILE}",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(4,0))

def _set_upload_on_stop(val):
    global upload_on_stop
    upload_on_stop = val; update_setting("upload_on_stop", val)

# ── Server actions ────────────────────────────────────────
def _check_eula(path):
    """
    Returns True if eula=true is already set.
    Otherwise shows a modal popup explaining the Minecraft EULA and lets the
    user accept or cancel.  If accepted, writes eula.txt and returns True.
    If cancelled, returns False (server will not start).
    """
    eula_path = os.path.join(path, "eula.txt")

    # Already accepted?
    try:
        txt = open(eula_path, encoding="utf-8").read().lower()
        if "eula=true" in txt:
            return True
    except FileNotFoundError:
        pass  # file doesn't exist yet — need to show popup

    # Show the popup on the main thread and block until the user responds
    result = [None]   # shared result between threads

    def _show():
        win = ctk.CTkToplevel(app)
        win.title("Minecraft EULA")
        win.resizable(False, False)
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: None)   # can't close with X

        # Centre over main window
        win.update_idletasks()
        w, h = 500, 390
        try:
            ax = app.winfo_x() + (app.winfo_width()  - w) // 2
            ay = app.winfo_y() + (app.winfo_height() - h) // 2
            win.geometry(f"{w}x{h}+{ax}+{ay}")
        except:
            win.geometry(f"{w}x{h}")

        # ── Icon row ──────────────────────────────────────
        ctk.CTkLabel(win, text="⚠", font=ctk.CTkFont(size=42),
                     text_color=T["handoff"]).pack(pady=(22, 0))

        ctk.CTkLabel(win, text="Minecraft End User Licence Agreement",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=T["text"]).pack(pady=(6, 0))

        # ── Body ──────────────────────────────────────────
        body = ctk.CTkFrame(win, fg_color=T["card"], border_color=T["border"],
                            border_width=1, corner_radius=10)
        body.pack(fill="x", padx=24, pady=14)

        ctk.CTkLabel(body, text=(
            "Before starting your server for the first time, you must\n"
            "agree to the Minecraft End User Licence Agreement (EULA).\n\n"
            "By accepting, you confirm that you have read and agreed to\n"
            "the terms at:\n\n"
            "  https://aka.ms/MinecraftEULA\n\n"
            "Accepting will write  eula=true  to eula.txt in your\n"
            "server folder so Minecraft can start."
        ), font=ctk.CTkFont(size=12), text_color=T["muted"],
           justify="left").pack(padx=18, pady=14)

        # ── Buttons ───────────────────────────────────────
        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=(0, 18))

        def _accept():
            try:
                os.makedirs(path, exist_ok=True)
                with open(eula_path, "w", encoding="utf-8") as f:
                    f.write(
                        "# Accepted via MC CTRL on "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        "# https://aka.ms/MinecraftEULA\n"
                        "eula=true\n"
                    )
                log("  EULA accepted — eula.txt written.")
            except Exception as ex:
                log(f"  EULA write error: {ex}")
            result[0] = True
            win.destroy()

        def _decline():
            result[0] = False
            win.destroy()

        ctk.CTkButton(btn_row, text="I Agree — Accept EULA", width=190, height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"],
                      text_color="#000000",
                      command=_accept).pack(side="left", padx=(0, 12))

        ctk.CTkButton(btn_row, text="Decline", width=100, height=36,
                      font=ctk.CTkFont(size=13),
                      fg_color="transparent", border_width=1,
                      border_color=T["stop"], text_color=T["stop"],
                      hover_color=T["border"],
                      command=_decline).pack(side="left")

        win.wait_window()   # blocks until accepted or declined

    app.after(0, _show)

    # spin-wait for the popup to be dismissed (we're on a daemon thread)
    while result[0] is None:
        time.sleep(0.05)

    return result[0]


def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    s    = load_settings()
    path = s.get("srv_path", SRV_PATH)
    java = s.get("java_path", JAVA_PATH)
    repo = s.get("repo_url", REPO_URL)

    # ── EULA check — must happen before launch ─────────────
    if not _check_eula(path):
        log("  Server start cancelled — EULA not accepted.")
        set_status("Stopped", T["stop"])
        set_all_buttons("normal")
        return

    set_status("Starting...", T["handoff"])
    log("-- Start Server ------------------")
    run_cmd(f"git remote set-url origin {repo}", cwd=path)
    log("Pulling latest world from GitHub...")
    run_cmd("git pull origin main", cwd=path)
    log("Launching server with Aikar flags...")
    java_cmd = (
        f'"{java}" -Xms2G -Xmx2G -XX:+UseG1GC -XX:+ParallelRefProcEnabled '
        '-XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC '
        '-XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M '
        '-XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 '
        '-XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 '
        '-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 '
        '-XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 '
        '-Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true '
        '-jar server.jar nogui'
    )
    server_proc = subprocess.Popen(
        java_cmd, shell=True, cwd=path,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, creationflags=CREATE_NO_WINDOW)
    server_stdin = server_proc.stdin; server_pid = server_proc.pid
    server_start_time = datetime.now()
    server_ready = False; player_count = 0; online_players.clear()
    perf["tps"] = perf["latency"] = "--"; perf["players"] = "0"
    threading.Thread(target=read_server_output, args=(server_proc,), daemon=True).start()
    if not perf_running:
        threading.Thread(target=perf_loop, daemon=True).start()
    set_status("Running", T["start"])
    log(f"Server is running! (PID {server_proc.pid})")
    try: btn_stop.configure(state="normal")
    except: pass

def stop_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready
    set_status("Stopping...", T["handoff"])
    log("-- Stop Server -------------------")
    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except: pass
        server_stdin = None
    r = subprocess.run("taskkill /F /IM java.exe", shell=True, capture_output=True,
                       text=True, creationflags=CREATE_NO_WINDOW)
    log("  Java killed." if r.returncode==0 else "  Java was not running.")
    server_proc = server_pid = server_start_time = None
    server_ready = perf_running = False
    for k in ("tps","latency","players","uptime","ram_srv","cpu_srv","threads"):
        perf[k] = "--"
    if upload_on_stop and backup_upload_on:
        s = load_settings(); path = s.get("srv_path", SRV_PATH)
        log("Pushing world to GitHub...")
        run_cmd("git add world/ world_nether/ world_the_end/", cwd=path)
        commit = subprocess.run(
            f'git commit -m "World update {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
            shell=True, cwd=path, capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW)
        if "nothing to commit" in commit.stdout or commit.returncode != 0:
            log("  World unchanged - nothing to commit.")
        else:
            for line in commit.stdout.strip().splitlines(): log(f"  {line}")
            run_cmd("git push origin main", cwd=path)
            app.after(0, show_toast, "World pushed to GitHub!", T["sync"])
    else:
        log("  Upload on stop disabled - skipping push.")
    set_status("Stopped", T["stop"]); log("Done.")
    set_all_buttons("normal")

def sync_git():
    set_all_buttons("disabled")
    s = load_settings(); path = s.get("srv_path", SRV_PATH); repo = s.get("repo_url", REPO_URL)
    set_status("Syncing...", T["handoff"])
    log("-- Sync & Upload -----------------")
    run_cmd(f"git remote set-url origin {repo}", cwd=path)
    run_cmd("git add .", cwd=path)
    run_cmd('git commit -m "Manual Sync"', cwd=path)
    ok = run_cmd("git push origin main", cwd=path)
    if ok: app.after(0, show_toast, "Manual sync complete!", T["sync"])
    log("Upload complete!" if ok else "Push failed.")
    set_status("Stopped", T["stop"]); set_all_buttons("normal")

# ── Boot ──────────────────────────────────────────────────
# Show a minimal loading screen immediately so the window
# appears instantly, then build the real UI on the next tick.
_splash_frame = ctk.CTkFrame(app, fg_color=T["bg"])
_splash_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
_splash_lbl = ctk.CTkLabel(
    _splash_frame,
    text="MC CTRL",
    font=ctk.CTkFont(size=48, weight="bold"),
    text_color=T["start"])
_splash_lbl.place(relx=0.5, rely=0.38, anchor="center")
_splash_sub = ctk.CTkLabel(
    _splash_frame,
    text="Loading…",
    font=ctk.CTkFont(size=14),
    text_color=T["muted"])
_splash_sub.place(relx=0.5, rely=0.50, anchor="center")
_splash_bar = ctk.CTkProgressBar(_splash_frame, width=260, height=6,
                                  fg_color=T["border"], progress_color=T["start"])
_splash_bar.place(relx=0.5, rely=0.57, anchor="center")
_splash_bar.set(0)
_splash_bar.start()

def _finish_boot():
    global _splash_frame
    _splash_bar.stop()
    build_ui()
    _splash_frame.destroy()
    if auto_upload: schedule_auto_upload()

app.after(50, _finish_boot)

def _splash():
    lines = [
        "",
        "  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗     ",
        "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║     ",
        "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║     ",
        "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║     ",
        "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗",
        "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
        "",
        f"  GamerMahir07's MC CTRL — Minecraft Server Controller",
        f"  Theme: {current_theme_name}  |  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}",
        f"  Auto-upload: {'ON' if auto_upload else 'OFF'}  |  Upload on stop: {'ON' if upload_on_stop else 'OFF'}",
        "",
    ]
    for line in lines: log(line)
    if is_first_launch: app.after(200, show_first_launch_dialog)

app.after(200, _splash)
app.after(800, _load_all_addons)  # load addons after UI is visible
app.mainloop()
