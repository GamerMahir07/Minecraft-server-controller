import time
import shutil
import tkinter as tk
import tkinter.filedialog as _tk_fd
import customtkinter as ctk
import subprocess
import threading
import json
import os
import re
import sys
import urllib.request
import urllib.error
import importlib.util
from datetime import datetime
try:
    import tkinterdnd2 as dnd
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

# ── Platform detection ────────────────────────────────────
IS_WINDOWS = sys.platform == "win32"
IS_LINUX   = sys.platform.startswith("linux")
IS_MAC     = sys.platform == "darwin"

if IS_WINDOWS:
    import ctypes
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0  # no-op on Linux/Mac

def _popen_flags():
    """Return creationflags for subprocess.Popen (Windows only)."""
    return CREATE_NO_WINDOW if IS_WINDOWS else 0

def _kill_java():
    """Kill all java processes running server.jar."""
    if IS_WINDOWS:
        return subprocess.run(
            "taskkill /F /IM java.exe", shell=True,
            capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW)
    else:
        return subprocess.run(
            "pkill -f 'server.jar'", shell=True,
            capture_output=True, text=True)

def _open_folder(path):
    """Open a folder in the system file manager."""
    try:
        if IS_WINDOWS:
            os.startfile(path)
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

def _set_window_icon(window, ico_path):
    try:
        if IS_WINDOWS:
            window.iconbitmap(ico_path)
        else:
            # On Linux/Mac use a .png if available
            png = ico_path.replace(".ico", ".png")
            if os.path.exists(png):
                img = tk.PhotoImage(file=png)
                window.iconphoto(True, img)
    except Exception:
        pass

def _set_taskbar_id():
    try:
        if IS_WINDOWS:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                'gamermahir07.mcserver.launcher.1')
    except Exception:
        pass

# Default paths differ by platform
if IS_WINDOWS:
    _DEFAULT_JAVA = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe"
    _DEFAULT_SRV  = r"C:\Users\DigitalComputer\Desktop\mc"
else:
    _DEFAULT_JAVA = "java"          # usually on PATH on Linux/Mac
    _DEFAULT_SRV  = os.path.expanduser("~/minecraft-server")

# ── playit.gg globals ─────────────────────────────────────
playit_proc      = None
playit_tunnel    = None
playit_log_lines = []
_playit_addr_re  = re.compile(
    r'((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg|joinmc\.link|plymc\.link|mc\.gg)(?::\d+)?)',
    re.IGNORECASE)
_playit_arrow_re = re.compile(
    r'([\w][\w\-.]+\.[a-z]{2,})\s*=>\s*[\d.]+:\d+', re.IGNORECASE)
_playit_claim_re = re.compile(
    r'(https?://[^\s]+(?:playit|claim|tunnel)[^\s]*)', re.IGNORECASE)

# ── App addon globals ──────────────────────────────────────
_loaded_addons   = {}   # name -> module

SRV_PATH  = _DEFAULT_SRV
JAVA_PATH = _DEFAULT_JAVA
REPO_URL  = "https://github.com/GamerMahir07/minecraft-server.git"

THEMES = {
    "Dark (Default)":            {"appearance":"dark", "bg":"#0d0d0d","card":"#1a1a1a","border":"#2a2a2a","text":"#e0e0e0","muted":"#555555","start":"#22c55e","stop":"#ef4444","sync":"#60a5fa","handoff":"#f59e0b"},
    "Light (Default)":           {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#e0e0e0","text":"#1a1a1a","muted":"#888888","start":"#16a34a","stop":"#dc2626","sync":"#2563eb","handoff":"#d97706"},
    "Midnight Blue Dark":        {"appearance":"dark", "bg":"#0a0f1e","card":"#111827","border":"#1e3a5f","text":"#e2e8f0","muted":"#4a6080","start":"#34d399","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Midnight Blue Light":       {"appearance":"light","bg":"#e8eeff","card":"#ffffff","border":"#7a9fd4","text":"#0a0f2e","muted":"#5570a0","start":"#059669","stop":"#dc2626","sync":"#4f46e5","handoff":"#d97706"},
    "Creeper Green Dark":        {"appearance":"dark", "bg":"#0a1a0a","card":"#0f2a0f","border":"#1a4a1a","text":"#c8f0c8","muted":"#3a6a3a","start":"#4ade80","stop":"#f87171","sync":"#86efac","handoff":"#fde047"},
    "Creeper Green Light":       {"appearance":"light","bg":"#f0fff0","card":"#ffffff","border":"#86efac","text":"#052e16","muted":"#3a7a3a","start":"#16a34a","stop":"#dc2626","sync":"#059669","handoff":"#ca8a04"},
    "Nether Red Dark":           {"appearance":"dark", "bg":"#000000","card":"#1a0000","border":"#6a0000","text":"#ff4444","muted":"#8b0000","start":"#ff6b6b","stop":"#ff0000","sync":"#ff8c8c","handoff":"#ffd700"},
    "Nether Red Light":          {"appearance":"light","bg":"#fff5f5","card":"#ffffff","border":"#fca5a5","text":"#3a0000","muted":"#b06060","start":"#b91c1c","stop":"#7f1d1d","sync":"#dc2626","handoff":"#c2410c"},
    "Ocean Dark":                {"appearance":"dark", "bg":"#01131e","card":"#021f30","border":"#0e4a6e","text":"#bae6fd","muted":"#2a6a8a","start":"#22d3ee","stop":"#f87171","sync":"#38bdf8","handoff":"#fbbf24"},
    "Ocean Light":               {"appearance":"light","bg":"#e0f7ff","card":"#ffffff","border":"#7dd3f0","text":"#003a52","muted":"#4a8fa8","start":"#0284c7","stop":"#e11d48","sync":"#0ea5e9","handoff":"#f59e0b"},
    "Obsidian Dark":             {"appearance":"dark", "bg":"#080808","card":"#101010","border":"#1e1e2e","text":"#cdd6f4","muted":"#45475a","start":"#a6e3a1","stop":"#f38ba8","sync":"#89b4fa","handoff":"#fab387"},
    "Obsidian Light":            {"appearance":"light","bg":"#f0f0f8","card":"#ffffff","border":"#c5c5e0","text":"#1e1e2e","muted":"#6e7090","start":"#40a02b","stop":"#d20f39","sync":"#1e66f5","handoff":"#e49320"},
    "Ender Night Dark":          {"appearance":"dark", "bg":"#000000","card":"#0d0010","border":"#3b0060","text":"#e8b4ff","muted":"#6a2a8a","start":"#bf7fff","stop":"#ff5f87","sync":"#d68fff","handoff":"#ffb347"},
    "Ender Night Light":         {"appearance":"light","bg":"#f8f0ff","card":"#ffffff","border":"#d4b0ff","text":"#200040","muted":"#7a40a0","start":"#7c3aed","stop":"#db2777","sync":"#6d28d9","handoff":"#c2410c"},
    "Dracula Dark":              {"appearance":"dark", "bg":"#282a36","card":"#313442","border":"#44475a","text":"#f8f8f2","muted":"#6272a4","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Nord Dark":                 {"appearance":"dark", "bg":"#2e3440","card":"#3b4252","border":"#434c5e","text":"#eceff4","muted":"#4c566a","start":"#a3be8c","stop":"#bf616a","sync":"#88c0d0","handoff":"#ebcb8b"},
    "Nord Light":                {"appearance":"light","bg":"#eceff4","card":"#ffffff","border":"#d8dee9","text":"#2e3440","muted":"#7a8898","start":"#4c9a2a","stop":"#bf616a","sync":"#5e81ac","handoff":"#d08770"},
    "Gruvbox Dark":              {"appearance":"dark", "bg":"#282828","card":"#3c3836","border":"#504945","text":"#ebdbb2","muted":"#7c6f64","start":"#b8bb26","stop":"#fb4934","sync":"#83a598","handoff":"#fabd2f"},
    "Gruvbox Light":             {"appearance":"light","bg":"#fbf1c7","card":"#f9f5d7","border":"#d5c4a1","text":"#3c3836","muted":"#928374","start":"#79740e","stop":"#9d0006","sync":"#076678","handoff":"#b57614"},
    "Solarized Dark":            {"appearance":"dark", "bg":"#002b36","card":"#073642","border":"#586e75","text":"#fdf6e3","muted":"#839496","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Solarized Light":           {"appearance":"light","bg":"#fdf6e3","card":"#eee8d5","border":"#93a1a1","text":"#073642","muted":"#657b83","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Cyberpunk Dark":            {"appearance":"dark", "bg":"#0a0014","card":"#110022","border":"#ff00ff","text":"#00ffff","muted":"#8800aa","start":"#00ffff","stop":"#ff0088","sync":"#ff00ff","handoff":"#ffff00"},
    "Matrix Dark":               {"appearance":"dark", "bg":"#000000","card":"#001400","border":"#004400","text":"#00ff41","muted":"#006600","start":"#00ff41","stop":"#ff0000","sync":"#00cc33","handoff":"#ffff00"},
    "Slate Dark":                {"appearance":"dark", "bg":"#0f172a","card":"#1e293b","border":"#334155","text":"#f1f5f9","muted":"#64748b","start":"#22d3ee","stop":"#f43f5e","sync":"#818cf8","handoff":"#fb923c"},
    "Slate Light":               {"appearance":"light","bg":"#f1f5f9","card":"#ffffff","border":"#cbd5e1","text":"#0f172a","muted":"#64748b","start":"#0891b2","stop":"#e11d48","sync":"#4f46e5","handoff":"#ea580c"},
    "Amber Dark":                {"appearance":"dark", "bg":"#1a1000","card":"#2a1a00","border":"#7a5500","text":"#ffe88a","muted":"#7a6020","start":"#fbbf24","stop":"#ef4444","sync":"#f59e0b","handoff":"#84cc16"},
    "Rose Gold Dark":            {"appearance":"dark", "bg":"#1a0008","card":"#2a0010","border":"#7a2040","text":"#ffd6e0","muted":"#8a4060","start":"#fb7185","stop":"#f43f5e","sync":"#f472b6","handoff":"#fb923c"},
    "Forest Dark":               {"appearance":"dark", "bg":"#0d1a0d","card":"#142414","border":"#254025","text":"#d4edda","muted":"#4a7a4a","start":"#86efac","stop":"#fca5a5","sync":"#6ee7b7","handoff":"#fde68a"},
    "Carbon Dark":               {"appearance":"dark", "bg":"#1a1a2e","card":"#16213e","border":"#0f3460","text":"#e0e0e0","muted":"#4a4a6a","start":"#00c896","stop":"#e94560","sync":"#4d9fff","handoff":"#f5a623"},
    "Lavender Dark":             {"appearance":"dark", "bg":"#0f0820","card":"#1a1035","border":"#3d2a7a","text":"#e8dfff","muted":"#6050a0","start":"#a78bfa","stop":"#f472b6","sync":"#818cf8","handoff":"#fbbf24"},
    "Mocha Dark":                {"appearance":"dark", "bg":"#1c1410","card":"#2a1f18","border":"#4a3428","text":"#f0dece","muted":"#7a5a48","start":"#c8a86e","stop":"#e05050","sync":"#90b8d0","handoff":"#e8c060"},
    "Void Dark":                 {"appearance":"dark", "bg":"#000000","card":"#0a0a0a","border":"#1a1a1a","text":"#aaaaaa","muted":"#333333","start":"#444444","stop":"#666666","sync":"#555555","handoff":"#777777"},
    "CB: Blue & Orange Dark":    {"appearance":"dark", "bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#ffffff","muted":"#888888","start":"#56b4e9","stop":"#d55e00","sync":"#0072b2","handoff":"#e69f00"},
    "CB: High Contrast Dark":    {"appearance":"dark", "bg":"#000000","card":"#1a1a1a","border":"#ffffff","text":"#ffffff","muted":"#aaaaaa","start":"#ffff00","stop":"#ff6600","sync":"#00ffff","handoff":"#ff99ff"},
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

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
backup_upload_on   = settings.get("backup_upload_on", True)
auto_upload_mins   = settings.get("auto_upload_mins", 10)
upload_on_stop     = settings.get("upload_on_stop", True)
ram_display_mode   = settings.get("ram_display_mode", "percent")

if current_theme_name not in THEMES:
    current_theme_name = "Dark (Default)"
T = THEMES[current_theme_name]

ctk.set_appearance_mode(T["appearance"])
ctk.set_default_color_theme("dark-blue")

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
_players_refresh_id = None

perf = {
    "ram_used":"--","ram_pct":"--","ram_srv":"--",
    "cpu_sys":"--","cpu_srv":"--",
    "tps":"--","latency":"--","players":"0",
    "uptime":"--","threads":"--",
}
server_start_time = None

CHAT_RE       = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE       = re.compile(r'^(\w+) joined the game', re.IGNORECASE)
LEAVE_RE      = re.compile(r'^(\w+) (?:lost connection|left the game)', re.IGNORECASE)
DEATH_RE      = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.IGNORECASE)
STRIP_RE      = re.compile(r'^\[[\d:]+\]\s*\[.*?(?:INFO|WARN|ERROR).*?\]:\s*', re.IGNORECASE)
DONE_RE       = re.compile(r'Done \([\d.]+s\)!', re.IGNORECASE)
SPARK_TPS     = re.compile(r'TPS from last 1m[^:]*:\s*([\d.]+)', re.IGNORECASE)
TPS_RE2       = re.compile(r'Current TPS[:\s]+([\d.]+)', re.IGNORECASE)
PLAYER_RE     = re.compile(r'There are (\d+) of a max of \d+ players', re.IGNORECASE)
LIST_NAMES_RE = re.compile(r'There are \d+[^:]*:\s*(.+)', re.IGNORECASE)
LATENCY_RE    = re.compile(r'(\w+)\s+has\s+(?:a\s+ping\s+of\s+)?(\d+)\s*ms', re.IGNORECASE)
LATENCY_RE2   = re.compile(r'(\w+)\s*\((\d+)\s*ms\)', re.IGNORECASE)
LATENCY_RE3   = re.compile(r'ping\[(\w+)\]\s*=\s*(\d+)', re.IGNORECASE)

def parse_server_line(raw):
    global player_count, server_ready
    clean = STRIP_RE.sub('', raw).strip()
    if not clean:
        return None
    if "Done (" in clean:
        if DONE_RE.search(clean):
            server_ready = True
            app.after(0, show_toast, "Server is ready!", T["start"])
            return ('log', clean)
    if "TPS" in clean or "tps" in clean:
        tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
        if tps:
            perf["tps"] = tps.group(1)
            return None
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
    if '<' in clean:
        chat = CHAT_RE.search(clean)
        if chat:
            return ('chat', f"[CHAT] {chat.group(1)}: {chat.group(2)}")
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
    if any(w in clean for w in ("was slain","died","fell","drowned","burned","blew up","suffocated","starved","withered")):
        if DEATH_RE.search(clean):
            return ('event', f"[DEATH] {clean}")
    return ('log', clean)

threading.Thread(target=load_settings, daemon=True).start()

app = ctk.CTk()
app.title("MC CTRL")
app.geometry("1020x720")
app.resizable(True, True)
app.configure(fg_color=T["bg"])

_set_taskbar_id()
try:
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    _set_window_icon(app, ico)
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
                           text=True, creationflags=_popen_flags())
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

# ── Toast ─────────────────────────────────────────────────
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
        schedule_auto_upload(); return
    s = load_settings()
    path = s.get("srv_path", SRV_PATH)
    repo = s.get("repo_url", REPO_URL)
    def _work():
        app.after(0, log, "-- Auto-upload -------------------")
        try:
            subprocess.run(f'git remote set-url origin {repo}', shell=True, cwd=path,
                           capture_output=True, creationflags=_popen_flags())
            subprocess.run('git add .', shell=True, cwd=path,
                           capture_output=True, creationflags=_popen_flags())
            r = subprocess.run(
                f'git commit -m "Auto-upload {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                shell=True, cwd=path, capture_output=True, text=True,
                creationflags=_popen_flags())
            if "nothing to commit" in r.stdout or r.returncode != 0:
                app.after(0, log, "  Nothing new to commit.")
            else:
                push = subprocess.run('git push origin main', shell=True, cwd=path,
                                      capture_output=True, text=True,
                                      creationflags=_popen_flags())
                if push.returncode == 0:
                    app.after(0, log, "  Auto-upload complete.")
                    app.after(0, show_toast, "Auto-upload complete!", T["sync"])
                else:
                    app.after(0, log, f"  Push failed: {push.stderr.strip()}")
        except Exception as ex:
            app.after(0, log, f"  Error: {ex}")
        schedule_auto_upload()
    threading.Thread(target=_work, daemon=True).start()

# ── Perf ──────────────────────────────────────────────────
perf_labels = {}

def find_java_proc():
    import psutil
    if server_pid:
        try:
            return psutil.Process(server_pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'java' in p.info['name'].lower():
                if 'server.jar' in ' '.join(p.info['cmdline'] or []):
                    return p
        except: pass
    return None

def perf_loop():
    import psutil
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

# ── Theme ─────────────────────────────────────────────────
def apply_theme(name):
    global T, current_theme_name
    current_theme_name = name; T = THEMES[name]
    update_setting("theme", name)
    ctk.set_appearance_mode(T["appearance"])
    app.configure(fg_color=T["bg"])
    _recolor_all(app)

def _recolor_all(widget):
    try:
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
            try: widget.configure(text_color=T["text"])
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

# ── First-launch dialog ───────────────────────────────────
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
    ctk.CTkLabel(b1, text="Pick a colour scheme. You can change it any time in Settings.",
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
        "Toggle ON to back up your world to GitHub.\n"
        "Toggle OFF if you don't want any files pushed online."
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

# ── Scroll frame ──────────────────────────────────────────
def make_scroll_frame(parent, **kwargs):
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

    top = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0)
    top.pack(fill="x")
    ctk.CTkLabel(top, text="MC CTRL",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=16, pady=10)

    # Platform badge
    plat_txt = "🐧 Linux" if IS_LINUX else ("🍎 Mac" if IS_MAC else "🪟 Windows")
    ctk.CTkLabel(top, text=plat_txt, font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(0, 8))

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

        hdr = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Theme Search",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=14, pady=10)

        mode_filter = tk.StringVar(value="any")
        text_filter = tk.StringVar(value="")
        _rebuild_timer = [None]

        mr = ctk.CTkFrame(hdr, fg_color="transparent"); mr.pack(side="right", padx=12, pady=8)
        for mv, ml in [("any","Any"),("dark","Dark"),("light","Light")]:
            ctk.CTkRadioButton(mr, text=ml, variable=mode_filter, value=mv,
                               font=ctk.CTkFont(size=11), text_color=T["text"],
                               fg_color=T["sync"], border_color=T["border"],
                               command=lambda: win.after(0, _rebuild_grid)
                               ).pack(side="left", padx=(0,8))

        sr = ctk.CTkFrame(win, fg_color=T["bg"]); sr.pack(fill="x", padx=14, pady=(8,4))
        ctk.CTkLabel(sr, text="🔍", font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")
        se = ctk.CTkEntry(sr, textvariable=text_filter, height=28,
                          font=ctk.CTkFont(size=12), fg_color=T["card"],
                          border_color=T["border"], text_color=T["text"],
                          placeholder_text="type to filter…")
        se.pack(side="left", fill="x", expand=True, padx=6)
        result_lbl = ctk.CTkLabel(sr, text="", font=ctk.CTkFont(size=10), text_color=T["muted"])
        result_lbl.pack(side="right")

        def _debounced_rebuild(*_):
            if _rebuild_timer[0]: win.after_cancel(_rebuild_timer[0])
            _rebuild_timer[0] = win.after(120, _rebuild_grid)
        text_filter.trace_add("write", _debounced_rebuild)

        ctk.CTkFrame(win, height=1, fg_color=T["border"]).pack(fill="x", padx=14)

        grid_outer = ctk.CTkScrollableFrame(win, fg_color="transparent")
        grid_outer.pack(fill="both", expand=True, padx=10, pady=6)
        _card_widgets = []

        def _theme_matches(name, tdata):
            m = mode_filter.get()
            if m != "any" and tdata["appearance"] != m: return False
            q = text_filter.get().strip().lower()
            if q and q not in name.lower(): return False
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
            result_lbl.configure(text=f"{len(matching)}/{len(THEMES)}")
            COLS = 3
            for i, (name, tdata) in enumerate(matching):
                col = i % COLS; row = i // COLS
                card = ctk.CTkFrame(grid_outer, fg_color=tdata["card"],
                                    border_color=tdata["border"],
                                    border_width=2, corner_radius=10)
                card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")
                grid_outer.columnconfigure(col, weight=1)
                _card_widgets.append(card)
                sw_row = ctk.CTkFrame(card, fg_color="transparent"); sw_row.pack(fill="x", padx=8, pady=(8,2))
                for role in ["bg","card","border","start","stop","sync"]:
                    s = ctk.CTkFrame(sw_row, width=16, height=16, corner_radius=3,
                                     fg_color=tdata.get(role,"#888888"))
                    s.pack(side="left", padx=2); s.pack_propagate(False)
                badge_col = "#334155" if tdata["appearance"]=="dark" else "#e2e8f0"
                badge_tc  = "#e2e8f0" if tdata["appearance"]=="dark" else "#334155"
                ctk.CTkLabel(sw_row, text="🌙" if tdata["appearance"]=="dark" else "☀",
                             font=ctk.CTkFont(size=11), fg_color=badge_col,
                             text_color=badge_tc, corner_radius=4,
                             width=22, height=18).pack(side="right", padx=(0,2))
                ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=tdata["text"], wraplength=180, justify="left"
                             ).pack(anchor="w", padx=10, pady=(2,0))
                ctk.CTkFrame(card, height=8, fg_color=tdata["bg"], corner_radius=0
                             ).pack(fill="x", pady=(3,0))
                is_current = (name == current_theme_name)
                ctk.CTkButton(card,
                              text="✓ Active" if is_current else "Apply",
                              height=26, corner_radius=6, font=ctk.CTkFont(size=11),
                              fg_color=tdata["start"] if is_current else tdata["sync"],
                              hover_color=tdata["start"], text_color="#000000",
                              command=lambda n=name: _pick(n)
                              ).pack(fill="x", padx=8, pady=(4,8))

        _rebuild_grid()

    theme_btn = ctk.CTkButton(top, text=f"🎨  {current_theme_name}", width=180, height=28,
                               font=ctk.CTkFont(size=11), corner_radius=6,
                               fg_color=T["bg"], border_width=1, border_color=T["border"],
                               text_color=T["text"], hover_color=T["border"],
                               command=open_theme_picker)
    theme_btn.pack(side="left", padx=(0,6), pady=8)

    _orig_apply = apply_theme
    def _apply_and_sync(name):
        _orig_apply(name)
        try: theme_btn.configure(text=f"🎨  {name}")
        except: pass
    globals()["apply_theme"] = _apply_and_sync

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
    addons_frame     = ctk.CTkFrame(tab_content, fg_color="transparent")
    multictrl_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")

    all_frames = {
        "dashboard":  dashboard_frame,
        "network":    network_frame,
        "serverinfo": serverinfo_frame,
        "playit":     playit_frame,
        "addons":     addons_frame,
        "multictrl":  multictrl_frame,
    }
    _built_tabs = set()
    tab_btns = {}

    def show_tab(name):
        for f in all_frames.values():
            f.pack_forget()
        for n, b in tab_btns.items():
            b.configure(fg_color="transparent", text_color=T["muted"])
        if name not in _built_tabs:
            _built_tabs.add(name)
            builders = {
                "dashboard":  lambda: build_dashboard(dashboard_frame, is_fs),
                "network":    lambda: build_network_tab(network_frame),
                "serverinfo": lambda: build_server_info_tab(serverinfo_frame),
                "playit":     lambda: build_playit_tab(playit_frame),
                "addons":     lambda: build_addons_tab(addons_frame),
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
        ("addons",     "🧩 Addons"),
        ("multictrl",  "⊞ Multi CTRL"),
    ]
    for key, label in TAB_DEFS:
        is_special = key in ("multictrl", "addons")
        b = ctk.CTkButton(tab_bar, text=label,
                          width=120, height=30,
                          font=ctk.CTkFont(size=12, weight="bold" if is_special else "normal"),
                          corner_radius=6,
                          fg_color=T["handoff"] if key == "multictrl" else "transparent",
                          text_color="#000" if key == "multictrl" else T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=(8 if key=="dashboard" else 2, 2), pady=6)
        tab_btns[key] = b

    show_tab("dashboard")

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
    import socket
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

    hf = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                      border_width=1, corner_radius=10)
    hf.pack(fill="x", padx=20, pady=(12,0))
    hi = ctk.CTkFrame(hf, fg_color="transparent"); hi.pack(fill="x", padx=16, pady=14)
    ctk.CTkLabel(hi, text="SERVER CONNECTION INFO",
                 font=ctk.CTkFont(size=14, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkLabel(hi, text="Share these IPs with players",
                 font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left", padx=12)

    def copy_to_clip(val):
        app.clipboard_clear(); app.clipboard_append(val)
        show_toast(f"Copied: {val}", T["sync"])

    grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    grid_frame.pack(fill="x", padx=20, pady=10)
    grid_frame.columnconfigure((0,1,2), weight=1)

    def get_local(): return f"{local_ip}:{port_var.get()}"
    def get_localhost(): return f"localhost:{port_var.get()}"

    # Port card
    port_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["border"],
                          border_width=2, corner_radius=12)
    port_c.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(port_c, text="PORT", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["muted"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkFrame(port_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    ctk.CTkEntry(port_c, textvariable=port_var, height=32,
                 font=ctk.CTkFont(size=13, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]
                 ).pack(fill="x", padx=14, pady=(0,12))

    # Local card
    local_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["start"],
                           border_width=2, corner_radius=12)
    local_c.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(local_c, text="LOCAL (LAN)", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["start"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkLabel(local_c, text="For players on your WiFi", font=ctk.CTkFont(size=9),
                 text_color=T["muted"]).pack(anchor="w", padx=14)
    ctk.CTkFrame(local_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    local_lbl = ctk.CTkLabel(local_c, text=get_local(),
                              font=ctk.CTkFont(size=12, weight="bold", family="Consolas"),
                              text_color=T["text"])
    local_lbl.pack(padx=14, pady=(2,6))
    def _upd_lan(*_): local_lbl.configure(text=get_local())
    port_var.trace_add("write", _upd_lan)
    ctk.CTkButton(local_c, text="Copy", font=ctk.CTkFont(size=11), height=28,
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=lambda: copy_to_clip(get_local())
                  ).pack(padx=14, pady=(0,12), fill="x")

    # External card
    ext_c = ctk.CTkFrame(grid_frame, fg_color=T["card"], border_color=T["sync"],
                         border_width=2, corner_radius=12)
    ext_c.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(ext_c, text="EXTERNAL", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["sync"]).pack(anchor="w", padx=14, pady=(12,2))
    ctk.CTkLabel(ext_c, text="For players over the internet", font=ctk.CTkFont(size=9),
                 text_color=T["muted"]).pack(anchor="w", padx=14)
    ctk.CTkFrame(ext_c, height=1, fg_color=T["border"]).pack(fill="x", padx=10, pady=6)
    ctk.CTkLabel(ext_c, textvariable=ext_ip_var,
                 font=ctk.CTkFont(size=12, weight="bold", family="Consolas"),
                 text_color=T["sync"]).pack(padx=14, pady=(2,6))
    ctk.CTkButton(ext_c, text="Copy", font=ctk.CTkFont(size=11), height=28,
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=lambda: copy_to_clip(ext_ip_var.get())
                  ).pack(padx=14, pady=(0,12), fill="x")

    def fetch_ext():
        try:
            ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
            saved = load_settings().get("custom_ip","")
            app.after(0, lambda: ext_ip_var.set(
                f"{saved}:{port_var.get()}" if saved else f"{ip}:{port_var.get()}"))
        except: app.after(0, lambda: ext_ip_var.set("unavailable"))
    threading.Thread(target=fetch_ext, daemon=True).start()

    guide = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
    guide.pack(fill="x", padx=20, pady=(0,12))
    ctk.CTkLabel(guide, text="CONNECTION GUIDE",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10,6))
    ctk.CTkFrame(guide, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    ctk.CTkLabel(guide, text=(
        "1. Same house / WiFi  →  share LOCAL address.\n"
        "2. Friends over the internet  →  share EXTERNAL. Router must port-forward 25565 TCP.\n"
        "3. Using playit.gg  →  use the tunnel address from the playit.gg tab.\n"
        "4. Testing locally  →  use localhost:25565."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       justify="left", wraplength=900).pack(anchor="w", padx=14, pady=(8,12))

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

    # Online Players
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
    ctk.CTkButton(ph, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=lambda: (send_server_cmd("list"), refresh_players_now())
                  ).pack(side="right")

    # Plugins
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

    # Server Properties
    spb, sph = section_card("Server Properties")

    ALL_PROPS = [
        ("gamemode","Game Mode","survival"),
        ("difficulty","Difficulty","easy"),
        ("max-players","Max Players","20"),
        ("view-distance","View Distance","10"),
        ("simulation-distance","Simulation Distance","10"),
        ("server-port","Port","25565"),
        ("online-mode","Online Mode","true"),
        ("pvp","PvP","true"),
        ("spawn-monsters","Spawn Monsters","true"),
        ("spawn-animals","Spawn Animals","true"),
        ("allow-flight","Allow Flight","false"),
        ("white-list","Whitelist","false"),
        ("level-name","World Name","world"),
        ("motd","MOTD","A Minecraft Server"),
        ("spawn-protection","Spawn Protection","16"),
        ("level-seed","World Seed",""),
        ("allow-nether","Allow Nether","true"),
        ("enable-command-block","Command Blocks","false"),
    ]

    props_vars = {}

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
            updated = set(); new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k, _, _ = stripped.partition("="); k = k.strip()
                    if k in props_vars:
                        new_lines.append(f"{k}={props_vars[k].get()}\n"); updated.add(k)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
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
                                 border_width=1, corner_radius=8, height=260)
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
        ctk.CTkEntry(cell, textvariable=var, height=28,
                     font=ctk.CTkFont(size=11, family="Consolas"),
                     fg_color=T["card"], border_color=T["border"],
                     text_color=T["text"]).pack(fill="x")

    ctk.CTkButton(spb, text="Save server.properties", height=34, corner_radius=8,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=save_props).pack(pady=(8,0), fill="x")
    ctk.CTkLabel(spb, text="Restart server for changes to take effect.",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(4,0))

    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

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
        "playit.gg is a free tunnel that gives your server a public address without port forwarding.\n"
        "Friends connect via a .ply.gg address. Free plan: up to 3 tunnels."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=840, justify="left").pack(anchor="w")

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
        exts = [("Executables","*.exe"),("All","*.*")] if IS_WINDOWS else [("All","*")]
        p = _tk_fd.askopenfilename(title="Select playit executable", filetypes=exts)
        if p: playit_path_var.set(p)

    def _dl_playit():
        if IS_WINDOWS:
            fname = "playit-windows.exe"
            dest_name = "playit.exe"
        elif IS_MAC:
            fname = "playit-darwin"
            dest_name = "playit"
        else:
            fname = "playit-linux-amd64"
            dest_name = "playit"
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), dest_name)
        _set_pt_st(f"Downloading {dest_name}...", T["sync"])
        def _do():
            url = f"https://github.com/playit-cloud/playit-agent/releases/latest/download/{fname}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"MC-CTRL/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    with open(dest,"wb") as f2: f2.write(r.read())
                if not IS_WINDOWS:
                    os.chmod(dest, 0o755)
                playit_path_var.set(dest)
                update_setting("playit_path", dest)
                app.after(0, _set_pt_st, "Downloaded!", T["start"])
                app.after(0, show_toast, f"{dest_name} downloaded!", T["start"])
            except Exception as ex:
                app.after(0, _set_pt_st, f"Failed: {ex}", T["stop"])
        threading.Thread(target=_do, daemon=True).start()

    pr = ctk.CTkFrame(sb, fg_color="transparent"); pr.pack(fill="x", pady=(0,6))
    exe_label = "playit.exe" if IS_WINDOWS else "playit binary"
    ctk.CTkLabel(pr, text=exe_label, font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=100, anchor="w").pack(side="left")
    ctk.CTkEntry(pr, textvariable=playit_path_var, height=30,
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="path/to/playit"
                 ).pack(side="left", fill="x", expand=True, padx=(0,8))
    ctk.CTkButton(pr, text="Browse", width=70, height=30, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_browse_pt).pack(side="left", padx=(0,6))
    ctk.CTkButton(pr, text="Auto-Download", height=30, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_dl_playit).pack(side="left")
    pt_status_lbl.pack(anchor="w", pady=(4,0))

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

    _PT_LOG_QUEUE = []; _PT_LOG_MAXLINES = 300; _PT_FLUSH_MS = 120
    _pt_flush_pending = [False]
    _ansi_re  = re.compile(r'\x1b(?:\[[0-9;]*[mABCDEFGHJKSTfhilmnprsuu]|\][^\x07]*\x07|[()][AB012]|[=>])')
    _coord_re = re.compile(r'\x1b\[\d+;\d+H')

    def _flush_ptlog():
        _pt_flush_pending[0] = False
        if not _PT_LOG_QUEUE: return
        batch = _PT_LOG_QUEUE[:]
        _PT_LOG_QUEUE.clear()
        try:
            pt_log.configure(state="normal")
            pt_log.insert("end", "\n".join(batch) + "\n")
            total = int(pt_log.index("end-1c").split(".")[0])
            if total > _PT_LOG_MAXLINES:
                pt_log.delete("1.0", f"{total - _PT_LOG_MAXLINES}.0")
            pt_log.configure(state="disabled")
            pt_log.see("end")
        except Exception: pass

    def _append_ptlog(line):
        _PT_LOG_QUEUE.append(line)
        if not _pt_flush_pending[0]:
            _pt_flush_pending[0] = True
            app.after(_PT_FLUSH_MS, _flush_ptlog)

    def _handle_line(raw_bytes, prefix=""):
        try: line = raw_bytes.decode("utf-8", errors="replace").rstrip()
        except Exception: line = repr(raw_bytes)
        clean = _ansi_re.sub("", _coord_re.sub(" ", line)).strip()
        if not clean: return
        tagged = f"{prefix}{clean}" if prefix else clean
        playit_log_lines.append(tagged)
        if len(playit_log_lines) > 300: del playit_log_lines[:150]
        m = _playit_addr_re.search(clean) or _playit_arrow_re.search(clean)
        if m: app.after(0, _set_addr, m.group(1))
        cm = _playit_claim_re.search(clean)
        if cm:
            url = cm.group(1)
            _append_ptlog(f"[MC CTRL] >>> CLAIM URL: {url} <<<")
            app.after(0, show_toast, "Open claim URL in browser!", T["handoff"], 8000)
        _append_ptlog(tagged)

    def _read_stream_bytes(stream, prefix=""):
        try:
            for raw in iter(stream.readline, b""):
                if not raw: break
                _handle_line(raw, prefix)
        except Exception: pass

    def _read_pt(proc):
        _read_stream_bytes(proc.stdout, "")
        code = proc.wait()
        app.after(0, _append_ptlog, f"[MC CTRL] Agent exited with code {code}.")
        app.after(0, _set_tst, "● Stopped", T["stop"])

    def _read_stderr_pt(proc):
        _read_stream_bytes(proc.stderr, "[stderr] ")

    def _start_pt():
        global playit_proc
        exe = playit_path_var.get().strip()
        if not exe or not os.path.exists(exe):
            show_toast("Set playit path first!", T["stop"]); return
        if playit_proc and playit_proc.poll() is None:
            show_toast("Already running.", T["muted"]); return

        saved_key = load_settings().get("playit_secret_key", "").strip()
        cmd = [exe]
        env = os.environ.copy()

        if saved_key:
            try:
                if IS_WINDOWS:
                    appdata = os.environ.get("APPDATA", "")
                    pt_dir = os.path.join(appdata, "playit") if appdata else os.path.dirname(exe)
                else:
                    pt_dir = os.path.join(os.path.expanduser("~"), ".config", "playit")
                os.makedirs(pt_dir, exist_ok=True)
                toml_path = os.path.join(pt_dir, "playit.toml")
                new_toml = [f'secret_key = "{saved_key}"\n']
                if os.path.exists(toml_path):
                    with open(toml_path, encoding="utf-8", errors="ignore") as tf:
                        existing = tf.readlines()
                    new_toml = []
                    found_key = False
                    for tl in existing:
                        if tl.strip().startswith("secret_key"):
                            new_toml.append(f'secret_key = "{saved_key}"\n'); found_key = True
                        else:
                            new_toml.append(tl)
                    if not found_key:
                        new_toml.insert(0, f'secret_key = "{saved_key}"\n')
                with open(toml_path, "w", encoding="utf-8") as tf:
                    tf.writelines(new_toml)
                app.after(0, _append_ptlog, f"[MC CTRL] Secret key written to: {toml_path}")
            except Exception as ex:
                app.after(0, _append_ptlog, f"[MC CTRL] Key write failed: {ex}")

        try:
            if IS_WINDOWS:
                _si = subprocess.STARTUPINFO()
                _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                _si.wShowWindow = 0
                extra = {"startupinfo": _si, "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW}
            else:
                extra = {}

            playit_proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL, text=False, bufsize=0, env=env, **extra)
            _set_tst("● Running", T["start"])
            log("-- playit.gg started --")
            app.after(0, _append_ptlog, "[MC CTRL] Agent started. Waiting for tunnel address...")
            threading.Thread(target=_read_pt,        args=(playit_proc,), daemon=True).start()
            threading.Thread(target=_read_stderr_pt, args=(playit_proc,), daemon=True).start()
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
        if addr: app.clipboard_clear(); app.clipboard_append(addr); show_toast(f"Copied: {addr}", T["sync"])
        else: show_toast("No address yet.", T["muted"])

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
                             wrap="word", state="disabled", height=200,
                             fg_color=T["bg"], text_color=T["text"]); pt_log.pack(fill="x")
    if playit_log_lines:
        pt_log.configure(state="normal")
        for line in playit_log_lines: pt_log.insert("end", line + "\n")
        pt_log.configure(state="disabled"); pt_log.see("end")
    if playit_tunnel: _set_addr(playit_tunnel)

    def _clear_ptlog():
        global playit_log_lines
        playit_log_lines.clear()
        pt_log.configure(state="normal"); pt_log.delete("1.0","end")
        pt_log.configure(state="disabled")

    ctk.CTkButton(lh,text="Clear",width=58,height=22,font=ctk.CTkFont(size=10),
                  fg_color="transparent",border_width=1,border_color=T["border"],
                  text_color=T["muted"],hover_color=T["border"],
                  command=_clear_ptlog).pack(side="right")
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

# ═══════════════════════════════════════════════════════════
# ── 🧩 ADDONS TAB — Split pane design ────────────────────
# Left pane: list of installed addons
# Right pane: detail view (description, preview, settings)
# ═══════════════════════════════════════════════════════════
def build_addons_tab(parent):
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)
    _ensure_addon_readme(addon_dir)

    # ── Root split container ──────────────────────────────
    root_pane = ctk.CTkFrame(parent, fg_color="transparent")
    root_pane.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    root_pane.rowconfigure(0, weight=1)
    root_pane.columnconfigure(0, weight=0)   # left list — fixed width
    root_pane.columnconfigure(1, weight=1)   # right detail — expands

    # ── LEFT PANE ─────────────────────────────────────────
    left_pane = ctk.CTkFrame(root_pane, fg_color=T["card"],
                              border_color=T["border"], border_width=1,
                              corner_radius=0, width=280)
    left_pane.grid(row=0, column=0, sticky="nsew")
    left_pane.grid_propagate(False)
    left_pane.rowconfigure(1, weight=1)
    left_pane.columnconfigure(0, weight=1)

    # Left header
    lhdr = ctk.CTkFrame(left_pane, fg_color=T["bg"], corner_radius=0)
    lhdr.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(lhdr, text="🧩  Addons",
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=14, pady=10)

    # Addon list scroll area
    list_scroll = ctk.CTkScrollableFrame(left_pane, fg_color="transparent")
    list_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
    list_scroll.columnconfigure(0, weight=1)

    # Left footer — install buttons
    lfooter = ctk.CTkFrame(left_pane, fg_color=T["bg"], corner_radius=0)
    lfooter.grid(row=2, column=0, sticky="ew")
    ctk.CTkFrame(lfooter, height=1, fg_color=T["border"]).pack(fill="x")

    # ── RIGHT PANE ────────────────────────────────────────
    right_pane = ctk.CTkFrame(root_pane, fg_color="transparent")
    right_pane.grid(row=0, column=1, sticky="nsew")
    right_pane.rowconfigure(0, weight=1)
    right_pane.columnconfigure(0, weight=1)

    # Right content area — rebuilt when an addon is selected
    right_content = ctk.CTkFrame(right_pane, fg_color="transparent")
    right_content.grid(row=0, column=0, sticky="nsew")
    right_content.rowconfigure(0, weight=1)
    right_content.columnconfigure(0, weight=1)

    _selected_addon = [None]   # [name or None]
    _list_btns      = {}       # name -> button widget

    # ── Addon metadata registry ───────────────────────────
    # Well-known addon metadata — for bundled/example addons
    # User addons without metadata show a generic info panel.
    ADDON_META = {
        "create_theme": {
            "title":       "Theme Creator",
            "version":     "1.0",
            "author":      "MC CTRL",
            "description": (
                "Create and save custom colour themes for MC CTRL.\n\n"
                "Opens a theme editor where you can pick colours for every\n"
                "UI role (background, card, text, buttons, etc.) and save\n"
                "your theme with a custom name.\n\n"
                "Saved themes appear instantly in the theme picker."
            ),
            "preview_colors": ["#0d0d0d","#1a1a1a","#22c55e","#ef4444","#60a5fa","#f59e0b"],
            "settings": [
                ("Default theme name", "theme_creator_default", "My Theme", "entry"),
                ("Auto-apply on save", "theme_creator_autoapply", True, "switch"),
            ],
        },
        "auto_announce": {
            "title":       "Auto Announcer",
            "version":     "1.0",
            "author":      "MC CTRL",
            "description": (
                "Broadcasts configurable messages to the server at a set interval.\n\n"
                "Useful for reminding players of rules, events, or Discord links\n"
                "while the server is running."
            ),
            "preview_colors": ["#0a1a0a","#1a4a1a","#4ade80","#fde047","#86efac","#f87171"],
            "settings": [
                ("Interval (minutes)", "auto_announce_interval", "15", "entry"),
                ("Message 1", "auto_announce_msg1", "Welcome to the server!", "entry"),
                ("Message 2", "auto_announce_msg2", "Join our Discord!", "entry"),
                ("Enabled", "auto_announce_enabled", True, "switch"),
            ],
        },
        "backup_manager": {
            "title":       "Backup Manager",
            "version":     "1.0",
            "author":      "MC CTRL",
            "description": (
                "Automatically creates timestamped ZIP backups of your world folders.\n\n"
                "Backups are saved to a local folder of your choice and optionally\n"
                "pruned to keep only the N most recent copies."
            ),
            "preview_colors": ["#1a1000","#2a1a00","#fbbf24","#ef4444","#f59e0b","#84cc16"],
            "settings": [
                ("Backup folder", "backup_dest", "~/mc-backups", "entry"),
                ("Max backups to keep", "backup_max_count", "10", "entry"),
                ("Interval (minutes)", "backup_interval", "30", "entry"),
                ("Enabled", "backup_enabled", True, "switch"),
            ],
        },
    }

    def _get_addon_meta(name):
        """Return metadata dict for an addon. Falls back to a generic template."""
        if name in ADDON_META:
            return ADDON_META[name]
        mod = _loaded_addons.get(name)
        # Check if module exposes __meta__
        if mod and hasattr(mod, "__meta__"):
            return mod.__meta__
        return {
            "title":       name.replace("_", " ").title(),
            "version":     "?",
            "author":      "Unknown",
            "description": (
                "No description available.\n\n"
                "To add a description, define __meta__ in your addon:\n\n"
                '  __meta__ = {\n'
                '    "title": "My Addon",\n'
                '    "description": "What it does.",\n'
                '    "settings": []\n'
                '  }'
            ),
            "preview_colors": [T["bg"],T["card"],T["start"],T["stop"],T["sync"],T["handoff"]],
            "settings": [],
        }

    # ── Right panel renderers ─────────────────────────────

    def _show_empty_state():
        for w in right_content.winfo_children(): w.destroy()
        empty = ctk.CTkFrame(right_content, fg_color="transparent")
        empty.grid(row=0, column=0, sticky="nsew")
        empty.rowconfigure(0, weight=1); empty.columnconfigure(0, weight=1)
        inner = ctk.CTkFrame(empty, fg_color="transparent")
        inner.place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(inner, text="🧩", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(inner, text="Select an addon",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=T["text"]).pack(pady=(8,4))
        ctk.CTkLabel(inner, text="Pick an addon from the left to view its\ndescription and settings.",
                     font=ctk.CTkFont(size=12), text_color=T["muted"],
                     justify="center").pack()

    def _show_addon_detail(name):
        for w in right_content.winfo_children(): w.destroy()

        meta    = _get_addon_meta(name)
        loaded  = name in _loaded_addons
        s_cfg   = load_settings()

        scroll  = ctk.CTkScrollableFrame(right_content, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        scroll.columnconfigure(0, weight=1)

        # ── Header card ───────────────────────────────────
        hcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                              border_width=1, corner_radius=12)
        hcard.pack(fill="x", pady=(0,8))

        hinner = ctk.CTkFrame(hcard, fg_color="transparent")
        hinner.pack(fill="x", padx=16, pady=14)

        # Colour swatch preview
        sw_row = ctk.CTkFrame(hinner, fg_color="transparent"); sw_row.pack(anchor="w", pady=(0,8))
        colors = meta.get("preview_colors", [T["start"],T["stop"],T["sync"]])
        for col in colors:
            sw = ctk.CTkFrame(sw_row, width=22, height=22, corner_radius=4, fg_color=col)
            sw.pack(side="left", padx=3); sw.pack_propagate(False)

        title_row = ctk.CTkFrame(hinner, fg_color="transparent"); title_row.pack(fill="x")
        ctk.CTkLabel(title_row,
                     text=meta.get("title", name),
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        status_badge = ctk.CTkLabel(title_row,
                                     text="● Loaded" if loaded else "○ Not loaded",
                                     font=ctk.CTkFont(size=11),
                                     text_color=T["start"] if loaded else T["muted"])
        status_badge.pack(side="left", padx=12)

        meta_row = ctk.CTkFrame(hinner, fg_color="transparent"); meta_row.pack(anchor="w", pady=(2,0))
        ctk.CTkLabel(meta_row,
                     text=f"v{meta.get('version','?')}  ·  by {meta.get('author','?')}",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")

        # Action buttons
        btn_row = ctk.CTkFrame(hcard, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0,14))

        def _reload_addon():
            path = os.path.join(addon_dir, name + ".py")
            if os.path.exists(path):
                _load_addon(path)
                show_toast(f"{name} reloaded!", T["sync"])
                _refresh_list()
                _show_addon_detail(name)

        def _remove_addon():
            try:
                os.remove(os.path.join(addon_dir, name + ".py"))
                _loaded_addons.pop(name, None)
                show_toast(f"{name} removed.", T["stop"])
                _refresh_list()
                _show_empty_state()
            except Exception as ex:
                show_toast(f"Error: {ex}", T["stop"])

        ctk.CTkButton(btn_row, text="↺  Reload", width=90, height=30,
                      font=ctk.CTkFont(size=11), fg_color=T["sync"],
                      hover_color=T["sync"], text_color="#000",
                      command=_reload_addon).pack(side="left", padx=(0,6))
        ctk.CTkButton(btn_row, text="🗑  Remove", width=90, height=30,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["stop"],
                      text_color=T["stop"], hover_color=T["border"],
                      command=_remove_addon).pack(side="left")

        # ── Description card ──────────────────────────────
        dcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                              border_width=1, corner_radius=12)
        dcard.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(dcard, text="About",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["muted"]).pack(anchor="w", padx=16, pady=(12,4))
        ctk.CTkFrame(dcard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)
        ctk.CTkLabel(dcard,
                     text=meta.get("description", "No description."),
                     font=ctk.CTkFont(size=12), text_color=T["text"],
                     justify="left", wraplength=580).pack(anchor="w", padx=16, pady=(10,14))

        # ── Settings card ─────────────────────────────────
        addon_settings = meta.get("settings", [])
        if addon_settings:
            scard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                                  border_width=1, corner_radius=12)
            scard.pack(fill="x", pady=(0,8))
            sh = ctk.CTkFrame(scard, fg_color="transparent"); sh.pack(fill="x", padx=16, pady=(12,4))
            ctk.CTkLabel(sh, text="Settings",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=T["muted"]).pack(side="left")
            ctk.CTkFrame(scard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)

            sbody = ctk.CTkFrame(scard, fg_color="transparent")
            sbody.pack(fill="x", padx=16, pady=(8,14))

            _setting_vars = {}

            for (label, key, default, widget_type) in addon_settings:
                row = ctk.CTkFrame(sbody, fg_color="transparent"); row.pack(fill="x", pady=5)
                ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12),
                             text_color=T["text"], width=200, anchor="w").pack(side="left")
                current_val = s_cfg.get(key, default)

                if widget_type == "switch":
                    var = ctk.BooleanVar(value=bool(current_val))
                    def _on_sw_change(v, k=key):
                        update_setting(k, v)
                    ctk.CTkSwitch(row, text="", variable=var,
                                  command=lambda k=key, v=var: update_setting(k, v.get()),
                                  button_color=T["sync"],
                                  progress_color=T["sync"]).pack(side="right")
                    _setting_vars[key] = var

                elif widget_type == "entry":
                    var = ctk.StringVar(value=str(current_val))
                    e = ctk.CTkEntry(row, textvariable=var, height=28,
                                     font=ctk.CTkFont(size=11),
                                     fg_color=T["bg"], border_color=T["border"],
                                     text_color=T["text"], width=200)
                    e.pack(side="right")
                    def _save_entry(*_, k=key, v=var): update_setting(k, v.get())
                    e.bind("<FocusOut>", _save_entry)
                    e.bind("<Return>",   _save_entry)
                    _setting_vars[key] = var

            def _save_all_settings():
                for key, var in _setting_vars.items():
                    update_setting(key, var.get())
                show_toast("Addon settings saved!", T["start"])

            ctk.CTkButton(sbody, text="Save Settings", height=30, corner_radius=6,
                          font=ctk.CTkFont(size=11, weight="bold"),
                          fg_color=T["start"], hover_color=T["start"], text_color="#000",
                          command=_save_all_settings).pack(anchor="w", pady=(8,0))

        # ── Source preview card ───────────────────────────
        src_path = os.path.join(addon_dir, name + ".py")
        if os.path.exists(src_path):
            try:
                with open(src_path, encoding="utf-8", errors="ignore") as f:
                    src_lines = f.readlines()[:30]
                src_preview = "".join(src_lines)
                if len(src_lines) == 30:
                    src_preview += "\n  ... (truncated)"

                pvcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                                       border_width=1, corner_radius=12)
                pvcard.pack(fill="x", pady=(0,8))
                pvh = ctk.CTkFrame(pvcard, fg_color="transparent"); pvih = pvh
                pvih.pack(fill="x", padx=16, pady=(12,4))
                ctk.CTkLabel(pvih, text="Source Preview",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=T["muted"]).pack(side="left")
                ctk.CTkLabel(pvih, text=f"{len(open(src_path).readlines())} lines",
                             font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="right")
                ctk.CTkFrame(pvcard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)
                src_box = ctk.CTkTextbox(pvcard,
                                          font=ctk.CTkFont(size=10, family="Consolas"),
                                          state="normal", height=160,
                                          fg_color=T["bg"], text_color=T["muted"],
                                          wrap="none")
                src_box.insert("1.0", src_preview)
                src_box.configure(state="disabled")
                src_box.pack(fill="x", padx=16, pady=(8,14))
            except Exception:
                pass

    # ── List item renderer ────────────────────────────────
    def _make_list_item(name):
        loaded = name in _loaded_addons
        meta   = _get_addon_meta(name)

        btn = ctk.CTkButton(
            list_scroll,
            text="",
            height=64,
            corner_radius=8,
            fg_color=T["bg"] if _selected_addon[0] != name else T["border"],
            hover_color=T["border"],
            border_width=0,
            command=lambda n=name: _select(n)
        )
        btn.pack(fill="x", padx=8, pady=3)
        _list_btns[name] = btn

        # Inner layout on top of button
        inner = ctk.CTkFrame(btn, fg_color="transparent", corner_radius=8)
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        inner.bind("<Button-1>", lambda e, n=name: _select(n))

        row1 = ctk.CTkFrame(inner, fg_color="transparent"); row1.pack(fill="x", padx=12, pady=(8,0))
        status_dot_lbl = ctk.CTkLabel(row1, text="●" if loaded else "○",
                                       font=ctk.CTkFont(size=10),
                                       text_color=T["start"] if loaded else T["muted"],
                                       width=14)
        status_dot_lbl.pack(side="left")
        ctk.CTkLabel(row1, text=meta.get("title", name),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=(4,0))
        ctk.CTkLabel(row1, text=f"v{meta.get('version','?')}",
                     font=ctk.CTkFont(size=9), text_color=T["muted"]).pack(side="right")

        row2 = ctk.CTkFrame(inner, fg_color="transparent"); row2.pack(fill="x", padx=12, pady=(2,6))
        desc_short = (meta.get("description","") or "")[:55].replace("\n"," ")
        if len(meta.get("description","")) > 55: desc_short += "…"
        ctk.CTkLabel(row2, text=desc_short, font=ctk.CTkFont(size=10),
                     text_color=T["muted"], anchor="w").pack(anchor="w")

    def _select(name):
        _selected_addon[0] = name
        for n, b in _list_btns.items():
            b.configure(fg_color=T["border"] if n == name else T["bg"])
        _show_addon_detail(name)

    def _refresh_list():
        for w in list_scroll.winfo_children(): w.destroy()
        _list_btns.clear()
        try:
            scripts = sorted([os.path.splitext(x)[0]
                              for x in os.listdir(addon_dir) if x.endswith(".py")])
        except:
            scripts = []

        if not scripts:
            ctk.CTkLabel(list_scroll,
                         text="No addons installed.\nClick + Install below.",
                         font=ctk.CTkFont(size=11), text_color=T["muted"],
                         justify="center").pack(pady=30)
        else:
            for s in scripts:
                _make_list_item(s)

        # Update count in header
        try:
            for w in lhdr.winfo_children():
                if hasattr(w, '_is_count_lbl'):
                    w.destroy()
            cnt = ctk.CTkLabel(lhdr, text=f"{len(scripts)}",
                               font=ctk.CTkFont(size=10),
                               text_color=T["muted"],
                               fg_color=T["border"],
                               corner_radius=8, width=24, height=18)
            cnt._is_count_lbl = True
            cnt.pack(side="right", padx=10)
        except: pass

    # Footer buttons
    def _install_addon():
        paths = _tk_fd.askopenfilenames(
            title="Select MC CTRL Addon (.py)",
            filetypes=[("Python","*.py"),("All","*.*")])
        if not paths: return
        for p in paths:
            dest = os.path.join(addon_dir, os.path.basename(p))
            try: shutil.copy2(p, dest); _load_addon(dest)
            except Exception as ex: show_toast(f"Failed: {ex}", T["stop"])
        show_toast(f"{len(paths)} addon(s) installed!", T["start"])
        _refresh_list()

    def _open_addon_folder():
        _open_folder(addon_dir)

    ctk.CTkButton(lfooter, text="+ Install", height=32,
                  font=ctk.CTkFont(size=11, weight="bold"),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_install_addon).pack(side="left", padx=(8,4), pady=8)
    ctk.CTkButton(lfooter, text="Open Folder", height=32,
                  font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"],
                  hover_color=T["border"],
                  command=_open_addon_folder).pack(side="left", padx=(0,8), pady=8)

    _refresh_list()
    _show_empty_state()


def _ensure_addon_readme(addon_dir):
    readme = os.path.join(addon_dir, "README.md")
    if os.path.exists(readme): return
    try:
        with open(readme, "w") as f:
            f.write("""# MC CTRL Addon API

Addons are .py files in this folder, loaded at startup.

## Minimal addon

```python
def setup(ctx):
    ctx["log"]("Hello from my addon!")
```

## Expose metadata (shows in the Addons tab)

```python
__meta__ = {
    "title": "My Addon",
    "version": "1.0",
    "author": "You",
    "description": "What this addon does.",
    "preview_colors": ["#ff0000", "#00ff00"],
    "settings": [
        ("My setting", "my_addon_key", "default_value", "entry"),
        ("Toggle",     "my_addon_on",  True,            "switch"),
    ]
}

def setup(ctx):
    ctx["log"]("My addon loaded!")
```

## Context keys
- ctx["app"]              — CTk root window
- ctx["T"]               — theme colour dict
- ctx["log"](msg)        — write to server log
- ctx["show_toast"](m,c) — show a toast notification
- ctx["send_server_cmd"] — send command to running MC server
- ctx["load_settings"]   — returns settings dict
""")
    except Exception:
        pass

# ── MULTI CTRL ────────────────────────────────────────────
_mc_servers = {}

def build_multictrl_tab(parent):
    global _mc_servers
    MAX_SLOTS = 3
    slots = {}
    for i in range(MAX_SLOTS):
        slots[i] = {"proc":None,"stdin":None,"path_var":ctk.StringVar(value=""),
                    "log_box":None,"status":None,"running":False}
    _mc_servers = slots

    parent.rowconfigure(0, weight=0); parent.rowconfigure(1, weight=1); parent.rowconfigure(2, weight=0)
    parent.columnconfigure(0, weight=1)

    toolbar = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                            border_width=1, corner_radius=0)
    toolbar.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(toolbar, text="⊞  MULTI CTRL",
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["handoff"]).pack(side="left", padx=14, pady=8)
    ctk.CTkLabel(toolbar, text="— control up to 3 servers simultaneously",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

    col_area = ctk.CTkFrame(parent, fg_color="transparent")
    col_area.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
    for i in range(MAX_SLOTS):
        col_area.columnconfigure(i, weight=1, uniform="col")
    col_area.rowconfigure(0, weight=1)

    def _mc_log(slot, msg):
        lb = slots[slot]["log_box"]
        if lb is None: return
        try:
            lb.configure(state="normal"); lb.insert("end", msg + "\n")
            lb.configure(state="disabled"); lb.see("end")
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
        slots[slot]["running"] = False; slots[slot]["proc"] = None; slots[slot]["stdin"] = None

    def _mc_start(slot):
        path = slots[slot]["path_var"].get().strip()
        if not path or not os.path.isdir(path):
            show_toast(f"Server {slot+1}: set a valid folder first.", T["stop"]); return
        if slots[slot]["running"]:
            show_toast(f"Server {slot+1} is already running.", T["muted"]); return
        s = load_settings()
        java = s.get("java_path", JAVA_PATH)
        jar  = os.path.join(path, "server.jar")
        if not os.path.exists(jar):
            show_toast(f"Server {slot+1}: no server.jar found.", T["stop"]); return
        if not _check_eula(path): return
        try:
            cmd = [java, "-Xms512M", "-Xmx2G", "-XX:+UseG1GC", "-jar", jar, "--nogui"]
            proc = subprocess.Popen(
                cmd, cwd=path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=_popen_flags())
            slots[slot]["proc"] = proc; slots[slot]["stdin"] = proc.stdin
            slots[slot]["running"] = True
            _mc_set_status(slot, "● Running", T["start"])
            app.after(0, _mc_log, slot, f"-- Server {slot+1} started --")
            threading.Thread(target=_mc_read_output, args=(slot, proc), daemon=True).start()
        except Exception as ex:
            show_toast(f"Server {slot+1} failed: {ex}", T["stop"])

    def _mc_stop(slot):
        proc = slots[slot]["proc"]
        if proc:
            try: slots[slot]["stdin"].write("stop\n"); slots[slot]["stdin"].flush()
            except: pass
            app.after(3000, lambda p=proc: p.terminate() if p.poll() is None else None)
        slots[slot]["running"] = False; slots[slot]["proc"] = None; slots[slot]["stdin"] = None
        _mc_set_status(slot, "● Stopped", T["stop"])
        app.after(0, _mc_log, slot, f"-- Server {slot+1} stopped --")

    for i in range(MAX_SLOTS):
        col = ctk.CTkFrame(col_area, fg_color=T["card"], border_color=T["border"],
                           border_width=1, corner_radius=10)
        col.grid(row=0, column=i, sticky="nsew", padx=4, pady=0)
        col.rowconfigure(2, weight=1); col.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(col, fg_color=T["bg"], corner_radius=8)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))
        ctk.CTkLabel(hdr, text=f"Server {i+1}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left", padx=10, pady=6)
        st_lbl = ctk.CTkLabel(hdr, text="● Stopped",
                               font=ctk.CTkFont(size=11, weight="bold"), text_color=T["stop"])
        st_lbl.pack(side="right", padx=10)
        slots[i]["status"] = st_lbl

        path_frame = ctk.CTkFrame(col, fg_color="transparent")
        path_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0,4))
        path_frame.columnconfigure(0, weight=1)
        ctk.CTkEntry(path_frame, textvariable=slots[i]["path_var"], height=28,
                     font=ctk.CTkFont(size=10, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                     placeholder_text=f"Server {i+1} folder path…"
                     ).grid(row=0, column=0, sticky="ew", padx=(0,4))
        def _browse_mc(slot=i):
            p = _tk_fd.askdirectory(title=f"Select Server {slot+1} Folder")
            if p: slots[slot]["path_var"].set(p)
        ctk.CTkButton(path_frame, text="…", width=28, height=28, font=ctk.CTkFont(size=11),
                      corner_radius=6, fg_color=T["bg"], border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                      command=lambda s=i: _browse_mc(s)).grid(row=0, column=1)

        btn_row = ctk.CTkFrame(path_frame, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4,0))
        ctk.CTkButton(btn_row, text="▶ Start", height=26, font=ctk.CTkFont(size=11),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000",
                      command=lambda s=i: threading.Thread(target=_mc_start, args=(s,), daemon=True).start()
                      ).pack(side="left", expand=True, fill="x", padx=(0,3))
        ctk.CTkButton(btn_row, text="■ Stop", height=26, font=ctk.CTkFont(size=11),
                      fg_color=T["stop"], hover_color=T["stop"], text_color="#fff",
                      command=lambda s=i: _mc_stop(s)
                      ).pack(side="left", expand=True, fill="x", padx=(3,0))

        lb = ctk.CTkTextbox(col, font=ctk.CTkFont(size=10, family="Consolas"),
                             wrap="word", state="disabled", fg_color=T["bg"], text_color=T["text"])
        lb.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0,8))
        slots[i]["log_box"] = lb

    chat_bar = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                             border_width=1, corner_radius=0)
    chat_bar.grid(row=2, column=0, sticky="ew")
    chat_bar.columnconfigure(2, weight=1)

    target_var = ctk.StringVar(value="Server 1")
    ctk.CTkLabel(chat_bar, text="Send to:", font=ctk.CTkFont(size=11),
                 text_color=T["muted"]).grid(row=0, column=0, padx=(10,4), pady=8)
    ctk.CTkOptionMenu(chat_bar, values=["Server 1","Server 2","Server 3","All Servers"],
                      variable=target_var, font=ctk.CTkFont(size=11), width=120, height=30,
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"],
                      dropdown_text_color=T["text"], dropdown_hover_color=T["border"]
                      ).grid(row=0, column=1, padx=(0,6), pady=8, sticky="w")

    mc_cmd_entry = ctk.CTkEntry(chat_bar, height=30, font=ctk.CTkFont(size=12),
                                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                                 placeholder_text="command or chat…")
    mc_cmd_entry.grid(row=0, column=2, sticky="ew", padx=(0,6), pady=8)

    def _mc_send(_event=None):
        cmd = mc_cmd_entry.get().strip()
        if not cmd: return
        target = target_var.get()
        targets = list(range(MAX_SLOTS)) if target == "All Servers" else [int(target.split()[-1])-1]
        for s in targets:
            stdin = slots[s]["stdin"]
            if stdin:
                try: stdin.write(cmd+"\n"); stdin.flush(); app.after(0, _mc_log, s, f">> {cmd}")
                except Exception as ex: app.after(0, _mc_log, s, f"[error] {ex}")
            else: app.after(0, _mc_log, s, f"[Server {s+1} not running]")
        mc_cmd_entry.delete(0, "end")

    mc_cmd_entry.bind("<Return>", _mc_send)
    ctk.CTkButton(chat_bar, text="Send", width=70, height=30, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_mc_send).grid(row=0, column=3, padx=(0,10), pady=8)

# ── Settings tab ──────────────────────────────────────────
def build_settings_tab(parent):
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

    b = section("Layout")
    row(b, "Log panel on left side",   lambda p: sw(p, lambda: log_left,  lambda v: swap_layout()))
    row(b, "Show performance panel",   lambda p: sw(p, lambda: show_perf, lambda v: toggle_perf()))
    row(b, "Show chat & events panel", lambda p: sw(p, lambda: show_chat, lambda v: toggle_chat()))

    b = section("Server")

    # Platform note on Linux/Mac
    if not IS_WINDOWS:
        plat_note = ctk.CTkFrame(b, fg_color=T["bg"], border_color=T["handoff"],
                                  border_width=1, corner_radius=6)
        plat_note.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(plat_note,
                     text=f"🐧  Running on {'Linux' if IS_LINUX else 'macOS'}. "
                          f"Java path defaults to 'java' (must be on PATH). "
                          f"taskkill replaced with pkill.",
                     font=ctk.CTkFont(size=11), text_color=T["handoff"],
                     wraplength=560, justify="left").pack(padx=12, pady=8)

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

    b = section("Auto Upload")
    row(b, "Enable auto upload",
        lambda p: sw(p, lambda: auto_upload, lambda v: toggle_auto_upload()))
    def _toggle_backup_upload(v):
        global backup_upload_on
        backup_upload_on = v; update_setting("backup_upload_on", v)
    row(b, "Backup upload (ON = push to GitHub)",
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
    row(b, "Upload world on server stop",
        lambda p: sw(p, lambda: upload_on_stop, lambda v: _set_upload_on_stop(v)))

    b = section("About")
    def reopen_fn(p):
        ctk.CTkButton(p, text="Re-open First-Launch Setup",
                      font=ctk.CTkFont(size=11), height=28,
                      fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                      command=show_first_launch_dialog).pack(side="right")
    row(b, "Re-read README / change initial settings", reopen_fn)

    plat_str = "Windows" if IS_WINDOWS else ("Linux" if IS_LINUX else "macOS")
    ctk.CTkLabel(scroll, text=f"Settings: {SETTINGS_FILE}  ·  Platform: {plat_str}",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(4,0))

def _set_upload_on_stop(val):
    global upload_on_stop
    upload_on_stop = val; update_setting("upload_on_stop", val)

# ── EULA check ────────────────────────────────────────────
def _check_eula(path):
    eula_path = os.path.join(path, "eula.txt")
    try:
        txt = open(eula_path, encoding="utf-8").read().lower()
        if "eula=true" in txt:
            return True
    except FileNotFoundError:
        pass

    result = [None]

    def _show():
        win = ctk.CTkToplevel(app)
        win.title("Minecraft EULA")
        win.resizable(False, False)
        win.configure(fg_color=T["bg"])
        win.grab_set(); win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        w, h = 500, 390
        try:
            ax = app.winfo_x() + (app.winfo_width()  - w) // 2
            ay = app.winfo_y() + (app.winfo_height() - h) // 2
            win.geometry(f"{w}x{h}+{ax}+{ay}")
        except: win.geometry(f"{w}x{h}")

        ctk.CTkLabel(win, text="⚠", font=ctk.CTkFont(size=42),
                     text_color=T["handoff"]).pack(pady=(22,0))
        ctk.CTkLabel(win, text="Minecraft End User Licence Agreement",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=T["text"]).pack(pady=(6,0))

        body = ctk.CTkFrame(win, fg_color=T["card"], border_color=T["border"],
                            border_width=1, corner_radius=10)
        body.pack(fill="x", padx=24, pady=14)
        ctk.CTkLabel(body, text=(
            "Before starting your server you must agree to the\n"
            "Minecraft End User Licence Agreement (EULA).\n\n"
            "By accepting you confirm you have read and agreed to:\n\n"
            "  https://aka.ms/MinecraftEULA\n\n"
            "This will write  eula=true  to eula.txt."
        ), font=ctk.CTkFont(size=12), text_color=T["muted"], justify="left").pack(padx=18, pady=14)

        btn_row = ctk.CTkFrame(win, fg_color="transparent"); btn_row.pack(pady=(0,18))

        def _accept():
            try:
                os.makedirs(path, exist_ok=True)
                with open(eula_path, "w", encoding="utf-8") as f:
                    f.write(f"# Accepted via MC CTRL on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            "# https://aka.ms/MinecraftEULA\neula=true\n")
                log("  EULA accepted — eula.txt written.")
            except Exception as ex: log(f"  EULA write error: {ex}")
            result[0] = True; win.destroy()

        def _decline():
            result[0] = False; win.destroy()

        ctk.CTkButton(btn_row, text="I Agree — Accept EULA", width=190, height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000000",
                      command=_accept).pack(side="left", padx=(0,12))
        ctk.CTkButton(btn_row, text="Decline", width=100, height=36,
                      font=ctk.CTkFont(size=13), fg_color="transparent",
                      border_width=1, border_color=T["stop"], text_color=T["stop"],
                      hover_color=T["border"], command=_decline).pack(side="left")
        win.wait_window()

    app.after(0, _show)
    while result[0] is None: time.sleep(0.05)
    return result[0]

# ── Server actions ────────────────────────────────────────
def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    s    = load_settings()
    path = s.get("srv_path", SRV_PATH)
    java = s.get("java_path", JAVA_PATH)
    repo = s.get("repo_url", REPO_URL)

    if not _check_eula(path):
        log("  Server start cancelled — EULA not accepted.")
        set_status("Stopped", T["stop"]); set_all_buttons("normal"); return

    set_status("Starting...", T["handoff"])
    log("-- Start Server ------------------")
    run_cmd(f"git remote set-url origin {repo}", cwd=path)
    log("Pulling latest world from GitHub...")
    run_cmd("git pull origin main", cwd=path)
    log("Launching server with Aikar flags...")

    # Quote java path only on Windows (it might have spaces); on Linux/Mac use list form
    if IS_WINDOWS:
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
    else:
        java_args = [
            java,
            "-Xms2G", "-Xmx2G", "-XX:+UseG1GC", "-XX:+ParallelRefProcEnabled",
            "-XX:MaxGCPauseMillis=200", "-XX:+UnlockExperimentalVMOptions",
            "-XX:+DisableExplicitGC", "-XX:G1NewSizePercent=30",
            "-XX:G1MaxNewSizePercent=40", "-XX:G1HeapRegionSize=8M",
            "-XX:G1ReservePercent=20", "-XX:G1HeapWastePercent=5",
            "-XX:G1MixedGCCountTarget=4", "-XX:InitiatingHeapOccupancyPercent=15",
            "-XX:G1MixedGCLiveThresholdPercent=90",
            "-XX:G1RSetUpdatingPauseTimePercent=5", "-XX:SurvivorRatio=32",
            "-XX:+PerfDisableSharedMem", "-XX:MaxTenuringThreshold=1",
            "-Dusing.aikars.flags=https://mcflags.emc.gs", "-Daikars.new.flags=true",
            "-jar", "server.jar", "nogui",
        ]
        server_proc = subprocess.Popen(
            java_args, cwd=path,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1)

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
    r = _kill_java()
    log("  Java killed." if r.returncode == 0 else "  Java was not running.")
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
            creationflags=_popen_flags())
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

# ── Addon loader ──────────────────────────────────────────
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
    _ensure_addon_readme(addon_dir)
    try:
        for s in sorted(os.listdir(addon_dir)):
            if s.endswith(".py"):
                _load_addon(os.path.join(addon_dir, s))
    except: pass

# ── Boot splash ───────────────────────────────────────────
_splash_frame = ctk.CTkFrame(app, fg_color=T["bg"])
_splash_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
ctk.CTkLabel(_splash_frame, text="MC CTRL",
             font=ctk.CTkFont(size=48, weight="bold"),
             text_color=T["start"]).place(relx=0.5, rely=0.38, anchor="center")
ctk.CTkLabel(_splash_frame, text="Loading…",
             font=ctk.CTkFont(size=14), text_color=T["muted"]
             ).place(relx=0.5, rely=0.50, anchor="center")
_splash_bar = ctk.CTkProgressBar(_splash_frame, width=260, height=6,
                                  fg_color=T["border"], progress_color=T["start"])
_splash_bar.place(relx=0.5, rely=0.57, anchor="center")
_splash_bar.set(0); _splash_bar.start()

def _finish_boot():
    global _splash_frame
    _splash_bar.stop()
    build_ui()
    _splash_frame.destroy()
    if auto_upload: schedule_auto_upload()

app.after(50, _finish_boot)

def _splash_log():
    plat_str = "Windows" if IS_WINDOWS else ("Linux" if IS_LINUX else "macOS")
    lines = [
        "",
        "  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗     ",
        "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║     ",
        "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║     ",
        "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║     ",
        "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗",
        "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
        "",
        f"  GamerMahir07's MC CTRL  ·  Platform: {plat_str}",
        f"  Theme: {current_theme_name}  |  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}",
        "",
    ]
    for line in lines: log(line)
    if is_first_launch: app.after(200, show_first_launch_dialog)

app.after(200, _splash_log)
app.after(800, _load_all_addons)
app.mainloop()
