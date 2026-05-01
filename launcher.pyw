import time
import shutil
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")
import customtkinter as ctk
import subprocess
import threading
import json
import os
import ctypes
import re
from datetime import datetime
import psutil

try:
    import tkinterdnd2 as dnd
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

CREATE_NO_WINDOW = 0x08000000

SRV_PATH  = r"C:\Users\DigitalComputer\Desktop\mc"
JAVA_PATH = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe"
REPO_URL  = "https://github.com/GamerMahir07/minecraft-server.git"

THEMES = {
    "Dark (Default)": {"appearance":"dark", "bg":"#0d0d0d","card":"#1a1a1a","border":"#2a2a2a","text":"#e0e0e0","muted":"#555555","start":"#22c55e","stop":"#ef4444","sync":"#60a5fa","handoff":"#f59e0b"},
    "Midnight Blue":  {"appearance":"dark", "bg":"#0a0f1e","card":"#111827","border":"#1e3a5f","text":"#e2e8f0","muted":"#4a6080","start":"#34d399","stop":"#f87171","sync":"#818cf8","handoff":"#fbbf24"},
    "Light":          {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#e0e0e0","text":"#1a1a1a","muted":"#888888","start":"#16a34a","stop":"#dc2626","sync":"#2563eb","handoff":"#d97706"},
    "Creeper Green":  {"appearance":"dark", "bg":"#0a1a0a","card":"#0f2a0f","border":"#1a4a1a","text":"#c8f0c8","muted":"#3a6a3a","start":"#4ade80","stop":"#f87171","sync":"#86efac","handoff":"#fde047"},
    "Nether Red":     {"appearance":"dark", "bg":"#000000","card":"#1a0000","border":"#6a0000","text":"#ff4444","muted":"#8b0000","start":"#ff6b6b","stop":"#ff0000","sync":"#ff8c8c","handoff":"#ffd700"},
    # Ocean is now a fresh light-cyan theme
    "Ocean":          {"appearance":"light","bg":"#e0f7ff","card":"#ffffff","border":"#7dd3f0","text":"#003a52","muted":"#4a8fa8","start":"#0284c7","stop":"#e11d48","sync":"#0ea5e9","handoff":"#f59e0b"},
    "Sunset":         {"appearance":"light","bg":"#fff7ed","card":"#ffffff","border":"#fed7aa","text":"#1c0a00","muted":"#9a6030","start":"#16a34a","stop":"#e11d48","sync":"#7c3aed","handoff":"#ea580c"},
    "Obsidian":       {"appearance":"dark", "bg":"#080808","card":"#101010","border":"#1e1e2e","text":"#cdd6f4","muted":"#45475a","start":"#a6e3a1","stop":"#f38ba8","sync":"#89b4fa","handoff":"#fab387"},
    "Ender Night":    {"appearance":"dark", "bg":"#000000","card":"#0d0010","border":"#3b0060","text":"#e8b4ff","muted":"#6a2a8a","start":"#bf7fff","stop":"#ff5f87","sync":"#d68fff","handoff":"#ffb347"},
    "Arctic":         {"appearance":"light","bg":"#eef4fb","card":"#ffffff","border":"#b8d4f0","text":"#0d2137","muted":"#6a90b0","start":"#0ea5e9","stop":"#e11d48","sync":"#6366f1","handoff":"#f59e0b"},
    "Forest":         {"appearance":"dark", "bg":"#0d1a0d","card":"#142414","border":"#254025","text":"#d4edda","muted":"#4a7a4a","start":"#86efac","stop":"#fca5a5","sync":"#6ee7b7","handoff":"#fde68a"},
    "Rose Gold":      {"appearance":"light","bg":"#fff0f3","card":"#ffffff","border":"#f4c2cb","text":"#3a0a14","muted":"#b06070","start":"#e11d48","stop":"#9f1239","sync":"#db2777","handoff":"#c2410c"},
    "Dracula":        {"appearance":"dark", "bg":"#282a36","card":"#313442","border":"#44475a","text":"#f8f8f2","muted":"#6272a4","start":"#50fa7b","stop":"#ff5555","sync":"#8be9fd","handoff":"#ffb86c"},
    "Lava":           {"appearance":"dark", "bg":"#120500","card":"#1e0a00","border":"#5a1a00","text":"#ffe8d0","muted":"#7a3a10","start":"#ff7c00","stop":"#ff3300","sync":"#ffaa00","handoff":"#ffdd00"},
    "Sand":           {"appearance":"light","bg":"#f5e6c8","card":"#fdf3e0","border":"#c8a96e","text":"#3d2b00","muted":"#8a6a30","start":"#5a8a00","stop":"#c0392b","sync":"#1a6b8a","handoff":"#c07000"},
    "Void":           {"appearance":"dark", "bg":"#000000","card":"#0a0a0a","border":"#1a1a1a","text":"#aaaaaa","muted":"#333333","start":"#444444","stop":"#666666","sync":"#555555","handoff":"#777777"},
    "Carbon":         {"appearance":"dark", "bg":"#1a1a2e","card":"#16213e","border":"#0f3460","text":"#e0e0e0","muted":"#4a4a6a","start":"#00c896","stop":"#e94560","sync":"#4d9fff","handoff":"#f5a623"},
    "Lavender":       {"appearance":"light","bg":"#f0eeff","card":"#ffffff","border":"#c5b8ff","text":"#1a0050","muted":"#7060a0","start":"#5b21b6","stop":"#db2777","sync":"#4f46e5","handoff":"#d97706"},
    "Mocha":          {"appearance":"dark", "bg":"#1c1410","card":"#2a1f18","border":"#4a3428","text":"#f0dece","muted":"#7a5a48","start":"#c8a86e","stop":"#e05050","sync":"#90b8d0","handoff":"#e8c060"},
    "Sakura":         {"appearance":"light","bg":"#fff0f5","card":"#ffffff","border":"#ffb8cc","text":"#3a0020","muted":"#c06080","start":"#be185d","stop":"#e11d48","sync":"#9d174d","handoff":"#f59e0b"},
    "Matrix":         {"appearance":"dark", "bg":"#000000","card":"#001400","border":"#004400","text":"#00ff41","muted":"#006600","start":"#00ff41","stop":"#ff0000","sync":"#00cc33","handoff":"#ffff00"},
    "Nord":           {"appearance":"dark", "bg":"#2e3440","card":"#3b4252","border":"#434c5e","text":"#eceff4","muted":"#4c566a","start":"#a3be8c","stop":"#bf616a","sync":"#88c0d0","handoff":"#ebcb8b"},
    "Solarized":      {"appearance":"light","bg":"#fdf6e3","card":"#eee8d5","border":"#93a1a1","text":"#073642","muted":"#657b83","start":"#859900","stop":"#dc322f","sync":"#268bd2","handoff":"#b58900"},
    "Gruvbox":        {"appearance":"dark", "bg":"#282828","card":"#3c3836","border":"#504945","text":"#ebdbb2","muted":"#7c6f64","start":"#b8bb26","stop":"#fb4934","sync":"#83a598","handoff":"#fabd2f"},
    "CB: Blue & Orange":      {"appearance":"light","bg":"#f7f7f7","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#0072b2","stop":"#d55e00","sync":"#56b4e9","handoff":"#e69f00"},
    "CB: Dark Blue & Orange": {"appearance":"dark", "bg":"#111111","card":"#1e1e1e","border":"#333333","text":"#ffffff","muted":"#888888","start":"#56b4e9","stop":"#d55e00","sync":"#0072b2","handoff":"#e69f00"},
    "CB: Green & Purple":     {"appearance":"light","bg":"#f5f5f5","card":"#ffffff","border":"#cccccc","text":"#000000","muted":"#767676","start":"#009e73","stop":"#cc79a7","sync":"#0072b2","handoff":"#f0e442"},
    "CB: High Contrast":      {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#000000","text":"#000000","muted":"#444444","start":"#0000ff","stop":"#ff0000","sync":"#007700","handoff":"#ff8800"},
    "CB: Dark High Contrast": {"appearance":"dark", "bg":"#000000","card":"#1a1a1a","border":"#ffffff","text":"#ffffff","muted":"#aaaaaa","start":"#ffff00","stop":"#ff6600","sync":"#00ffff","handoff":"#ff99ff"},
    "CB: Tol Muted":  {"appearance":"light","bg":"#f8f4f0","card":"#ffffff","border":"#bbaabb","text":"#221122","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    "CB: Tol Dark":   {"appearance":"dark", "bg":"#221122","card":"#332244","border":"#554466","text":"#eeddff","muted":"#887799","start":"#44aa99","stop":"#cc6677","sync":"#88ccee","handoff":"#ddcc77"},
    "CB: Monochrome": {"appearance":"light","bg":"#ffffff","card":"#f0f0f0","border":"#999999","text":"#000000","muted":"#666666","start":"#222222","stop":"#777777","sync":"#444444","handoff":"#555555"},
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# ── Settings helpers ──────────────────────────────────────
def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def update_setting(key, value):
    s = load_settings(); s[key] = value; save_settings(s)

settings           = load_settings()
is_first_launch    = "theme" not in settings
current_theme_name = settings.get("theme", "Dark (Default)")
show_chat          = settings.get("show_chat", True)
log_left           = settings.get("log_left", False)
show_perf          = settings.get("show_perf", True)
fullscreen         = settings.get("fullscreen", False)
auto_upload        = settings.get("auto_upload", False)
auto_upload_mins   = settings.get("auto_upload_mins", 10)
upload_on_stop     = settings.get("upload_on_stop", True)
ram_display_mode   = settings.get("ram_display_mode", "percent")
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

    # Server ready
    if DONE_RE.search(clean):
        server_ready = True
        app.after(0, show_toast, "Server is ready!", T["start"])
        return ('log', clean)

    # TPS (spark)
    tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
    if tps:
        perf["tps"] = tps.group(1)
        return None

    # Latency — try three different formats
    lat = LATENCY_RE.search(clean) or LATENCY_RE2.search(clean) or LATENCY_RE3.search(clean)
    if lat:
        try:
            pings = [int(m[1]) for m in
                     (LATENCY_RE.findall(clean) or
                      LATENCY_RE2.findall(clean) or
                      LATENCY_RE3.findall(clean))]
            if pings:
                avg = sum(pings) // len(pings)
                perf["latency"] = f"{avg} ms"
        except:
            pass
        return None

    # Player count + name list from /list
    pl = PLAYER_RE.search(clean)
    if pl:
        player_count = int(pl.group(1))
        perf["players"] = str(player_count)
        # Also try to extract names from same line
        nm = LIST_NAMES_RE.search(clean)
        if nm:
            raw_names = nm.group(1).strip()
            if raw_names and raw_names not in ("", "online:"):
                names = [n.strip() for n in raw_names.split(",") if n.strip()]
                now = datetime.now().strftime("%H:%M")
                for n in names:
                    if n not in online_players:
                        online_players[n] = now
                # Remove stale players not in this list
                for gone in [k for k in online_players if k not in names]:
                    online_players.pop(gone, None)
        return None

    # Chat
    chat = CHAT_RE.search(clean)
    if chat:
        return ('chat', f"[CHAT] {chat.group(1)}: {chat.group(2)}")

    # Join
    join = JOIN_RE.search(clean)
    if join:
        name = join.group(1)
        player_count += 1
        perf["players"] = str(player_count)
        online_players[name] = datetime.now().strftime("%H:%M")
        return ('event', f">> {name} joined")

    # Leave
    leave = LEAVE_RE.search(clean)
    if leave:
        name = leave.group(1)
        player_count = max(0, player_count - 1)
        perf["players"] = str(player_count)
        online_players.pop(name, None)
        return ('event', f"<< {name} left")

    # Death
    if DEATH_RE.search(clean):
        return ('event', f"[DEATH] {clean}")

    return ('log', clean)

# ── App window ────────────────────────────────────────────
app = ctk.CTk()
app.title("MCSC")
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
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'java' in p.info['name'].lower():
                if 'server.jar' in ' '.join(p.info['cmdline'] or []):
                    return p
        except: pass
    return None

def perf_loop():
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
    rebuild_ui()

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

# ── UI ────────────────────────────────────────────────────
def build_ui():
    global status_dot, status_lbl, e_path, e_repo, e_java
    global btn_start, btn_stop, btn_sync

    is_fs = app.attributes("-fullscreen")

    # ── Top bar ───────────────────────────────────────────
    top = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0)
    top.pack(fill="x")
    ctk.CTkLabel(top, text="MCSC",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=16, pady=10)

    # Theme picker in top bar
    tm_menu = ctk.CTkOptionMenu(top, values=list(THEMES.keys()),
                                command=apply_theme,
                                font=ctk.CTkFont(size=11), width=160, height=28,
                                fg_color=T["bg"], button_color=T["border"],
                                button_hover_color=T["muted"], text_color=T["text"],
                                dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                                dropdown_hover_color=T["border"])
    tm_menu.set(current_theme_name)
    tm_menu.pack(side="left", padx=(0, 6), pady=8)

    # ⚙ Settings button in top bar
    def open_settings_window():
        win = ctk.CTkToplevel(app)
        win.title("Settings")
        win.geometry("640x680")
        win.resizable(True, True)
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        try:
            ax = app.winfo_x() + (app.winfo_width()  - 640) // 2
            ay = app.winfo_y() + (app.winfo_height() - 680) // 2
            win.geometry(f"640x680+{ax}+{ay}")
        except: pass
        build_settings_tab(win)

    ctk.CTkButton(top, text="⚙  Settings", width=100, height=28,
                  font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=open_settings_window).pack(side="left", padx=(0, 8), pady=8)

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

    tab_btns = {}

    def show_tab(name):
        for f in [dashboard_frame, network_frame, serverinfo_frame]:
            f.pack_forget()
        for n, b in tab_btns.items():
            b.configure(fg_color="transparent", text_color=T["muted"])
        frames = {"dashboard": dashboard_frame, "network": network_frame,
                  "serverinfo": serverinfo_frame}
        frames[name].pack(fill="both", expand=True)
        tab_btns[name].configure(fg_color=T["sync"], text_color="#000")

    for key, label in [("dashboard","Dashboard"), ("network","Network & IPs"),
                       ("serverinfo","Server Info")]:
        b = ctk.CTkButton(tab_bar, text=label, width=120, height=30,
                          font=ctk.CTkFont(size=12), corner_radius=6,
                          fg_color="transparent", text_color=T["muted"],
                          hover_color=T["border"],
                          command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=(8 if key=="dashboard" else 2, 2), pady=6)
        tab_btns[key] = b

    build_dashboard(dashboard_frame, is_fs)
    build_network_tab(network_frame)
    build_server_info_tab(serverinfo_frame)

    show_tab("dashboard")

# ── Dashboard ─────────────────────────────────────────────
def build_dashboard(parent, is_fs):
    global btn_start, btn_stop, btn_sync
    global log_box, chat_box, cmd_entry, chat_toggle_btn

    if not is_fs:
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
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

    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

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
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

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
def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    s    = load_settings()
    path = s.get("srv_path", SRV_PATH)
    java = s.get("java_path", JAVA_PATH)
    repo = s.get("repo_url", REPO_URL)
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
    if upload_on_stop:
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
build_ui()
if auto_upload: schedule_auto_upload()

def _splash():
    lines = [
        "",
        "  ██  ████  ██  ██ ████  ████  ████ ██████",
        "  ██ ██  ██ ██  ██ ██   ██  ██ ██  ██  ██ ",
        "  ██ ██  ██ ██  ██ ████ ██████ ██  ██  ██ ",
        "  ██ ██  ██ ██  ██ ██   ██  ██ ██  ██  ██ ",
        "  ██  ████   ████  ████ ██  ██ ████    ██ ",
        "",
        f"  GamerMahir07's MCSC — Minecraft Server Controller",
        f"  Theme: {current_theme_name}  |  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}",
        f"  Auto-upload: {'ON' if auto_upload else 'OFF'}  |  Upload on stop: {'ON' if upload_on_stop else 'OFF'}",
        "",
    ]
    for line in lines: log(line)
    if is_first_launch: app.after(200, show_first_launch_dialog)

app.after(300, _splash)
app.mainloop()
