"""
MC CTRL — launcher.pyw  (Redesigned)
Tabs: Dashboard (with Ctrl Mode selector), Server Info (with Backup sub-tab),
      Docker, Modpacks, Multi-CTRL.
Settings window: Addons, paths, appearance, auto-upload.
Ctrl Modes: Dashboard | MC Ctrl | Network | playit.gg | Remote
"""

import time, shutil, threading, json, os, re, sys, urllib.request, urllib.error
import importlib.util, subprocess
import tkinter as tk
import tkinter.filedialog as _tk_fd
import customtkinter as ctk
from datetime import datetime

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# ── Platform ──────────────────────────────────────────────
IS_WIN  = sys.platform == "win32"
IS_MAC  = sys.platform == "darwin"
IS_LIN  = sys.platform.startswith("linux")

if IS_WIN:
    import ctypes
    _NO_WIN = 0x08000000
else:
    _NO_WIN = 0

def _popen_flags(): return _NO_WIN if IS_WIN else 0

def _kill_java():
    if IS_WIN:
        return subprocess.run("taskkill /F /IM java.exe", shell=True,
                              capture_output=True, text=True, creationflags=_NO_WIN)
    return subprocess.run("pkill -f 'server.jar'", shell=True, capture_output=True, text=True)

def _open_folder(path):
    try:
        if IS_WIN:   os.startfile(path)
        elif IS_MAC: subprocess.Popen(["open", path])
        else:        subprocess.Popen(["xdg-open", path])
    except Exception: pass

def _set_win_icon(win, ico):
    try:
        if IS_WIN: win.iconbitmap(ico)
        else:
            png = ico.replace(".ico", ".png")
            if os.path.exists(png):
                img = tk.PhotoImage(file=png); win.iconphoto(True, img)
    except Exception: pass

def _set_taskbar_id():
    try:
        if IS_WIN:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "gamermahir07.mcserver.launcher.1")
    except Exception: pass

_DEFAULT_JAVA = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe" if IS_WIN else "java"
_DEFAULT_SRV  = r"C:\Users\DigitalComputer\Desktop\mc" if IS_WIN else os.path.expanduser("~/minecraft-server")
REPO_URL      = "https://github.com/GamerMahir07/minecraft-server.git"
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# ── Settings ──────────────────────────────────────────────
_settings_cache = None
_settings_lock  = threading.Lock()

def load_settings():
    global _settings_cache
    with _settings_lock:
        if _settings_cache is not None: return dict(_settings_cache)
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f: _settings_cache = json.load(f)
        except Exception: _settings_cache = {}
        return dict(_settings_cache)

def save_settings(data):
    global _settings_cache
    with _settings_lock: _settings_cache = dict(data)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
    except Exception: pass

def update_setting(key, value):
    global _settings_cache
    with _settings_lock:
        if _settings_cache is None: _settings_cache = {}
        _settings_cache[key] = value
    def _w():
        try:
            with _settings_lock: snap = dict(_settings_cache)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(snap, f, indent=2)
        except Exception: pass
    threading.Thread(target=_w, daemon=True).start()

# ── Themes ────────────────────────────────────────────────
THEMES = {
    'Dark (Default)': {"a":'dark',"bg":'#0d0d0d',"card":'#1a1a1a',"border":'#2a2a2a',"text":'#e0e0e0',"muted":'#555555',"start":'#22c55e',"stop":'#ef4444',"sync":'#60a5fa',"hand":'#f59e0b'},
    'Light (Default)': {"a":'light',"bg":'#f5f5f5',"card":'#ffffff',"border":'#e0e0e0',"text":'#1a1a1a',"muted":'#888888',"start":'#16a34a',"stop":'#dc2626',"sync":'#2563eb',"hand":'#d97706'},
    'Midnight Blue Dark': {"a":'dark',"bg":'#0a0f1e',"card":'#111827',"border":'#1e3a5f',"text":'#e2e8f0',"muted":'#4a6080',"start":'#34d399',"stop":'#f87171',"sync":'#818cf8',"hand":'#fbbf24'},
    'Midnight Blue Light': {"a":'light',"bg":'#e8eeff',"card":'#ffffff',"border":'#7a9fd4',"text":'#0a0f2e',"muted":'#5570a0',"start":'#059669',"stop":'#dc2626',"sync":'#4f46e5',"hand":'#d97706'},
    'Creeper Green Dark': {"a":'dark',"bg":'#0a1a0a',"card":'#0f2a0f',"border":'#1a4a1a',"text":'#c8f0c8',"muted":'#3a6a3a',"start":'#4ade80',"stop":'#f87171',"sync":'#86efac',"hand":'#fde047'},
    'Creeper Green Light': {"a":'light',"bg":'#f0fff0',"card":'#ffffff',"border":'#86efac',"text":'#052e16',"muted":'#3a7a3a',"start":'#16a34a',"stop":'#dc2626',"sync":'#059669',"hand":'#ca8a04'},
    'Nether Red Dark': {"a":'dark',"bg":'#000000',"card":'#1a0000',"border":'#6a0000',"text":'#ff4444',"muted":'#8b0000',"start":'#ff6b6b',"stop":'#ff0000',"sync":'#ff8c8c',"hand":'#ffd700'},
    'Nether Red Light': {"a":'light',"bg":'#fff5f5',"card":'#ffffff',"border":'#fca5a5',"text":'#3a0000',"muted":'#b06060',"start":'#b91c1c',"stop":'#7f1d1d',"sync":'#dc2626',"hand":'#c2410c'},
    'Ocean Dark': {"a":'dark',"bg":'#01131e',"card":'#021f30',"border":'#0e4a6e',"text":'#bae6fd',"muted":'#2a6a8a',"start":'#22d3ee',"stop":'#f87171',"sync":'#38bdf8',"hand":'#fbbf24'},
    'Ocean Light': {"a":'light',"bg":'#e0f7ff',"card":'#ffffff',"border":'#7dd3f0',"text":'#003a52',"muted":'#4a8fa8',"start":'#0284c7',"stop":'#e11d48',"sync":'#0ea5e9',"hand":'#f59e0b'},
    'Sunset Dark': {"a":'dark',"bg":'#1a0a00',"card":'#2a1200',"border":'#7c3a10',"text":'#ffe4c4',"muted":'#8a5030',"start":'#4ade80',"stop":'#f87171',"sync":'#c084fc',"hand":'#fb923c'},
    'Sunset Light': {"a":'light',"bg":'#fff7ed',"card":'#ffffff',"border":'#fed7aa',"text":'#1c0a00',"muted":'#9a6030',"start":'#16a34a',"stop":'#e11d48',"sync":'#7c3aed',"hand":'#ea580c'},
    'Obsidian Dark': {"a":'dark',"bg":'#020202',"card":'#070710',"border":'#13132a',"text":'#cdd6f4',"muted":'#3a3a52',"start":'#a6e3a1',"stop":'#f38ba8',"sync":'#89b4fa',"hand":'#fab387'},
    'Obsidian Light': {"a":'light',"bg":'#f0f0f8',"card":'#ffffff',"border":'#c5c5e0',"text":'#1e1e2e',"muted":'#6e7090',"start":'#40a02b',"stop":'#d20f39',"sync":'#1e66f5',"hand":'#e49320'},
    'Ender Night Dark': {"a":'dark',"bg":'#000000',"card":'#0d0010',"border":'#3b0060',"text":'#e8b4ff',"muted":'#6a2a8a',"start":'#bf7fff',"stop":'#ff5f87',"sync":'#d68fff',"hand":'#ffb347'},
    'Ender Night Light': {"a":'light',"bg":'#f8f0ff',"card":'#ffffff',"border":'#d4b0ff',"text":'#200040',"muted":'#7a40a0',"start":'#7c3aed',"stop":'#db2777',"sync":'#6d28d9',"hand":'#c2410c'},
    'Arctic Light': {"a":'light',"bg":'#eef4fb',"card":'#ffffff',"border":'#b8d4f0',"text":'#0d2137',"muted":'#6a90b0',"start":'#0ea5e9',"stop":'#e11d48',"sync":'#6366f1',"hand":'#f59e0b'},
    'Arctic Dark': {"a":'dark',"bg":'#071520',"card":'#0d2035',"border":'#1a4060',"text":'#dbeafe',"muted":'#3a6080',"start":'#38bdf8',"stop":'#f87171',"sync":'#818cf8',"hand":'#fbbf24'},
    'Forest Dark': {"a":'dark',"bg":'#0d1a0d',"card":'#142414',"border":'#254025',"text":'#d4edda',"muted":'#4a7a4a',"start":'#86efac',"stop":'#fca5a5',"sync":'#6ee7b7',"hand":'#fde68a'},
    'Forest Light': {"a":'light',"bg":'#f0faf0',"card":'#ffffff',"border":'#a7d7a7',"text":'#0a2010',"muted":'#4a7a4a',"start":'#16a34a',"stop":'#dc2626',"sync":'#0d9488',"hand":'#ca8a04'},
    'Rose Gold Dark': {"a":'dark',"bg":'#1a0008',"card":'#2a0010',"border":'#7a2040',"text":'#ffd6e0',"muted":'#8a4060',"start":'#fb7185',"stop":'#f43f5e',"sync":'#f472b6',"hand":'#fb923c'},
    'Rose Gold Light': {"a":'light',"bg":'#fff0f3',"card":'#ffffff',"border":'#f4c2cb',"text":'#3a0a14',"muted":'#b06070',"start":'#e11d48',"stop":'#9f1239',"sync":'#db2777',"hand":'#c2410c'},
    'Dracula Dark': {"a":'dark',"bg":'#282a36',"card":'#313442',"border":'#44475a',"text":'#f8f8f2',"muted":'#6272a4',"start":'#50fa7b',"stop":'#ff5555',"sync":'#8be9fd',"hand":'#ffb86c'},
    'Dracula Light': {"a":'light',"bg":'#f8f8f5',"card":'#ffffff',"border":'#bdbdcc',"text":'#282a36',"muted":'#6272a4',"start":'#2da44e',"stop":'#d0333e',"sync":'#0087cc',"hand":'#c47900'},
    'Lava Dark': {"a":'dark',"bg":'#120500',"card":'#1e0a00',"border":'#5a1a00',"text":'#ffe8d0',"muted":'#7a3a10',"start":'#ff7c00',"stop":'#ff3300',"sync":'#ffaa00',"hand":'#ffdd00'},
    'Lava Light': {"a":'light',"bg":'#fff8f0',"card":'#ffffff',"border":'#ffc080',"text":'#2a0a00',"muted":'#a05020',"start":'#c2410c',"stop":'#b91c1c',"sync":'#ea580c',"hand":'#b45309'},
    'Sand Light': {"a":'light',"bg":'#f5e6c8',"card":'#fdf3e0',"border":'#c8a96e',"text":'#3d2b00',"muted":'#8a6a30',"start":'#5a8a00',"stop":'#c0392b',"sync":'#1a6b8a',"hand":'#c07000'},
    'Sand Dark': {"a":'dark',"bg":'#1a1200',"card":'#2a1e00',"border":'#7a5a20',"text":'#f0dcb0',"muted":'#7a6030',"start":'#a0c040',"stop":'#e05030',"sync":'#40a0c0',"hand":'#e0a000'},
    'Void Dark': {"a":'dark',"bg":'#000000',"card":'#0a0a0a',"border":'#1a1a1a',"text":'#aaaaaa',"muted":'#333333',"start":'#444444',"stop":'#666666',"sync":'#555555',"hand":'#777777'},
    'Void Light': {"a":'light',"bg":'#f0f0f0',"card":'#ffffff',"border":'#cccccc',"text":'#222222',"muted":'#999999',"start":'#444444',"stop":'#888888',"sync":'#666666',"hand":'#777777'},
    'Carbon Dark': {"a":'dark',"bg":'#1a1a2e',"card":'#16213e',"border":'#0f3460',"text":'#e0e0e0',"muted":'#4a4a6a',"start":'#00c896',"stop":'#e94560',"sync":'#4d9fff',"hand":'#f5a623'},
    'Carbon Light': {"a":'light',"bg":'#eef0ff',"card":'#ffffff',"border":'#8090cc',"text":'#0a0a20',"muted":'#5060a0',"start":'#009966',"stop":'#cc2244',"sync":'#2266cc',"hand":'#c07000'},
    'Lavender Light': {"a":'light',"bg":'#f0eeff',"card":'#ffffff',"border":'#c5b8ff',"text":'#1a0050',"muted":'#7060a0',"start":'#5b21b6',"stop":'#db2777',"sync":'#4f46e5',"hand":'#d97706'},
    'Lavender Dark': {"a":'dark',"bg":'#0f0820',"card":'#1a1035',"border":'#3d2a7a',"text":'#e8dfff',"muted":'#6050a0',"start":'#a78bfa',"stop":'#f472b6',"sync":'#818cf8',"hand":'#fbbf24'},
    'Mocha Dark': {"a":'dark',"bg":'#1c1410',"card":'#2a1f18',"border":'#4a3428',"text":'#f0dece',"muted":'#7a5a48',"start":'#c8a86e',"stop":'#e05050',"sync":'#90b8d0',"hand":'#e8c060'},
    'Mocha Light': {"a":'light',"bg":'#fdf6ee',"card":'#ffffff',"border":'#d4b896',"text":'#2a1a0a',"muted":'#9a7a60',"start":'#7a5a28',"stop":'#c0392b',"sync":'#2a6080',"hand":'#c07020'},
    'Sakura Light': {"a":'light',"bg":'#fff0f5',"card":'#ffffff',"border":'#ffb8cc',"text":'#3a0020',"muted":'#c06080',"start":'#be185d',"stop":'#e11d48',"sync":'#9d174d',"hand":'#f59e0b'},
    'Sakura Dark': {"a":'dark',"bg":'#1a0010',"card":'#2a0018',"border":'#7a2050',"text":'#ffd6e8',"muted":'#8a4068',"start":'#f472b6',"stop":'#fb7185',"sync":'#e879f9',"hand":'#fbbf24'},
    'Matrix Dark': {"a":'dark',"bg":'#000000',"card":'#001400',"border":'#004400',"text":'#00ff41',"muted":'#006600',"start":'#00ff41',"stop":'#ff0000',"sync":'#00cc33',"hand":'#ffff00'},
    'Matrix Light': {"a":'light',"bg":'#f0fff0',"card":'#ffffff',"border":'#80cc80',"text":'#002200',"muted":'#408040',"start":'#166534',"stop":'#b91c1c',"sync":'#14532d',"hand":'#713f12'},
    'Nord Dark': {"a":'dark',"bg":'#2e3440',"card":'#3b4252',"border":'#434c5e',"text":'#eceff4',"muted":'#4c566a',"start":'#a3be8c',"stop":'#bf616a',"sync":'#88c0d0',"hand":'#ebcb8b'},
    'Nord Light': {"a":'light',"bg":'#eceff4',"card":'#ffffff',"border":'#d8dee9',"text":'#2e3440',"muted":'#7a8898',"start":'#4c9a2a',"stop":'#bf616a',"sync":'#5e81ac',"hand":'#d08770'},
    'Solarized Light': {"a":'light',"bg":'#fdf6e3',"card":'#eee8d5',"border":'#93a1a1',"text":'#073642',"muted":'#657b83',"start":'#859900',"stop":'#dc322f',"sync":'#268bd2',"hand":'#b58900'},
    'Solarized Dark': {"a":'dark',"bg":'#002b36',"card":'#073642',"border":'#586e75',"text":'#fdf6e3',"muted":'#839496',"start":'#859900',"stop":'#dc322f',"sync":'#268bd2',"hand":'#b58900'},
    'Gruvbox Dark': {"a":'dark',"bg":'#282828',"card":'#3c3836',"border":'#504945',"text":'#ebdbb2',"muted":'#7c6f64',"start":'#b8bb26',"stop":'#fb4934',"sync":'#83a598',"hand":'#fabd2f'},
    'Gruvbox Light': {"a":'light',"bg":'#fbf1c7',"card":'#f9f5d7',"border":'#d5c4a1',"text":'#3c3836',"muted":'#928374',"start":'#79740e',"stop":'#9d0006',"sync":'#076678',"hand":'#b57614'},
    'Cyberpunk Dark': {"a":'dark',"bg":'#0a0014',"card":'#110022',"border":'#ff00ff',"text":'#00ffff',"muted":'#8800aa',"start":'#00ffff',"stop":'#ff0088',"sync":'#ff00ff',"hand":'#ffff00'},
    'Cyberpunk Light': {"a":'light',"bg":'#f0e8ff',"card":'#ffffff',"border":'#cc44ff',"text":'#1a0030',"muted":'#8840aa',"start":'#0088cc',"stop":'#cc0066',"sync":'#8800ff',"hand":'#cc8800'},
    'Slate Dark': {"a":'dark',"bg":'#0f172a',"card":'#1e293b',"border":'#334155',"text":'#f1f5f9',"muted":'#64748b',"start":'#22d3ee',"stop":'#f43f5e',"sync":'#818cf8',"hand":'#fb923c'},
    'Slate Light': {"a":'light',"bg":'#f1f5f9',"card":'#ffffff',"border":'#cbd5e1',"text":'#0f172a',"muted":'#64748b',"start":'#0891b2',"stop":'#e11d48',"sync":'#4f46e5',"hand":'#ea580c'},
    'Amber Dark': {"a":'dark',"bg":'#1a1000',"card":'#2a1a00',"border":'#7a5500',"text":'#ffe88a',"muted":'#7a6020',"start":'#fbbf24',"stop":'#ef4444',"sync":'#f59e0b',"hand":'#84cc16'},
    'Amber Light': {"a":'light',"bg":'#fffbeb',"card":'#ffffff',"border":'#fde68a',"text":'#1c1400',"muted":'#9a7a00',"start":'#b45309',"stop":'#dc2626',"sync":'#d97706',"hand":'#65a30d'},
    'Copper Dark': {"a":'dark',"bg":'#150900',"card":'#221200',"border":'#7a3a10',"text":'#ffcc99',"muted":'#7a4a20',"start":'#f97316',"stop":'#ef4444',"sync":'#fb923c',"hand":'#fbbf24'},
    'Copper Light': {"a":'light',"bg":'#fff8f0',"card":'#ffffff',"border":'#e0a060',"text":'#1a0800',"muted":'#a06030',"start":'#c2410c',"stop":'#b91c1c',"sync":'#d97706',"hand":'#65a30d'},
    'CB: Blue & Orange Light': {"a":'light',"bg":'#f7f7f7',"card":'#ffffff',"border":'#cccccc',"text":'#000000',"muted":'#767676',"start":'#0072b2',"stop":'#d55e00',"sync":'#56b4e9',"hand":'#e69f00'},
    'CB: Blue & Orange Dark': {"a":'dark',"bg":'#111111',"card":'#1e1e1e',"border":'#333333',"text":'#ffffff',"muted":'#888888',"start":'#56b4e9',"stop":'#d55e00',"sync":'#0072b2',"hand":'#e69f00'},
    'CB: Green & Purple Light': {"a":'light',"bg":'#f5f5f5',"card":'#ffffff',"border":'#cccccc',"text":'#000000',"muted":'#767676',"start":'#009e73',"stop":'#cc79a7',"sync":'#0072b2',"hand":'#f0e442'},
    'CB: Green & Purple Dark': {"a":'dark',"bg":'#111111',"card":'#1e1e1e',"border":'#333333',"text":'#eeeeee',"muted":'#888888',"start":'#009e73',"stop":'#cc79a7',"sync":'#56b4e9',"hand":'#f0e442'},
    'CB: High Contrast Light': {"a":'light',"bg":'#ffffff',"card":'#f0f0f0',"border":'#000000',"text":'#000000',"muted":'#444444',"start":'#0000ff',"stop":'#ff0000',"sync":'#007700',"hand":'#ff8800'},
    'CB: High Contrast Dark': {"a":'dark',"bg":'#000000',"card":'#1a1a1a',"border":'#ffffff',"text":'#ffffff',"muted":'#aaaaaa',"start":'#ffff00',"stop":'#ff6600',"sync":'#00ffff',"hand":'#ff99ff'},
    'CB: Tol Muted Light': {"a":'light',"bg":'#f8f4f0',"card":'#ffffff',"border":'#bbaabb',"text":'#221122',"muted":'#887799',"start":'#44aa99',"stop":'#cc6677',"sync":'#88ccee',"hand":'#ddcc77'},
    'CB: Tol Muted Dark': {"a":'dark',"bg":'#221122',"card":'#332244',"border":'#554466',"text":'#eeddff',"muted":'#887799',"start":'#44aa99',"stop":'#cc6677',"sync":'#88ccee',"hand":'#ddcc77'},
    'CB: Monochrome Light': {"a":'light',"bg":'#ffffff',"card":'#f0f0f0',"border":'#999999',"text":'#000000',"muted":'#666666',"start":'#222222',"stop":'#777777',"sync":'#444444',"hand":'#555555'},
    'CB: Monochrome Dark': {"a":'dark',"bg":'#111111',"card":'#1e1e1e',"border":'#555555',"text":'#eeeeee',"muted":'#888888',"start":'#cccccc',"stop":'#888888',"sync":'#aaaaaa',"hand":'#bbbbbb'},
    'Pastel Light': {"a":'light',"bg":'#fdf4ff',"card":'#ffffff',"border":'#e9d5ff',"text":'#3b0764',"muted":'#a78bca',"start":'#7c3aed',"stop":'#e11d48',"sync":'#2563eb',"hand":'#d97706'},
    'Pastel Dark': {"a":'dark',"bg":'#1a0a2e',"card":'#2d1b4e',"border":'#5b3a8a',"text":'#e9d5ff',"muted":'#9d7ac0',"start":'#a78bfa',"stop":'#fb7185',"sync":'#60a5fa',"hand":'#fbbf24'},
    'Teal Light': {"a":'light',"bg":'#eefffe',"card":'#ffffff',"border":'#80d8d0',"text":'#002420',"muted":'#4a9a90',"start":'#007a70',"stop":'#cc2244',"sync":'#0066aa',"hand":'#cc8800'},
    'Teal Dark': {"a":'dark',"bg":'#00100e',"card":'#001a18',"border":'#00524a',"text":'#a0fff5',"muted":'#2a7a72',"start":'#00d4c0',"stop":'#ff4466',"sync":'#00aaff',"hand":'#ffcc00'},
    'Peach Light': {"a":'light',"bg":'#fff8f5',"card":'#ffffff',"border":'#fed7aa',"text":'#431407',"muted":'#c47c5a',"start":'#c2410c',"stop":'#be123c',"sync":'#9333ea',"hand":'#ca8a04'},
    'Peach Dark': {"a":'dark',"bg":'#180a00',"card":'#2c1200',"border":'#7c2d12',"text":'#ffedd5',"muted":'#c47c5a',"start":'#fb923c',"stop":'#f43f5e',"sync":'#c084fc',"hand":'#fbbf24'},
    'Sky Light': {"a":'light',"bg":'#f0f9ff',"card":'#ffffff',"border":'#bae6fd',"text":'#0c4a6e',"muted":'#7dd3fc',"start":'#0284c7',"stop":'#e11d48',"sync":'#7c3aed',"hand":'#d97706'},
    'Sky Dark': {"a":'dark',"bg":'#020d18',"card":'#082032',"border":'#0c4a6e',"text":'#e0f2fe',"muted":'#38bdf8',"start":'#38bdf8',"stop":'#f87171',"sync":'#a78bfa',"hand":'#fbbf24'},
    'Lilac Light': {"a":'light',"bg":'#faf5ff',"card":'#ffffff',"border":'#e9d5ff',"text":'#3b0764',"muted":'#c4b5fd',"start":'#7c3aed',"stop":'#db2777',"sync":'#0284c7',"hand":'#d97706'},
    'Lilac Dark': {"a":'dark',"bg":'#120820',"card":'#1e1035',"border":'#4c1d95',"text":'#ede9fe',"muted":'#a78bfa',"start":'#c4b5fd',"stop":'#f472b6',"sync":'#60a5fa',"hand":'#fbbf24'},
    'Honey Light': {"a":'light',"bg":'#fffbeb',"card":'#ffffff',"border":'#fde68a',"text":'#1c1400',"muted":'#d9a22e',"start":'#d97706',"stop":'#dc2626',"sync":'#0284c7',"hand":'#65a30d'},
    'Honey Dark': {"a":'dark',"bg":'#160e00',"card":'#241800',"border":'#92400e',"text":'#fef3c7',"muted":'#d97706',"start":'#fbbf24',"stop":'#f87171',"sync":'#38bdf8',"hand":'#86efac'},
    'Ruby Light': {"a":'light',"bg":'#fff1f2',"card":'#ffffff',"border":'#fecdd3',"text":'#4c0519',"muted":'#fb7185',"start":'#be123c',"stop":'#dc2626',"sync":'#0284c7',"hand":'#d97706'},
    'Ruby Dark': {"a":'dark',"bg":'#1a0008',"card":'#2d000f',"border":'#881337',"text":'#ffe4e6',"muted":'#fb7185',"start":'#fb7185',"stop":'#ef4444',"sync":'#38bdf8',"hand":'#fbbf24'},
    'Jade Light': {"a":'light',"bg":'#f0fdf4',"card":'#ffffff',"border":'#bbf7d0',"text":'#052e16',"muted":'#6ee7b7',"start":'#059669',"stop":'#dc2626',"sync":'#0284c7',"hand":'#d97706'},
    'Jade Dark': {"a":'dark',"bg":'#011810',"card":'#022c1e',"border":'#065f46',"text":'#d1fae5',"muted":'#34d399',"start":'#34d399',"stop":'#f87171',"sync":'#38bdf8',"hand":'#fbbf24'},
    'Dusk Dark': {"a":'dark',"bg":'#0a0014',"card":'#130022',"border":'#38006b',"text":'#e8d5ff',"muted":'#9d74cc',"start":'#c084fc',"stop":'#f472b6',"sync":'#818cf8',"hand":'#fb923c'},
    'Dusk Light': {"a":'light',"bg":'#f9f0ff',"card":'#ffffff',"border":'#d8b4fe',"text":'#1e0050',"muted":'#9d74cc',"start":'#7c3aed',"stop":'#be185d',"sync":'#4f46e5',"hand":'#d97706'},
    'Espresso Dark': {"a":'dark',"bg":'#100800',"card":'#1a1000',"border":'#3d2000',"text":'#f5e6c8',"muted":'#7a5a30',"start":'#d4a96e',"stop":'#e05050',"sync":'#7eb8d0',"hand":'#e8c060'},
    'Espresso Light': {"a":'light',"bg":'#fdf8f0',"card":'#fff9f2',"border":'#d4b896',"text":'#1c0e00',"muted":'#8a6a40',"start":'#92400e',"stop":'#b91c1c',"sync":'#0369a1',"hand":'#b45309'},
    'Steel Light': {"a":'light',"bg":'#f8fafc',"card":'#ffffff',"border":'#cbd5e1',"text":'#0f172a',"muted":'#94a3b8',"start":'#0284c7',"stop":'#e11d48',"sync":'#7c3aed',"hand":'#d97706'},
    'Steel Dark': {"a":'dark',"bg":'#0d1117',"card":'#161b22',"border":'#30363d',"text":'#e6edf3',"muted":'#8b949e',"start":'#3fb950',"stop":'#f85149',"sync":'#58a6ff',"hand":'#d29922'},
    'Cherry Blossom Light': {"a":'light',"bg":'#fff8fa',"card":'#ffffff',"border":'#fecdd3',"text":'#3d0015',"muted":'#f9a8d4',"start":'#e11d48',"stop":'#be123c',"sync":'#db2777',"hand":'#f59e0b'},
    'Cherry Blossom Dark': {"a":'dark',"bg":'#1a0010',"card":'#2d0018',"border":'#9f1239',"text":'#ffe4e6',"muted":'#fda4af',"start":'#fb7185',"stop":'#f43f5e',"sync":'#e879f9',"hand":'#fbbf24'},
    'Glacier Light': {"a":'light',"bg":'#f0fdff',"card":'#ffffff',"border":'#a5f3fc',"text":'#083344',"muted":'#67e8f9',"start":'#0891b2',"stop":'#e11d48',"sync":'#6366f1',"hand":'#f59e0b'},
    'Glacier Dark': {"a":'dark',"bg":'#001a22',"card":'#002e3a',"border":'#164e63',"text":'#cffafe',"muted":'#22d3ee',"start":'#22d3ee',"stop":'#f87171',"sync":'#818cf8',"hand":'#fbbf24'},
    'Tangerine Light': {"a":'light',"bg":'#fff7ed',"card":'#ffffff',"border":'#fed7aa',"text":'#1c0a00',"muted":'#fb923c',"start":'#ea580c',"stop":'#dc2626',"sync":'#0284c7',"hand":'#65a30d'},
    'Tangerine Dark': {"a":'dark',"bg":'#1a0800',"card":'#2c1200',"border":'#c2410c',"text":'#ffedd5',"muted":'#fb923c',"start":'#fb923c',"stop":'#ef4444',"sync":'#38bdf8',"hand":'#86efac'},
    'Parchment Light': {"a":'light',"bg":'#fdf8ee',"card":'#fef9f0',"border":'#d6c89a',"text":'#2a1e00',"muted":'#a08840',"start":'#7a5a00',"stop":'#b91c1c',"sync":'#0369a1',"hand":'#b45309'},
    'Parchment Dark': {"a":'dark',"bg":'#15100a',"card":'#201a10',"border":'#5a4820',"text":'#f0e4c0',"muted":'#8a7040',"start":'#d4aa60',"stop":'#e05050',"sync":'#70a8c0',"hand":'#d4aa30'},
    'Volcanic Dark': {"a":'dark',"bg":'#0a0000',"card":'#160000',"border":'#7f1d1d',"text":'#fecaca',"muted":'#991b1b',"start":'#ef4444',"stop":'#f97316',"sync":'#fbbf24',"hand":'#a3e635'},
    'Volcanic Light': {"a":'light',"bg":'#fff5f5',"card":'#ffffff',"border":'#fca5a5',"text":'#1a0000',"muted":'#ef4444',"start":'#dc2626',"stop":'#c2410c',"sync":'#d97706',"hand":'#65a30d'},
    'Deep Sea Dark': {"a":'dark',"bg":'#000d1a',"card":'#001a33',"border":'#003366',"text":'#b3d9ff',"muted":'#336699',"start":'#0066cc',"stop":'#cc0033',"sync":'#00aacc',"hand":'#ffaa00'},
    'Deep Sea Light': {"a":'light',"bg":'#e8f4ff',"card":'#ffffff',"border":'#99c9f5',"text":'#001433',"muted":'#6699cc',"start":'#0066cc',"stop":'#cc0033',"sync":'#0099bb',"hand":'#cc8800'},
    'Bubblegum Light': {"a":'light',"bg":'#fff0fa',"card":'#ffffff',"border":'#f9a8d4',"text":'#2d0025',"muted":'#f472b6',"start":'#ec4899',"stop":'#e11d48',"sync":'#8b5cf6',"hand":'#f59e0b'},
    'Bubblegum Dark': {"a":'dark',"bg":'#1a0016',"card":'#2d0026',"border":'#9d174d',"text":'#fce7f3',"muted":'#f472b6',"start":'#f472b6',"stop":'#fb7185',"sync":'#c084fc',"hand":'#fbbf24'},
    'programmer Green Dark': {"a":'dark',"bg":'#000000',"card":'#000d00',"border":'#003b00',"text":'#b4ffb4',"muted":'#2a6a2a',"start":'#7fff7f',"stop":'#ff5f87',"sync":'#7dff8f',"hand":'#ffb347'},
    'programmer Green Light': {"a":'light',"bg":'#f0fff0',"card":'#ffffff',"border":'#b0d4b0',"text":'#002000',"muted":'#408040',"start":'#276327',"stop":'#db2777',"sync":'#2d7a2d',"hand":'#c2410c'},
    'Midnight Purple Dark': {"a":'dark',"bg":'#05000f',"card":'#0d0020',"border":'#4c1d95',"text":'#ede9fe',"muted":'#7c3aed',"start":'#a78bfa',"stop":'#f472b6',"sync":'#818cf8',"hand":'#fbbf24'},
    'Midnight Purple Light': {"a":'light',"bg":'#faf5ff',"card":'#ffffff',"border":'#c4b5fd',"text":'#1e0050',"muted":'#7c3aed',"start":'#6d28d9',"stop":'#be185d',"sync":'#4f46e5',"hand":'#d97706'},
    'Cinnamon Light': {"a":'light',"bg":'#fdf5ee',"card":'#ffffff',"border":'#d4a57a',"text":'#2a1200',"muted":'#a0622a',"start":'#9a3412',"stop":'#b91c1c',"sync":'#0369a1',"hand":'#b45309'},
    'Cinnamon Dark': {"a":'dark',"bg":'#180900',"card":'#281400',"border":'#92400e',"text":'#fde8d0',"muted":'#c47c4a',"start":'#f97316',"stop":'#ef4444',"sync":'#38bdf8',"hand":'#fbbf24'},
    'Petal Light': {"a":'light',"bg":'#fef9ff',"card":'#ffffff',"border":'#f0abfc',"text":'#3b0764',"muted":'#e879f9',"start":'#a21caf',"stop":'#e11d48',"sync":'#7c3aed',"hand":'#d97706'},
    'Petal Dark': {"a":'dark',"bg":'#1a0020',"card":'#2a0035',"border":'#701a75',"text":'#fae8ff',"muted":'#e879f9',"start":'#d946ef',"stop":'#f43f5e',"sync":'#818cf8',"hand":'#fbbf24'},
    'Golden Hour Light': {"a":'light',"bg":'#fffbf0',"card":'#ffffff',"border":'#fde68a',"text":'#1c1200',"muted":'#d9a520',"start":'#b45309',"stop":'#dc2626',"sync":'#7c3aed',"hand":'#65a30d'},
    'Golden Hour Dark': {"a":'dark',"bg":'#130e00',"card":'#201600',"border":'#854d0e',"text":'#fefce8',"muted":'#d97706',"start":'#eab308',"stop":'#f87171',"sync":'#c084fc',"hand":'#86efac'},
    'Neon Nights Dark': {"a":'dark',"bg":'#050010',"card":'#0d0020',"border":'#330066',"text":'#e8d0ff',"muted":'#6600cc',"start":'#cc00ff',"stop":'#ff0066',"sync":'#00ffcc',"hand":'#ffcc00'},
    'Neon Nights Light': {"a":'light',"bg":'#f5f0ff',"card":'#ffffff',"border":'#cc99ff',"text":'#1a0040',"muted":'#8844cc',"start":'#7c00cc',"stop":'#cc0055',"sync":'#008866',"hand":'#997700'},
    'Tundra Light': {"a":'light',"bg":'#f5f8fa',"card":'#ffffff',"border":'#b0c4cc',"text":'#1a2530',"muted":'#7a9aaa',"start":'#1d6a8a',"stop":'#c0392b',"sync":'#2c7a4b',"hand":'#c07a00'},
    'Tundra Dark': {"a":'dark',"bg":'#0a1218',"card":'#111e26',"border":'#1e3a4a',"text":'#d4e8f0',"muted":'#4a7a8a',"start":'#4ab8d8',"stop":'#e05060',"sync":'#4ac880',"hand":'#e8c050'},
    'Autumn Light': {"a":'light',"bg":'#fdf7f0',"card":'#ffffff',"border":'#d4a87a',"text":'#2a1400',"muted":'#a07040',"start":'#c05010',"stop":'#c0392b',"sync":'#2c6080',"hand":'#c08020'},
    'Autumn Dark': {"a":'dark',"bg":'#180a00',"card":'#281400',"border":'#8b4513',"text":'#ffecd0',"muted":'#b06030',"start":'#e07030',"stop":'#e05050',"sync":'#50a0c0',"hand":'#e0b020'},
    'Abyss Dark': {"a":'dark',"bg":'#000408',"card":'#00080f',"border":'#001a33',"text":'#80c8ff',"muted":'#004488',"start":'#0080ff',"stop":'#ff2244',"sync":'#00ccaa',"hand":'#ffaa00'},
    'Abyss Light': {"a":'light',"bg":'#f0f8ff',"card":'#ffffff',"border":'#80b8e8',"text":'#000810',"muted":'#4488bb',"start":'#0066cc',"stop":'#cc2233',"sync":'#008877',"hand":'#bb8800'},
    'Hazel Light': {"a":'light',"bg":'#faf8f5',"card":'#ffffff',"border":'#c8b89a',"text":'#2a2015',"muted":'#8a7a60',"start":'#5a4020',"stop":'#b91c1c',"sync":'#1d4ed8',"hand":'#b45309'},
    'Hazel Dark': {"a":'dark',"bg":'#141008',"card":'#1e1810',"border":'#5a4830',"text":'#ecdcc8',"muted":'#8a7050',"start":'#d0a870',"stop":'#e05050',"sync":'#60a0d0',"hand":'#d8b040'},
    'Deep Space Dark': {"a":'dark',"bg":'#00000a',"card":'#00000f',"border":'#0a0a2a',"text":'#c8c8ff',"muted":'#4444aa',"start":'#6688ff',"stop":'#ff4466',"sync":'#44ddff',"hand":'#ffcc44'},
    'Deep Space Light': {"a":'light',"bg":'#f0f0ff',"card":'#ffffff',"border":'#9090cc',"text":'#00001a',"muted":'#5555aa',"start":'#3344cc',"stop":'#cc2244',"sync":'#0088cc',"hand":'#aa7700'},
    'Moss Light': {"a":'light',"bg":'#f4f9f0',"card":'#ffffff',"border":'#a0c090',"text":'#0f2010',"muted":'#607850',"start":'#3a6030',"stop":'#c0392b',"sync":'#1d6080',"hand":'#b08020'},
    'Moss Dark': {"a":'dark',"bg":'#0a1208',"card":'#101e0e',"border":'#204020',"text":'#d0e8c0',"muted":'#608050',"start":'#70c050',"stop":'#e05050',"sync":'#50a0c0',"hand":'#d0b840'},
    'Tokyonight Dark': {"a":'dark',"bg":'#1a1b2e',"card":'#16213e',"border":'#0f3460',"text":'#a9b1d6',"muted":'#414868',"start":'#73daca',"stop":'#f7768e',"sync":'#7aa2f7',"hand":'#ff9e64'},
    'Tokyonight Light': {"a":'light',"bg":'#d5d6db',"card":'#ffffff',"border":'#a8aecb',"text":'#343b58',"muted":'#9699a6',"start":'#33635c',"stop":'#8c4351',"sync":'#34548a',"hand":'#8f5e15'},
    'Frostbite Dark': {"a":'dark',"bg":'#050f1a',"card":'#0a1e2e',"border":'#1a4060',"text":'#e0f8ff',"muted":'#3080aa',"start":'#00c8ff',"stop":'#ff4488',"sync":'#88ddff',"hand":'#ffdd44'},
    'Frostbite Light': {"a":'light',"bg":'#e8f8ff',"card":'#ffffff',"border":'#88ccee',"text":'#001830',"muted":'#4499bb',"start":'#0088cc',"stop":'#cc2266',"sync":'#5588ff',"hand":'#cc9900'},
    'Ultra White Light': {"a":'light',"bg":'#ffffff',"card":'#ffffff',"border":'#eeeeee',"text":'#000000',"muted":'#bbbbbb',"start":'#000000',"stop":'#ff0000',"sync":'#444444',"hand":'#ff8800'},
    'Ultra Black Dark': {"a":'dark',"bg":'#000000',"card":'#050505',"border":'#0f0f0f',"text":'#ffffff',"muted":'#333333',"start":'#ffffff',"stop":'#ff0000',"sync":'#aaaaaa',"hand":'#ffff00'},
}

settings           = load_settings()
_first_launch      = "theme" not in settings
_theme_name        = settings.get("theme", "Dark (Default)")
show_chat          = settings.get("show_chat", True)
log_left           = settings.get("log_left", False)
show_perf          = settings.get("show_perf", True)
fullscreen         = settings.get("fullscreen", False)
auto_upload        = settings.get("auto_upload", False)
backup_upload_on   = settings.get("backup_upload_on", True)
auto_upload_mins   = settings.get("auto_upload_mins", 10)
upload_on_stop     = settings.get("upload_on_stop", True)
ram_display_mode   = settings.get("ram_display_mode", "percent")
_ctrl_mode         = settings.get("ctrl_mode", "Dashboard")
if _ctrl_mode == "MC Ctrl": _ctrl_mode = "Dashboard"

if _theme_name not in THEMES: _theme_name = "Dark (Default)"
T = THEMES[_theme_name]

ctk.set_appearance_mode(T["a"])
ctk.set_default_color_theme("dark-blue")

# ── Global server state ───────────────────────────────────
server_proc       = None
server_stdin      = None
server_pid        = None
perf_running      = False
server_ready      = False
player_count      = 0
online_players    = {}
auto_upload_timer = None
log_history       = ""
chat_history      = ""
playit_proc       = None
playit_tunnel     = None
playit_log_lines  = []
_remote_proc      = [None]
_loaded_addons    = {}
_players_refresh_id = None

perf = {"ram_used":"--","ram_pct":"--","ram_srv":"--","cpu_sys":"--","cpu_srv":"--",
        "tps":"--","latency":"--","players":"0","uptime":"--","threads":"--"}
server_start_time = None

# ── Log parsers ───────────────────────────────────────────
CHAT_RE    = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE    = re.compile(r'^(\w+) joined the game', re.I)
LEAVE_RE   = re.compile(r'^(\w+) (?:lost connection|left the game)', re.I)
DEATH_RE   = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.I)
STRIP_RE   = re.compile(r'^\[[\d:]+\]\s*\[.*?(?:INFO|WARN|ERROR).*?\]:\s*', re.I)
DONE_RE    = re.compile(r'Done \([\d.]+s\)!', re.I)
SPARK_TPS  = re.compile(r'TPS from last 1m[^:]*:\s*([\d.]+)', re.I)
TPS_RE2    = re.compile(r'Current TPS[:\s]+([\d.]+)', re.I)
PLAYER_RE  = re.compile(r'There are (\d+) of a max of \d+ players', re.I)
LIST_NM_RE = re.compile(r'There are \d+[^:]*:\s*(.+)', re.I)
LAT_RE     = re.compile(r'(\w+)\s+has\s+(?:a\s+ping\s+of\s+)?(\d+)\s*ms', re.I)
LAT_RE2    = re.compile(r'(\w+)\s*\((\d+)\s*ms\)', re.I)

def parse_server_line(raw):
    global player_count, server_ready
    clean = STRIP_RE.sub('', raw).strip()
    if not clean: return None
    if "Done (" in clean and DONE_RE.search(clean):
        server_ready = True
        app.after(0, show_toast, "Server is ready!", T["start"])
        return ('log', clean)
    if "TPS" in clean:
        tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
        if tps: perf["tps"] = tps.group(1); return None
    if "ms" in clean:
        lat = LAT_RE.search(clean) or LAT_RE2.search(clean)
        if lat:
            try:
                pings = [int(m[1]) for m in (LAT_RE.findall(clean) or LAT_RE2.findall(clean))]
                if pings: perf["latency"] = f"{sum(pings)//len(pings)} ms"
            except: pass
            return None
    if "There are" in clean:
        pl = PLAYER_RE.search(clean)
        if pl:
            player_count = int(pl.group(1)); perf["players"] = str(player_count)
            nm = LIST_NM_RE.search(clean)
            if nm:
                raw_names = nm.group(1).strip()
                if raw_names:
                    names = [n.strip() for n in raw_names.split(",") if n.strip()]
                    now = datetime.now().strftime("%H:%M")
                    for n in names:
                        if n not in online_players: online_players[n] = now
                    for gone in [k for k in online_players if k not in names]:
                        online_players.pop(gone, None)
        return None
    if '<' in clean:
        c = CHAT_RE.search(clean)
        if c: return ('chat', f"[CHAT] {c.group(1)}: {c.group(2)}")
    if "joined the game" in clean:
        j = JOIN_RE.search(clean)
        if j:
            n = j.group(1); player_count += 1; perf["players"] = str(player_count)
            online_players[n] = datetime.now().strftime("%H:%M")
            return ('event', f">> {n} joined")
    if "left the game" in clean or "lost connection" in clean:
        lv = LEAVE_RE.search(clean)
        if lv:
            n = lv.group(1); player_count = max(0, player_count-1); perf["players"] = str(player_count)
            online_players.pop(n, None); return ('event', f"<< {n} left")
    if any(w in clean for w in ("was slain","died","fell","drowned","burned","blew up","suffocated","starved","withered")):
        if DEATH_RE.search(clean): return ('event', f"[DEATH] {clean}")
    return ('log', clean)

# ── App window ────────────────────────────────────────────
app = ctk.CTk()
app.title("MC CTRL")
app.geometry("1100x740")
app.resizable(True, True)
app.configure(fg_color=T["bg"])
_set_taskbar_id()
try: _set_win_icon(app, os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
except: pass
if fullscreen: app.after(100, lambda: app.attributes("-fullscreen", True))

# ── Core helpers ──────────────────────────────────────────
_log_buffer = []   # messages logged before log_box exists
def log(msg):
    global log_history
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}]  {msg}\n"
    log_history += line          # always persist so tab switches keep history
    if len(log_history) > 200_000:  # cap at ~200 KB
        log_history = log_history[-150_000:]
    try:
        log_box.configure(state="normal")
        log_box.insert("end", line)
        log_box.configure(state="disabled"); log_box.see("end")
    except:
        _log_buffer.append(line)   # queue until log_box ready

def log_chat(msg):
    if not show_chat: return
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        chat_box.configure(state="normal")
        chat_box.insert("end", f"[{ts}]  {msg}\n")
        chat_box.configure(state="disabled"); chat_box.see("end")
    except: pass

def set_status(txt, color):
    try: status_lbl.configure(text=txt); status_dot.configure(text_color=color)
    except: pass

def send_server_cmd(cmd):
    global server_stdin
    _stdin = server_stdin  # snapshot to avoid race with stop_server
    if _stdin is None: show_toast("Server not running!", T["stop"]); return
    try: _stdin.write(cmd + "\n"); _stdin.flush(); log(f">> {cmd}")
    except BrokenPipeError: server_stdin = None; show_toast("Lost connection!", T["stop"])
    except Exception as ex: log(f"Command failed: {ex}")

def send_command():
    try: cmd = cmd_entry.get().strip()
    except: return
    if not cmd: return
    cmd_entry.delete(0, "end"); send_server_cmd(cmd)

def run_cmd(cmd, cwd=None):
    log(f"$ {cmd}")
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                           text=True, creationflags=_popen_flags())
        for line in p.stdout.strip().splitlines(): log(f"  {line}")
        if p.returncode != 0:
            for line in p.stderr.strip().splitlines(): log(f"  {line}")
        return p.returncode == 0
    except Exception as ex: log(str(ex)); return False

def set_all_buttons(state):
    for b in [btn_start, btn_stop, btn_sync]:
        try: b.configure(state=state)
        except: pass

_remote_state_log_fn = [None]  # set by _build_mode_remote to append to state buf

def read_server_output(proc):
    for raw in iter(proc.stdout.readline, ''):
        if not raw: break
        parsed = parse_server_line(raw)
        if parsed is None: continue
        cat, text = parsed
        if _remote_state_log_fn[0]:
            try: _remote_state_log_fn[0](text)
            except: pass
        if cat in ('chat', 'event'): app.after(0, log_chat, text)
        else: app.after(0, log, text)

# ── Toast ─────────────────────────────────────────────────
_toast_win = None
def show_toast(msg, color=None, ms=3000):
    global _toast_win
    if color is None: color = T["sync"]
    try:
        if _toast_win and _toast_win.winfo_exists(): _toast_win.destroy()
    except: pass
    t = ctk.CTkToplevel(app)
    t.overrideredirect(True); t.attributes("-topmost", True); t.configure(fg_color=T["card"])
    _toast_win = t
    f = ctk.CTkFrame(t, fg_color=T["card"], border_color=color, border_width=2, corner_radius=10)
    f.pack(padx=2, pady=2)
    ctk.CTkLabel(f, text=msg, font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=color).pack(padx=18, pady=12)
    def _place():
        try: t.geometry(f"+{app.winfo_x()+app.winfo_width()-360}+{app.winfo_y()+app.winfo_height()-80}")
        except: pass
    app.after(10, _place)
    app.after(ms, lambda: t.destroy() if t.winfo_exists() else None)

# ── Auto-upload ───────────────────────────────────────────
def toggle_auto_upload():
    global auto_upload
    auto_upload = not auto_upload; update_setting("auto_upload", auto_upload)
    if auto_upload: schedule_auto_upload()
    elif auto_upload_timer:
        try: auto_upload_timer.cancel()
        except: pass

def schedule_auto_upload():
    global auto_upload_timer
    if auto_upload_timer:
        try: auto_upload_timer.cancel()
        except: pass
    if not auto_upload: return
    auto_upload_timer = threading.Timer(auto_upload_mins * 60, _do_auto_upload)
    auto_upload_timer.daemon = True; auto_upload_timer.start()

def _do_auto_upload():
    if not auto_upload: return
    s = load_settings(); path = s.get("srv_path", _DEFAULT_SRV); repo = s.get("repo_url", REPO_URL)
    def _work():
        app.after(0, log, "-- Auto-upload ---")
        try:
            subprocess.run(f"git remote set-url origin {repo}", shell=True, cwd=path,
                           capture_output=True, creationflags=_popen_flags())
            subprocess.run("git add .", shell=True, cwd=path,
                           capture_output=True, creationflags=_popen_flags())
            r = subprocess.run(
                f'git commit -m "Auto {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                shell=True, cwd=path, capture_output=True, text=True, creationflags=_popen_flags())
            if "nothing to commit" not in r.stdout and r.returncode == 0:
                push = subprocess.run("git push origin main", shell=True, cwd=path,
                                      capture_output=True, text=True, creationflags=_popen_flags())
                if push.returncode == 0:
                    app.after(0, log, "  Auto-upload done.")
                    app.after(0, show_toast, "Auto-upload complete!", T["sync"])
        except Exception as ex: app.after(0, log, f"  Error: {ex}")
        schedule_auto_upload()
    threading.Thread(target=_work, daemon=True).start()

# ── Performance ───────────────────────────────────────────
perf_labels = {}

def find_java_proc():
    if not _PSUTIL: return None
    if server_pid:
        try: return psutil.Process(server_pid)
        except: pass
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'java' in p.info['name'].lower():
                if 'server.jar' in ' '.join(p.info['cmdline'] or []): return p
        except: pass
    return None

def perf_loop():
    global perf_running
    if not _PSUTIL: return
    perf_running = True; java_proc = None; tick = 0
    psutil.cpu_percent(interval=None)  # warmup — discard first reading which is always 0
    while perf_running:
        try:
            vm = psutil.virtual_memory()
            perf["ram_used"] = f"{vm.used/1024**3:.1f} GB"
            perf["ram_pct"]  = f"{vm.percent:.0f}%"
            perf["cpu_sys"]  = f"{psutil.cpu_percent(interval=None):.0f}%"
            if java_proc is None: java_proc = find_java_proc()
            if java_proc:
                try:
                    perf["ram_srv"] = f"{java_proc.memory_info().rss/1024**2:.0f} MB"
                    perf["cpu_srv"] = f"{java_proc.cpu_percent(interval=None):.0f}%"
                    perf["threads"] = str(java_proc.num_threads())
                except: java_proc = None; perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            if server_start_time:
                e = int((datetime.now()-server_start_time).total_seconds()); h,r=divmod(e,3600); m,s=divmod(r,60)
                perf["uptime"] = f"{h:02d}:{m:02d}:{s:02d}"
            else: perf["uptime"] = "--"
            if server_ready and server_stdin:
                try:
                    if tick % 5  == 0: server_stdin.write("tps\n");  server_stdin.flush()
                    if tick % 10 == 0: server_stdin.write("list\n"); server_stdin.flush()
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
                try: v=float(val); c=T["start"] if v>=18 else T["hand"] if v>=15 else T["stop"]
                except: c=T["text"]
                lbl.configure(text=val, text_color=c)
            elif key in ("cpu_sys","cpu_srv","ram_pct"):
                try: n=float(str(val).replace("%","")); c=T["start"] if n<60 else T["hand"] if n<85 else T["stop"]
                except: c=T["text"]
                lbl.configure(text=val, text_color=c)
            else: lbl.configure(text=val, text_color=T["text"])
        except: pass

# ── Theme ─────────────────────────────────────────────────
def _pulse_btn(btn, base_color, ms=120):
    """Brief color flash on button press for tactile feedback."""
    try:
        lighter = base_color  # already highlighted on press; just briefly desaturate
        btn.configure(fg_color=T["border"])
        app.after(ms, lambda: btn.configure(fg_color=base_color) if btn.winfo_exists() else None)
    except: pass

def apply_theme(name):
    global T, _theme_name
    _theme_name = name; T = THEMES[name]; update_setting("theme", name)
    ctk.set_appearance_mode(T["a"]); app.configure(fg_color=T["bg"])

def rebuild_ui():
    global log_history, chat_history
    _ip_footer_labels.clear()
    try: log_history  = log_box.get("1.0","end")
    except: pass
    try: chat_history = chat_box.get("1.0","end")
    except: pass
    for w in app.winfo_children(): w.destroy()
    build_ui()

# ── EULA ──────────────────────────────────────────────────
def _check_eula(path):
    eula = os.path.join(path, "eula.txt")
    try:
        if "eula=true" in open(eula, encoding="utf-8").read().lower(): return True
    except FileNotFoundError: pass
    result = [None]
    def _show():
        win = ctk.CTkToplevel(app); win.title("Minecraft EULA")
        win.resizable(False, False); win.configure(fg_color=T["bg"])
        win.grab_set(); win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        try:
            ax=app.winfo_x()+(app.winfo_width()-500)//2; ay=app.winfo_y()+(app.winfo_height()-360)//2
            win.geometry(f"500x360+{ax}+{ay}")
        except: win.geometry("500x360")
        ctk.CTkLabel(win, text="⚠", font=ctk.CTkFont(size=40), text_color=T["hand"]).pack(pady=(20,0))
        ctk.CTkLabel(win, text="Minecraft EULA", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=T["text"]).pack()
        f = ctk.CTkFrame(win, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
        f.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(f, text=(
            "You must agree to the Minecraft EULA before starting.\n"
            "This writes  eula=true  to eula.txt.\n\n"
            "https://aka.ms/MinecraftEULA"
        ), font=ctk.CTkFont(size=12), text_color=T["muted"], justify="left").pack(padx=16, pady=12)
        br = ctk.CTkFrame(win, fg_color="transparent"); br.pack(pady=8)
        def _acc():
            try:
                os.makedirs(path, exist_ok=True)
                with open(eula, "w", encoding="utf-8") as f2:
                    f2.write(f"# Accepted {datetime.now().strftime('%Y-%m-%d %H:%M')}\n# https://aka.ms/MinecraftEULA\neula=true\n")
            except Exception as ex: log(f"  EULA write error: {ex}")
            result[0] = True; win.destroy()
        ctk.CTkButton(br, text="Accept EULA", width=160, height=34,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000",
                      command=_acc).pack(side="left", padx=(0,10))
        ctk.CTkButton(br, text="Decline", width=90, height=34,
                      font=ctk.CTkFont(size=13), fg_color="transparent",
                      border_width=1, border_color=T["stop"], text_color=T["stop"],
                      hover_color=T["border"], command=lambda: (result.__setitem__(0,False),win.destroy())).pack(side="left")
        win.wait_window()
    app.after(0, _show)
    while result[0] is None: time.sleep(0.05)
    return result[0]

# ── Server actions ────────────────────────────────────────
def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    s = load_settings(); path = s.get("srv_path", _DEFAULT_SRV)
    java = s.get("java_path", _DEFAULT_JAVA); repo = s.get("repo_url", REPO_URL)
    if not _check_eula(path):
        log("  Cancelled — EULA not accepted."); set_status("Stopped", T["stop"]); set_all_buttons("normal"); return
    set_status("Starting...", T["hand"])
    log("-- Start Server --")
    run_cmd(f"git remote set-url origin {repo}", cwd=path)
    run_cmd("git pull origin main", cwd=path)
    _ram_gb = s.get("server_ram_gb", 2); _ram_str = f"{_ram_gb}G"
    aikar = [
        f"-Xms{_ram_str}", f"-Xmx{_ram_str}", "-XX:+UseG1GC", "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200", "-XX:+UnlockExperimentalVMOptions",
        "-XX:+DisableExplicitGC", "-XX:G1NewSizePercent=30",
        "-XX:G1MaxNewSizePercent=40", "-XX:G1HeapRegionSize=8M",
        "-XX:G1ReservePercent=20", "-XX:G1HeapWastePercent=5",
        "-XX:G1MixedGCCountTarget=4", "-XX:InitiatingHeapOccupancyPercent=15",
        "-XX:G1MixedGCLiveThresholdPercent=90",
        "-XX:G1RSetUpdatingPauseTimePercent=5", "-XX:SurvivorRatio=32",
        "-XX:+PerfDisableSharedMem", "-XX:MaxTenuringThreshold=1",
        "-Dusing.aikars.flags=https://mcflags.emc.gs", "-Daikars.new.flags=true",
    ]
    cmd = [java] + aikar + ["-jar", "server.jar", "nogui"]
    kw = {"cwd":path, "stdin":subprocess.PIPE, "stdout":subprocess.PIPE,
          "stderr":subprocess.STDOUT, "text":True, "bufsize":1}
    if IS_WIN: kw["creationflags"] = _NO_WIN
    try:
        server_proc = subprocess.Popen(cmd, **kw)
    except Exception as ex:
        log(f"  Failed to start: {ex}"); set_status("Stopped", T["stop"]); set_all_buttons("normal"); return
    server_stdin = server_proc.stdin; server_pid = server_proc.pid
    server_start_time = datetime.now(); server_ready = False; player_count = 0
    online_players.clear(); perf["tps"] = perf["latency"] = "--"; perf["players"] = "0"
    threading.Thread(target=read_server_output, args=(server_proc,), daemon=True).start()
    if not perf_running: threading.Thread(target=perf_loop, daemon=True).start()
    set_status("Running", T["start"]); log(f"Server running (PID {server_proc.pid})")
    try: btn_stop.configure(state="normal")
    except: pass

def stop_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready
    set_status("Stopping...", T["hand"]); log("-- Stop Server --")
    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except: pass
        server_stdin = None
    r = _kill_java()
    log("  Killed." if r.returncode == 0 else "  Not running.")
    server_proc = server_pid = server_start_time = None; server_ready = perf_running = False
    for k in ("tps","latency","players","uptime","ram_srv","cpu_srv","threads"): perf[k] = "--"
    if upload_on_stop and backup_upload_on:
        s = load_settings(); path = s.get("srv_path", _DEFAULT_SRV)
        log("Pushing world to GitHub...")
        run_cmd("git add world/ world_nether/ world_the_end/", cwd=path)
        c = subprocess.run(
            f'git commit -m "World update {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
            shell=True, cwd=path, capture_output=True, text=True, creationflags=_popen_flags())
        if "nothing to commit" in (c.stdout or ""):
            log("  Nothing to commit.")
        else:
            run_cmd("git push origin main", cwd=path)
            app.after(0, show_toast, "World pushed to GitHub!", T["sync"])
    if _remote_proc[0]:
        try: _remote_proc[0].terminate()
        except: pass
        _remote_proc[0] = None
    set_status("Stopped", T["stop"]); log("Done."); set_all_buttons("normal")

def sync_git():
    set_all_buttons("disabled")
    s = load_settings(); path = s.get("srv_path", _DEFAULT_SRV); repo = s.get("repo_url", REPO_URL)
    set_status("Syncing...", T["hand"]); log("-- Sync & Upload --")
    run_cmd(f"git remote set-url origin {repo}", cwd=path)
    run_cmd("git add .", cwd=path)
    run_cmd('git commit -m "Manual Sync"', cwd=path)
    ok = run_cmd("git push origin main", cwd=path)
    if ok: app.after(0, show_toast, "Sync complete!", T["sync"])
    set_status("Stopped", T["stop"]); set_all_buttons("normal")

# ── Addon loader ──────────────────────────────────────────
def _load_addon(path):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec); sys.modules[name] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "setup"):
            mod.setup({"app":app,"T":T,"log":log,"show_toast":show_toast,
                       "send_server_cmd":send_server_cmd,"load_settings":load_settings})
        _loaded_addons[name] = mod; log(f"  Addon: {name}")
    except Exception as ex: log(f"  Addon error [{name}]: {ex}")

def _load_all_addons():
    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)
    try:
        for s in sorted(os.listdir(addon_dir)):
            if s.endswith(".py"): _load_addon(os.path.join(addon_dir, s))
    except: pass

# ══════════════════════════════════════════════════════════
# UI BUILDER
# ══════════════════════════════════════════════════════════
def build_ui():
    global status_dot, status_lbl, btn_start, btn_stop, btn_sync

    is_fs = app.attributes("-fullscreen")

    # ── Top bar ───────────────────────────────────────────
    top = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0)
    top.pack(fill="x")
    ctk.CTkLabel(top, text="MC CTRL",
                 font=ctk.CTkFont(size=15, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=14, pady=8)
    plat = "🐧 Linux" if IS_LIN else ("🍎 Mac" if IS_MAC else "🪟 Windows")
    ctk.CTkLabel(top, text=plat, font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(0,8))
    # GPU display
    _gpu_lbl = ctk.CTkLabel(top, text="GPU: detecting…", font=ctk.CTkFont(size=10), text_color=T["muted"])
    _gpu_lbl.pack(side="left", padx=(0,8))
    def _detect_gpu():
        gpu = ""
        import queue as _q
        result_q = _q.Queue()
        def _try():
            try:
                if IS_WIN:
                    r = subprocess.run("wmic path win32_VideoController get Name /value",
                                       shell=True, capture_output=True, text=True, timeout=4,
                                       creationflags=_NO_WIN)
                    for line in r.stdout.splitlines():
                        if "Name=" in line:
                            v = line.split("=",1)[1].strip()
                            if v: result_q.put(v); return
                elif IS_LIN:
                    r = subprocess.run("lspci | grep -i vga", shell=True, capture_output=True,
                                       text=True, timeout=4)
                    if r.stdout: result_q.put(r.stdout.strip().split(":")[-1].strip()[:48]); return
                elif IS_MAC:
                    r = subprocess.run("system_profiler SPDisplaysDataType | grep Chipset",
                                       shell=True, capture_output=True, text=True, timeout=4)
                    if r.stdout: result_q.put(r.stdout.strip().split(":")[-1].strip()); return
            except: pass
            result_q.put("")
        t = threading.Thread(target=_try, daemon=True); t.start()
        t.join(timeout=4.5)   # hard 4.5s wall-clock cap
        try: gpu = result_q.get_nowait()
        except: gpu = ""
        if not gpu:
            # fallback: show CPU name instead
            try:
                if IS_WIN:
                    r2 = subprocess.run("wmic cpu get Name /value", shell=True,
                                        capture_output=True, text=True, timeout=3,
                                        creationflags=_NO_WIN)
                    for line in r2.stdout.splitlines():
                        if "Name=" in line:
                            gpu = "CPU: " + line.split("=",1)[1].strip()[:36]; break
                elif IS_LIN:
                    r2 = subprocess.run("cat /proc/cpuinfo | grep 'model name' | head -1",
                                        shell=True, capture_output=True, text=True, timeout=3)
                    if r2.stdout: gpu = "CPU: " + r2.stdout.split(":")[-1].strip()[:36]
            except: pass
        label = ("🖥 " + gpu[:48]) if gpu else "🖥 GPU/CPU: unknown"
        try: app.after(0, _gpu_lbl.configure, {"text": label})
        except: pass
    threading.Thread(target=_detect_gpu, daemon=True).start()

    # ── Theme search button ───────────────────────────────
    _theme_btn_lbl = ctk.StringVar(value=f"🎨 {_theme_name}")
    def _open_theme_picker():
        win = ctk.CTkToplevel(app); win.title("Theme Picker"); win.geometry("780x540")
        win.configure(fg_color=T["bg"]); win.grab_set(); win.attributes("-topmost", True)
        try:
            ax=app.winfo_x()+(app.winfo_width()-780)//2; ay=app.winfo_y()+(app.winfo_height()-540)//2
            win.geometry(f"780x540+{ax}+{ay}")
        except: pass
        win.rowconfigure(1, weight=1); win.columnconfigure(0, weight=1)
        # Search bar
        sf = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=0); sf.grid(row=0,column=0,sticky="ew")
        sf.columnconfigure(1, weight=1)
        ctk.CTkLabel(sf, text="🔍", font=ctk.CTkFont(size=14), text_color=T["muted"]).grid(row=0,column=0,padx=(10,4),pady=8)
        search_var = ctk.StringVar()
        se = ctk.CTkEntry(sf, textvariable=search_var, placeholder_text="Search themes…",
                          height=30, font=ctk.CTkFont(size=12),
                          fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
        se.grid(row=0,column=1,sticky="ew",padx=(0,8),pady=8); se.focus()
        # Filter buttons (Dark / Light / All)
        _filt = ctk.StringVar(value="All")
        fbf = ctk.CTkFrame(sf, fg_color="transparent"); fbf.grid(row=0,column=2,padx=(0,8))
        for lbl,val in [("All","All"),("Dark","dark"),("Light","light")]:
            ctk.CTkButton(fbf, text=lbl, width=52, height=26, font=ctk.CTkFont(size=10),
                          fg_color=T["sync"] if val=="All" else T["bg"],
                          border_width=1, border_color=T["border"],
                          text_color="#000" if val=="All" else T["muted"],
                          hover_color=T["border"],
                          command=lambda v=val, b=lbl: (_filt.set(v), _refresh_grid())).pack(side="left",padx=2)
        # Scrollable grid
        grid_scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        grid_scroll.grid(row=1,column=0,sticky="nsew",padx=4,pady=4)
        _cards = []
        def _pick(name):
            _theme_btn_lbl.set(f"🎨 {name}")
            apply_theme(name); win.destroy(); app.after(10, rebuild_ui)
        def _refresh_grid():
            for w in grid_scroll.winfo_children(): w.destroy()
            q = search_var.get().lower(); filt = _filt.get()
            results = [(n,t) for n,t in THEMES.items()
                       if (q in n.lower() or q in t.get("bg","") or q in t.get("start",""))
                       and (filt=="All" or t.get("a","dark")==filt)]
            COLS = 4
            for i,(name,t) in enumerate(results):
                row_i,col_i = i//COLS, i%COLS
                card = ctk.CTkFrame(grid_scroll, fg_color=t["card"],
                                    border_color=t["border"] if name==_theme_name else t["card"],
                                    border_width=2, corner_radius=10,
                                    cursor="hand2")
                card.grid(row=row_i, column=col_i, padx=4, pady=4, sticky="ew")
                grid_scroll.columnconfigure(col_i, weight=1)
                # Swatch row: 6 color dots
                sw = ctk.CTkFrame(card, fg_color="transparent"); sw.pack(padx=8, pady=(8,4))
                for hex_c in [t["bg"],t["card"],t["border"],t["start"],t["stop"],t["sync"]]:
                    try:
                        c = ctk.CTkLabel(sw, text="", width=18, height=18, corner_radius=4,
                                         fg_color=hex_c); c.pack(side="left",padx=1)
                    except: pass
                ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=t["text"], wraplength=150, justify="center").pack(padx=6, pady=(0,6))
                card.bind("<Button-1>", lambda e,n=name: _pick(n))
                for child in card.winfo_children():
                    child.bind("<Button-1>", lambda e,n=name: _pick(n))
            if not results:
                ctk.CTkLabel(grid_scroll, text="No themes match.", font=ctk.CTkFont(size=13),
                             text_color=T["muted"]).grid(row=0,column=0,pady=40)
        search_var.trace_add("write", lambda *_: _refresh_grid())
        _refresh_grid()
    ctk.CTkButton(top, textvariable=_theme_btn_lbl, width=160, height=26,
                  font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_open_theme_picker).pack(side="left", padx=(0,6), pady=6)

    def _open_settings():
        win = ctk.CTkToplevel(app); win.title("Settings"); win.geometry("720x700")
        win.configure(fg_color=T["bg"]); win.grab_set(); win.attributes("-topmost", True)
        try:
            ax=app.winfo_x()+(app.winfo_width()-720)//2; ay=app.winfo_y()+(app.winfo_height()-700)//2
            win.geometry(f"720x700+{ax}+{ay}")
        except: pass
        build_settings_window(win)

    ctk.CTkButton(top, text="⚙ Settings", width=90, height=26,
                  font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_open_settings).pack(side="left", padx=(0,8), pady=6)

    status_dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=13), text_color=T["stop"])
    status_dot.pack(side="right", padx=(0,12))
    status_lbl = ctk.CTkLabel(top, text="Stopped", font=ctk.CTkFont(size=12), text_color=T["muted"])
    status_lbl.pack(side="right", padx=(0,4))

    # ── Tab bar ───────────────────────────────────────────
    tab_bar = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0,
                            border_color=T["border"], border_width=1)
    tab_bar.pack(fill="x")
    tab_content = ctk.CTkFrame(app, fg_color="transparent")
    tab_content.pack(fill="both", expand=True)

    # Tabs: Dashboard (merged), Server Info, Docker, Modpacks, Multi
    tab_frames = {k: ctk.CTkFrame(tab_content, fg_color="transparent") for k in
                  ["dash", "info", "docker", "mods", "multi"]}
    _built = set(); tab_btns = {}

    def show_tab(name):
        for f in tab_frames.values(): f.pack_forget()
        for n, b in tab_btns.items():
            b.configure(fg_color=T["hand"] if n=="multi" else "transparent",
                        text_color="#000" if n=="multi" else T["muted"])
        tab_frames[name].pack(fill="both", expand=True)
        tab_btns[name].configure(fg_color=T["sync"], text_color="#000")
        if name not in _built:
            _built.add(name)
            _TAB_LOAD_INFO = {
                "dash":   ("Building Dashboard",    "Server controls, quick commands, log…"),
                "info":   ("Building Server Info",  "Players, plugins, properties, backups…"),
                "docker": ("Building Docker",       "Container config, compose, controls…"),
                "mods":   ("Building Modpacks",     "Modrinth search, installer, browser…"),
                "multi":  ("Building Multi-CTRL",   "Up to 3 independent server slots…"),
            }
            _lt, _ld = _TAB_LOAD_INFO.get(name, ("Loading…", ""))
            _dismiss = _build_loading_overlay(tab_frames[name], _lt, _ld)
            def _build_and_dismiss(n=name, dismiss=_dismiss):
                try:
                    {
                        "dash":   lambda: build_dashboard(tab_frames["dash"], is_fs),
                        "info":   lambda: build_server_info_tab(tab_frames["info"]),
                        "docker": lambda: build_docker_tab(tab_frames["docker"]),
                        "mods":   lambda: build_modpack_tab(tab_frames["mods"]),
                        "multi":  lambda: build_multictrl_tab(tab_frames["multi"]),
                    }[n]()
                except Exception as _e:
                    log(f"Tab build error [{n}]: {_e}")
                finally:
                    dismiss()
            app.after(60, _build_and_dismiss)

    TABS = [
        ("dash","Dashboard"), ("info","Server Info"),
        ("docker","Docker"), ("mods","📦 Modpacks"), ("multi","⊞ MULTI"),
    ]
    for key, label in TABS:
        is_multi = key == "multi"
        b = ctk.CTkButton(tab_bar, text=label, width=120, height=28,
                          font=ctk.CTkFont(size=11, weight="bold" if is_multi else "normal"),
                          corner_radius=5,
                          fg_color=T["hand"] if is_multi else "transparent",
                          text_color="#000" if is_multi else T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=(6 if key=="dash" else 2, 2), pady=5)
        tab_btns[key] = b

    show_tab("dash")


# ══════════════════════════════════════════════════════════
# SHARED UI HELPERS
# ══════════════════════════════════════════════════════════
_cached_local_ip  = ["…"]
_cached_ext_ip    = ["…"]
_ip_footer_labels = []   # list of (local_lbl, ext_lbl) across all tabs

def _refresh_ip_footers():
    for local_lbl, ext_lbl in _ip_footer_labels:
        try: local_lbl.configure(text=f"LAN  {_cached_local_ip[0]}")
        except: pass
        try: ext_lbl.configure(text=f"EXT  {_cached_ext_ip[0]}")
        except: pass

def _start_ip_detection():
    import socket
    def _work():
        # Local IP
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s2.connect(("8.8.8.8", 80)); lip = s2.getsockname()[0]; s2.close()
        except: lip = "127.0.0.1"
        port = load_settings().get("server_port","25565")
        _cached_local_ip[0] = f"{lip}:{port}"
        app.after(0, _refresh_ip_footers)
        # External IP
        try:
            eip = urllib.request.urlopen("https://api.ipify.org", timeout=6).read().decode().strip()
            _cached_ext_ip[0] = f"{eip}:{port}"
        except: _cached_ext_ip[0] = "unavailable"
        app.after(0, _refresh_ip_footers)
    threading.Thread(target=_work, daemon=True).start()

def _build_ip_footer(parent):
    """Persistent IP strip added to the bottom of any tab."""
    bar = ctk.CTkFrame(parent, fg_color=T["bg"], corner_radius=0,
                       border_color=T["border"], border_width=1)
    bar.pack(side="bottom", fill="x")
    bar.columnconfigure(2, weight=1)
    ctk.CTkLabel(bar, text="⬡", font=ctk.CTkFont(size=11), text_color=T["border"]).pack(side="left", padx=(10,4), pady=5)
    local_lbl = ctk.CTkLabel(bar, text=f"LAN  {_cached_local_ip[0]}",
                              font=ctk.CTkFont(size=11, family="Consolas", weight="bold"),
                              text_color=T["start"])
    local_lbl.pack(side="left", padx=(0,16))
    ext_lbl = ctk.CTkLabel(bar, text=f"EXT  {_cached_ext_ip[0]}",
                            font=ctk.CTkFont(size=11, family="Consolas", weight="bold"),
                            text_color=T["sync"])
    ext_lbl.pack(side="left")
    # Copy buttons
    ctk.CTkButton(bar, text="⎘ LAN", width=56, height=20, font=ctk.CTkFont(size=9),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["start"], hover_color=T["border"],
                  command=lambda: (app.clipboard_clear(), app.clipboard_append(_cached_local_ip[0]),
                                   show_toast(f"Copied: {_cached_local_ip[0]}", T["start"]))
                  ).pack(side="left", padx=(8,2), pady=4)
    ctk.CTkButton(bar, text="⎘ EXT", width=56, height=20, font=ctk.CTkFont(size=9),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=lambda: (app.clipboard_clear(), app.clipboard_append(_cached_ext_ip[0]),
                                   show_toast(f"Copied: {_cached_ext_ip[0]}", T["sync"]))
                  ).pack(side="left", padx=2, pady=4)
    ctk.CTkButton(bar, text="↺", width=30, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_start_ip_detection).pack(side="left", padx=2, pady=4)
    _ip_footer_labels.append((local_lbl, ext_lbl))
    return bar

def _build_loading_overlay(parent, text="Loading…", detail=""):
    """Animated loading overlay with label showing what is being built."""
    overlay = ctk.CTkFrame(parent, fg_color=T["bg"], corner_radius=0)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()
    # Spinner icon that rotates via text cycling
    _spin_chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    _spin_idx   = [0]
    spin_lbl = ctk.CTkLabel(overlay, text=_spin_chars[0],
                             font=ctk.CTkFont(size=22), text_color=T["sync"])
    spin_lbl.place(relx=0.5, rely=0.38, anchor="center")
    title_lbl = ctk.CTkLabel(overlay, text=text,
                              font=ctk.CTkFont(size=15, weight="bold"),
                              text_color=T["text"])
    title_lbl.place(relx=0.5, rely=0.47, anchor="center")
    detail_lbl = ctk.CTkLabel(overlay, text=detail,
                               font=ctk.CTkFont(size=11), text_color=T["muted"])
    detail_lbl.place(relx=0.5, rely=0.54, anchor="center")
    bar = ctk.CTkProgressBar(overlay, width=220, height=3,
                              fg_color=T["border"], progress_color=T["sync"])
    bar.place(relx=0.5, rely=0.61, anchor="center"); bar.set(0); bar.start()
    _running = [True]
    def _tick():
        if not _running[0]: return
        _spin_idx[0] = (_spin_idx[0] + 1) % len(_spin_chars)
        try: spin_lbl.configure(text=_spin_chars[_spin_idx[0]])
        except: return
        overlay.after(80, _tick)
    overlay.after(80, _tick)
    def _dismiss():
        _running[0] = False
        try: bar.stop(); overlay.destroy()
        except: pass
    return _dismiss

# ══════════════════════════════════════════════════════════
# DASHBOARD — contains Ctrl Mode selector at bottom
# Modes: Dashboard | MC Ctrl | Network | playit.gg | Remote
# ══════════════════════════════════════════════════════════
def build_dashboard(parent, is_fs):
    _build_ip_footer(parent)   # packs side="bottom"
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(side="top", fill="both", expand=True)
    _build_mode_dashboard(f, is_fs)

# ── MODE: Dashboard (tabbed) ─────────────────────────────
def _build_mode_dashboard(parent, is_fs):
    global btn_start, btn_stop, btn_sync, log_box, chat_box, cmd_entry, chat_toggle_btn

    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="both", expand=True)

    # Sub-tab button bar
    bar = ctk.CTkFrame(outer, fg_color=T["card"], corner_radius=0,
                       border_color=T["border"], border_width=1)
    bar.pack(side="top", fill="x")

    # Single content slot — we destroy/recreate on each tab switch
    _slot = [None]   # holds the current content frame
    _active = [None]
    dsub_btns = {}

    BUILDERS = {
        "control":  _build_dsub_control,
        "playit":   _build_mode_playit,
        "remote":   _build_mode_remote,
    }

    def show_dsub(name):
        if name == _active[0]:
            return
        _active[0] = name
        # Update button styles
        for n, b in dsub_btns.items():
            b.configure(fg_color=T["sync"] if n==name else "transparent",
                        text_color="#000" if n==name else T["muted"])
        # Destroy old content, build fresh
        if _slot[0] is not None:
            try: _slot[0].destroy()
            except: pass
        frame = ctk.CTkFrame(outer, fg_color="transparent")
        frame.pack(side="top", fill="both", expand=True)
        _slot[0] = frame
        try:
            BUILDERS[name](frame)
        except Exception as e:
            import traceback
            ctk.CTkLabel(frame, text=f"Error: {e}", text_color=T["stop"],
                         font=ctk.CTkFont(size=12)).pack(pady=20)
            traceback.print_exc()

    DSUBS = [
        ("control",  "⚙ Control"),
        ("playit",   "🚇 playit.gg"),
        ("remote",   "📱 Remote"),
    ]
    for key, label in DSUBS:
        b = ctk.CTkButton(bar, text=label, height=28, width=100,
                          font=ctk.CTkFont(size=10, weight="bold"),
                          corner_radius=0, fg_color="transparent",
                          text_color=T["muted"], hover_color=T["border"],
                          command=lambda k=key: show_dsub(k))
        b.pack(side="left", padx=1, pady=4)
        dsub_btns[key] = b

    show_dsub("control")
    globals()["_dsub_goto_remote"] = lambda: show_dsub("remote")


# ── DSUB builders — pure pack, no grid mixing ─────────────

def _build_dsub_control(parent):
    global btn_start, btn_stop, btn_sync, log_box, chat_box, cmd_entry, chat_toggle_btn

    # outer scrollable so stats graph fits when expanded
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", border_width=0)
    scroll.pack(fill="both", expand=True)

    # ── Two-column body ───────────────────────────────────
    body = ctk.CTkFrame(scroll, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=16, pady=10)
    ctrl_col = 1 if log_left else 0
    log_col  = 0 if log_left else 1
    body.columnconfigure(ctrl_col, weight=0, minsize=330)
    body.columnconfigure(log_col,  weight=1)
    body.rowconfigure(0, weight=1)

    # ── LEFT ──────────────────────────────────────────────
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=ctrl_col, sticky="nsew",
              padx=(8,0) if log_left else (0,8))

    def make_btn(par, text, desc, color, cmd):
        f = ctk.CTkFrame(par, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(f, fg_color="transparent"); inner.pack(fill="x", padx=12, pady=8)
        top_r = ctk.CTkFrame(inner, fg_color="transparent"); top_r.pack(fill="x")
        ctk.CTkLabel(top_r, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=color, anchor="w").pack(side="left")
        b = ctk.CTkButton(top_r, text="Run", width=64, height=26,
                          font=ctk.CTkFont(size=11), fg_color=color,
                          hover_color=color, text_color="#000", command=cmd)
        b.pack(side="right")
        ctk.CTkLabel(inner, text=desc, font=ctk.CTkFont(size=10),
                     text_color=T["muted"], anchor="w",
                     wraplength=260, justify="left").pack(anchor="w", pady=(2,0))
        return b

    btn_start = make_btn(left, "Start Server",  "Git pull then launch with Aikar JVM flags",   T["start"], lambda: threading.Thread(target=start_server, daemon=True).start())
    btn_stop  = make_btn(left, "Stop Server",   "Kill Java process then push world to GitHub",  T["stop"],  lambda: threading.Thread(target=stop_server,  daemon=True).start())
    btn_sync  = make_btn(left, "Sync & Upload", "Git add all, commit Manual Sync, push",        T["sync"],  lambda: threading.Thread(target=sync_git,      daemon=True).start())

    # Quick commands
    qf = ctk.CTkFrame(left, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    qf.pack(fill="x", pady=(8,3))
    ctk.CTkLabel(qf, text="QUICK COMMANDS",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,4))
    ctk.CTkFrame(qf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    qgrid = ctk.CTkFrame(qf, fg_color="transparent"); qgrid.pack(fill="x", padx=10, pady=8)
    QUICK_CMDS = [
        ("Save World",    "save-all",             T["sync"]),
        ("Player List",   "list",                  T["sync"]),
        ("Check TPS",     "tps",                   T["sync"]),
        ("Set Day",       "time set day",           T["hand"]),
        ("Set Night",     "time set night",         T["hand"]),
        ("Clear Weather", "weather clear",          T["hand"]),
        ("Hard Mode",     "difficulty hard",        T["stop"]),
        ("Peaceful",      "difficulty peaceful",    T["start"]),
        ("Safe Stop",     "stop",                   T["stop"]),
        ("Reload",        "reload",                 T["muted"]),
    ]
    for i, (label, cmd_txt, color) in enumerate(QUICK_CMDS):
        ri, ci = i // 2, i % 2
        ctk.CTkButton(qgrid, text=label, width=130, height=26,
                      font=ctk.CTkFont(size=10), corner_radius=6,
                      fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=color,
                      hover_color=T["border"],
                      command=lambda c=cmd_txt: send_server_cmd(c)
                      ).grid(row=ri, column=ci, padx=3, pady=2, sticky="ew")
        qgrid.columnconfigure(ci, weight=1)

    # Live stat pills
    sc_f = ctk.CTkFrame(left, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=10)
    sc_f.pack(fill="x", pady=(6,0))
    sc_hdr = ctk.CTkFrame(sc_f, fg_color="transparent"); sc_hdr.pack(fill="x", padx=12, pady=(8,4))
    ctk.CTkLabel(sc_hdr, text="LIVE STATS",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=T["muted"]).pack(side="left")
    # ∨ expand graph toggle
    _graph_open = [False]
    _graph_slot  = [None]
    _hist = {"tps":[], "ram":[], "cpu":[]}  # rolling 60-point history

    def _toggle_graph():
        _graph_open[0] = not _graph_open[0]
        tog_btn.configure(text="∧" if _graph_open[0] else "∨")
        if _graph_open[0]:
            _graph_slot[0] = ctk.CTkFrame(sc_f, fg_color=T["bg"],
                                           border_color=T["border"], border_width=1,
                                           corner_radius=8, height=160)
            _graph_slot[0].pack(fill="x", padx=12, pady=(0,10))
            _graph_slot[0].pack_propagate(False)
            _draw_graph()
        else:
            if _graph_slot[0]:
                _graph_slot[0].destroy(); _graph_slot[0] = None

    tog_btn = ctk.CTkButton(sc_hdr, text="∨", width=28, height=20,
                             font=ctk.CTkFont(size=12), fg_color="transparent",
                             border_width=1, border_color=T["border"],
                             text_color=T["muted"], hover_color=T["border"],
                             command=_toggle_graph)
    tog_btn.pack(side="right")
    ctk.CTkFrame(sc_f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)

    sg = ctk.CTkFrame(sc_f, fg_color="transparent"); sg.pack(fill="x", padx=10, pady=8)
    _stat_lbls = {}
    for key, label in [("players","Players"),("tps","TPS"),("uptime","Uptime"),("ram_srv","RAM")]:
        cell = ctk.CTkFrame(sg, fg_color=T["bg"], border_color=T["border"],
                            border_width=1, corner_radius=8)
        cell.pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=9),
                     text_color=T["muted"]).pack(pady=(5,0))
        lbl = ctk.CTkLabel(cell, text=perf.get(key,"--"),
                           font=ctk.CTkFont(size=16, weight="bold"), text_color=T["text"])
        lbl.pack(pady=(0,5)); _stat_lbls[key] = lbl

    def _parse_float(val):
        try: return float(str(val).replace("%","").replace(" MB","").replace(" GB","").split()[0])
        except: return 0.0

    def _draw_graph():
        gf = _graph_slot[0]
        if gf is None: return
        try: import tkinter as _tk
        except: return
        for w in gf.winfo_children(): w.destroy()
        W, H = 380, 140
        canvas = _tk.Canvas(gf, width=W, height=H, bg=T["bg"], highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=4, pady=4)
        series = [
            ("TPS",   _hist["tps"],  T["start"],  20.0),
            ("RAM%",  _hist["ram"],  T["sync"],   100.0),
            ("CPU%",  _hist["cpu"],  T["stop"],   100.0),
        ]
        def _draw():
            canvas.delete("all")
            cw = canvas.winfo_width() or W
            ch = canvas.winfo_height() or H
            pad = 28
            # axes
            canvas.create_line(pad, 4, pad, ch-pad, fill=T["border"], width=1)
            canvas.create_line(pad, ch-pad, cw-6, ch-pad, fill=T["border"], width=1)
            for s_label, s_data, s_color, s_max in series:
                pts = s_data[-60:] if s_data else []
                if len(pts) < 2: continue
                xs = [pad + (cw-pad-6)*i/(len(pts)-1) for i in range(len(pts))]
                ys = [(ch-pad) - (ch-pad-4)*min(v,s_max)/s_max for v in pts]
                for i in range(len(pts)-1):
                    canvas.create_line(xs[i],ys[i],xs[i+1],ys[i+1], fill=s_color, width=2)
                # label last value
                canvas.create_text(cw-5, ys[-1], text=f"{s_label}:{pts[-1]:.0f}",
                                   fill=s_color, font=("Consolas",8), anchor="e")
        canvas.bind("<Configure>", lambda e: _draw())
        _draw()

    def _tick():
        # update pills
        for k,l in _stat_lbls.items():
            try: l.configure(text=perf.get(k,"--"))
            except: return
        # update history
        try:
            _hist["tps"].append(_parse_float(perf.get("tps",0)))
            _hist["ram"].append(_parse_float(perf.get("ram_pct",0)))
            _hist["cpu"].append(_parse_float(perf.get("cpu_srv",0)))
            for h in _hist.values():
                if len(h) > 60: del h[:-60]
        except: pass
        if _graph_open[0]: _draw_graph()
        try: list(_stat_lbls.values())[0].after(2000, _tick)
        except: pass
    _tick()

    # World size row
    wf = ctk.CTkFrame(left, fg_color="transparent"); wf.pack(fill="x", pady=(6,0))
    _wlbl = ctk.CTkLabel(wf, text="Size: calculating…", font=ctk.CTkFont(size=10),
                          text_color=T["muted"]); _wlbl.pack(side="left")
    _blbl = ctk.CTkLabel(wf, text="", font=ctk.CTkFont(size=10),
                          text_color=T["muted"]); _blbl.pack(side="right")
    _bkup_next_ts = [None]
    def _calc_world():
        try:
            s2 = load_settings(); path = s2.get("srv_path", _DEFAULT_SRV)
            dirs = [os.path.join(path,d) for d in ("world","world_nether","world_the_end")
                    if os.path.isdir(os.path.join(path,d))]
            total = sum(sum(os.path.getsize(os.path.join(r,fn))
                            for r,_,fs in os.walk(d) for fn in fs) for d in dirs)
            mb = total/1048576
            app.after(0, _wlbl.configure, {"text": ("Size: %.0f MB"%mb) if mb<1024 else ("Size: %.2f GB"%(mb/1024))})
        except: app.after(0, _wlbl.configure, {"text": "Size: --"})
    def _tick_bkp():
        try:
            if _bkup_next_ts[0]:
                rem = max(0, int(_bkup_next_ts[0]-time.time()))
                m2,s3=divmod(rem,60)
                _blbl.configure(text="Backup in %02d:%02d"%(m2,s3),
                                 text_color=T["sync"] if rem<300 else T["muted"])
            _blbl.after(5000, _tick_bkp)
        except: pass
    globals()["_dashboard_set_backup_ts"] = lambda ts: _bkup_next_ts.__setitem__(0, ts)
    threading.Thread(target=_calc_world, daemon=True).start()
    app.after(1000, _tick_bkp)

    # ── RIGHT: log + chat + console ───────────────────────
    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=log_col, sticky="nsew")
    right.rowconfigure(0, weight=1); right.rowconfigure(1, weight=0); right.rowconfigure(2, weight=0)
    right.columnconfigure(0, weight=1)

    # Activity log
    lf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    lf.grid(row=0, column=0, sticky="nsew", pady=(0,5))
    lt = ctk.CTkFrame(lf, fg_color="transparent"); lt.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(side="left")
    for txt2, fn in [
        ("Swap",  lambda: _toggle_log_left()),
        ("Copy",  lambda: (app.clipboard_clear(), app.clipboard_append(log_box.get("1.0","end")), show_toast("Copied!", T["sync"]))),
        ("Clear", lambda: (log_box.configure(state="normal"), log_box.delete("1.0","end"), log_box.configure(state="disabled"))),
    ]:
        ctk.CTkButton(lt, text=txt2, width=44, height=20,
                      font=ctk.CTkFont(size=10), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=fn).pack(side="right", padx=2)
    ctk.CTkFrame(lf, height=1, fg_color=T["border"]).pack(fill="x", padx=10)
    log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),
                              wrap="word", state="disabled",
                              fg_color="transparent", text_color=T["text"])
    log_box.pack(fill="both", expand=True, padx=6, pady=(3,6))
    log_box.configure(state="normal")
    # log_history already contains everything (buffered lines + live lines)
    if log_history.strip(): log_box.insert("1.0", log_history)
    _log_buffer.clear()
    log_box.configure(state="disabled"); log_box.see("end")

    # Chat card
    cf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    cf.grid(row=1, column=0, sticky="ew", pady=(0,5))
    ct = ctk.CTkFrame(cf, fg_color="transparent"); ct.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(ct, text="SERVER CHAT & EVENTS",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=T["muted"]).pack(side="left")
    chat_toggle_btn = ctk.CTkButton(ct, text="Hide" if show_chat else "Show",
                                     width=44, height=20, font=ctk.CTkFont(size=10),
                                     fg_color="transparent", border_width=1,
                                     border_color=T["border"], text_color=T["muted"],
                                     hover_color=T["border"], command=_toggle_chat)
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
                               text_color=T["text"], height=100)
    if show_chat: chat_box.pack(fill="x", padx=6, pady=(3,6))
    if chat_history.strip():
        chat_box.configure(state="normal"); chat_box.insert("1.0", chat_history)
        chat_box.configure(state="disabled"); chat_box.see("end")

    # Console / command entry
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


def _build_dsub_log(parent):
    global log_box, chat_box, chat_toggle_btn

    # Log card — fills most of the space
    lf = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    lf.pack(fill="both", expand=True, padx=12, pady=(8,4))
    # header
    lt = ctk.CTkFrame(lf, fg_color="transparent"); lt.pack(fill="x", padx=10, pady=(7,0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(side="left")
    for txt2, fn in [
        ("Swap",  lambda: (_toggle_log_left())),
        ("Copy",  lambda: (app.clipboard_clear(), app.clipboard_append(log_box.get("1.0","end")), show_toast("Copied!", T["sync"]))),
        ("Clear", lambda: (log_box.configure(state="normal"), log_box.delete("1.0","end"), log_box.configure(state="disabled"))),
    ]:
        ctk.CTkButton(lt, text=txt2, width=44, height=20, font=ctk.CTkFont(size=10),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=fn).pack(side="right", padx=2)
    ctk.CTkFrame(lf, height=1, fg_color=T["border"]).pack(fill="x", padx=10)
    log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),
                              wrap="word", state="disabled", fg_color="transparent", text_color=T["text"])
    log_box.pack(fill="both", expand=True, padx=6, pady=(3,6))
    log_box.configure(state="normal")
    for line in _log_buffer: log_box.insert("end", line)
    _log_buffer.clear()
    if log_history.strip(): log_box.insert("1.0", log_history)
    log_box.configure(state="disabled"); log_box.see("end")

    # Chat card — fixed height at bottom
    cf = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    cf.pack(fill="x", padx=12, pady=(0,8))
    ct = ctk.CTkFrame(cf, fg_color="transparent"); ct.pack(fill="x", padx=10, pady=(7,0))
    ctk.CTkLabel(ct, text="CHAT & EVENTS", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(side="left")
    chat_toggle_btn = ctk.CTkButton(ct, text="Hide" if show_chat else "Show", width=40, height=20,
                                     font=ctk.CTkFont(size=10), fg_color="transparent",
                                     border_width=1, border_color=T["border"],
                                     text_color=T["muted"], hover_color=T["border"],
                                     command=_toggle_chat)
    chat_toggle_btn.pack(side="right")
    chat_box = ctk.CTkTextbox(cf, font=ctk.CTkFont(size=11, family="Consolas"),
                               wrap="word", state="disabled", fg_color="transparent",
                               text_color=T["text"], height=80)
    if show_chat:
        chat_box.pack(fill="x", padx=6, pady=(3,6))
    if chat_history.strip():
        chat_box.configure(state="normal"); chat_box.insert("1.0", chat_history)
        chat_box.configure(state="disabled"); chat_box.see("end")


def _build_dsub_commands(parent):
    card = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=12)
    card.pack(fill="both", expand=True, padx=12, pady=8)
    ctk.CTkLabel(card, text="QUICK COMMANDS", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10,4))
    ctk.CTkFrame(card, height=1, fg_color=T["border"]).pack(fill="x", padx=14)

    QUICK = [
        ("💾 Save World","save-all"),    ("📋 List Players","list"),
        ("📊 Check TPS","tps"),          ("🌅 Set Day","time set day"),
        ("🌙 Set Night","time set night"),("☀ Clear Weather","weather clear"),
        ("🌧 Rain","weather rain"),       ("🌩 Thunder","weather thunder"),
        ("⚔ Hard","difficulty hard"),    ("🕊 Peaceful","difficulty peaceful"),
        ("⏹ Safe Stop","stop"),          ("🔁 Reload","reload"),
        ("🛡 WL On","whitelist on"),      ("🔓 WL Off","whitelist off"),
        ("🎮 Creative","defaultgamemode creative"),("⛏ Survival","defaultgamemode survival"),
        ("🔧 Op…","op "),                ("🚫 Deop…","deop "),
    ]
    ROW_SIZE = 3
    row_f = None
    for i, (label, cmd) in enumerate(QUICK):
        if i % ROW_SIZE == 0:
            row_f = ctk.CTkFrame(card, fg_color="transparent")
            row_f.pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(row_f, text=label, height=30, font=ctk.CTkFont(size=10),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["text"], hover_color=T["border"],
                      command=lambda c=cmd: (send_server_cmd(c) if not c.endswith(" ")
                                             else show_toast("Type full command in Console", T["hand"]))
                      ).pack(side="left", fill="x", expand=True, padx=2)


def _build_dsub_console(parent):
    global cmd_entry
    card = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=12)
    card.pack(fill="both", expand=True, padx=12, pady=8)
    # header
    hdr = ctk.CTkFrame(card, fg_color="transparent"); hdr.pack(fill="x", padx=10, pady=(7,0))
    ctk.CTkLabel(hdr, text="CONSOLE", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(side="left")
    ctk.CTkButton(hdr, text="Clear", width=50, height=22, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: (log_box.configure(state="normal") if log_box else None,
                                   log_box.delete("1.0","end") if log_box else None,
                                   log_box.configure(state="disabled") if log_box else None)
                  ).pack(side="right")
    ctk.CTkFrame(card, height=1, fg_color=T["border"]).pack(fill="x", padx=10)
    con_box = ctk.CTkTextbox(card, font=ctk.CTkFont(size=11, family="Consolas"),
                              wrap="word", state="disabled", fg_color="transparent", text_color=T["text"])
    con_box.pack(fill="both", expand=True, padx=6, pady=(3,0))
    if log_history.strip():
        con_box.configure(state="normal"); con_box.insert("1.0", log_history)
        con_box.configure(state="disabled"); con_box.see("end")
    def _sync():
        try:
            if log_box:
                txt = log_box.get("1.0","end")
                con_box.configure(state="normal"); con_box.delete("1.0","end")
                con_box.insert("1.0", txt); con_box.configure(state="disabled"); con_box.see("end")
            con_box.after(1000, _sync)
        except: pass
    app.after(1200, _sync)
    # command entry
    ce = ctk.CTkFrame(card, fg_color=T["bg"]); ce.pack(fill="x")
    ctk.CTkFrame(ce, height=1, fg_color=T["border"]).pack(fill="x")
    ci = ctk.CTkFrame(ce, fg_color="transparent"); ci.pack(fill="x", padx=10, pady=8)
    ctk.CTkLabel(ci, text="/", font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=T["muted"], width=14).pack(side="left")
    cmd_entry = ctk.CTkEntry(ci, font=ctk.CTkFont(size=12, family="Consolas"),
                              fg_color=T["card"], border_color=T["border"], text_color=T["text"],
                              placeholder_text="command…", height=30)
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(4,6))
    cmd_entry.bind("<Return>", lambda e: send_command())
    ctk.CTkButton(ci, text="Send", width=60, height=30, font=ctk.CTkFont(size=12),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=send_command).pack(side="left")


def _build_dsub_multi(parent):
    """Multi-server control embedded in dashboard tab."""
    MAX = 3
    slots = {}
    for i in range(MAX):
        slots[i] = {"proc":None,"stdin":None,"path_var":ctk.StringVar(value=""),
                    "log_box":None,"status":None,"running":False}

    # Header
    hdr = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                       border_width=1, corner_radius=0)
    hdr.pack(fill="x")
    ctk.CTkLabel(hdr, text="⊞ MULTI SERVER CONTROL",
                 font=ctk.CTkFont(size=13, weight="bold"), text_color=T["hand"]).pack(side="left", padx=12, pady=7)
    ctk.CTkLabel(hdr, text="— up to 3 servers simultaneously",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

    # Remote server button
    def _open_remote_tab():
        try: parent.master.master.master  # walk up to find show_dsub
        except: pass
        # Trigger via show_dsub in the enclosing _build_mode_dashboard scope
        # We use a global event flag instead
        globals().get("_dsub_goto_remote", lambda: None)()
    ctk.CTkButton(hdr, text="📱 Remote Dashboard", width=130, height=26,
                  font=ctk.CTkFont(size=10), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=_open_remote_tab).pack(side="right", padx=8)

    # Server columns
    ca = ctk.CTkFrame(parent, fg_color="transparent"); ca.pack(fill="both", expand=True, padx=3, pady=3)
    for i in range(MAX): ca.columnconfigure(i, weight=1, uniform="col")
    ca.rowconfigure(0, weight=1)

    def _mclog(slot, msg):
        lb = slots[slot]["log_box"]
        if lb is None: return
        try: lb.configure(state="normal"); lb.insert("end", msg+"\n"); lb.configure(state="disabled"); lb.see("end")
        except: pass
    def _mcst(slot, txt, col):
        lbl = slots[slot]["status"]
        if lbl:
            try: lbl.configure(text=txt, text_color=col)
            except: pass
    def _read_mc(slot, proc):
        for raw in iter(proc.stdout.readline, ""):
            if not raw: break
            app.after(0, _mclog, slot, raw.rstrip())
        app.after(0, _mcst, slot, "● Stopped", T["stop"])
        slots[slot].update({"running":False,"proc":None,"stdin":None})
    def _start_mc(slot):
        path = slots[slot]["path_var"].get().strip()
        if not path or not os.path.isdir(path): show_toast(f"Server {slot+1}: invalid folder.", T["stop"]); return
        if slots[slot]["running"]: show_toast(f"Server {slot+1} already running.", T["muted"]); return
        s = load_settings(); java = s.get("java_path", _DEFAULT_JAVA)
        jar = os.path.join(path, "server.jar")
        if not os.path.exists(jar): show_toast(f"Server {slot+1}: no server.jar.", T["stop"]); return
        if not _check_eula(path): return
        try:
            kw = {"cwd":path,"stdin":subprocess.PIPE,"stdout":subprocess.PIPE,
                  "stderr":subprocess.STDOUT,"text":True,"bufsize":1}
            if IS_WIN: kw["creationflags"] = _NO_WIN
            proc = subprocess.Popen([java,"-Xms512M","-Xmx2G","-XX:+UseG1GC","-jar",jar,"--nogui"], **kw)
            slots[slot].update({"proc":proc,"stdin":proc.stdin,"running":True})
            _mcst(slot, "● Running", T["start"])
            threading.Thread(target=_read_mc, args=(slot,proc), daemon=True).start()
        except Exception as ex: show_toast(f"Server {slot+1} failed: {ex}", T["stop"])
    def _stop_mc(slot):
        proc = slots[slot]["proc"]
        if proc:
            try: slots[slot]["stdin"].write("stop\n"); slots[slot]["stdin"].flush()
            except: pass
            app.after(3000, lambda p=proc: p.terminate() if p.poll() is None else None)
        slots[slot].update({"running":False,"proc":None,"stdin":None})
        _mcst(slot, "● Stopped", T["stop"])

    for i in range(MAX):
        col = ctk.CTkFrame(ca, fg_color=T["card"], border_color=T["border"],
                           border_width=1, corner_radius=10)
        col.grid(row=0, column=i, sticky="nsew", padx=3, pady=0)
        col.rowconfigure(2, weight=1); col.columnconfigure(0, weight=1)
        h = ctk.CTkFrame(col, fg_color=T["bg"], corner_radius=6)
        h.grid(row=0, column=0, sticky="ew", padx=6, pady=(6,3))
        ctk.CTkLabel(h, text=f"Server {i+1}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=8, pady=5)
        st = ctk.CTkLabel(h, text="● Stopped", font=ctk.CTkFont(size=10, weight="bold"),
                          text_color=T["stop"]); st.pack(side="right", padx=8)
        slots[i]["status"] = st
        pf = ctk.CTkFrame(col, fg_color="transparent")
        pf.grid(row=1, column=0, sticky="ew", padx=6, pady=(0,3)); pf.columnconfigure(0, weight=1)
        ctk.CTkEntry(pf, textvariable=slots[i]["path_var"], height=26,
                     font=ctk.CTkFont(size=10, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                     placeholder_text=f"Server {i+1} folder…"
                     ).grid(row=0, column=0, sticky="ew", padx=(0,3))
        ctk.CTkButton(pf, text="…", width=26, height=26, font=ctk.CTkFont(size=11),
                      corner_radius=5, fg_color=T["bg"], border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                      command=lambda s=i: slots[s]["path_var"].set(
                          _tk_fd.askdirectory(title=f"Server {s+1}") or slots[s]["path_var"].get())
                      ).grid(row=0, column=1)
        br = ctk.CTkFrame(pf, fg_color="transparent")
        br.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3,0))
        ctk.CTkButton(br, text="▶ Start", height=24, font=ctk.CTkFont(size=10),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000",
                      command=lambda s=i: threading.Thread(target=_start_mc, args=(s,), daemon=True).start()
                      ).pack(side="left", expand=True, fill="x", padx=(0,2))
        ctk.CTkButton(br, text="■ Stop", height=24, font=ctk.CTkFont(size=10),
                      fg_color=T["stop"], hover_color=T["stop"], text_color="#fff",
                      command=lambda s=i: _stop_mc(s)
                      ).pack(side="left", expand=True, fill="x", padx=(2,0))
        lb = ctk.CTkTextbox(col, font=ctk.CTkFont(size=10, family="Consolas"),
                            wrap="word", state="disabled", fg_color=T["bg"], text_color=T["text"])
        lb.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0,6))
        slots[i]["log_box"] = lb

    # Command bar
    chatbar = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                           border_width=1, corner_radius=0)
    chatbar.pack(fill="x"); chatbar.columnconfigure(2, weight=1)
    tgt = ctk.StringVar(value="Server 1")
    ctk.CTkLabel(chatbar, text="Send to:", font=ctk.CTkFont(size=11),
                 text_color=T["muted"]).grid(row=0, column=0, padx=(8,4), pady=7)
    ctk.CTkOptionMenu(chatbar, values=["Server 1","Server 2","Server 3","All Servers"],
                      variable=tgt, font=ctk.CTkFont(size=11), width=110, height=28,
                      fg_color=T["bg"], button_color=T["border"],
                      button_hover_color=T["muted"], text_color=T["text"],
                      dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"]
                      ).grid(row=0, column=1, padx=(0,5), pady=7)
    mc_cmd = ctk.CTkEntry(chatbar, height=28, font=ctk.CTkFont(size=12),
                           fg_color=T["bg"], border_color=T["border"],
                           text_color=T["text"], placeholder_text="command…")
    mc_cmd.grid(row=0, column=2, sticky="ew", padx=(0,5), pady=7)
    def _mc_send(_e=None):
        cmd = mc_cmd.get().strip()
        if not cmd: return
        t = tgt.get(); targets = list(range(MAX)) if t=="All Servers" else [int(t.split()[-1])-1]
        for s in targets:
            si = slots[s]["stdin"]
            if si:
                try: si.write(cmd+"\n"); si.flush(); app.after(0, _mclog, s, f">> {cmd}")
                except Exception as ex: app.after(0, _mclog, s, f"[error] {ex}")
            else: app.after(0, _mclog, s, f"[Server {s+1} not running]")
        mc_cmd.delete(0,"end")
    mc_cmd.bind("<Return>", _mc_send)
    ctk.CTkButton(chatbar, text="Send", width=66, height=28, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_mc_send).grid(row=0, column=3, padx=(0,8), pady=7)


def _build_dsub_stats(parent):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="both", expand=True)
    _build_perf_panel(f)


# ── Kept for MC Ctrl compat (unused now) ──────────────────
def _build_mode_mcctrl(parent):
    _build_mode_dashboard(parent, False)

def _build_log_area(right):
    pass  # no longer used

# ── MODE: Network ─────────────────────────────────────────
def _build_mode_network(parent):
    import socket
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s2.connect(("8.8.8.8",80))
        local_ip = s2.getsockname()[0]; s2.close()
    except: local_ip = "127.0.0.1"
    port_var   = ctk.StringVar(value=load_settings().get("server_port","25565"))
    ext_ip_var = ctk.StringVar(value="Fetching…")
    port_var.trace_add("write", lambda *_: update_setting("server_port", port_var.get()))

    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12,0))
    ctk.CTkLabel(hf, text="CONNECTION INFO", font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["text"]).pack(anchor="w", padx=14, pady=(12,4))
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=14)

    gf = ctk.CTkFrame(scroll, fg_color="transparent"); gf.pack(fill="x", padx=18, pady=8)
    gf.columnconfigure((0,1,2), weight=1)

    def copy_val(v): app.clipboard_clear(); app.clipboard_append(v); show_toast(f"Copied: {v}", T["sync"])
    def get_lan(): return f"{local_ip}:{port_var.get()}"
    def get_ext(): return ext_ip_var.get()

    for col,(title,sub,color,get_fn) in enumerate([
        ("PORT","",T["muted"],lambda: port_var.get()),
        ("LOCAL (LAN)","Same WiFi",T["start"],get_lan),
        ("EXTERNAL","Over internet",T["sync"],get_ext),
    ]):
        c = ctk.CTkFrame(gf, fg_color=T["card"], border_color=color, border_width=2, corner_radius=12)
        c.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=color).pack(anchor="w", padx=12, pady=(10,0))
        if sub: ctk.CTkLabel(c, text=sub, font=ctk.CTkFont(size=9), text_color=T["muted"]).pack(anchor="w", padx=12)
        ctk.CTkFrame(c, height=1, fg_color=T["border"]).pack(fill="x", padx=8, pady=5)
        if col == 0:
            ctk.CTkEntry(c, textvariable=port_var, height=28,
                         font=ctk.CTkFont(size=13,family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"], text_color=T["text"]
                         ).pack(fill="x", padx=12, pady=(0,10))
        else:
            val_lbl = ctk.CTkLabel(c, text=get_fn() if col==1 else "…",
                                   font=ctk.CTkFont(size=12,weight="bold",family="Consolas"),
                                   text_color=color)
            val_lbl.pack(padx=12, pady=(2,5))
            if col == 1:
                def _upd_lan(*_,lbl=val_lbl): lbl.configure(text=get_lan())
                port_var.trace_add("write", _upd_lan)
            else:
                ext_ip_var.trace_add("write", lambda *_,lbl=val_lbl: lbl.configure(text=ext_ip_var.get()))
            ctk.CTkButton(c, text="Copy", height=26, font=ctk.CTkFont(size=11),
                          fg_color=color, hover_color=color, text_color="#000",
                          command=lambda g=get_fn: copy_val(g())
                          ).pack(fill="x", padx=12, pady=(0,10))

    def _fetch_ext():
        try:
            ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
            sv = load_settings().get("custom_ip","")
            app.after(0, ext_ip_var.set, f"{sv}:{port_var.get()}" if sv else f"{ip}:{port_var.get()}")
        except: app.after(0, ext_ip_var.set, "unavailable")
    threading.Thread(target=_fetch_ext, daemon=True).start()

    guide = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=12)
    guide.pack(fill="x", padx=18, pady=(0,12))
    ctk.CTkLabel(guide, text="GUIDE", font=ctk.CTkFont(size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,4))
    ctk.CTkFrame(guide, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    ctk.CTkLabel(guide, text=(
        "1. Same WiFi  →  share LOCAL address.\n"
        "2. Internet friends  →  share EXTERNAL (requires port-forward 25565 TCP on router).\n"
        "3. Using playit.gg  →  switch to playit.gg mode in the Ctrl Mode selector below.\n"
        "4. Local test  →  localhost:25565"
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], justify="left", wraplength=860
    ).pack(anchor="w", padx=12, pady=(6,10))

# ── MODE: playit.gg ───────────────────────────────────────
def _build_mode_playit(parent):
    global playit_proc, playit_tunnel, playit_log_lines
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)

    def card(title, sub=None):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=12); f.pack(fill="x", padx=18, pady=(10,0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=12, pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        if sub: ctk.CTkLabel(h, text=sub, font=ctk.CTkFont(size=10),
                              text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        b = ctk.CTkFrame(f, fg_color="transparent"); b.pack(fill="x", padx=12, pady=(8,10))
        return b, h

    ab, _ = card("About playit.gg")
    ctk.CTkLabel(ab, text=(
        "playit.gg is a free tunnel that gives your server a public address without port forwarding.\n"
        "Friends connect via a .ply.gg address. Free plan supports up to 3 tunnels."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")

    sb, _ = card("Setup")
    s = load_settings(); pt_var = ctk.StringVar(value=s.get("playit_path",""))
    pt_var.trace_add("write", lambda *_: update_setting("playit_path", pt_var.get()))
    pt_st = ctk.CTkLabel(sb, text="", font=ctk.CTkFont(size=11), text_color=T["muted"])

    def _browse_pt():
        p = _tk_fd.askopenfilename(title="Select playit binary", filetypes=[("All","*.*")])
        if p: pt_var.set(p)

    def _dl_pt():
        fname = "playit-windows.exe" if IS_WIN else ("playit-darwin" if IS_MAC else "playit-linux-amd64")
        dest_name = "playit.exe" if IS_WIN else "playit"
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), dest_name)
        pt_st.configure(text="Downloading…", text_color=T["sync"])
        def _do():
            url = f"https://github.com/playit-cloud/playit-agent/releases/latest/download/{fname}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"MC-CTRL/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    with open(dest,"wb") as f2: f2.write(r.read())
                if not IS_WIN: os.chmod(dest, 0o755)
                pt_var.set(dest)
                app.after(0, pt_st.configure, {"text":"Downloaded!", "text_color":T["start"]})
            except Exception as ex: app.after(0, pt_st.configure, {"text":f"Failed: {ex}", "text_color":T["stop"]})
        threading.Thread(target=_do, daemon=True).start()

    pr = ctk.CTkFrame(sb, fg_color="transparent"); pr.pack(fill="x", pady=(0,4))
    ctk.CTkEntry(pr, textvariable=pt_var, height=28, font=ctk.CTkFont(size=11,family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="path/to/playit").pack(side="left", fill="x", expand=True, padx=(0,6))
    ctk.CTkButton(pr, text="Browse", width=66, height=28, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_browse_pt).pack(side="left", padx=(0,5))
    ctk.CTkButton(pr, text="Auto-Download", height=28, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_dl_pt).pack(side="left")
    pt_st.pack(anchor="w", pady=(4,0))

    _ADDR_RE  = re.compile(r'((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg|joinmc\.link|mc\.gg)(?::\d+)?)', re.I)
    _CLAIM_RE = re.compile(r'(https?://[^\s]+(?:playit|claim|tunnel)[^\s]*)', re.I)
    _ANSI_RE  = re.compile(r'\x1b(?:\[[0-9;]*[mABCDEFGHJKSTfhilmnprsuu]|\][^\x07]*\x07|[()][AB012]|[=>])')

    cb, ch = card("Tunnel Control")
    tun_st   = ctk.CTkLabel(cb, text="● Stopped", font=ctk.CTkFont(size=13,weight="bold"), text_color=T["stop"])
    tun_st.pack(side="left")
    tun_addr = ctk.CTkLabel(cb, text="", font=ctk.CTkFont(size=13,family="Consolas"), text_color=T["start"])
    tun_addr.pack(side="left", padx=(12,0))

    def _set_tst(txt, col):
        try: tun_st.configure(text=txt, text_color=col)
        except: pass
    def _set_addr(addr):
        global playit_tunnel; playit_tunnel = addr
        try: tun_addr.configure(text=addr or ""); (show_toast(f"Tunnel: {addr}", T["start"]) if addr else None)
        except: pass

    _PT_Q = []; _PT_FL = [False]
    def _flush_pt():
        _PT_FL[0] = False
        if not _PT_Q: return
        batch = _PT_Q[:]; _PT_Q.clear()
        try:
            pt_log.configure(state="normal"); pt_log.insert("end", "\n".join(batch)+"\n")
            total = int(pt_log.index("end-1c").split(".")[0])
            if total > 300: pt_log.delete("1.0", f"{total-300}.0")
            pt_log.configure(state="disabled"); pt_log.see("end")
        except: pass
    def _qlog(line):
        _PT_Q.append(line)
        if not _PT_FL[0]: _PT_FL[0]=True; app.after(120, _flush_pt)
    def _handle(raw):
        try: line = raw.decode("utf-8", errors="replace").rstrip()
        except: line = repr(raw)
        clean = _ANSI_RE.sub("", line).strip()
        if not clean: return
        playit_log_lines.append(clean)
        if len(playit_log_lines) > 300: del playit_log_lines[:150]
        m = _ADDR_RE.search(clean)
        if m: app.after(0, _set_addr, m.group(1))
        cm = _CLAIM_RE.search(clean)
        if cm: _qlog(f"[MC CTRL] CLAIM URL: {cm.group(1)}"); app.after(0, show_toast, "Open claim URL!", T["hand"], 8000)
        _qlog(clean)
    def _read_pt(proc):
        for raw in iter(proc.stdout.readline, b""):
            if raw: _handle(raw)
        code = proc.wait()
        app.after(0, _qlog, f"[MC CTRL] Exited with code {code}.")
        app.after(0, _set_tst, "● Stopped", T["stop"])
    def _read_stderr_pt(proc):
        for raw in iter(proc.stderr.readline, b""):
            if raw: _handle(raw)

    def _start_pt():
        global playit_proc
        exe = pt_var.get().strip()
        if not exe or not os.path.exists(exe): show_toast("Set playit path first!", T["stop"]); return
        if playit_proc and playit_proc.poll() is None: show_toast("Already running.", T["muted"]); return
        try:
            kw = {"stdout":subprocess.PIPE, "stderr":subprocess.PIPE,
                  "stdin":subprocess.DEVNULL, "text":False, "bufsize":0}
            if IS_WIN: kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | _NO_WIN
            playit_proc = subprocess.Popen([exe], **kw)
            _set_tst("● Running", T["start"])
            threading.Thread(target=_read_pt,        args=(playit_proc,), daemon=True).start()
            threading.Thread(target=_read_stderr_pt, args=(playit_proc,), daemon=True).start()
        except Exception as ex: show_toast(f"Failed: {ex}", T["stop"]); _set_tst("● Error", T["stop"])

    def _stop_pt():
        global playit_proc, playit_tunnel
        if playit_proc:
            try: playit_proc.terminate()
            except: pass
            playit_proc = None
        playit_tunnel = None; _set_addr(""); _set_tst("● Stopped", T["stop"])

    br = ctk.CTkFrame(ch, fg_color="transparent"); br.pack(side="right")
    for txt,cmd,fc,tc in [("▶ Start",_start_pt,T["start"],"#000"),
                           ("■ Stop", _stop_pt, T["stop"], "#fff")]:
        ctk.CTkButton(br, text=txt, width=74, height=26, font=ctk.CTkFont(size=11),
                      fg_color=fc, hover_color=fc, text_color=tc, command=cmd).pack(side="left",padx=(0,4))
    ctk.CTkButton(br, text="Copy Address", width=100, height=26, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=lambda: (app.clipboard_clear(), app.clipboard_append(tun_addr.cget("text")),
                                   show_toast(f"Copied: {tun_addr.cget('text')}", T["sync"]))
                  ).pack(side="left")
    ctk.CTkButton(br, text="📱 Remote Server", width=120, height=26, font=ctk.CTkFont(size=11),
                  fg_color=T["hand"], hover_color=T["hand"], text_color="#000",
                  command=lambda: globals().get("_dsub_goto_remote", lambda: None)()
                  ).pack(side="left", padx=(6,0))

    lb, lh = card("Agent Log")
    pt_log = ctk.CTkTextbox(lb, font=ctk.CTkFont(size=11,family="Consolas"),
                             wrap="word", state="disabled", height=180,
                             fg_color=T["bg"], text_color=T["text"]); pt_log.pack(fill="x")
    if playit_log_lines:
        pt_log.configure(state="normal")
        for line in playit_log_lines: pt_log.insert("end", line+"\n")
        pt_log.configure(state="disabled"); pt_log.see("end")
    if playit_tunnel: _set_addr(playit_tunnel)
    ctk.CTkButton(lh, text="Clear", width=50, height=22, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: (playit_log_lines.clear(),
                                   pt_log.configure(state="normal"),
                                   pt_log.delete("1.0","end"),
                                   pt_log.configure(state="disabled"))).pack(side="right")
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

# ── MODE: Remote ──────────────────────────────────────────
def _build_mode_remote(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)

    def card(title):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=12); f.pack(fill="x", padx=18, pady=(10,0))
        h = ctk.CTkFrame(f,fg_color="transparent"); h.pack(fill="x",padx=12,pady=(10,4))
        ctk.CTkLabel(h,text=title,font=ctk.CTkFont(size=12,weight="bold"),text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f,height=1,fg_color=T["border"]).pack(fill="x",padx=12)
        b = ctk.CTkFrame(f,fg_color="transparent"); b.pack(fill="x",padx=12,pady=(8,10))
        return b, h

    ab, _ = card("About Remote Dashboard")
    ctk.CTkLabel(ab, text=(
        "Starts a lightweight web server so you can control Minecraft from your phone or another device.\n"
        "Open  http://<your-local-ip>:<port>  in any browser — no app required.\n"
        "Features: start/stop, live log, commands, player list, TPS/RAM stats."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")

    s = load_settings(); port_var = ctk.StringVar(value=str(s.get("remote_port",5000)))
    pass_var = ctk.StringVar(value=s.get("remote_password",""))
    def _save_rd(*_): update_setting("remote_port",port_var.get()); update_setting("remote_password",pass_var.get())

    cb, _ = card("Configuration")
    r0 = ctk.CTkFrame(cb,fg_color="transparent"); r0.pack(fill="x",pady=3)
    ctk.CTkLabel(r0,text="Port",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    pe = ctk.CTkEntry(r0,textvariable=port_var,width=80,height=26,font=ctk.CTkFont(size=12,family="Consolas"),
                      fg_color=T["bg"],border_color=T["border"],text_color=T["text"])
    pe.pack(side="left"); pe.bind("<FocusOut>",_save_rd); pe.bind("<Return>",_save_rd)
    r1 = ctk.CTkFrame(cb,fg_color="transparent"); r1.pack(fill="x",pady=3)
    ctk.CTkLabel(r1,text="Password (optional)",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    pwe = ctk.CTkEntry(r1,textvariable=pass_var,width=200,height=26,show="•",
                       font=ctk.CTkFont(size=12,family="Consolas"),
                       fg_color=T["bg"],border_color=T["border"],text_color=T["text"],
                       placeholder_text="blank = no auth")
    pwe.pack(side="left",padx=(0,6)); pwe.bind("<FocusOut>",_save_rd)
    ctk.CTkButton(r1,text="Show",width=48,height=26,font=ctk.CTkFont(size=10),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],
                  command=lambda: pwe.configure(show="" if pwe.cget("show")=="•" else "•")).pack(side="left")

    ctrl_b, ctrl_h = card("Dashboard Control")
    rd_st = ctk.CTkLabel(ctrl_b,text="● Stopped",font=ctk.CTkFont(size=13,weight="bold"),text_color=T["stop"])
    rd_st.pack(side="left")
    rd_url = ctk.CTkLabel(ctrl_b,text="",font=ctk.CTkFont(size=12,family="Consolas"),text_color=T["sync"])
    rd_url.pack(side="left",padx=(12,0))
    _cur_url = [""]

    def _set_st(txt,col):
        try: rd_st.configure(text=txt,text_color=col)
        except: pass
    def _set_url(url):
        _cur_url[0] = url
        try: rd_url.configure(text=url)
        except: pass

    _state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_mc_ctrl_state.json")

    _state_log_buf = []
    _state_log_lock = threading.Lock()

    def _append_state_log(line):
        with _state_log_lock:
            _state_log_buf.append(line)
            if len(_state_log_buf) > 200:
                del _state_log_buf[:100]

    def _write_state():
        try:
            with _state_log_lock:
                new_lines = _state_log_buf[-30:] if _state_log_buf else []
            state = {
                "running": server_proc is not None and server_proc.poll() is None,
                "tps":     perf.get("tps","--"),
                "players": perf.get("players","0"),
                "player_list": list(online_players.keys()),
                "ram_srv": perf.get("ram_srv","--"),
                "ram_pct": perf.get("ram_pct","--"),
                "ram_used":perf.get("ram_used","--"),
                "cpu_srv": perf.get("cpu_srv","--"),
                "cpu_sys": perf.get("cpu_sys","--"),
                "uptime":  perf.get("uptime","--"),
                "threads": perf.get("threads","--"),
                "latency": perf.get("latency","--"),
                "log":     new_lines,
            }
            try:
                with open(_state_file) as _sf2: existing = json.loads(_sf2.read())
                if existing.get("pending_action"):
                    act = existing.pop("pending_action")
                    if act == "start": threading.Thread(target=start_server,daemon=True).start()
                    elif act == "stop": threading.Thread(target=stop_server,daemon=True).start()
                if existing.get("pending_cmd"):
                    send_server_cmd(existing.pop("pending_cmd"))
            except: pass
            with open(_state_file,"w") as _sf: _sf.write(json.dumps(state))
        except: pass

    def _sync_loop():
        while _remote_proc[0] and _remote_proc[0].poll() is None:
            app.after(0, _write_state); time.sleep(2)

    def _write_flask():
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_mc_ctrl_remote.py")
        code = '''import sys,json,os,threading,time
from datetime import datetime
try:
    from flask import Flask,request,jsonify,render_template_string
except ImportError:
    import subprocess; subprocess.run([sys.executable,"-m","pip","install","flask","--quiet"])
    from flask import Flask,request,jsonify,render_template_string

PORT=int(sys.argv[1]) if len(sys.argv)>1 else 5000
STATE=sys.argv[2] if len(sys.argv)>2 else ""
app=Flask(__name__); app.secret_key=os.urandom(24)
LOG=[]; LOG_LOCK=threading.Lock()

def rstate():
    try:
        if STATE and os.path.exists(STATE): return json.loads(open(STATE).read())
    except: pass
    return {}

HTML="""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>MC CTRL Remote</title>
<style>
@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap\');
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#080808;--card:#111;--card2:#161616;--border:#1f1f1f;--border2:#2a2a2a;--text:#e8e8e8;--muted:#555;--muted2:#888;--green:#22c55e;--green-dim:#16a34a;--red:#ef4444;--blue:#60a5fa;--amber:#f59e0b;--glow:rgba(34,197,94,0.12)}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:\'Inter\',system-ui,sans-serif;font-size:14px;line-height:1.5}
body{padding:0;overflow-x:hidden}
.topbar{background:var(--card);border-bottom:1px solid var(--border);padding:12px 18px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:10}
.topbar-logo{font-size:13px;font-weight:700;letter-spacing:.08em;color:var(--green)}
.topbar-logo span{color:var(--muted2);font-weight:400}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}
.dot-green{background:var(--green);box-shadow:0 0 8px var(--green)}
.dot-red{background:var(--red)}
.dot-amber{background:var(--amber)}
#srv-status-text{font-size:13px;font-weight:500;color:var(--text)}
.spacer{flex:1}
.page{padding:16px 14px 32px;max-width:520px;margin:0 auto;display:flex;flex-direction:column;gap:10px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.card-hdr{padding:12px 16px 10px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.card-title{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted2)}
.card-body{padding:14px 16px}
.hero-card{position:relative;overflow:hidden}
.hero-glow{position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% -10%,var(--glow),transparent);pointer-events:none;transition:opacity .6s}
.hero-glow.off{opacity:0}
.hero-num{font-size:52px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--green);transition:color .4s}
.hero-num.off{color:var(--muted)}
.hero-label{font-size:11px;color:var(--muted2);margin-top:4px;text-transform:uppercase;letter-spacing:.08em}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border)}
.stat-cell{background:var(--card);padding:12px 14px}
.stat-row-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;display:flex;align-items:center;gap:5px}
.stat-val{font-size:20px;font-weight:600;font-family:\'JetBrains Mono\',monospace;color:var(--text);letter-spacing:-.02em}
.metric-list{display:flex;flex-direction:column;gap:0}
.metric-row{display:flex;align-items:center;padding:10px 0;border-bottom:1px solid var(--border)}
.metric-row:last-child{border-bottom:none}
.metric-label{font-size:12px;color:var(--muted2);display:flex;align-items:center;gap:7px;flex:1}
.metric-val{font-size:13px;font-weight:500;font-family:\'JetBrains Mono\',monospace;color:var(--text)}
.player-row{display:flex;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);gap:10px}
.player-row:last-child{border-bottom:none}
.player-avatar{width:28px;height:28px;border-radius:6px;background:var(--card2);border:1px solid var(--border2);display:flex;align-items:center;justify-content:center;font-size:13px}
.player-name{font-size:13px;font-weight:500;color:var(--text);flex:1}
.player-time{font-size:11px;color:var(--muted)}
.no-players{color:var(--muted);font-size:12px;padding:10px 0;text-align:center}
.btn-row{display:flex;gap:8px;flex-wrap:wrap}
button{border:none;border-radius:8px;cursor:pointer;font-family:\'Inter\',sans-serif;font-weight:600;font-size:13px;padding:10px 18px;transition:opacity .15s,transform .1s;display:inline-flex;align-items:center;gap:6px;letter-spacing:.01em}
button:active{transform:scale(.97)}
.btn-start{background:var(--green);color:#000}
.btn-stop{background:var(--red);color:#fff}
.btn-outline{background:transparent;border:1px solid var(--border2);color:var(--muted2);font-size:11px;padding:7px 12px}
.btn-outline:hover{border-color:var(--muted);color:var(--text)}
.cmd-wrap{display:flex;gap:8px;margin-bottom:10px}
.cmd-input{flex:1;background:var(--card2);border:1px solid var(--border2);border-radius:8px;color:var(--text);font-family:\'JetBrains Mono\',monospace;font-size:13px;padding:10px 12px;outline:none}
.cmd-input:focus{border-color:var(--muted)}
.cmd-input::placeholder{color:var(--muted)}
.quick-btns{display:flex;flex-wrap:wrap;gap:6px}
.log-box{background:var(--bg);border-radius:8px;border:1px solid var(--border);font-family:\'JetBrains Mono\',monospace;font-size:11px;color:#666;padding:10px 12px;height:200px;overflow-y:auto;white-space:pre-wrap;line-height:1.6}
.log-box::-webkit-scrollbar{width:4px}.log-box::-webkit-scrollbar-track{background:transparent}.log-box::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
.log-line-event{color:var(--blue)}
.log-line-warn{color:var(--amber)}
.pulse{animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.section-label{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:4px 0 8px}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-logo">MC CTRL <span>remote</span></div>
  <span class="dot" id="status-dot" style="background:var(--red)"></span>
  <span id="srv-status-text">Connecting...</span>
  <div class="spacer"></div>
  <span style="font-size:10px;color:var(--muted)" id="poll-time"></span>
</div>

<div class="page">

  <!-- HERO STATUS CARD -->
  <div class="card hero-card">
    <div class="hero-glow off" id="hero-glow"></div>
    <div class="card-hdr"><span class="card-title">Server Health</span></div>
    <div class="card-body" style="display:flex;align-items:flex-end;gap:20px;padding-bottom:18px">
      <div>
        <div class="hero-num off" id="hero-pct">--</div>
        <div class="hero-label">TPS</div>
      </div>
      <div style="flex:1">
        <div class="stat-grid" style="border-radius:8px;overflow:hidden;border:1px solid var(--border);grid-template-columns:1fr 1fr 1fr">
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-ram" style="background:var(--muted)"></span>Srv RAM</div>
            <div class="stat-val" id="h-ram">--</div>
          </div>
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-rampct" style="background:var(--muted)"></span>RAM %</div>
            <div class="stat-val" id="h-rampct">--</div>
          </div>
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-cpu" style="background:var(--muted)"></span>Srv CPU</div>
            <div class="stat-val" id="h-cpu">--</div>
          </div>
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-cpusys" style="background:var(--muted)"></span>Sys CPU</div>
            <div class="stat-val" id="h-cpusys">--</div>
          </div>
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-up" style="background:var(--muted)"></span>Uptime</div>
            <div class="stat-val" id="h-up" style="font-size:14px">--</div>
          </div>
          <div class="stat-cell">
            <div class="stat-row-label"><span class="dot" id="dot-pl" style="background:var(--muted)"></span>Players</div>
            <div class="stat-val" id="h-pl">--</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ACTIONS -->
  <div class="card">
    <div class="card-hdr"><span class="card-title">Server Control</span></div>
    <div class="card-body">
      <div class="btn-row" style="margin-bottom:12px">
        <button class="btn-start" onclick="act(\'start\')">&#9654; Start</button>
        <button class="btn-stop" onclick="act(\'stop\')">&#9632; Stop</button>
      </div>
      <div class="section-label">Quick Commands</div>
      <div class="quick-btns">
        <button class="btn-outline" onclick="sv(\'list\')">list</button>
        <button class="btn-outline" onclick="sv(\'tps\')">tps</button>
        <button class="btn-outline" onclick="sv(\'save-all\')">save</button>
        <button class="btn-outline" onclick="sv(\'time set day\')">set day</button>
        <button class="btn-outline" onclick="sv(\'weather clear\')">clear weather</button>
        <button class="btn-outline" onclick="sv(\'difficulty peaceful\')">peaceful</button>
      </div>
    </div>
  </div>

  <!-- COMMAND -->
  <div class="card">
    <div class="card-hdr"><span class="card-title">Console</span></div>
    <div class="card-body">
      <div class="cmd-wrap">
        <input class="cmd-input" id="cmd" type="text" placeholder="Enter command..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"/>
        <button class="btn-start" onclick="sc()" style="padding:10px 16px">Send</button>
      </div>
      <div class="log-box" id="log"></div>
    </div>
  </div>

  <!-- PLAYERS -->
  <div class="card">
    <div class="card-hdr"><span class="card-title">Online Players</span><div style="flex:1"></div><span style="font-size:11px;color:var(--muted)" id="player-count">0 online</span></div>
    <div class="card-body" style="padding-top:4px;padding-bottom:4px">
      <div id="player-list"><div class="no-players">No players online</div></div>
    </div>
  </div>

</div>

<script>
var _lastLog=0;
async function api(p,b){
  try{const r=await fetch(p,{method:b?"POST":"GET",headers:b?{"Content-Type":"application/json"}:{},body:b?JSON.stringify(b):undefined});return await r.json()}
  catch(e){return null}
}
async function act(a){await api("/api/action",{action:a})}
async function sc(){
  var v=document.getElementById("cmd").value.trim();
  if(!v)return;
  appendLog(">> "+v,"");
  await api("/api/cmd",{cmd:v});
  document.getElementById("cmd").value="";
}
function sv(v){document.getElementById("cmd").value=v;sc()}
document.getElementById("cmd").addEventListener("keydown",function(e){if(e.key==="Enter")sc()});

function dot_color(val,type){
  if(val==="--"||val==null)return"#333";
  if(type==="tps"){var n=parseFloat(val);return n>=18?"#22c55e":n>=15?"#f59e0b":"#ef4444"}
  if(type==="pct"){var n=parseFloat(val);return n<60?"#22c55e":n<85?"#f59e0b":"#ef4444"}
  return"#22c55e";
}

function appendLog(line,cls){
  var el=document.getElementById("log");
  var div=document.createElement("div");
  if(cls)div.className="log-line-"+cls;
  div.textContent=line;
  el.appendChild(div);
  if(el.children.length>200){el.removeChild(el.firstChild)}
  el.scrollTop=el.scrollHeight;
}

async function poll(){
  var d=await api("/api/state");
  if(!d){setTimeout(poll,3000);return}
  var on=d.running;
  document.getElementById("status-dot").style.background=on?"var(--green)":"var(--red)";
  document.getElementById("status-dot").style.boxShadow=on?"0 0 8px var(--green)":"none";
  document.getElementById("srv-status-text").textContent=on?"Running":"Stopped";
  document.getElementById("poll-time").textContent=new Date().toLocaleTimeString();
  // hero
  var tps=d.tps||"--";
  var hNum=document.getElementById("hero-pct");
  var glow=document.getElementById("hero-glow");
  hNum.textContent=tps;
  hNum.className="hero-num"+(on?"":"off");
  glow.className="hero-glow"+(on?" on":" off");
  // stat dots
  document.getElementById("dot-ram").style.background=dot_color(d.ram_srv,"pct");
  document.getElementById("dot-rampct").style.background=dot_color(d.ram_pct,"pct");
  document.getElementById("dot-cpu").style.background=dot_color(d.cpu_srv,"pct");
  document.getElementById("dot-cpusys").style.background=dot_color(d.cpu_sys,"pct");
  document.getElementById("dot-up").style.background=on?"var(--green)":"var(--muted)";
  document.getElementById("dot-pl").style.background=on?"var(--blue)":"var(--muted)";
  document.getElementById("h-ram").textContent=d.ram_srv||"--";
  document.getElementById("h-rampct").textContent=d.ram_pct||"--";
  document.getElementById("h-cpu").textContent=d.cpu_srv||"--";
  document.getElementById("h-cpusys").textContent=d.cpu_sys||"--";
  document.getElementById("h-up").textContent=d.uptime||"--";
  document.getElementById("h-pl").textContent=d.players||"0";
  // players
  var pl=d.player_list||[];
  document.getElementById("player-count").textContent=(d.players||"0")+" online";
  var plEl=document.getElementById("player-list");
  if(pl.length===0){plEl.innerHTML=\'<div class="no-players">No players online</div>\'}
  else{
    plEl.innerHTML=pl.map(function(nm){
      return\'<div class="player-row"><div class="player-avatar">&#128100;</div><div class="player-name">\'+nm+\'</div><span class="dot dot-green"></span></div>\';
    }).join("");
  }
  // log
  if(d.log&&d.log.length){
    d.log.forEach(function(l){
      var cls=l.startsWith(">>")||l.startsWith("<<")?\'event\':(l.toLowerCase().includes("warn")?\'warn\':"");
      appendLog(l,cls);
    });
  }
  setTimeout(poll,2000);
}
poll();
</script>
</body>
</html>"""

@app.route("/")
def index(): return render_template_string(HTML)
@app.route("/api/state")
def state():
    s=rstate()
    with LOG_LOCK: lines=list(LOG); LOG.clear()
    s["log"]=lines
    if "player_list" not in s: s["player_list"]=[]
    return jsonify(s)
@app.route("/api/stats")
def api_stats():
    s=rstate()
    return jsonify({"tps":s.get("tps","--"),"ram":s.get("ram_pct","--"),
                    "ram_srv":s.get("ram_srv","--"),"cpu":s.get("cpu_sys","--"),
                    "cpu_srv":s.get("cpu_srv","--"),"players":s.get("players","0"),
                    "uptime":s.get("uptime","--"),"threads":s.get("threads","--"),
                    "running":s.get("running",False)})
@app.route("/api/action",methods=["POST"])
def do_action():
    d=request.get_json(force=True); s=rstate()
    try: s["pending_action"]=d.get("action",""); open(STATE,"w").write(json.dumps(s))
    except: pass
    return jsonify({"ok":True})
@app.route("/api/cmd",methods=["POST"])
def do_cmd():
    d=request.get_json(force=True); s=rstate()
    try: s["pending_cmd"]=d.get("cmd",""); open(STATE,"w").write(json.dumps(s))
    except: pass
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=PORT,debug=False,use_reloader=False)
'''
        with open(path,"w",encoding="utf-8") as f: f.write(code)
        return path

    def _start_remote():
        if _remote_proc[0] and _remote_proc[0].poll() is None:
            show_toast("Already running.", T["muted"]); return
        try:
            if importlib.util.find_spec("flask") is None:
                _set_st("Installing Flask…", T["hand"])
                subprocess.run([sys.executable,"-m","pip","install","flask","--quiet"],
                               creationflags=_popen_flags())
        except: pass
        script = _write_flask(); port = port_var.get().strip() or "5000"
        # hook log lines into the state buffer
        _remote_state_log_fn[0] = _append_state_log
        try:
            proc = subprocess.Popen([sys.executable,script,port,_state_file],
                                    creationflags=_popen_flags(),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            _remote_proc[0] = proc
            import socket
            try:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s2.connect(("8.8.8.8",80))
                lip = s2.getsockname()[0]; s2.close()
            except: lip = "127.0.0.1"
            url = f"http://{lip}:{port}"
            _set_st("● Running", T["start"]); _set_url(url)
            show_toast(f"Dashboard: {url}", T["start"], 5000)
            threading.Thread(target=_sync_loop, daemon=True).start()
        except Exception as ex: show_toast(f"Failed: {ex}", T["stop"]); _set_st("● Error", T["stop"])

    def _stop_remote():
        if _remote_proc[0]:
            try: _remote_proc[0].terminate()
            except: pass
            _remote_proc[0] = None
        _remote_state_log_fn[0] = None
        _set_st("● Stopped", T["stop"]); _set_url("")

    br = ctk.CTkFrame(ctrl_h,fg_color="transparent"); br.pack(side="right")
    ctk.CTkButton(br,text="▶ Start",width=74,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["start"],hover_color=T["start"],text_color="#000",
                  command=_start_remote).pack(side="left",padx=(0,4))
    ctk.CTkButton(br,text="■ Stop",width=74,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["stop"],hover_color=T["stop"],text_color="#fff",
                  command=_stop_remote).pack(side="left",padx=(0,4))
    ctk.CTkButton(br,text="Copy URL",width=78,height=26,font=ctk.CTkFont(size=11),
                  fg_color=T["sync"],hover_color=T["sync"],text_color="#000",
                  command=lambda: (app.clipboard_clear(),app.clipboard_append(_cur_url[0]),
                                   show_toast(f"Copied: {_cur_url[0]}",T["sync"]))
                  ).pack(side="left")

    gb, _ = card("How to use from your phone")
    ctk.CTkLabel(gb, text=(
        "1. Start the Remote Dashboard above.\n"
        "2. Ensure your phone is on the same WiFi as this PC.\n"
        "3. Open the URL shown in your phone's browser.\n"
        "4. Use the web UI to start/stop, send commands, watch the live log.\n\n"
        "For outside-home access, use a VPN like Tailscale — don't expose port 5000 to the internet."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    ctk.CTkFrame(scroll,height=12,fg_color="transparent").pack()

def _toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    update_setting("fullscreen", fullscreen)
    app.attributes("-fullscreen", fullscreen)
    if not fullscreen:
        app.geometry("1100x740")
    rebuild_ui()

def _toggle_perf():
    global show_perf
    show_perf = not show_perf
    update_setting("show_perf", show_perf)
    rebuild_ui()

def _toggle_log_left():
    global log_left
    log_left = not log_left
    update_setting("log_left", log_left)
    rebuild_ui()

def _toggle_chat():
    global show_chat
    show_chat = not show_chat; update_setting("show_chat", show_chat)
    try:
        chat_toggle_btn.configure(text="Hide" if show_chat else "Show")
        if show_chat:
            chat_box.configure(height=80); chat_box.pack(fill="x", padx=6, pady=(3,6))
        else:
            chat_box.pack_forget(); chat_box.configure(height=0)
    except: pass

def _build_perf_panel(parent):
    global perf_labels; perf_labels = {}
    pf = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    pf.pack(fill="x", padx=18, pady=(0,10))
    ph = ctk.CTkFrame(pf, fg_color="transparent"); ph.pack(fill="x", padx=12, pady=(8,4))
    ctk.CTkLabel(ph, text="PERFORMANCE", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(side="left")
    ctk.CTkLabel(ph, text="2s refresh", font=ctk.CTkFont(size=9),
                 text_color=T["muted"]).pack(side="right")
    ctk.CTkFrame(pf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    g = ctk.CTkFrame(pf, fg_color="transparent"); g.pack(fill="x", padx=8, pady=(6,8))
    # (label, key, good_thresh, warn_thresh, invert)
    stats = [
        ("TPS",     "tps",      18.0, 15.0, False),
        ("Players", "players",  None, None, False),
        ("Latency", "latency",  None, None, False),
        ("Uptime",  "uptime",   None, None, False),
        ("RAM",     "ram_used", None, None, False),
        ("RAM %",   "ram_pct",  60.0, 85.0, True),
        ("Srv RAM", "ram_srv",  None, None, False),
        ("CPU Sys", "cpu_sys",  60.0, 85.0, True),
        ("CPU Srv", "cpu_srv",  60.0, 85.0, True),
        ("Threads", "threads",  None, None, False),
    ]
    _dot_refs = {}
    def _dot_color(val, good, warn, inv):
        if good is None: return T["start"]
        try:
            n = float(str(val).replace("%","").replace(" MB","").replace(" GB","").replace(" ms","").split()[0])
        except: return T["muted"]
        if inv:
            return T["start"] if n < good else (T["hand"] if n < warn else T["stop"])
        else:
            return T["start"] if n >= good else (T["hand"] if n >= warn else T["stop"])
    for i,(label,key,good,warn,inv) in enumerate(stats):
        col, row = i%5, i//5
        cell = ctk.CTkFrame(g, fg_color=T["bg"], border_color=T["border"],
                            border_width=1, corner_radius=8)
        cell.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
        g.columnconfigure(col, weight=1)
        top = ctk.CTkFrame(cell, fg_color="transparent"); top.pack(fill="x", padx=8, pady=(6,0))
        dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=9), text_color=T["muted"], width=12)
        dot.pack(side="left")
        ctk.CTkLabel(top, text=label, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=T["muted"]).pack(side="left", padx=(2,0))
        lbl = ctk.CTkLabel(cell, text=perf[key], font=ctk.CTkFont(size=17, weight="bold"),
                           text_color=T["text"])
        lbl.pack(pady=(2,7))
        perf_labels[key] = lbl
        _dot_refs[key] = (dot, good, warn, inv)
    _orig_fn = update_perf_labels
    def _patched():
        _orig_fn()
        for k,(dot,good,warn,inv) in _dot_refs.items():
            try: dot.configure(text_color=_dot_color(perf.get(k,"--"),good,warn,inv))
            except: pass
    globals()["update_perf_labels"] = _patched

# ══════════════════════════════════════════════════════════
# SERVER INFO TAB — with sub-tabs (Players, Plugins, Properties, Backup)
# ══════════════════════════════════════════════════════════
def build_server_info_tab(parent):
    _build_ip_footer(parent)

    # Sub-tab bar — pure pack (NEVER mix grid and pack on same parent!)
    sub_bar = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=0,
                            border_color=T["border"], border_width=1)
    sub_bar.pack(side="top", fill="x")

    sub_content = ctk.CTkFrame(parent, fg_color="transparent")
    sub_content.pack(side="top", fill="both", expand=True)

    SUB_TABS = [
        ("players", "👥 Players"),
        ("plugins", "🔌 Plugins"),
        ("props",   "⚙ Properties"),
        ("backup",  "💾 Backup"),
    ]
    sub_frames = {k: ctk.CTkFrame(sub_content, fg_color="transparent") for k,_ in SUB_TABS}
    _sub_built = set(); sub_btns = {}

    def show_sub(name):
        for f in sub_frames.values(): f.pack_forget()
        for n, b in sub_btns.items():
            b.configure(fg_color=T["sync"] if n==name else "transparent",
                        text_color="#000" if n==name else T["muted"])
        if name not in _sub_built:
            _sub_built.add(name)
            {
                "players": lambda: _build_players_sub(sub_frames["players"]),
                "plugins": lambda: _build_plugins_sub(sub_frames["plugins"]),
                "props":   lambda: _build_props_sub(sub_frames["props"]),
                "backup":  lambda: _build_backup_sub(sub_frames["backup"]),
            }[name]()
        sub_frames[name].pack(fill="both", expand=True)

    for key, label in SUB_TABS:
        b = ctk.CTkButton(sub_bar, text=label, width=110, height=26,
                          font=ctk.CTkFont(size=11), corner_radius=5,
                          fg_color="transparent", text_color=T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_sub(k))
        b.pack(side="left", padx=(6 if key=="players" else 2, 2), pady=4)
        sub_btns[key] = b

    show_sub("players")

def _build_players_sub(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)

    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12,0))
    hdr = ctk.CTkFrame(hf, fg_color="transparent"); hdr.pack(fill="x", padx=12, pady=(10,4))
    ctk.CTkLabel(hdr, text="Online Players", font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=T["text"]).pack(side="left")
    ctk.CTkButton(hdr, text="Refresh", width=66, height=22, font=ctk.CTkFont(size=10),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=lambda: (send_server_cmd("list"),)).pack(side="right")
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)

    pf = ctk.CTkFrame(hf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8)
    pf.pack(fill="x", padx=12, pady=(6,10))

    _head_cache = {}
    def _fetch_head(name, lbl):
        if name in _head_cache:
            try: app.after(0, lbl.configure, {"image": _head_cache[name], "text": ""})
            except: pass
            return
        try:
            from PIL import Image, ImageTk
            import io
            url = f"https://mc-heads.net/avatar/{name}/32"
            req = urllib.request.Request(url, headers={"User-Agent":"MC-CTRL/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                img = Image.open(io.BytesIO(resp.read())).resize((28,28), Image.NEAREST)
                photo = ctk.CTkImage(img, size=(28,28))
                _head_cache[name] = photo
                try: app.after(0, lbl.configure, {"image": photo, "text": ""})
                except: pass
        except: pass

    def refresh_players():
        for w in pf.winfo_children(): w.destroy()
        names = list(online_players.keys())
        if not names:
            ctk.CTkLabel(pf, text="No players online.", font=ctk.CTkFont(size=12),
                         text_color=T["muted"]).pack(padx=12, pady=8)
        else:
            for nm in sorted(names):
                r = ctk.CTkFrame(pf, fg_color="transparent"); r.pack(fill="x", padx=8, pady=4)
                # Head icon placeholder
                head_lbl = ctk.CTkLabel(r, text="👤", font=ctk.CTkFont(size=20), width=32)
                head_lbl.pack(side="left", padx=(0,8))
                threading.Thread(target=_fetch_head, args=(nm, head_lbl), daemon=True).start()
                info = ctk.CTkFrame(r, fg_color="transparent"); info.pack(side="left", fill="y")
                ctk.CTkLabel(info, text=nm, font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=T["text"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(info, text=f"joined {online_players.get(nm,'?')}",
                             font=ctk.CTkFont(size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
                ctk.CTkButton(r, text="Kick", width=48, height=22, font=ctk.CTkFont(size=10),
                              fg_color="transparent", border_width=1, border_color=T["stop"],
                              text_color=T["stop"], hover_color=T["border"],
                              command=lambda n=nm: send_server_cmd(f"kick {n}")
                              ).pack(side="right")
                ctk.CTkButton(r, text="Msg", width=40, height=22, font=ctk.CTkFont(size=10),
                              fg_color="transparent", border_width=1, border_color=T["sync"],
                              text_color=T["sync"], hover_color=T["border"],
                              command=lambda n=nm: send_server_cmd(f"msg {n} Hello!")
                              ).pack(side="right", padx=(0,4))

    def _auto_refresh():
        global _players_refresh_id
        try:
            if not pf.winfo_exists(): return  # tab destroyed, stop loop
            refresh_players()
        except: return
        _players_refresh_id = app.after(2000, _auto_refresh)
    _auto_refresh()

def _build_plugins_sub(parent):
    import zipfile, json as _json
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)

    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12,0))
    hdr = ctk.CTkFrame(hf, fg_color="transparent"); hdr.pack(fill="x", padx=12, pady=(10,4))
    ctk.CTkLabel(hdr, text="Plugins & Mods", font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=T["text"]).pack(side="left")
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    plf = ctk.CTkFrame(hf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8)
    plf.pack(fill="x", padx=12, pady=(6,10))

    # detail panel shown below list
    detail_frame = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                                border_width=1, corner_radius=12)
    _detail_open = [False]
    _detail_name = [None]

    def _read_jar_meta(jar_path):
        """Extract name, version, description from plugin.yml or fabric.mod.json or mods.toml."""
        info = {"name": os.path.basename(jar_path).replace(".jar",""),
                "version": "", "description": "", "author": "", "icon": None}
        try:
            with zipfile.ZipFile(jar_path, "r") as z:
                names = z.namelist()
                # Bukkit/Spigot/Paper plugin
                for yml_name in ("plugin.yml", "bungee.yml"):
                    if yml_name in names:
                        raw = z.read(yml_name).decode("utf-8", errors="ignore")
                        for line in raw.splitlines():
                            if ":" in line:
                                k, _, v = line.partition(":")
                                k, v = k.strip(), v.strip().strip('"\'').strip()
                                if k == "name":        info["name"]        = v
                                if k == "version":     info["version"]     = v
                                if k == "description": info["description"] = v
                                if k in ("author","authors"): info["author"] = v
                        break
                # Fabric mod
                if "fabric.mod.json" in names:
                    try:
                        d = _json.loads(z.read("fabric.mod.json").decode("utf-8", errors="ignore"))
                        info["name"]        = d.get("name", info["name"])
                        info["version"]     = d.get("version", "")
                        info["description"] = d.get("description", "")
                        auths = d.get("authors", [])
                        info["author"]      = auths[0] if auths else ""
                        # icon
                        icon_path = d.get("icon","")
                        if icon_path and icon_path in names:
                            info["icon"] = z.read(icon_path)
                    except: pass
                # Forge/NeoForge mods.toml
                for toml_path in ("META-INF/mods.toml", "META-INF/MANIFEST.MF"):
                    if toml_path in names:
                        raw = z.read(toml_path).decode("utf-8", errors="ignore")
                        for line in raw.splitlines():
                            if "=" in line:
                                k, _, v = line.partition("=")
                                k, v = k.strip(), v.strip().strip('"\' ').strip()
                                if k in ("displayName","Implementation-Title"): info["name"] = v
                                if k in ("version","Implementation-Version"):   info["version"] = v
                                if k == "description": info["description"] = v
                        break
        except: pass
        return info

    _icon_cache = {}

    def _make_icon_widget(parent, icon_bytes, size=32):
        """Return a CTkLabel with plugin icon, or emoji fallback."""
        if icon_bytes:
            try:
                from PIL import Image, ImageTk
                import io
                img = Image.open(io.BytesIO(icon_bytes)).resize((size,size), Image.NEAREST).convert("RGBA")
                photo = ctk.CTkImage(img, size=(size,size))
                lbl = ctk.CTkLabel(parent, image=photo, text="")
                return lbl
            except: pass
        lbl = ctk.CTkLabel(parent, text="🔌", font=ctk.CTkFont(size=size-4))
        return lbl

    def _show_detail(jar_path, meta):
        _detail_name[0] = jar_path
        for w in detail_frame.winfo_children(): w.destroy()
        detail_frame.pack(fill="x", padx=18, pady=(8,0))

        dh = ctk.CTkFrame(detail_frame, fg_color="transparent"); dh.pack(fill="x", padx=12, pady=(10,4))
        # icon (48px)
        icon_w = _make_icon_widget(dh, meta["icon"], size=48)
        icon_w.pack(side="left", padx=(0,12))
        # name + version + author
        info_col = ctk.CTkFrame(dh, fg_color="transparent"); info_col.pack(side="left", fill="y")
        ctk.CTkLabel(info_col, text=meta["name"],
                     font=ctk.CTkFont(size=14, weight="bold"), text_color=T["text"], anchor="w").pack(anchor="w")
        if meta["version"]:
            ctk.CTkLabel(info_col, text=f"v{meta['version']}",
                         font=ctk.CTkFont(size=10), text_color=T["sync"], anchor="w").pack(anchor="w")
        if meta["author"]:
            ctk.CTkLabel(info_col, text=f"by {meta['author']}",
                         font=ctk.CTkFont(size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
        # close button
        ctk.CTkButton(dh, text="✕", width=28, height=28, font=ctk.CTkFont(size=12),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: (detail_frame.pack_forget(), setattr(_detail_name,"__setitem__",(0,None)))
                      ).pack(side="right")
        ctk.CTkFrame(detail_frame, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        # description
        desc = meta["description"] or "No description available."
        ctk.CTkLabel(detail_frame, text=desc,
                     font=ctk.CTkFont(size=12), text_color=T["muted"],
                     wraplength=760, justify="left", anchor="w"
                     ).pack(anchor="w", padx=14, pady=(8,4))
        # file info
        try:
            sz = os.path.getsize(jar_path)
            ctk.CTkLabel(detail_frame,
                         text=f"File: {os.path.basename(jar_path)}  •  {sz//1024} KB",
                         font=ctk.CTkFont(size=10), text_color=T["muted"], anchor="w"
                         ).pack(anchor="w", padx=14, pady=(0,10))
        except: pass

    def refresh_plugins():
        for w in plf.winfo_children(): w.destroy()
        detail_frame.pack_forget()
        path = load_settings().get("srv_path", _DEFAULT_SRV)

        # look in both plugins/ (Bukkit) and mods/ (Fabric/Forge)
        jars = []
        for sub in ("plugins", "mods"):
            d = os.path.join(path, sub)
            if os.path.isdir(d):
                jars += [(sub, j) for j in sorted(os.listdir(d)) if j.endswith(".jar")]

        if not jars:
            ctk.CTkLabel(plf, text="No plugins or mods found.", font=ctk.CTkFont(size=12),
                         text_color=T["muted"]).pack(padx=12, pady=8); return

        def _build_rows():
            for sub, j in jars:
                jar_path = os.path.join(path, sub, j)
                meta = _read_jar_meta(jar_path)
                icon_bytes = meta.get("icon")
                row = ctk.CTkFrame(plf, fg_color="transparent",
                                   cursor="hand2")
                row.pack(fill="x", padx=6, pady=2)
                ctk.CTkFrame(row, height=1, fg_color=T["border"]).pack(fill="x")
                inner = ctk.CTkFrame(row, fg_color="transparent"); inner.pack(fill="x", padx=4, pady=4)
                # icon
                ic = _make_icon_widget(inner, icon_bytes, size=32)
                ic.pack(side="left", padx=(0,10))
                # text
                txt_col = ctk.CTkFrame(inner, fg_color="transparent"); txt_col.pack(side="left", fill="y", expand=True)
                name_lbl = ctk.CTkLabel(txt_col, text=meta["name"],
                                        font=ctk.CTkFont(size=12, weight="bold"),
                                        text_color=T["text"], anchor="w")
                name_lbl.pack(anchor="w")
                desc_short = (meta["description"][:80]+"…") if len(meta["description"])>80 else meta["description"]
                if not desc_short: desc_short = f"{sub}/{j}"
                ctk.CTkLabel(txt_col, text=desc_short,
                             font=ctk.CTkFont(size=10), text_color=T["muted"], anchor="w"
                             ).pack(anchor="w")
                # version badge
                if meta["version"]:
                    ctk.CTkLabel(inner, text=f"v{meta['version']}",
                                 font=ctk.CTkFont(size=9), text_color=T["sync"],
                                 fg_color=T["bg"], corner_radius=4,
                                 width=50).pack(side="right", padx=4)
                # click anywhere on row opens detail
                for w in (inner, ic, txt_col, name_lbl):
                    try: w.bind("<Button-1>", lambda e,jp=jar_path,m=meta: _show_detail(jp,m))
                    except: pass

        threading.Thread(target=_build_rows, daemon=True).start()

    refresh_plugins()
    ctk.CTkButton(hdr, text="Refresh", width=66, height=22, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=refresh_plugins).pack(side="right")


def _build_props_sub(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)
    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12,0))
    ctk.CTkLabel(hf, text="Server Properties", font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=T["text"]).pack(anchor="w", padx=12, pady=(10,4))
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)

    ALL_PROPS = [
        ("gamemode","Game Mode","survival"), ("difficulty","Difficulty","easy"),
        ("max-players","Max Players","20"), ("view-distance","View Distance","10"),
        ("server-port","Port","25565"), ("online-mode","Online Mode","true"),
        ("pvp","PvP","true"), ("spawn-monsters","Spawn Monsters","true"),
        ("allow-flight","Allow Flight","false"), ("white-list","Whitelist","false"),
        ("level-name","World Name","world"), ("motd","MOTD","A Minecraft Server"),
        ("spawn-protection","Spawn Protection","16"), ("level-seed","Seed",""),
        ("allow-nether","Allow Nether","true"), ("enable-command-block","Command Blocks","false"),
    ]
    props_vars = {}

    def load_props():
        path = load_settings().get("srv_path", _DEFAULT_SRV); kv = {}
        try:
            with open(os.path.join(path,"server.properties"), encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k,_,v = line.partition("="); kv[k.strip()] = v.strip()
        except: pass
        return kv

    def save_props():
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        pfile = os.path.join(path, "server.properties")
        try:
            lines = open(pfile, encoding="utf-8", errors="ignore").readlines()
            updated = set(); new_lines = []
            for line in lines:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k = s.partition("=")[0].strip()
                    new_lines.append(f"{k}={props_vars[k].get()}\n" if k in props_vars else line)
                    if k in props_vars: updated.add(k)
                else: new_lines.append(line)
            for k in props_vars:
                if k not in updated: new_lines.append(f"{k}={props_vars[k].get()}\n")
            with open(pfile, "w", encoding="utf-8") as fp: fp.writelines(new_lines)
            show_toast("Saved!", T["start"])
        except Exception as ex: show_toast(f"Save failed: {ex}", T["stop"])

    kv = load_props()
    pb = ctk.CTkFrame(hf, fg_color="transparent"); pb.pack(fill="x", padx=12, pady=(6,0))
    pg = ctk.CTkScrollableFrame(pb, fg_color=T["bg"], border_color=T["border"],
                                 border_width=1, corner_radius=8, height=280)
    pg.pack(fill="x"); pg.columnconfigure((0,1,2), weight=1)
    for i,(key,label,default) in enumerate(ALL_PROPS):
        var = ctk.StringVar(value=kv.get(key,default)); props_vars[key] = var
        cell = ctk.CTkFrame(pg, fg_color="transparent")
        cell.grid(row=i//3, column=i%3, padx=4, pady=2, sticky="ew")
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
        ctk.CTkEntry(cell, textvariable=var, height=26,
                     font=ctk.CTkFont(size=11,family="Consolas"),
                     fg_color=T["card"], border_color=T["border"], text_color=T["text"]).pack(fill="x")
    ctk.CTkButton(pb, text="Save server.properties", height=32, corner_radius=8,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=save_props).pack(pady=(8,0), fill="x")
    ctk.CTkLabel(pb, text="Restart server for changes to take effect.",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(3,10))

# ── Backup sub-tab (inside Server Info) ──────────────────
def _build_backup_sub(parent):
    import zipfile
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(fill="both", expand=True)
    s = load_settings()
    bdir_var  = ctk.StringVar(value=s.get("backup_dir",""))
    keep_var  = ctk.StringVar(value=str(s.get("backup_keep",10)))
    auto_var  = ctk.BooleanVar(value=s.get("backup_auto",False))
    mins_var  = ctk.StringVar(value=str(s.get("backup_interval_mins",30)))
    _btimer   = [None]

    def card(title):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=12); f.pack(fill="x", padx=18, pady=(10,0))
        h = ctk.CTkFrame(f,fg_color="transparent"); h.pack(fill="x",padx=12,pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12,weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f,height=1,fg_color=T["border"]).pack(fill="x",padx=12)
        b = ctk.CTkFrame(f,fg_color="transparent"); b.pack(fill="x",padx=12,pady=(8,10))
        return b, h

    # ── Tutorial card ────────────────────────────────────
    tb, _ = card("📖 How to use Backups")
    tutorial = (
        "Backups create a .zip snapshot of your world folders — safe even if GitHub goes down.\n\n"
        "Quick start:\n"
        "  1. Set Destination (leave blank to save in  server/backups/).\n"
        "  2. Set 'Keep last N' — older backups are auto-deleted when that limit is hit.\n"
        "  3. Click 'Create Backup Now' for an instant manual snapshot.\n"
        "  4. Toggle 'Auto backup while running' + set Interval for hands-free backups.\n\n"
        "Restore a backup:\n"
        "  1. Stop the server first.\n"
        "  2. Click 'Open' on any listed backup — it opens the backups folder.\n"
        "  3. Extract the .zip and replace the world/, world_nether/, world_the_end/ folders.\n"
        "  4. Start the server again.\n\n"
        "Tips:\n"
        "  • Keep at least 5–10 backups. Storage is cheap; world corruption is not.\n"
        "  • Auto-backup every 30–60 minutes is a good default for active servers.\n"
        "  • Manual backup before major builds or events is always a good idea."
    )
    ctk.CTkLabel(tb, text=tutorial, font=ctk.CTkFont(size=11), text_color=T["muted"],
                 justify="left", wraplength=820).pack(anchor="w")

    def save_bs(*_):
        update_setting("backup_dir",           bdir_var.get())
        update_setting("backup_keep",          int(keep_var.get() or 10))
        update_setting("backup_interval_mins", int(mins_var.get() or 30))

    sb, _ = card("Backup Settings")
    r0 = ctk.CTkFrame(sb,fg_color="transparent"); r0.pack(fill="x",pady=3)
    ctk.CTkLabel(r0,text="Destination",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    ctk.CTkEntry(r0, textvariable=bdir_var, height=26, font=ctk.CTkFont(size=11,family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="blank = server/backups/").pack(side="left",fill="x",expand=True,padx=(0,6))
    ctk.CTkButton(r0, text="Browse", width=64, height=26, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: (bdir_var.set(_tk_fd.askdirectory(title="Backup destination")), save_bs())
                  ).pack(side="left")

    for label, var in [("Keep last N", keep_var), ("Interval (mins)", mins_var)]:
        r = ctk.CTkFrame(sb,fg_color="transparent"); r.pack(fill="x",pady=3)
        ctk.CTkLabel(r,text=label,font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
        e = ctk.CTkEntry(r, textvariable=var, width=80, height=26,
                         font=ctk.CTkFont(size=12,family="Consolas"),
                         fg_color=T["bg"],border_color=T["border"],text_color=T["text"])
        e.pack(side="left"); e.bind("<FocusOut>",save_bs); e.bind("<Return>",save_bs)

    r2 = ctk.CTkFrame(sb,fg_color="transparent"); r2.pack(fill="x",pady=3)
    ctk.CTkLabel(r2,text="Auto backup while running",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    def _tog_auto(v): update_setting("backup_auto",v); (_schedule_bkp() if v else None)
    ctk.CTkSwitch(r2,text="",variable=auto_var,command=lambda: _tog_auto(auto_var.get()),
                  button_color=T["sync"],progress_color=T["sync"]).pack(side="left")

    def _get_dest():
        custom = bdir_var.get().strip()
        if custom and os.path.isdir(custom): return custom
        path = load_settings().get("srv_path",_DEFAULT_SRV)
        dest = os.path.join(path,"backups"); os.makedirs(dest,exist_ok=True); return dest

    def _prune(dest):
        keep = int(keep_var.get() or 10)
        zips = sorted([os.path.join(dest,f) for f in os.listdir(dest) if f.endswith(".zip")], key=os.path.getmtime)
        while len(zips) > keep:
            try: os.remove(zips.pop(0))
            except: pass

    mb, _ = card("Create Backup")
    wrld_var = ctk.StringVar(value="world,world_nether,world_the_end")
    r4 = ctk.CTkFrame(mb,fg_color="transparent"); r4.pack(fill="x",pady=3)
    ctk.CTkLabel(r4,text="Folders (comma-sep)",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    ctk.CTkEntry(r4, textvariable=wrld_var, height=26,
                 font=ctk.CTkFont(size=11,family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]).pack(side="left",fill="x",expand=True)
    bk_st = ctk.CTkLabel(mb,text="",font=ctk.CTkFont(size=11),text_color=T["muted"]); bk_st.pack(anchor="w",pady=(4,0))
    bk_pg = ctk.CTkProgressBar(mb,height=5); bk_pg.set(0)

    def _do_backup(auto=False):
        s2 = load_settings(); path = s2.get("srv_path",_DEFAULT_SRV); dest = _get_dest()
        folders = [f.strip() for f in wrld_var.get().split(",") if f.strip()]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zname = os.path.join(dest, f"backup_{'auto' if auto else 'manual'}_{ts}.zip")
        def _work():
            try:
                app.after(0, lambda: bk_st.configure(text="Creating backup…",text_color=T["sync"]))
                app.after(0, lambda: (bk_pg.set(0), bk_pg.pack(fill="x",pady=(4,0))))
                total = sum(sum(1 for _ in os.walk(os.path.join(path,f))) for f in folders if os.path.isdir(os.path.join(path,f)))
                done = [0]
                with zipfile.ZipFile(zname,"w",zipfile.ZIP_DEFLATED) as zf:
                    for folder in folders:
                        src = os.path.join(path,folder)
                        if not os.path.isdir(src): continue
                        for root2,dirs,files in os.walk(src):
                            for file in files:
                                fp = os.path.join(root2,file); arcname = os.path.relpath(fp,path)
                                zf.write(fp,arcname); done[0] += 1
                                if total: app.after(0, bk_pg.set, min(done[0]/total,1.0))
                size_mb = os.path.getsize(zname)/1048576; _prune(dest)
                app.after(0, lambda: bk_st.configure(text=f"Done! {size_mb:.1f} MB",text_color=T["start"]))
                app.after(0, bk_pg.set, 1.0)
                app.after(0, show_toast, f"Backup done ({size_mb:.1f} MB)", T["start"])
                app.after(0, _refresh_bklist)
            except Exception as ex: app.after(0, lambda: bk_st.configure(text=f"Failed: {ex}",text_color=T["stop"]))
        threading.Thread(target=_work,daemon=True).start()

    def _schedule_bkp():
        if _btimer[0]:
            try: _btimer[0].cancel()
            except: pass
        if not auto_var.get(): return
        mins = int(mins_var.get() or 30)
        def _fire(): _do_backup(auto=True); _schedule_bkp()
        _next_ts = time.time() + mins*60
        try: globals().get("_dashboard_set_backup_ts", lambda x:None)(_next_ts)
        except: pass
        _btimer[0] = threading.Timer(mins*60,_fire); _btimer[0].daemon=True; _btimer[0].start()

    ctk.CTkButton(mb, text="Create Backup Now", height=32, corner_radius=8,
                  font=ctk.CTkFont(size=12,weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=lambda: threading.Thread(target=_do_backup,daemon=True).start()
                  ).pack(anchor="w",pady=(6,0))

    lb, lh = card("Saved Backups")
    blf = ctk.CTkScrollableFrame(lb, fg_color=T["bg"], border_color=T["border"],
                                  border_width=1, corner_radius=8, height=200)
    blf.pack(fill="x")

    def _refresh_bklist():
        for w in blf.winfo_children(): w.destroy()
        dest = _get_dest()
        try: zips = sorted([f for f in os.listdir(dest) if f.endswith(".zip")],
                            key=lambda f: os.path.getmtime(os.path.join(dest,f)), reverse=True)
        except: zips = []
        if not zips:
            ctk.CTkLabel(blf,text="No backups found.",font=ctk.CTkFont(size=12),text_color=T["muted"]).pack(padx=12,pady=8); return
        for z in zips:
            full = os.path.join(dest,z); sz = os.path.getsize(full)/1048576
            mt = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
            row = ctk.CTkFrame(blf,fg_color="transparent"); row.pack(fill="x",padx=6,pady=2)
            ctk.CTkLabel(row,text=z,font=ctk.CTkFont(size=10,family="Consolas"),text_color=T["text"]).pack(side="left")
            ctk.CTkLabel(row,text=f"{sz:.1f}MB  {mt}",font=ctk.CTkFont(size=10),text_color=T["muted"]).pack(side="left",padx=6)
            ctk.CTkButton(row,text="Delete",width=54,height=20,font=ctk.CTkFont(size=10),
                          fg_color="transparent",border_width=1,border_color=T["stop"],
                          text_color=T["stop"],hover_color=T["border"],
                          command=lambda p=full,n=z: (os.remove(p),show_toast(f"Deleted {n}",T["stop"]),_refresh_bklist())
                          ).pack(side="right")
            ctk.CTkButton(row,text="Open",width=46,height=20,font=ctk.CTkFont(size=10),
                          fg_color="transparent",border_width=1,border_color=T["border"],
                          text_color=T["muted"],hover_color=T["border"],
                          command=lambda d=dest: _open_folder(d)).pack(side="right",padx=(0,4))

    _refresh_bklist()
    ctk.CTkButton(lh,text="Refresh",width=66,height=22,font=ctk.CTkFont(size=10),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],command=_refresh_bklist).pack(side="right")
    ctk.CTkFrame(scroll,height=12,fg_color="transparent").pack()
    if auto_var.get(): _schedule_bkp()

# ══════════════════════════════════════════════════════════
# DOCKER TAB
# ══════════════════════════════════════════════════════════
def build_docker_tab(parent):
    _build_ip_footer(parent)
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent"); scroll.pack(side="top", fill="both", expand=True)

    def card(title):
        f = ctk.CTkFrame(scroll,fg_color=T["card"],border_color=T["border"],border_width=1,corner_radius=12)
        f.pack(fill="x",padx=18,pady=(10,0))
        h = ctk.CTkFrame(f,fg_color="transparent"); h.pack(fill="x",padx=12,pady=(10,4))
        ctk.CTkLabel(h,text=title,font=ctk.CTkFont(size=12,weight="bold"),text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f,height=1,fg_color=T["border"]).pack(fill="x",padx=12)
        b = ctk.CTkFrame(f,fg_color="transparent"); b.pack(fill="x",padx=12,pady=(8,10))
        return b, h

    def _docker_ok():
        try: return subprocess.run("docker version",shell=True,capture_output=True,text=True,
                                   creationflags=_popen_flags(),timeout=5).returncode==0
        except: return False

    ab, _ = card("Docker Support")
    dok = _docker_ok()
    ctk.CTkLabel(ab,text=(
        "Run your Minecraft server inside a Docker container.\n"
        "No Java install needed — it's bundled in the container.\n\n"
        "docker compose up  →  server starts instantly\n"
        "Persistent data    →  world files mount to your server folder"
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    ctk.CTkLabel(ab, text="● Docker available" if dok else "● Docker not found",
                 font=ctk.CTkFont(size=11,weight="bold"),
                 text_color=T["start"] if dok else T["stop"]).pack(anchor="w",pady=(6,0))
    if not dok:
        ctk.CTkLabel(ab,text="Install Docker Desktop: https://www.docker.com/products/docker-desktop/",
                     font=ctk.CTkFont(size=10),text_color=T["muted"]).pack(anchor="w")

    s = load_settings()
    dc_image = ctk.StringVar(value=s.get("docker_image","itzg/minecraft-server"))
    dc_port  = ctk.StringVar(value=s.get("docker_port","25565"))
    dc_ram   = ctk.StringVar(value=s.get("docker_ram","2G"))
    dc_type  = ctk.StringVar(value=s.get("docker_type","PAPER"))
    dc_ver   = ctk.StringVar(value=s.get("docker_version","LATEST"))
    dc_name  = ctk.StringVar(value=s.get("docker_name","mc-server"))

    def _save_dc(*_):
        for k,v in [("docker_image",dc_image),("docker_port",dc_port),("docker_ram",dc_ram),
                    ("docker_type",dc_type),("docker_version",dc_ver),("docker_name",dc_name)]:
            update_setting(k,v.get())

    cc, ch = card("Docker Compose Config")
    def row_e(parent,label,var,w=160,ph=""):
        r = ctk.CTkFrame(parent,fg_color="transparent"); r.pack(fill="x",pady=2)
        ctk.CTkLabel(r,text=label,font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
        e = ctk.CTkEntry(r,textvariable=var,width=w,height=26,font=ctk.CTkFont(size=11,family="Consolas"),
                         fg_color=T["bg"],border_color=T["border"],text_color=T["text"],placeholder_text=ph)
        e.pack(side="left"); e.bind("<FocusOut>",_save_dc); e.bind("<Return>",_save_dc)
    row_e(cc,"Container name",dc_name,placeholder="mc-server")
    row_e(cc,"Docker image",dc_image,w=280,placeholder="itzg/minecraft-server")
    row_e(cc,"Port",dc_port,placeholder="25565")
    row_e(cc,"RAM limit",dc_ram,placeholder="2G")
    rt = ctk.CTkFrame(cc,fg_color="transparent"); rt.pack(fill="x",pady=2)
    ctk.CTkLabel(rt,text="Server type",font=ctk.CTkFont(size=12),text_color=T["text"],width=180,anchor="w").pack(side="left")
    ctk.CTkOptionMenu(rt,values=["PAPER","PURPUR","VANILLA","FABRIC","FORGE","SPIGOT"],
                      variable=dc_type,command=lambda _: _save_dc(),
                      font=ctk.CTkFont(size=12),width=130,height=26,
                      fg_color=T["bg"],button_color=T["border"],button_hover_color=T["muted"],
                      text_color=T["text"],dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"],dropdown_hover_color=T["border"]).pack(side="left",padx=(0,10))
    row_e(cc,"MC version",dc_ver,w=100,ph="LATEST")

    pv_box = None
    def _gen():
        nonlocal pv_box
        path = load_settings().get("srv_path",_DEFAULT_SRV)
        yaml = f"""version: "3.8"\nservices:\n  {dc_name.get()}:\n    image: {dc_image.get()}\n    container_name: {dc_name.get()}\n    environment:\n      EULA: "TRUE"\n      TYPE: "{dc_type.get()}"\n      VERSION: "{dc_ver.get()}"\n      MEMORY: "{dc_ram.get()}"\n      USE_AIKAR_FLAGS: "true"\n    ports:\n      - "{dc_port.get()}:{dc_port.get()}"\n    volumes:\n      - ./data:/data\n    restart: unless-stopped\n"""
        dest = os.path.join(path,"docker-compose.yml")
        try:
            with open(dest,"w") as f2: f2.write(yaml)
            show_toast("docker-compose.yml written!", T["start"])
            if pv_box:
                try: pv_box.configure(state="normal"); pv_box.delete("1.0","end"); pv_box.insert("end",yaml); pv_box.configure(state="disabled")
                except: pass
        except Exception as ex: show_toast(f"Error: {ex}", T["stop"])

    ctk.CTkButton(ch,text="Generate compose",height=24,width=140,font=ctk.CTkFont(size=11),
                  fg_color=T["start"],hover_color=T["start"],text_color="#000",command=_gen).pack(side="right")

    pb, _ = card("docker-compose.yml Preview")
    pv_box = ctk.CTkTextbox(pb,font=ctk.CTkFont(size=11,family="Consolas"),height=160,
                             fg_color=T["bg"],text_color=T["text"],state="disabled")
    pv_box.pack(fill="x")
    cp = os.path.join(load_settings().get("srv_path",_DEFAULT_SRV),"docker-compose.yml")
    if os.path.exists(cp):
        try: pv_box.configure(state="normal"); pv_box.insert("end",open(cp).read()); pv_box.configure(state="disabled")
        except: pass

    ctrl_b, ctrl_h = card("Container Control")
    dc_st = ctk.CTkLabel(ctrl_b,text="● Unknown",font=ctk.CTkFont(size=13,weight="bold"),text_color=T["muted"])
    dc_st.pack(side="left")
    dc_log = ctk.CTkTextbox(ctrl_b,font=ctk.CTkFont(size=10,family="Consolas"),height=110,
                             fg_color=T["bg"],text_color=T["text"],state="disabled")

    def _dclog(msg):
        try: dc_log.configure(state="normal"); dc_log.insert("end",msg+"\n"); dc_log.configure(state="disabled"); dc_log.see("end")
        except: pass

    def _dc_status():
        name = dc_name.get().strip() or "mc-server"
        try:
            r = subprocess.run(f"docker inspect --format={{{{.State.Status}}}} {name}",
                               shell=True,capture_output=True,text=True,creationflags=_popen_flags(),timeout=5)
            st = r.stdout.strip()
            dc_st.configure(text=f"● {st.capitalize() if st else 'Not created'}",
                            text_color=T["start"] if st=="running" else T["muted"] if st else T["stop"])
        except: dc_st.configure(text="● Docker unavailable",text_color=T["stop"])

    def _run_dc(cmd_str, label):
        path = load_settings().get("srv_path",_DEFAULT_SRV)
        def _w():
            app.after(0,_dclog,f"$ {cmd_str}")
            try:
                proc = subprocess.Popen(cmd_str,shell=True,cwd=path,stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,text=True,creationflags=_popen_flags())
                for line in proc.stdout: app.after(0,_dclog,line.rstrip())
                proc.wait(); app.after(0,_dc_status); app.after(0,show_toast,f"{label} done",T["start"])
            except Exception as ex: app.after(0,_dclog,f"Error: {ex}")
        threading.Thread(target=_w,daemon=True).start()

    name = dc_name.get().strip() or "mc-server"
    br = ctk.CTkFrame(ctrl_h,fg_color="transparent"); br.pack(side="right")
    for label,cmd,fc in [("▶ Up","docker compose up -d",T["start"]),("■ Down","docker compose down",T["stop"]),
                          ("↺ Restart",f"docker restart {name}",T["sync"]),("Logs",f"docker logs --tail=50 {name}",T["muted"])]:
        ctk.CTkButton(br,text=label,width=74,height=26,font=ctk.CTkFont(size=11),
                      fg_color=fc,hover_color=fc,text_color="#000" if fc!=T["stop"] else "#fff",
                      command=lambda c=cmd,l=label: _run_dc(c,l)).pack(side="left",padx=(0,3))
    ctk.CTkButton(br,text="Status",width=60,height=26,font=ctk.CTkFont(size=11),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],command=_dc_status).pack(side="left")
    ctk.CTkButton(br,text="Pull Image",width=80,height=26,font=ctk.CTkFont(size=11),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],
                  command=lambda: _run_dc(f"docker pull {dc_image.get()}","Pull")).pack(side="left",padx=(3,0))
    dc_log.pack(fill="x",pady=(8,0))
    app.after(500, _dc_status)  # defer status check so widget is fully rendered first

    def _auto_dc_status():
        try: _dc_status(); dc_st.after(10000, _auto_dc_status)
        except: pass
    app.after(1000, _auto_dc_status)
    ctk.CTkFrame(scroll,height=12,fg_color="transparent").pack()

# ══════════════════════════════════════════════════════════
# MULTI CTRL TAB
# ══════════════════════════════════════════════════════════
def build_multictrl_tab(parent):
    _build_ip_footer(parent)
    MAX = 3; slots = {}
    for i in range(MAX):
        slots[i] = {"proc":None,"stdin":None,"path_var":ctk.StringVar(value=""),"log_box":None,"status":None,"running":False}
    _mc_wrap = ctk.CTkFrame(parent, fg_color="transparent")
    _mc_wrap.pack(side="top", fill="both", expand=True)
    parent = _mc_wrap
    parent.rowconfigure(0,weight=0); parent.rowconfigure(1,weight=1); parent.rowconfigure(2,weight=0)
    parent.columnconfigure(0,weight=1)

    tb = ctk.CTkFrame(parent,fg_color=T["card"],border_color=T["border"],border_width=1,corner_radius=0)
    tb.grid(row=0,column=0,sticky="ew")
    ctk.CTkLabel(tb,text="⊞ MULTI CTRL",font=ctk.CTkFont(size=13,weight="bold"),text_color=T["hand"]).pack(side="left",padx=12,pady=7)
    ctk.CTkLabel(tb,text="— control up to 3 servers simultaneously",font=ctk.CTkFont(size=10),text_color=T["muted"]).pack(side="left")

    ca = ctk.CTkFrame(parent,fg_color="transparent")
    ca.grid(row=1,column=0,sticky="nsew",padx=3,pady=3)
    for i in range(MAX): ca.columnconfigure(i,weight=1,uniform="col")
    ca.rowconfigure(0,weight=1)

    def _mclog(slot,msg):
        lb=slots[slot]["log_box"]
        if lb is None: return
        try: lb.configure(state="normal"); lb.insert("end",msg+"\n"); lb.configure(state="disabled"); lb.see("end")
        except: pass
    def _mcst(slot,txt,col):
        lbl=slots[slot]["status"]
        if lbl:
            try: lbl.configure(text=txt,text_color=col)
            except: pass
    def _read_mc(slot,proc):
        for raw in iter(proc.stdout.readline,""):
            if not raw: break
            app.after(0,_mclog,slot,raw.rstrip())
        app.after(0,_mcst,slot,"● Stopped",T["stop"])
        slots[slot].update({"running":False,"proc":None,"stdin":None})
    def _start_mc(slot):
        path=slots[slot]["path_var"].get().strip()
        if not path or not os.path.isdir(path): show_toast(f"Server {slot+1}: invalid folder.",T["stop"]); return
        if slots[slot]["running"]: show_toast(f"Server {slot+1} already running.",T["muted"]); return
        s=load_settings(); java=s.get("java_path",_DEFAULT_JAVA); jar=os.path.join(path,"server.jar")
        if not os.path.exists(jar): show_toast(f"Server {slot+1}: no server.jar.",T["stop"]); return
        if not _check_eula(path): return
        try:
            kw={"cwd":path,"stdin":subprocess.PIPE,"stdout":subprocess.PIPE,"stderr":subprocess.STDOUT,"text":True,"bufsize":1}
            if IS_WIN: kw["creationflags"]=_NO_WIN
            proc=subprocess.Popen([java,"-Xms512M","-Xmx2G","-XX:+UseG1GC","-jar",jar,"--nogui"],**kw)
            slots[slot].update({"proc":proc,"stdin":proc.stdin,"running":True})
            _mcst(slot,"● Running",T["start"])
            threading.Thread(target=_read_mc,args=(slot,proc),daemon=True).start()
        except Exception as ex: show_toast(f"Server {slot+1} failed: {ex}",T["stop"])
    def _stop_mc(slot):
        proc=slots[slot]["proc"]
        if proc:
            try: slots[slot]["stdin"].write("stop\n"); slots[slot]["stdin"].flush()
            except: pass
            app.after(3000,lambda p=proc: p.terminate() if p.poll() is None else None)
        slots[slot].update({"running":False,"proc":None,"stdin":None})
        _mcst(slot,"● Stopped",T["stop"])

    for i in range(MAX):
        col=ctk.CTkFrame(ca,fg_color=T["card"],border_color=T["border"],border_width=1,corner_radius=10)
        col.grid(row=0,column=i,sticky="nsew",padx=3,pady=0)
        col.rowconfigure(2,weight=1); col.columnconfigure(0,weight=1)
        hdr=ctk.CTkFrame(col,fg_color=T["bg"],corner_radius=6)
        hdr.grid(row=0,column=0,sticky="ew",padx=6,pady=(6,3))
        ctk.CTkLabel(hdr,text=f"Server {i+1}",font=ctk.CTkFont(size=12,weight="bold"),text_color=T["text"]).pack(side="left",padx=8,pady=5)
        st=ctk.CTkLabel(hdr,text="● Stopped",font=ctk.CTkFont(size=10,weight="bold"),text_color=T["stop"]); st.pack(side="right",padx=8)
        slots[i]["status"]=st
        pf=ctk.CTkFrame(col,fg_color="transparent"); pf.grid(row=1,column=0,sticky="ew",padx=6,pady=(0,3)); pf.columnconfigure(0,weight=1)
        ctk.CTkEntry(pf,textvariable=slots[i]["path_var"],height=26,font=ctk.CTkFont(size=10,family="Consolas"),
                     fg_color=T["bg"],border_color=T["border"],text_color=T["text"],
                     placeholder_text=f"Server {i+1} folder…").grid(row=0,column=0,sticky="ew",padx=(0,3))
        ctk.CTkButton(pf,text="…",width=26,height=26,font=ctk.CTkFont(size=11),corner_radius=5,
                      fg_color=T["bg"],border_width=1,border_color=T["border"],
                      text_color=T["muted"],hover_color=T["border"],
                      command=lambda s=i: slots[s]["path_var"].set(_tk_fd.askdirectory(title=f"Server {s+1}") or slots[s]["path_var"].get())
                      ).grid(row=0,column=1)
        br=ctk.CTkFrame(pf,fg_color="transparent"); br.grid(row=1,column=0,columnspan=2,sticky="ew",pady=(3,0))
        ctk.CTkButton(br,text="▶ Start",height=24,font=ctk.CTkFont(size=10),fg_color=T["start"],
                      hover_color=T["start"],text_color="#000",
                      command=lambda s=i: threading.Thread(target=_start_mc,args=(s,),daemon=True).start()
                      ).pack(side="left",expand=True,fill="x",padx=(0,2))
        ctk.CTkButton(br,text="■ Stop",height=24,font=ctk.CTkFont(size=10),fg_color=T["stop"],
                      hover_color=T["stop"],text_color="#fff",command=lambda s=i: _stop_mc(s)
                      ).pack(side="left",expand=True,fill="x",padx=(2,0))
        lb=ctk.CTkTextbox(col,font=ctk.CTkFont(size=10,family="Consolas"),wrap="word",
                           state="disabled",fg_color=T["bg"],text_color=T["text"])
        lb.grid(row=2,column=0,sticky="nsew",padx=6,pady=(0,6)); slots[i]["log_box"]=lb

    chatbar=ctk.CTkFrame(parent,fg_color=T["card"],border_color=T["border"],border_width=1,corner_radius=0)
    chatbar.grid(row=2,column=0,sticky="ew"); chatbar.columnconfigure(2,weight=1)
    tgt=ctk.StringVar(value="Server 1")
    ctk.CTkLabel(chatbar,text="Send to:",font=ctk.CTkFont(size=11),text_color=T["muted"]).grid(row=0,column=0,padx=(8,4),pady=7)
    ctk.CTkOptionMenu(chatbar,values=["Server 1","Server 2","Server 3","All Servers"],variable=tgt,
                      font=ctk.CTkFont(size=11),width=110,height=28,
                      fg_color=T["bg"],button_color=T["border"],button_hover_color=T["muted"],
                      text_color=T["text"],dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"],dropdown_hover_color=T["border"]
                      ).grid(row=0,column=1,padx=(0,5),pady=7)
    mc_cmd=ctk.CTkEntry(chatbar,height=28,font=ctk.CTkFont(size=12),fg_color=T["bg"],
                         border_color=T["border"],text_color=T["text"],placeholder_text="command…")
    mc_cmd.grid(row=0,column=2,sticky="ew",padx=(0,5),pady=7)
    def _mc_send(_e=None):
        cmd=mc_cmd.get().strip()
        if not cmd: return
        t=tgt.get(); targets=list(range(MAX)) if t=="All Servers" else [int(t.split()[-1])-1]
        for s in targets:
            si=slots[s]["stdin"]
            if si:
                try: si.write(cmd+"\n"); si.flush(); app.after(0,_mclog,s,f">> {cmd}")
                except Exception as ex: app.after(0,_mclog,s,f"[error] {ex}")
            else: app.after(0,_mclog,s,f"[Server {s+1} not running]")
        mc_cmd.delete(0,"end")
    mc_cmd.bind("<Return>",_mc_send)
    ctk.CTkButton(chatbar,text="Send",width=66,height=28,font=ctk.CTkFont(size=11),
                  fg_color=T["sync"],hover_color=T["sync"],text_color="#000",
                  command=_mc_send).grid(row=0,column=3,padx=(0,8),pady=7)
    ctk.CTkButton(chatbar,text="📱 Remote Server",width=130,height=28,font=ctk.CTkFont(size=11),
                  fg_color=T["hand"],hover_color=T["hand"],text_color="#000",
                  command=lambda: globals().get("_dsub_goto_remote",lambda:None)()
                  ).grid(row=0,column=4,padx=(0,8),pady=7)

# ══════════════════════════════════════════════════════════
# MODPACK TAB
# ══════════════════════════════════════════════════════════
def build_modpack_tab(parent):
    _build_ip_footer(parent)
    _mp_f = ctk.CTkFrame(parent, fg_color="transparent")
    _mp_f.pack(side="top", fill="both", expand=True)
    parent = _mp_f
    try:
        spec = importlib.util.spec_from_file_location(
            "mc_modpack",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "mc_modpack.py"))
        mod  = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.build_modpack_tab(parent, T, show_toast, load_settings, _DEFAULT_SRV)
    except Exception as ex:
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=f"⚠  mc_modpack.py not found or has an error:\n{ex}",
                     font=ctk.CTkFont(size=13), text_color=T["stop"],
                     justify="center").place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(f, text="Place mc_modpack.py in the same folder as launcher.pyw",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).place(relx=0.5, rely=0.48, anchor="center")

# ══════════════════════════════════════════════════════════
# SETTINGS WINDOW — includes Addons section
# ══════════════════════════════════════════════════════════
def build_settings_window(parent):
    # Tab bar inside settings
    stab_bar = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=0,
                             border_color=T["border"], border_width=1)
    stab_bar.pack(side="top", fill="x")
    stab_content = ctk.CTkFrame(parent, fg_color="transparent")
    stab_content.pack(side="top", fill="both", expand=True)

    STABS = [("general","General"), ("addons","🧩 Addons")]
    stab_frames = {k: ctk.CTkFrame(stab_content, fg_color="transparent") for k,_ in STABS}
    _stab_built = set(); stab_btns = {}

    def show_stab(name):
        for f in stab_frames.values(): f.pack_forget()
        for n, b in stab_btns.items():
            b.configure(fg_color=T["sync"] if n==name else "transparent",
                        text_color="#000" if n==name else T["muted"])
        if name not in _stab_built:
            _stab_built.add(name)
            {"general": lambda: _build_general_settings(stab_frames["general"]),
             "addons":  lambda: _build_addons_settings(stab_frames["addons"])}[name]()
        stab_frames[name].pack(fill="both", expand=True)

    for key, label in STABS:
        b = ctk.CTkButton(stab_bar, text=label, width=100, height=26,
                          font=ctk.CTkFont(size=11), corner_radius=5,
                          fg_color="transparent", text_color=T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_stab(k))
        b.pack(side="left", padx=(6 if key=="general" else 2, 2), pady=4)
        stab_btns[key] = b

    show_stab("general")

def _build_general_settings(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=18, pady=10)

    def section(title):
        f = ctk.CTkFrame(scroll,fg_color=T["card"],border_color=T["border"],border_width=1,corner_radius=12)
        f.pack(fill="x",pady=(0,10))
        ctk.CTkLabel(f,text=title,font=ctk.CTkFont(size=11,weight="bold"),text_color=T["text"]).pack(anchor="w",padx=12,pady=(10,4))
        ctk.CTkFrame(f,height=1,fg_color=T["border"]).pack(fill="x",padx=12)
        b=ctk.CTkFrame(f,fg_color="transparent"); b.pack(fill="x",padx=12,pady=(6,10)); return b

    def row_sw(parent,label,get_val,on_change):
        r=ctk.CTkFrame(parent,fg_color="transparent"); r.pack(fill="x",pady=4)
        ctk.CTkLabel(r,text=label,font=ctk.CTkFont(size=12),text_color=T["text"],width=280,anchor="w").pack(side="left")
        var=ctk.BooleanVar(value=get_val())
        ctk.CTkSwitch(r,text="",variable=var,command=lambda: on_change(var.get()),
                      button_color=T["sync"],progress_color=T["sync"]).pack(side="right")

    def row_entry(parent, label, key, default):
        r=ctk.CTkFrame(parent,fg_color="transparent"); r.pack(fill="x",pady=4)
        ctk.CTkLabel(r,text=label,font=ctk.CTkFont(size=12),text_color=T["text"],width=280,anchor="w").pack(side="left")
        e=ctk.CTkEntry(r,font=ctk.CTkFont(size=11,family="Consolas"),fg_color=T["bg"],
                       border_color=T["border"],text_color=T["text"],height=26)
        e.insert(0, load_settings().get(key, default)); e.pack(side="left",fill="x",expand=True)
        def save(*_): update_setting(key,e.get())
        e.bind("<FocusOut>",save); e.bind("<Return>",save)

    b = section("Appearance")
    r=ctk.CTkFrame(b,fg_color="transparent"); r.pack(fill="x",pady=4)
    ctk.CTkLabel(r,text="Theme",font=ctk.CTkFont(size=12),text_color=T["text"],width=280,anchor="w").pack(side="left")
    def _settings_open_theme():
        apply_theme(_theme_name)  # ensure T is current
        _open_theme_picker() if "_open_theme_picker" in dir() else None
    _stm_lbl = ctk.CTkLabel(r, text=f"🎨 {_theme_name}  (change via top bar picker)",
                             font=ctk.CTkFont(size=11), text_color=T["muted"])
    _stm_lbl.pack(side="right")
    row_sw(b,"Fullscreen",lambda: fullscreen,lambda v: _toggle_fullscreen())

    b = section("Layout")
    row_sw(b,"Log on left side",lambda: log_left,lambda v: _toggle_log_left())
    row_sw(b,"Show performance panel",lambda: show_perf,lambda v: _toggle_perf())
    row_sw(b,"Show chat & events",lambda: show_chat,lambda v: _toggle_chat())

    b = section("Server")
    row_entry(b,"Server path","srv_path",_DEFAULT_SRV)
    row_entry(b,"GitHub repo URL","repo_url",REPO_URL)
    row_entry(b,"Java path","java_path",_DEFAULT_JAVA)
    # Java version detector
    java_ver_r = ctk.CTkFrame(b, fg_color="transparent"); java_ver_r.pack(fill="x", pady=(0,4))
    _jver_lbl = ctk.CTkLabel(java_ver_r, text="Java: detecting…", font=ctk.CTkFont(size=10, family="Consolas"),
                              text_color=T["muted"]); _jver_lbl.pack(side="left", padx=(0,8))
    def _detect_java():
        s3 = load_settings(); java_exe = s3.get("java_path", _DEFAULT_JAVA)
        try:
            r = subprocess.run([java_exe, "-version"], capture_output=True, text=True, timeout=5,
                               creationflags=_popen_flags())
            out = (r.stderr or r.stdout or "").strip().splitlines()
            ver_line = out[0] if out else "unknown"
            try: app.after(0, _jver_lbl.configure, {"text": f"Java: {ver_line}", "text_color": T["start"]})
            except: pass
        except Exception as ex:
            try: app.after(0, _jver_lbl.configure, {"text": f"Java: not found ({ex})", "text_color": T["stop"]})
            except: pass
    ctk.CTkButton(java_ver_r, text="Detect", width=60, height=22, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: threading.Thread(target=_detect_java, daemon=True).start()
                  ).pack(side="left")
    threading.Thread(target=_detect_java, daemon=True).start()
    # RAM slider
    ram_r = ctk.CTkFrame(b, fg_color="transparent"); ram_r.pack(fill="x", pady=4)
    ctk.CTkLabel(ram_r, text="Server RAM (GB)", font=ctk.CTkFont(size=12), text_color=T["text"], width=280, anchor="w").pack(side="left")
    _ram_gb = load_settings().get("server_ram_gb", 2)
    _ram_var = ctk.IntVar(value=_ram_gb)
    _ram_lbl = ctk.CTkLabel(ram_r, text=f"{_ram_gb} GB", font=ctk.CTkFont(size=12, family="Consolas"), text_color=T["sync"], width=44, anchor="e")
    _ram_lbl.pack(side="right")
    def _on_ram(v):
        iv = int(float(v)); _ram_lbl.configure(text=f"{iv} GB"); update_setting("server_ram_gb", iv)
    ctk.CTkSlider(ram_r, from_=1, to=16, number_of_steps=15, variable=_ram_var, command=_on_ram,
                  button_color=T["sync"], progress_color=T["sync"], width=160).pack(side="right", padx=(0,8))

    b = section("Auto Upload")
    row_sw(b,"Enable auto upload",lambda: auto_upload,lambda v: toggle_auto_upload())
    row_sw(b,"Upload on server stop",lambda: upload_on_stop,lambda v: (globals().update({'upload_on_stop':v}),update_setting('upload_on_stop',v)))
    row_entry(b,"Upload interval (minutes)","auto_upload_mins",str(auto_upload_mins))

    plat = "Windows" if IS_WIN else ("Linux" if IS_LIN else "macOS")
    ctk.CTkLabel(scroll,text=f"Settings: {SETTINGS_FILE}  ·  Platform: {plat}",
                 font=ctk.CTkFont(size=10),text_color=T["muted"]).pack(anchor="w",pady=(4,0))

def _build_addons_settings(parent):
    """Addons manager — moved from main tab into Settings."""
    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)

    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    root = ctk.CTkFrame(parent, fg_color="transparent")
    root.grid(row=0, column=0, sticky="nsew")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=1)

    left = ctk.CTkFrame(root, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=0, width=240)
    left.grid(row=0, column=0, sticky="nsew")
    left.grid_propagate(False)
    left.rowconfigure(1, weight=1)
    left.columnconfigure(0, weight=1)

    lhdr = ctk.CTkFrame(left, fg_color=T["bg"], corner_radius=0)
    lhdr.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(lhdr, text="🧩 Addons", font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=12, pady=8)
    list_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
    list_scroll.grid(row=1, column=0, sticky="nsew")
    list_scroll.columnconfigure(0, weight=1)
    lfooter = ctk.CTkFrame(left, fg_color=T["bg"], corner_radius=0)
    lfooter.grid(row=2, column=0, sticky="ew")
    ctk.CTkFrame(lfooter, height=1, fg_color=T["border"]).pack(fill="x")

    right = ctk.CTkFrame(root, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")
    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)
    detail = ctk.CTkFrame(right, fg_color="transparent")
    detail.grid(row=0, column=0, sticky="nsew")
    detail.rowconfigure(0, weight=1)
    detail.columnconfigure(0, weight=1)

    _sel = [None]; _btns = {}

    def _get_meta(name):
        mod = _loaded_addons.get(name)
        if mod and hasattr(mod, "__meta__"): return mod.__meta__
        return {"title":name.replace("_"," ").title(),"version":"?","author":"Unknown",
                "description":"No description available.","settings":[]}

    def _show_empty():
        for w in detail.winfo_children(): w.destroy()
        empty = ctk.CTkFrame(detail, fg_color="transparent")
        empty.grid(row=0, column=0, sticky="nsew")
        empty.rowconfigure(0, weight=1); empty.columnconfigure(0, weight=1)
        inner = ctk.CTkFrame(empty, fg_color="transparent")
        inner.place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(inner, text="🧩", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(inner, text="Select an addon", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=T["text"]).pack(pady=(8,4))
        ctk.CTkLabel(inner, text="Pick an addon from the list to view details.",
                     font=ctk.CTkFont(size=12), text_color=T["muted"]).pack()

    def _show_detail(name):
        for w in detail.winfo_children(): w.destroy()
        meta = _get_meta(name); loaded = name in _loaded_addons
        sc = ctk.CTkScrollableFrame(detail, fg_color="transparent")
        sc.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        sc.columnconfigure(0, weight=1)
        hc = ctk.CTkFrame(sc, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        hc.pack(fill="x", pady=(0,8))
        hi = ctk.CTkFrame(hc, fg_color="transparent"); hi.pack(fill="x", padx=14, pady=12)
        tr = ctk.CTkFrame(hi, fg_color="transparent"); tr.pack(fill="x")
        ctk.CTkLabel(tr, text=meta.get("title",name), font=ctk.CTkFont(size=18,weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(tr, text="● Loaded" if loaded else "○ Not loaded",
                     font=ctk.CTkFont(size=11),
                     text_color=T["start"] if loaded else T["muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hi, text=f"v{meta.get('version','?')}  ·  by {meta.get('author','?')}",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(anchor="w", pady=(2,0))
        br = ctk.CTkFrame(hc, fg_color="transparent"); br.pack(fill="x", padx=14, pady=(0,10))
        ctk.CTkButton(br, text="↺ Reload", width=80, height=28,
                      font=ctk.CTkFont(size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                      command=lambda: (_load_addon(os.path.join(addon_dir,name+".py")),
                                       show_toast(f"{name} reloaded!",T["sync"]),
                                       _refresh_list(), _show_detail(name))
                      ).pack(side="left", padx=(0,6))
        ctk.CTkButton(br, text="🗑 Remove", width=80, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["stop"], text_color=T["stop"], hover_color=T["border"],
                      command=lambda: (os.remove(os.path.join(addon_dir,name+".py")),
                                       _loaded_addons.pop(name,None),
                                       show_toast(f"{name} removed.",T["stop"]),
                                       _refresh_list(), _show_empty())
                      ).pack(side="left")
        dc = ctk.CTkFrame(sc, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        dc.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(dc, text="About", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10,4))
        ctk.CTkFrame(dc, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        ctk.CTkLabel(dc, text=meta.get("description","No description."),
                     font=ctk.CTkFont(size=12), text_color=T["text"],
                     justify="left", wraplength=420).pack(anchor="w", padx=14, pady=(8,12))

    def _select(name):
        _sel[0] = name
        for n,b in _btns.items(): b.configure(fg_color=T["border"] if n==name else T["bg"])
        _show_detail(name)

    def _refresh_list():
        for w in list_scroll.winfo_children(): w.destroy(); _btns.clear()
        try: scripts = sorted([os.path.splitext(x)[0] for x in os.listdir(addon_dir) if x.endswith(".py")])
        except: scripts = []
        if not scripts:
            ctk.CTkLabel(list_scroll, text="No addons.\nClick + Install below.",
                         font=ctk.CTkFont(size=11), text_color=T["muted"], justify="center").pack(pady=30)
            return
        for name in scripts:
            loaded = name in _loaded_addons
            btn = ctk.CTkButton(list_scroll, text="", height=54, corner_radius=8,
                                fg_color=T["border"] if _sel[0]==name else T["bg"],
                                hover_color=T["border"], border_width=0,
                                command=lambda n=name: _select(n))
            btn.pack(fill="x", padx=6, pady=2); _btns[name] = btn
            inner = ctk.CTkFrame(btn, fg_color="transparent")
            inner.place(relx=0, rely=0, relwidth=1, relheight=1)
            inner.bind("<Button-1>", lambda e,n=name: _select(n))
            r1 = ctk.CTkFrame(inner, fg_color="transparent"); r1.pack(fill="x", padx=10, pady=(7,0))
            ctk.CTkLabel(r1, text="●" if loaded else "○", font=ctk.CTkFont(size=10),
                         text_color=T["start"] if loaded else T["muted"], width=14).pack(side="left")
            ctk.CTkLabel(r1, text=name.replace("_"," ").title(),
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=T["text"]).pack(side="left", padx=4)
            r2 = ctk.CTkFrame(inner, fg_color="transparent"); r2.pack(fill="x", padx=10, pady=(2,5))
            ctk.CTkLabel(r2, text="Loaded" if loaded else "Not loaded",
                         font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w")

    def _install():
        paths = _tk_fd.askopenfilenames(title="Select Addon (.py)", filetypes=[("Python","*.py"),("All","*.*")])
        if not paths: return
        for p in paths:
            dest = os.path.join(addon_dir, os.path.basename(p))
            try: shutil.copy2(p, dest); _load_addon(dest)
            except Exception as ex: show_toast(f"Failed: {ex}", T["stop"])
        show_toast(f"{len(paths)} addon(s) installed!", T["start"]); _refresh_list()

    ctk.CTkButton(lfooter, text="+ Install", height=30, font=ctk.CTkFont(size=11,weight="bold"),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_install).pack(side="left", padx=(8,4), pady=6)
    ctk.CTkButton(lfooter, text="Open Folder", height=30, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=lambda: _open_folder(addon_dir)).pack(side="left", padx=(0,8), pady=6)
    _refresh_list(); _show_empty()

# ══════════════════════════════════════════════════════════
# SPLASH + BOOT
# ══════════════════════════════════════════════════════════
_splash = ctk.CTkFrame(app, fg_color=T["bg"]); _splash.place(relx=0, rely=0, relwidth=1, relheight=1)
ctk.CTkLabel(_splash, text="MC CTRL", font=ctk.CTkFont(size=48, weight="bold"),
             text_color=T["start"]).place(relx=0.5, rely=0.36, anchor="center")
ctk.CTkLabel(_splash, text="Minecraft Server Launcher", font=ctk.CTkFont(size=12),
             text_color=T["muted"]).place(relx=0.5, rely=0.445, anchor="center")
_splash_status = ctk.CTkLabel(_splash, text="Initializing…", font=ctk.CTkFont(size=11),
                               text_color=T["sync"])
_splash_status.place(relx=0.5, rely=0.52, anchor="center")
_sbar = ctk.CTkProgressBar(_splash, width=260, height=4,
                            fg_color=T["border"], progress_color=T["start"])
_sbar.place(relx=0.5, rely=0.585, anchor="center"); _sbar.set(0); _sbar.start()

def _splash_msg(msg):
    try: _splash_status.configure(text=msg)
    except: pass

def _boot():
    _splash_msg("Loading settings…"); app.update_idletasks()
    _splash_msg("Building UI…");      app.update_idletasks()
    _sbar.stop(); build_ui()
    _splash_msg("Starting services…"); app.update_idletasks()
    _splash.destroy()
    if auto_upload: schedule_auto_upload()
    _splash_msg("Detecting network…"); _start_ip_detection()
    app.after(300, lambda: [log(l) for l in [
        "","  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗     ",
        "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║     ",
        "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║     ",
        "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║     ",
        "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗",
        "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
        f"  MC CTRL  ·  {datetime.now().strftime('%A %B %d %Y  %H:%M')}",""
    ]])
    app.after(500, lambda: _load_all_addons())

app.after(80, _boot)
app.mainloop()
