import customtkinter as ctk
import subprocess
import threading
import json
import os
import ctypes
import re
from datetime import datetime

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
        "bg": "#1a0a0a", "card": "#2a0f0f", "border": "#4a1a1a",
        "text": "#fde0d0", "muted": "#6a3a3a",
        "start": "#fb923c", "stop": "#f87171", "sync": "#fca5a5", "handoff": "#fcd34d",
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
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_settings():
    try:
        with open(SETTINGS_FILE) as f: return json.load(f)
    except: return {"theme": "Dark (Default)", "show_chat": True}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f)
    except: pass

settings = load_settings()
current_theme_name = settings.get("theme", "Dark (Default)")
show_chat = settings.get("show_chat", True)
T = THEMES[current_theme_name]

ctk.set_appearance_mode(T["appearance"])
ctk.set_default_color_theme("dark-blue")

server_proc  = None
server_stdin = None  # pipe to server process stdin

# ── Window ────────────────────────────────────────────────
app = ctk.CTk()
app.title("MC Server Controller")
app.geometry("900x680")
app.resizable(False, False)
app.configure(fg_color=T["bg"])

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gamermahir07.mcserver.launcher.1')
try:
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    app.iconbitmap(ico)
except: pass

# ── Theme ─────────────────────────────────────────────────
def apply_theme(name):
    global T, current_theme_name
    current_theme_name = name
    T = THEMES[name]
    s = load_settings(); s["theme"] = name; save_settings(s)
    ctk.set_appearance_mode(T["appearance"])
    app.configure(fg_color=T["bg"])
    rebuild_ui()

def rebuild_ui():
    for w in app.winfo_children(): w.destroy()
    build_ui()

# ── Patterns for server output ────────────────────────────
CHAT_RE    = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE    = re.compile(r'(\w+) joined the game')
LEAVE_RE   = re.compile(r'(\w+) left the game')
DEATH_RE   = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.IGNORECASE)
STRIP_RE   = re.compile(r'^\[[\d:]+\]\s*\[.*?(?:INFO|WARN|ERROR).*?\]:\s*', re.IGNORECASE)

def parse_server_line(raw):
    """Returns (category, display_text) or None to suppress."""
    clean = STRIP_RE.sub('', raw).strip()
    if not clean: return None
    chat = CHAT_RE.search(clean)
    if chat: return ('chat', f"💬 {chat.group(1)}: {chat.group(2)}")
    if JOIN_RE.search(clean):  return ('event', f"→ {JOIN_RE.search(clean).group(1)} joined")
    if LEAVE_RE.search(clean): return ('event', f"← {LEAVE_RE.search(clean).group(1)} left")
    if DEATH_RE.search(clean): return ('event', f"💀 {clean}")
    return ('log', clean)

# ── UI ────────────────────────────────────────────────────
def build_ui():
    global status_dot, status_lbl, e_path, e_repo, e_java
    global btn_start, btn_stop, btn_sync, btn_handoff
    global log_box, chat_box, cmd_entry, chat_toggle_btn

    # Top bar
    top = ctk.CTkFrame(app, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(16,0))
    ctk.CTkLabel(top, text="⛏  MC Server Controller",
                 font=ctk.CTkFont(size=17, weight="bold"),
                 text_color=T["text"]).pack(side="left")
    status_dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=13), text_color=T["stop"])
    status_dot.pack(side="right", padx=(0,4))
    status_lbl = ctk.CTkLabel(top, text="Stopped", font=ctk.CTkFont(size=12), text_color=T["muted"])
    status_lbl.pack(side="right", padx=(0,6))
    ctk.CTkLabel(top, text="Theme:", font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(side="right", padx=(0,6))
    tm = ctk.CTkOptionMenu(top, values=list(THEMES.keys()), command=apply_theme,
                           font=ctk.CTkFont(size=12), width=160,
                           fg_color=T["card"], button_color=T["border"],
                           button_hover_color=T["muted"], text_color=T["text"],
                           dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                           dropdown_hover_color=T["border"])
    tm.set(current_theme_name)
    tm.pack(side="right", padx=(0,12))

    # Body
    body = ctk.CTkFrame(app, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=(12,16))
    body.columnconfigure(0, weight=0, minsize=360)
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    # ── Left ──────────────────────────────────────────────
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0,10))

    cfg = ctk.CTkFrame(left, fg_color=T["card"], border_color=T["border"], border_width=1)
    cfg.pack(fill="x", pady=(0,8))
    ctk.CTkLabel(cfg, text="CONFIGURATION", font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,4))

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

    # ── Right ─────────────────────────────────────────────
    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")
    right.rowconfigure(0, weight=1)
    right.rowconfigure(1, weight=0)
    right.rowconfigure(2, weight=0)
    right.columnconfigure(0, weight=1)

    # Activity log
    lf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    lf.grid(row=0, column=0, sticky="nsew", pady=(0,6))
    lt = ctk.CTkFrame(lf, fg_color="transparent")
    lt.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG", font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")
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

    # Chat / server output box
    cf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    cf.grid(row=1, column=0, sticky="ew", pady=(0,6))
    ct = ctk.CTkFrame(cf, fg_color="transparent")
    ct.pack(fill="x", padx=12, pady=(8,0))
    ctk.CTkLabel(ct, text="SERVER CHAT & EVENTS", font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

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
                              wrap="word", state="disabled",
                              fg_color="transparent", text_color=T["text"],
                              height=120 if show_chat else 0)
    if show_chat:
        chat_box.pack(fill="x", expand=False, padx=8, pady=(4,8))

    # Command input
    cmdf = ctk.CTkFrame(right, fg_color=T["card"], border_color=T["border"], border_width=1)
    cmdf.grid(row=2, column=0, sticky="ew")
    cmdf_inner = ctk.CTkFrame(cmdf, fg_color="transparent")
    cmdf_inner.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(cmdf_inner, text="/", font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=T["muted"], width=14).pack(side="left")
    cmd_entry = ctk.CTkEntry(cmdf_inner, font=ctk.CTkFont(size=12, family="Consolas"),
                             fg_color=T["bg"], border_color=T["border"],
                             text_color=T["text"], placeholder_text="type a command or chat message...",
                             height=32)
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(4,8))
    cmd_entry.bind("<Return>", lambda e: send_command())
    ctk.CTkButton(cmdf_inner, text="Send", width=60, height=32,
                  font=ctk.CTkFont(size=12), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=send_command).pack(side="left")

# ── Helpers ───────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    log_box.configure(state="normal")
    log_box.insert("end", f"[{ts}]  {msg}\n")
    log_box.configure(state="disabled")
    log_box.see("end")

def log_chat(msg):
    if not show_chat: return
    ts = datetime.now().strftime("%H:%M:%S")
    chat_box.configure(state="normal")
    chat_box.insert("end", f"[{ts}]  {msg}\n")
    chat_box.configure(state="disabled")
    chat_box.see("end")

def set_status(txt, color):
    status_lbl.configure(text=txt)
    status_dot.configure(text_color=color)

def toggle_chat():
    global show_chat
    show_chat = not show_chat
    s = load_settings(); s["show_chat"] = show_chat; save_settings(s)
    chat_toggle_btn.configure(text="Hide" if show_chat else "Show")
    if show_chat:
        chat_box.configure(height=120)
        chat_box.pack(fill="x", expand=False, padx=8, pady=(4,8))
    else:
        chat_box.pack_forget()
        chat_box.configure(height=0)

def send_command():
    global server_stdin
    cmd = cmd_entry.get().strip()
    if not cmd: return
    cmd_entry.delete(0, "end")
    if server_stdin is None:
        log("Server is not running — start the server first.")
        return
    try:
        server_stdin.write(cmd + "\n")
        server_stdin.flush()
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
    for b in [btn_start, btn_stop, btn_sync, btn_handoff]: b.configure(state=state)

# ── Server stdout reader ──────────────────────────────────
def read_server_output(proc):
    """Reads server stdout line by line and routes to chat or log."""
    for raw in iter(proc.stdout.readline, ''):
        if not raw: break
        parsed = parse_server_line(raw)
        if parsed is None: continue
        cat, text = parsed
        if cat == 'chat':
            app.after(0, log_chat, text)
        elif cat == 'event':
            app.after(0, log_chat, text)
        else:
            app.after(0, log, text)

# ── Actions ───────────────────────────────────────────────
def start_server():
    global server_proc, server_stdin
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
        text=True, bufsize=1, creationflags=CREATE_NO_WINDOW
    )
    server_stdin = server_proc.stdin
    threading.Thread(target=read_server_output, args=(server_proc,), daemon=True).start()
    set_status("Running", T["start"])
    log("Server is running! (PID " + str(server_proc.pid) + ")")
    btn_stop.configure(state="normal")

def stop_server():
    global server_proc, server_stdin
    set_status("Stopping...", T["handoff"])
    log("── Stop Server ───────────────────")
    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except: pass
        server_stdin = None
    result = subprocess.run("taskkill /F /IM java.exe", shell=True, capture_output=True,
                            text=True, creationflags=CREATE_NO_WINDOW)
    log("  Java process killed." if result.returncode == 0 else "  Java was not running.")
    if server_proc:
        try: server_proc.terminate()
        except: pass
        server_proc = None
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
    global server_stdin
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
app.mainloop()