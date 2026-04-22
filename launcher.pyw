import customtkinter as ctk
import subprocess
import threading
import json
import os
import ctypes
import re
from datetime import datetime
import psutil

CREATE_NO_WINDOW = 0x08000000

SRV_PATH = r"C:\Users\DigitalComputer\Desktop\mc"
JAVA_PATH = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe"
REPO_URL  = "https://github.com/GamerMahir07/minecraft-server.git"

THEMES = {
    "Dark (Default)": {
        "appearance": "dark",
        "bg": "#0d0d0d", "card": "#1a1a1a", "border": "#2a2a2a",
        "text": "#e0e0e0", "muted": "#555555",
        "start": "#22c55e", "stop": "#ef4444", "sync": "#60a5fa", "handoff": "#f59e0b",
    },
    "Midnight Blue": {
        "appearance": "dark",
        "bg": "#0a0f1e", "card": "#111827", "border": "#1e3a5f",
        "text": "#e2e8f0", "muted": "#4a6080",
        "start": "#34d399", "stop": "#f87171", "sync": "#818cf8", "handoff": "#fbbf24",
    },
    "Light": {
        "appearance": "light",
        "bg": "#f5f5f5", "card": "#ffffff", "border": "#e0e0e0",
        "text": "#1a1a1a", "muted": "#888888",
        "start": "#16a34a", "stop": "#dc2626", "sync": "#2563eb", "handoff": "#d97706",
    },
    "Creeper Green": {
        "appearance": "dark",
        "bg": "#0a1a0a", "card": "#0f2a0f", "border": "#1a4a1a",
        "text": "#c8f0c8", "muted": "#3a6a3a",
        "start": "#4ade80", "stop": "#f87171", "sync": "#86efac", "handoff": "#fde047",
    },
    "Nether Red": {
        "appearance": "dark",
        "bg": "#000000", "card": "#1a0000", "border": "#6a0000",
        "text": "#ff4444", "muted": "#8b0000",
        "start": "#ff6b6b", "stop": "#ff0000", "sync": "#ff8c8c", "handoff": "#ffd700",
    },
    "Ocean": {
        "appearance": "dark",
        "bg": "#020e1a", "card": "#051929", "border": "#0a3050",
        "text": "#cce8ff", "muted": "#2a5a7a",
        "start": "#22d3ee", "stop": "#f87171", "sync": "#38bdf8", "handoff": "#a78bfa",
    },
    "Sunset": {
        "appearance": "light",
        "bg": "#fff7ed", "card": "#ffffff", "border": "#fed7aa",
        "text": "#1c0a00", "muted": "#9a6030",
        "start": "#16a34a", "stop": "#e11d48", "sync": "#7c3aed", "handoff": "#ea580c",
    },
    "Obsidian": {
        "appearance": "dark",
        "bg": "#080808", "card": "#101010", "border": "#1e1e2e",
        "text": "#cdd6f4", "muted": "#45475a",
        "start": "#a6e3a1", "stop": "#f38ba8", "sync": "#89b4fa", "handoff": "#fab387",
    },
    "Ender Night": {
        "appearance": "dark",
        "bg": "#000000", "card": "#0d0010", "border": "#3b0060",
        "text": "#e8b4ff", "muted": "#6a2a8a",
        "start": "#bf7fff", "stop": "#ff5f87", "sync": "#d68fff", "handoff": "#ffb347",
    },
    "Arctic": {
        "appearance": "light",
        "bg": "#eef4fb", "card": "#ffffff", "border": "#b8d4f0",
        "text": "#0d2137", "muted": "#6a90b0",
        "start": "#0ea5e9", "stop": "#e11d48", "sync": "#6366f1", "handoff": "#f59e0b",
    },
    "Forest": {
        "appearance": "dark",
        "bg": "#0d1a0d", "card": "#142414", "border": "#254025",
        "text": "#d4edda", "muted": "#4a7a4a",
        "start": "#86efac", "stop": "#fca5a5", "sync": "#6ee7b7", "handoff": "#fde68a",
    },
    "Rose Gold": {
        "appearance": "light",
        "bg": "#fff0f3", "card": "#ffffff", "border": "#f4c2cb",
        "text": "#3a0a14", "muted": "#b06070",
        "start": "#e11d48", "stop": "#9f1239", "sync": "#db2777", "handoff": "#c2410c",
    },
    "Dracula": {
        "appearance": "dark",
        "bg": "#282a36", "card": "#313442", "border": "#44475a",
        "text": "#f8f8f2", "muted": "#6272a4",
        "start": "#50fa7b", "stop": "#ff5555", "sync": "#8be9fd", "handoff": "#ffb86c",
    },
    "Lava": {
        "appearance": "dark",
        "bg": "#120500", "card": "#1e0a00", "border": "#5a1a00",
        "text": "#ffe8d0", "muted": "#7a3a10",
        "start": "#ff7c00", "stop": "#ff3300", "sync": "#ffaa00", "handoff": "#ffdd00",
    },
    "Sand": {
        "appearance": "light",
        "bg": "#f5e6c8", "card": "#fdf3e0", "border": "#c8a96e",
        "text": "#3d2b00", "muted": "#8a6a30",
        "start": "#5a8a00", "stop": "#c0392b", "sync": "#1a6b8a", "handoff": "#c07000",
    },
    "Void": {
        "appearance": "dark",
        "bg": "#000000", "card": "#0a0a0a", "border": "#1a1a1a",
        "text": "#aaaaaa", "muted": "#333333",
        "start": "#444444", "stop": "#666666", "sync": "#555555", "handoff": "#777777",
    },
    "Carbon": {
        "appearance": "dark",
        "bg": "#1a1a2e", "card": "#16213e", "border": "#0f3460",
        "text": "#e0e0e0", "muted": "#4a4a6a",
        "start": "#00c896", "stop": "#e94560", "sync": "#4d9fff", "handoff": "#f5a623",
    },
    "Lavender": {
        "appearance": "light",
        "bg": "#f0eeff", "card": "#ffffff", "border": "#c5b8ff",
        "text": "#1a0050", "muted": "#7060a0",
        "start": "#5b21b6", "stop": "#db2777", "sync": "#4f46e5", "handoff": "#d97706",
    },
    "Mocha": {
        "appearance": "dark",
        "bg": "#1c1410", "card": "#2a1f18", "border": "#4a3428",
        "text": "#f0dece", "muted": "#7a5a48",
        "start": "#c8a86e", "stop": "#e05050", "sync": "#90b8d0", "handoff": "#e8c060",
    },
    "Sakura": {
        "appearance": "light",
        "bg": "#fff0f5", "card": "#ffffff", "border": "#ffb8cc",
        "text": "#3a0020", "muted": "#c06080",
        "start": "#be185d", "stop": "#e11d48", "sync": "#9d174d", "handoff": "#f59e0b",
    },
    "Matrix": {
        "appearance": "dark",
        "bg": "#000000", "card": "#001400", "border": "#004400",
        "text": "#00ff41", "muted": "#006600",
        "start": "#00ff41", "stop": "#ff0000", "sync": "#00cc33", "handoff": "#ffff00",
    },
    "Nord": {
        "appearance": "dark",
        "bg": "#2e3440", "card": "#3b4252", "border": "#434c5e",
        "text": "#eceff4", "muted": "#4c566a",
        "start": "#a3be8c", "stop": "#bf616a", "sync": "#88c0d0", "handoff": "#ebcb8b",
    },
    "Solarized": {
        "appearance": "light",
        "bg": "#fdf6e3", "card": "#eee8d5", "border": "#93a1a1",
        "text": "#073642", "muted": "#657b83",
        "start": "#859900", "stop": "#dc322f", "sync": "#268bd2", "handoff": "#b58900",
    },
    "Gruvbox": {
        "appearance": "dark",
        "bg": "#282828", "card": "#3c3836", "border": "#504945",
        "text": "#ebdbb2", "muted": "#7c6f64",
        "start": "#b8bb26", "stop": "#fb4934", "sync": "#83a598", "handoff": "#fabd2f",
    },
    "CB: Blue & Orange": {
        "appearance": "light",
        "bg": "#f7f7f7", "card": "#ffffff", "border": "#cccccc",
        "text": "#000000", "muted": "#767676",
        "start": "#0072b2", "stop": "#d55e00", "sync": "#56b4e9", "handoff": "#e69f00",
    },
    "CB: Dark Blue & Orange": {
        "appearance": "dark",
        "bg": "#111111", "card": "#1e1e1e", "border": "#333333",
        "text": "#ffffff", "muted": "#888888",
        "start": "#56b4e9", "stop": "#d55e00", "sync": "#0072b2", "handoff": "#e69f00",
    },
    "CB: Green & Purple": {
        "appearance": "light",
        "bg": "#f5f5f5", "card": "#ffffff", "border": "#cccccc",
        "text": "#000000", "muted": "#767676",
        "start": "#009e73", "stop": "#cc79a7", "sync": "#0072b2", "handoff": "#f0e442",
    },
    "CB: High Contrast": {
        "appearance": "light",
        "bg": "#ffffff", "card": "#f0f0f0", "border": "#000000",
        "text": "#000000", "muted": "#444444",
        "start": "#0000ff", "stop": "#ff0000", "sync": "#007700", "handoff": "#ff8800",
    },
    "CB: Dark High Contrast": {
        "appearance": "dark",
        "bg": "#000000", "card": "#1a1a1a", "border": "#ffffff",
        "text": "#ffffff", "muted": "#aaaaaa",
        "start": "#ffff00", "stop": "#ff6600", "sync": "#00ffff", "handoff": "#ff99ff",
    },
    "CB: Tol Muted": {
        "appearance": "light",
        "bg": "#f8f4f0", "card": "#ffffff", "border": "#bbaabb",
        "text": "#221122", "muted": "#887799",
        "start": "#44aa99", "stop": "#cc6677", "sync": "#88ccee", "handoff": "#ddcc77",
    },
    "CB: Tol Dark": {
        "appearance": "dark",
        "bg": "#221122", "card": "#332244", "border": "#554466",
        "text": "#eeddff", "muted": "#887799",
        "start": "#44aa99", "stop": "#cc6677", "sync": "#88ccee", "handoff": "#ddcc77",
    },
    "CB: Monochrome": {
        "appearance": "light",
        "bg": "#ffffff", "card": "#f0f0f0", "border": "#999999",
        "text": "#000000", "muted": "#666666",
        "start": "#222222", "stop": "#777777", "sync": "#444444", "handoff": "#555555",
    },
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_settings():
    try:
        with open(SETTINGS_FILE) as f: return json.load(f)
    except: return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f)
    except: pass

settings           = load_settings()
current_theme_name = settings.get("theme", "Dark (Default)")
show_chat          = settings.get("show_chat", True)
log_left           = settings.get("log_left", False)
show_perf          = settings.get("show_perf", True)
fullscreen         = settings.get("fullscreen", False)
auto_upload        = settings.get("auto_upload", False)
auto_upload_mins   = settings.get("auto_upload_mins", 10)
T                  = THEMES[current_theme_name]

ctk.set_appearance_mode(T["appearance"])
ctk.set_default_color_theme("dark-blue")

server_proc   = None
server_stdin  = None
server_pid    = None
perf_running  = False
server_ready  = False
player_count  = 0
auto_upload_timer = None

perf = {
    "ram_used": "—", "ram_pct": "—", "ram_srv": "—",
    "cpu_sys": "—",  "cpu_srv": "—",
    "tps": "—",      "latency": "—", "players": "0",
    "uptime": "—",   "threads": "—",
}
server_start_time = None

# ── Regex ─────────────────────────────────────────────────
CHAT_RE    = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE    = re.compile(r'^(\w+) joined the game', re.IGNORECASE)
LEAVE_RE   = re.compile(r'^(\w+) lost connection:', re.IGNORECASE)
DEATH_RE   = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.IGNORECASE)
STRIP_RE   = re.compile(r'^\[[\d:]+\]\s*\[.*?(?:INFO|WARN|ERROR).*?\]:\s*', re.IGNORECASE)
DONE_RE    = re.compile(r'Done \([\d.]+s\)!', re.IGNORECASE)
SPARK_TPS  = re.compile(r'TPS from last 1m, 5m, 15m: ([\d.]+)', re.IGNORECASE)
TPS_RE2    = re.compile(r'Current TPS[:\s]+([\d.]+)', re.IGNORECASE)
PLAYER_RE  = re.compile(r'There are (\d+) of a max of \d+ players', re.IGNORECASE)
LIST_RE    = re.compile(r'There are (\d+)/\d+ players', re.IGNORECASE)
LATENCY_RE = re.compile(r'Average latency.*?(\d+)', re.IGNORECASE)
PING_RE    = re.compile(r'(\w+).*?(\d+)ms', re.IGNORECASE)

def parse_server_line(raw):
    global player_count, server_ready
    clean = STRIP_RE.sub('', raw).strip()
    if not clean: return None
    if DONE_RE.search(clean):
        server_ready = True
        return ('log', clean)
    tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
    if tps: perf["tps"] = tps.group(1); return None
    lat = LATENCY_RE.search(clean)
    if lat: perf["latency"] = f"{lat.group(1)} ms"; return None
    pl = PLAYER_RE.search(clean) or LIST_RE.search(clean)
    if pl:
        player_count = int(pl.group(1))
        perf["players"] = str(player_count)
        return None
    chat = CHAT_RE.search(clean)
    if chat: return ('chat', f"💬 {chat.group(1)}: {chat.group(2)}")
    join = JOIN_RE.search(clean)
    if join:
        player_count += 1; perf["players"] = str(player_count)
        return ('event', f"→ {join.group(1)} joined")
    leave = LEAVE_RE.search(clean)
    if leave:
        player_count = max(0, player_count - 1); perf["players"] = str(player_count)
        return ('event', f"← {leave.group(1)} left")
    if DEATH_RE.search(clean): return ('event', f"💀 {clean}")
    return ('log', clean)

# ── App ───────────────────────────────────────────────────
app = ctk.CTk()
app.title("MC Server Controller")
app.geometry("900x680")
app.resizable(True, True)
app.configure(fg_color=T["bg"])

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gamermahir07.mcserver.launcher.1')
try:
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    app.iconbitmap(ico)
except: pass

if fullscreen:
    app.after(100, lambda: app.attributes("-fullscreen", True))

# ── Theme / layout ────────────────────────────────────────
def apply_theme(name):
    global T, current_theme_name
    current_theme_name = name; T = THEMES[name]
    s = load_settings(); s["theme"] = name; save_settings(s)
    ctk.set_appearance_mode(T["appearance"])
    app.configure(fg_color=T["bg"])
    rebuild_ui()

def rebuild_ui():
    for w in app.winfo_children(): w.destroy()
    build_ui()

def swap_layout():
    global log_left
    log_left = not log_left
    s = load_settings(); s["log_left"] = log_left; save_settings(s)
    rebuild_ui()

def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    s = load_settings(); s["fullscreen"] = fullscreen; save_settings(s)
    app.attributes("-fullscreen", fullscreen)
    if not fullscreen: app.geometry("900x680")
    rebuild_ui()

def toggle_perf():
    global show_perf
    show_perf = not show_perf
    s = load_settings(); s["show_perf"] = show_perf; save_settings(s)
    rebuild_ui()

def toggle_chat():
    global show_chat
    show_chat = not show_chat
    s = load_settings(); s["show_chat"] = show_chat; save_settings(s)
    chat_toggle_btn.configure(text="Hide" if show_chat else "Show")
    if show_chat:
        chat_box.configure(height=110)
        chat_box.pack(fill="x", padx=8, pady=(4,8))
    else:
        chat_box.pack_forget()
        chat_box.configure(height=0)

# ── Auto upload ───────────────────────────────────────────
def open_auto_upload_config():
    win = ctk.CTkToplevel(app)
    win.title("Auto Upload Config")
    win.geometry("300x200")
    win.resizable(False, False)
    win.configure(fg_color=T["bg"])
    win.grab_set()
    ctk.CTkLabel(win, text="AUTO UPLOAD", font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["text"]).pack(pady=(18,4))
    ctk.CTkLabel(win, text="Automatically push files to GitHub on a timer.",
                 font=ctk.CTkFont(size=11), text_color=T["muted"], wraplength=260).pack(pady=(0,14))
    row = ctk.CTkFrame(win, fg_color="transparent")
    row.pack(fill="x", padx=24, pady=(0,10))
    ctk.CTkLabel(row, text="Interval (minutes):", font=ctk.CTkFont(size=12),
                 text_color=T["text"]).pack(side="left")
    mins_var = ctk.StringVar(value=str(auto_upload_mins))
    ctk.CTkEntry(row, width=56, height=28, textvariable=mins_var,
                 font=ctk.CTkFont(size=12, family="Consolas"),
                 fg_color=T["card"], border_color=T["border"],
                 text_color=T["text"]).pack(side="right")
    def save_and_close():
        set_auto_upload_mins(mins_var.get())
        win.destroy(); rebuild_ui()
    def toggle_and_close():
        toggle_auto_upload(); win.destroy()
    btns = ctk.CTkFrame(win, fg_color="transparent")
    btns.pack(fill="x", padx=24)
    ctk.CTkButton(btns, text="Turn OFF" if auto_upload else "Turn ON",
                  height=30, font=ctk.CTkFont(size=12),
                  fg_color=T["stop"] if auto_upload else T["start"],
                  hover_color=T["stop"] if auto_upload else T["start"],
                  text_color="#000", command=toggle_and_close).pack(side="left", expand=True, padx=(0,4))
    ctk.CTkButton(btns, text="Save", height=30, font=ctk.CTkFont(size=12),
                  fg_color=T["sync"], hover_color=T["sync"],
                  text_color="#000", command=save_and_close).pack(side="left", expand=True)

def toggle_auto_upload():
    global auto_upload
    auto_upload = not auto_upload
    s = load_settings(); s["auto_upload"] = auto_upload; save_settings(s)
    if auto_upload:
        log(f"Auto-upload enabled every {auto_upload_mins} min.")
        schedule_auto_upload()
    else:
        log("Auto-upload disabled.")
        if auto_upload_timer: auto_upload_timer.cancel()
    rebuild_ui()

def set_auto_upload_mins(val):
    global auto_upload_mins
    try:
        auto_upload_mins = max(1, int(float(val)))
        s = load_settings(); s["auto_upload_mins"] = auto_upload_mins; save_settings(s)
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
    app.after(0, log, "── Auto-upload ───────────────────")
    try: path = e_path.get(); repo = e_repo.get()
    except: path = SRV_PATH; repo = REPO_URL
    run_cmd("git remote set-url origin " + repo, cwd=path)
    run_cmd("git add .", cwd=path)
    result = subprocess.run(
        f'git commit -m "Auto-upload {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
        shell=True, cwd=path, capture_output=True, text=True,
        creationflags=CREATE_NO_WINDOW)
    if "nothing to commit" in result.stdout or result.returncode != 0:
        app.after(0, log, "  Auto-upload: nothing new to commit.")
    else:
        run_cmd("git push origin main", cwd=path)
        app.after(0, log, "  Auto-upload complete.")
    schedule_auto_upload()

# ── Build UI ──────────────────────────────────────────────
perf_labels = {}

def build_ui():
    global status_dot, status_lbl, e_path, e_repo, e_java
    global btn_start, btn_stop, btn_sync, btn_handoff
    global log_box, chat_box, cmd_entry, chat_toggle_btn

    is_fs = app.attributes("-fullscreen")

    # Top bar
    top = ctk.CTkFrame(app, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(12,0))
    ctk.CTkLabel(top, text="⛏  MC Server Controller",
                 font=ctk.CTkFont(size=17, weight="bold"),
                 text_color=T["text"]).pack(side="left")
    status_dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=13), text_color=T["stop"])
    status_dot.pack(side="right", padx=(0,4))
    status_lbl = ctk.CTkLabel(top, text="Stopped", font=ctk.CTkFont(size=12), text_color=T["muted"])
    status_lbl.pack(side="right", padx=(0,8))
    ctk.CTkButton(top, text="⛶ " + ("Exit FS" if is_fs else "Fullscreen"),
                  width=90, height=24, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"],
                  hover_color=T["border"], command=toggle_fullscreen).pack(side="right", padx=(0,6))
    ctk.CTkButton(top, text="📊 " + ("Hide Perf" if show_perf else "Show Perf"),
                  width=90, height=24, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1,
                  border_color=T["sync"], text_color=T["sync"],
                  hover_color=T["border"], command=toggle_perf).pack(side="right", padx=(0,6))
    ctk.CTkButton(top, text="↑ Auto Upload",
                  width=100, height=24, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1,
                  border_color=T["start"] if auto_upload else T["border"],
                  text_color=T["start"] if auto_upload else T["muted"],
                  hover_color=T["border"], command=open_auto_upload_config).pack(side="right", padx=(0,6))
    tm = ctk.CTkOptionMenu(top, values=list(THEMES.keys()), command=apply_theme,
                           font=ctk.CTkFont(size=12), width=150,
                           fg_color=T["card"], button_color=T["border"],
                           button_hover_color=T["muted"], text_color=T["text"],
                           dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                           dropdown_hover_color=T["border"])
    tm.set(current_theme_name)
    tm.pack(side="right", padx=(0,8))

    # Main scrollable or fixed container
    if not is_fs:
        scroll = ctk.CTkScrollableFrame(app, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=(8,0))
        scroll.columnconfigure(0, weight=1)
        main_container = scroll
    else:
        main_container = ctk.CTkFrame(app, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=0, pady=(8,0))
        main_container.columnconfigure(0, weight=1)

    # Body
    body = ctk.CTkFrame(main_container, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=(0,12))
    ctrl_col = 1 if log_left else 0
    log_col  = 0 if log_left else 1
    body.columnconfigure(ctrl_col, weight=0, minsize=360)
    body.columnconfigure(log_col,  weight=1)
    body.rowconfigure(0, weight=1)

    # Controls
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=ctrl_col, sticky="nsew", padx=(10,0) if log_left else (0,10))

    cfg = ctk.CTkFrame(left, fg_color=T["card"], border_color=T["border"], border_width=1)
    cfg.pack(fill="x", pady=(0,8))
    ctk.CTkLabel(cfg, text="CONFIGURATION", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,4))

    def cfg_row(parent, label, default):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(row, text=label, width=64, anchor="w",
                     font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")
        e = ctk.CTkEntry(row, font=ctk.CTkFont(size=10, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"], text_color=T["text"], height=28)
        e.insert(0, default)
        e.pack(side="left", fill="x", expand=True)
        return e

    e_path = cfg_row(cfg, "Path",     SRV_PATH)
    e_repo = cfg_row(cfg, "Repo URL", REPO_URL)
    e_java = cfg_row(cfg, "Java",     JAVA_PATH)
    ctk.CTkFrame(cfg, height=6, fg_color="transparent").pack()

    def make_btn(parent, text, desc, color, cmd):
        f = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(inner, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=color, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text=desc, font=ctk.CTkFont(size=10), text_color=T["muted"],
                     anchor="w", wraplength=280, justify="left").pack(anchor="w")
        b = ctk.CTkButton(inner, text="Run", width=56, height=22,
                          font=ctk.CTkFont(size=11), fg_color=color,
                          hover_color=color, text_color="#000", command=cmd)
        b.pack(anchor="e", pady=(4,0))
        return b

    btn_start   = make_btn(left, "▶  Start Server",  "Git pull → launch with Aikar JVM flags",      T["start"],   lambda: threading.Thread(target=start_server, daemon=True).start())
    btn_stop    = make_btn(left, "■  Stop Server",   "Kill Java process → push world to GitHub",    T["stop"],    lambda: threading.Thread(target=stop_server,  daemon=True).start())
    btn_sync    = make_btn(left, "↑  Sync & Upload", "Git add all → commit 'Manual Sync' → push",   T["sync"],    lambda: threading.Thread(target=sync_git,    daemon=True).start())
    btn_handoff = make_btn(left, "⇄  Hand Off",      "Stop → push world → friend pulls and starts", T["handoff"], lambda: threading.Thread(target=handoff,     daemon=True).start())

    # Log panel
    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=log_col, sticky="nsew")
    right.rowconfigure(0, weight=1)
    right.rowconfigure(1, weight=0)
    right.rowconfigure(2, weight=0)
    right.columnconfigure(0, weight=1)

    lf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    lf.grid(row=0, column=0, sticky="nsew", pady=(0,6))
    lt = ctk.CTkFrame(lf, fg_color="transparent")
    lt.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG", font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")
    ctk.CTkButton(lt, text="⇄ Swap", width=54, height=20, font=ctk.CTkFont(size=10),
                  fg_color="transparent", border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=swap_layout).pack(side="right", padx=(4,0))
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

    cf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    cf.grid(row=1, column=0, sticky="ew", pady=(0,6))
    ct = ctk.CTkFrame(cf, fg_color="transparent")
    ct.pack(fill="x", padx=12, pady=(8,0))
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
    if show_chat:
        chat_box.pack(fill="x", padx=8, pady=(4,8))

    cmdf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    cmdf.grid(row=2, column=0, sticky="ew")
    cmdf_i = ctk.CTkFrame(cmdf, fg_color="transparent")
    cmdf_i.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(cmdf_i, text="/", font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=T["muted"], width=14).pack(side="left")
    cmd_entry = ctk.CTkEntry(cmdf_i, font=ctk.CTkFont(size=12, family="Consolas"),
                             fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                             placeholder_text="type a command or chat message...", height=32)
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(4,8))
    cmd_entry.bind("<Return>", lambda e: send_command())
    ctk.CTkButton(cmdf_i, text="Send", width=60, height=32,
                  font=ctk.CTkFont(size=12), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=send_command).pack(side="left")

    if show_perf:
        build_perf_panel(main_container if not is_fs else app, is_fs)

def build_perf_panel(parent, pinned_bottom=False):
    global perf_labels
    perf_labels = {}
    pf = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"], border_width=1)
    if pinned_bottom:
        pf.pack(side="bottom", fill="x", padx=20, pady=(0,12))
    else:
        pf.pack(fill="x", padx=20, pady=(0,12))
    ph = ctk.CTkFrame(pf, fg_color="transparent")
    ph.pack(fill="x", padx=12, pady=(8,4))
    ctk.CTkLabel(ph, text="SERVER PERFORMANCE", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left")
    ctk.CTkLabel(ph, text="Updates every 2s", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="right")
    grid = ctk.CTkFrame(pf, fg_color="transparent")
    grid.pack(fill="x", padx=12, pady=(0,10))
    stats = [
        ("TPS",           "tps",      "Ticks/sec (20 = perfect)"),
        ("Players",       "players",  "Online players"),
        ("Avg Latency",   "latency",  "Avg player-to-server ping"),
        ("Uptime",        "uptime",   "Server uptime"),
        ("RAM (Total)",   "ram_used", "System RAM used"),
        ("RAM %",         "ram_pct",  "System RAM usage %"),
        ("RAM (Server)",  "ram_srv",  "Java process RAM"),
        ("CPU (System)",  "cpu_sys",  "Total CPU usage"),
        ("CPU (Server)",  "cpu_srv",  "Java process CPU"),
        ("Threads",       "threads",  "Java thread count"),
    ]
    for i, (label, key, _) in enumerate(stats):
        col = i % 5; row = i // 5
        cell = ctk.CTkFrame(grid, fg_color=T["bg"], border_color=T["border"],
                            border_width=1, corner_radius=6)
        cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        grid.columnconfigure(col, weight=1)
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=10),
                     text_color=T["muted"]).pack(pady=(6,0))
        lbl = ctk.CTkLabel(cell, text=perf[key],
                           font=ctk.CTkFont(size=14, weight="bold"),
                           text_color=T["text"])
        lbl.pack(pady=(0,6))
        perf_labels[key] = lbl

def update_perf_labels():
    for key, lbl in perf_labels.items():
        try:
            val = perf[key]
            if key == "tps":
                try:
                    t = float(val)
                    color = T["start"] if t >= 18 else T["handoff"] if t >= 15 else T["stop"]
                except: color = T["text"]
                lbl.configure(text=val, text_color=color)
            elif key in ("cpu_sys", "cpu_srv", "ram_pct"):
                try:
                    n = float(str(val).replace("%",""))
                    color = T["start"] if n < 60 else T["handoff"] if n < 85 else T["stop"]
                except: color = T["text"]
                lbl.configure(text=val, text_color=color)
            elif key == "latency":
                try:
                    n = float(str(val).replace("ms","").strip())
                    color = T["start"] if n < 60 else T["handoff"] if n < 120 else T["stop"]
                except: color = T["text"]
                lbl.configure(text=val, text_color=color)
            else:
                lbl.configure(text=val, text_color=T["text"])
        except: pass

# ── Performance polling ───────────────────────────────────
def find_java_proc():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'java' in proc.info['name'].lower():
                if 'server.jar' in ' '.join(proc.info['cmdline'] or []):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    return None

def perf_loop():
    global perf_running
    perf_running = True
    java_proc = None
    poll_tick = 0
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
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    java_proc = None
                    perf["ram_srv"] = "—"; perf["cpu_srv"] = "—"; perf["threads"] = "—"
            else:
                perf["ram_srv"] = "—"; perf["cpu_srv"] = "—"; perf["threads"] = "—"
            if server_start_time:
                secs = int((datetime.now()-server_start_time).total_seconds())
                h,r = divmod(secs,3600); m,s = divmod(r,60)
                perf["uptime"] = f"{h:02d}:{m:02d}:{s:02d}"
            else:
                perf["uptime"] = "—"
            if server_ready and server_stdin:
                try:
                    if poll_tick % 5  == 0: server_stdin.write("tps\n");  server_stdin.flush()
                    if poll_tick % 10 == 0: server_stdin.write("ping\n"); server_stdin.flush()
                    if poll_tick % 15 == 0: server_stdin.write("list\n"); server_stdin.flush()
                except: pass
            poll_tick += 1
            app.after(0, update_perf_labels)
        except: pass
        import time; time.sleep(2)

# ── Helpers ───────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        log_box.configure(state="normal")
        log_box.insert("end", f"[{ts}]  {msg}\n")
        log_box.configure(state="disabled")
        log_box.see("end")
    except: pass

def log_chat(msg):
    if not show_chat: return
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        chat_box.configure(state="normal")
        chat_box.insert("end", f"[{ts}]  {msg}\n")
        chat_box.configure(state="disabled")
        chat_box.see("end")
    except: pass

def set_status(txt, color):
    try: status_lbl.configure(text=txt); status_dot.configure(text_color=color)
    except: pass

def send_command():
    cmd = cmd_entry.get().strip()
    if not cmd: return
    cmd_entry.delete(0, "end")
    if server_stdin is None:
        log("Server is not running — start it first."); return
    try:
        server_stdin.write(cmd + "\n"); server_stdin.flush()
        log(f"→ {cmd}")
    except Exception as ex:
        log(f"Failed to send command: {ex}")

def run_cmd(cmd, cwd=None):
    log(f"$ {cmd}")
    try:
        proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                              text=True, creationflags=CREATE_NO_WINDOW)
        for l in proc.stdout.strip().splitlines(): log(f"  {l}")
        if proc.returncode != 0:
            for l in proc.stderr.strip().splitlines(): log(f"  {l}")
        return proc.returncode == 0
    except Exception as ex:
        log(str(ex)); return False

def set_all_buttons(state):
    for b in [btn_start, btn_stop, btn_sync, btn_handoff]:
        try: b.configure(state=state)
        except: pass

def read_server_output(proc):
    for raw in iter(proc.stdout.readline, ''):
        if not raw: break
        parsed = parse_server_line(raw)
        if parsed is None: continue
        cat, text = parsed
        if cat in ('chat','event'): app.after(0, log_chat, text)
        else: app.after(0, log, text)

# ── Actions ───────────────────────────────────────────────
def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    path, java = e_path.get(), e_java.get()
    set_status("Starting...", T["handoff"])
    log("── Start Server ──────────────────")
    run_cmd("git remote set-url origin " + e_repo.get(), cwd=path)
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
    server_stdin      = server_proc.stdin
    server_pid        = server_proc.pid
    server_start_time = datetime.now()
    server_ready      = False
    player_count      = 0
    perf["tps"] = "—"; perf["latency"] = "—"; perf["players"] = "0"
    threading.Thread(target=read_server_output, args=(server_proc,), daemon=True).start()
    if not perf_running:
        threading.Thread(target=perf_loop, daemon=True).start()
    set_status("Running", T["start"])
    log("Server is running! (PID " + str(server_proc.pid) + ")")
    btn_stop.configure(state="normal")

def stop_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready
    set_status("Stopping...", T["handoff"])
    log("── Stop Server ───────────────────")
    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except: pass
        server_stdin = None
    result = subprocess.run("taskkill /F /IM java.exe", shell=True, capture_output=True,
                            text=True, creationflags=CREATE_NO_WINDOW)
    log("  Java process killed." if result.returncode == 0 else "  Java was not running.")
    server_proc = None; server_pid = None; server_start_time = None
    server_ready = False; perf_running = False
    for k in ("tps","latency","players","uptime","ram_srv","cpu_srv","threads"):
        perf[k] = "—"
    path = e_path.get()
    log("Pushing world to GitHub...")
    run_cmd("git add world/ world_nether/ world_the_end/", cwd=path)
    commit = subprocess.run(
        f'git commit -m "World update {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
        shell=True, cwd=path, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if "nothing to commit" in commit.stdout or commit.returncode != 0:
        log("  World unchanged — nothing new to commit.")
    else:
        for l in commit.stdout.strip().splitlines(): log(f"  {l}")
        run_cmd("git push origin main", cwd=path)
    set_status("Stopped", T["stop"])
    log("Done.")
    set_all_buttons("normal")

def sync_git():
    set_all_buttons("disabled")
    path = e_path.get()
    set_status("Syncing...", T["handoff"])
    log("── Sync & Upload ─────────────────")
    run_cmd("git remote set-url origin " + e_repo.get(), cwd=path)
    run_cmd("git add .", cwd=path)
    run_cmd('git commit -m "Manual Sync"', cwd=path)
    ok = run_cmd("git push origin main", cwd=path)
    log("Upload complete!" if ok else "Push failed — check log above.")
    set_status("Stopped", T["stop"])
    set_all_buttons("normal")

def handoff():
    global server_stdin, server_pid, server_start_time, perf_running, server_ready
    set_all_buttons("disabled")
    path = e_path.get()
    set_status("Handing off...", T["handoff"])
    log("── Hand Off ──────────────────────")
    log("[1/3] Stopping server gracefully...")
    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except: pass
        server_stdin = None
    run_cmd("taskkill /F /IM java.exe")
    server_pid = None; server_start_time = None
    server_ready = False; perf_running = False
    for k in ("tps","latency","players","uptime","ram_srv","cpu_srv","threads"):
        perf[k] = "—"
    log("[2/3] Syncing world to GitHub...")
    run_cmd("git pull origin main --rebase", cwd=path)
    run_cmd("git add world/ world_nether/ world_the_end/", cwd=path)
    commit = subprocess.run(
        f'git commit -m "Handoff {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
        shell=True, cwd=path, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if "nothing to commit" not in commit.stdout and commit.returncode == 0:
        run_cmd("git push origin main", cwd=path)
    log("[3/3] Done! Tell your friend to start their launcher.")
    set_status("Handed off", T["handoff"])
    set_all_buttons("normal")

build_ui()
if auto_upload:
    schedule_auto_upload()
app.mainloop()