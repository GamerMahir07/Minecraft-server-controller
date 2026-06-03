"""
MC CTRL — launcher.pyw  (Optimized v2)
Tabs: Dashboard, Server Info, Docker, Modpacks.
Settings: Addons, paths, appearance, auto-upload, logo.
"""
import time
import shutil
import threading
import json
import os
import re
import sys
import urllib.request
import urllib.error
import importlib.util
import subprocess
import tkinter as tk
import tkinter.filedialog as _tk_fd
import customtkinter as ctk
from datetime import datetime
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

if sys.platform == "win32":
    import ctypes
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LIN = sys.platform.startswith("linux")
_NO_WIN = 0x08000000 if IS_WIN else 0
def _popen_flags(): return _NO_WIN


def _kill_java():
    if IS_WIN:
        return subprocess.run("taskkill /F /IM java.exe", shell=True, capture_output=True, text=True, creationflags=_NO_WIN)
    return subprocess.run("pkill -f 'server.jar'", shell=True, capture_output=True, text=True)


def _open_folder(path):
    try:
        if IS_WIN:
            os.startfile(path)
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _set_win_icon(win, ico):
    try:
        if IS_WIN:
            win.iconbitmap(ico)
        else:
            png = ico.replace(".ico", ".png")
            if os.path.exists(png):
                win.iconphoto(True, tk.PhotoImage(file=png))
    except Exception:
        pass


def _set_taskbar_id():
    try:
        if IS_WIN:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "gamermahir07.mcserver.launcher.1")
    except Exception:
        pass


_DEFAULT_JAVA = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot\bin\java.exe" if IS_WIN else "java"
_DEFAULT_SRV = r"C:\Users\DigitalComputer\Desktop\mc" if IS_WIN else os.path.expanduser(
    "~/minecraft-server")
REPO_URL = "https://github.com/GamerMahir07/minecraft-server.git"
SETTINGS_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "settings.json")
# ── Auto-update ──────────────────────────────────────────────────────────────
_APP_VERSION = "2.1.0"
_UPDATE_URL = "https://api.github.com/repos/GamerMahir07/minecraft-server/releases/latest"
_update_info = [None]   # {"version": str, "url": str} or None


def check_for_updates(silent=False):
    """Check GitHub releases for a newer launcher version."""
    def _work():
        try:
            req = urllib.request.Request(_UPDATE_URL, headers={
                                         "User-Agent": "MC-CTRL/"+_APP_VERSION, "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            if not tag:
                return

            def _ver(s):
                try:
                    return tuple(int(x) for x in s.split(".")[:3])
                except:
                    return (0,)
            if _ver(tag) > _ver(_APP_VERSION):
                url = data.get(
                    "html_url", "https://github.com/GamerMahir07/minecraft-server/releases")
                _update_info[0] = {"version": tag, "url": url}
                app.after(0, _show_update_banner, tag, url)
            elif not silent:
                app.after(0, show_toast,
                          f"MC CTRL is up to date (v{_APP_VERSION})", None)
        except Exception:
            if not silent:
                app.after(0, show_toast,
                          "Update check failed – check internet", None)
    threading.Thread(target=_work, daemon=True).start()


def _show_update_banner(version, url):
    show_toast(
        f"Update available: v{version} — click Settings → Check Updates", None, 7000)


_settings_cache, _settings_lock = None, threading.Lock()


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

    def _w():
        try:
            with _settings_lock:
                snap = dict(_settings_cache)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(snap, f, indent=2)
        except Exception:
            pass
    threading.Thread(target=_w, daemon=True).start()


THEMES = {
    'Dark (Default)': {"a": 'dark', "bg": '#0d0d0d', "card": '#1a1a1a', "border": '#2a2a2a', "text": '#e0e0e0', "muted": '#555555', "start": '#22c55e', "stop": '#ef4444', "sync": '#60a5fa', "hand": '#f59e0b'},
    'Light (Default)': {"a": 'light', "bg": '#f5f5f5', "card": '#ffffff', "border": '#e0e0e0', "text": '#1a1a1a', "muted": '#888888', "start": '#16a34a', "stop": '#dc2626', "sync": '#2563eb', "hand": '#d97706'},
    # ... (keeping existing themes for brevity in thought, will include all in output)
    'Obsidian Dark': {"a": 'dark', "bg": '#06060e', "card": '#0d0d1a', "border": '#1e1e30', "text": '#dde1f0', "muted": '#4a4d62', "start": '#7c3aed', "stop": '#ef4444', "sync": '#818cf8', "hand": '#f59e0b'},
    'Obsidian Light': {"a": 'light', "bg": '#f0f0f8', "card": '#ffffff', "border": '#c8c9dc', "text": '#0d0d20', "muted": '#5a5b72', "start": '#6d28d9', "stop": '#dc2626', "sync": '#4f46e5', "hand": '#d97706'},
    # 20 NEW THEMES ADDED BELOW
    'Aurora Borealis': {"a": 'dark', "bg": '#00120f', "card": '#00221a', "border": '#004a3a', "text": '#a0f8e0', "muted": '#3a7a6a', "start": '#34d399', "stop": '#f472b6', "sync": '#818cf8', "hand": '#fbbf24'},
    'Copper Moon': {"a": 'dark', "bg": '#0f0600', "card": '#1e0e00', "border": '#7a3a10', "text": '#ffc499', "muted": '#8a5030', "start": '#f97316', "stop": '#ef4444', "sync": '#fb923c', "hand": '#fbbf24'},
    'Stormy Gray': {"a": 'dark', "bg": '#0a0a0d', "card": '#121218', "border": '#2a2a35', "text": '#c8c9d0', "muted": '#4a4b55', "start": '#60a5fa', "stop": '#f87171', "sync": '#818cf8', "hand": '#fbbf24'},
    'Golden Sands': {"a": 'light', "bg": '#fdf9ef', "card": '#ffffff', "border": '#e0d0a0', "text": '#1c1800', "muted": '#8a7a30', "start": '#b45309', "stop": '#dc2626', "sync": '#0284c7', "hand": '#65a30d'},
    'Emerald City': {"a": 'dark', "bg": '#001200', "card": '#002200', "border": '#004400', "text": '#c0f0c0', "muted": '#3a7a3a', "start": '#4ade80', "stop": '#f87171', "sync": '#86efac', "hand": '#fde047'},
    'Ruby Night': {"a": 'dark', "bg": '#100008', "card": '#200010', "border": '#7a1030', "text": '#ffc0d0', "muted": '#8a4060', "start": '#fb7185', "stop": '#f43f5e', "sync": '#f472b6', "hand": '#fb923c'},
    'Sapphire Dream': {"a": 'light', "bg": '#f0f8ff', "card": '#ffffff', "border": '#a0c4e8', "text": '#001430', "muted": '#5070a0', "start": '#0ea5e9', "stop": '#e11d48', "sync": '#6366f1', "hand": '#f59e0b'},
    'Twilight Lavender': {"a": 'dark', "bg": '#0f0818', "card": '#1e1230', "border": '#4a2a60', "text": '#e8d8ff', "muted": '#6a50a0', "start": '#a78bfa', "stop": '#f472b6', "sync": '#c084fc', "hand": '#fb923c'},
    'Forest Canopy': {"a": 'light', "bg": '#f0faf0', "card": '#ffffff', "border": '#90c090', "text": '#0a2010', "muted": '#4a7a4a', "start": '#16a34a', "stop": '#dc2626', "sync": '#0d9488', "hand": '#ca8a04'},
    'Arctic Fox': {"a": 'light', "bg": '#f8fbff', "card": '#ffffff', "border": '#b0c8e0', "text": '#0a1a30', "muted": '#6a8aaa', "start": '#0ea5e9', "stop": '#e11d48', "sync": '#4f46e5', "hand": '#f59e0b'},
    'Iron Forge': {"a": 'dark', "bg": '#0a0a0c', "card": '#121216', "border": '#2a2a32', "text": '#d0d2d8', "muted": '#4a4b52', "start": '#d4d6dc', "stop": '#ef4444', "sync": '#60a5fa', "hand": '#f59e0b'},
    'Volcanic Ash': {"a": 'dark', "bg": '#0a0200', "card": '#1a0600', "border": '#7a2000', "text": '#ffc8a0', "muted": '#8a4020', "start": '#ff7c00', "stop": '#ff3300', "sync": '#ffaa00', "hand": '#ffdd00'},
    'Ocean Pearl': {"a": 'light', "bg": '#f5fcff', "card": '#ffffff', "border": '#a0d8e8', "text": '#002030', "muted": '#5080a0', "start": '#0284c7', "stop": '#e11d48', "sync": '#7c3aed', "hand": '#d97706'},
    'Shadow Steel': {"a": 'dark', "bg": '#08080a', "card": '#101014', "border": '#252530', "text": '#c8cad0', "muted": '#4a4b55', "start": '#9ca3af', "stop": '#ef4444', "sync": '#6366f1', "hand": '#f59e0b'},
    'Coral Reef': {"a": 'light', "bg": '#fff5f0', "card": '#ffffff', "border": '#f0c0b0', "text": '#2a1008', "muted": '#a06050', "start": '#ea580c', "stop": '#be123c', "sync": '#0284c7', "hand": '#ca8a04'},
    'Desert Wind': {"a": 'dark', "bg": '#140a00', "card": '#241400', "border": '#8a5010', "text": '#ffd8a0', "muted": '#8a6030', "start": '#d4aa60', "stop": '#e05050', "sync": '#70a8c0', "hand": '#e8c060'},
    'Midnight Jazz': {"a": 'dark', "bg": '#080010', "card": '#120020', "border": '#3b0060', "text": '#e0b8ff', "muted": '#6a2a8a', "start": '#bf7fff', "stop": '#ff5f87', "sync": '#d68fff', "hand": '#ffb347'},
    'Vintage Sepia': {"a": 'light', "bg": '#fdf6ee', "card": '#fff9f2', "border": '#d4b896', "text": '#1c0e00', "muted": '#8a6a40', "start": '#92400e', "stop": '#b91c1c', "sync": '#0369a1', "hand": '#b45309'},
    'Cyber Neon': {"a": 'dark', "bg": '#05000a', "card": '#0f0018', "border": '#330066', "text": '#e0d0ff', "muted": '#6600cc', "start": '#cc00ff', "stop": '#ff0066', "sync": '#00ffcc', "hand": '#ffcc00'},
    'Mystic Purple': {"a": 'dark', "bg": '#0f0020', "card": '#1a0035', "border": '#4a0080', "text": '#e8d8ff', "muted": '#7a40a0', "start": '#9d4edd', "stop": '#f72585', "sync": '#4cc9f0', "hand": '#f7b731'}
}

settings = load_settings()
_first_launch = "theme" not in settings
_theme_name = settings.get("theme", "Dark (Default)").strip()
show_chat = settings.get("show_chat", True)
log_left = settings.get("log_left", False)
show_perf = settings.get("show_perf", True)
fullscreen = settings.get("fullscreen", False)
auto_upload = settings.get("auto_upload", False)
backup_upload_on = settings.get("backup_upload_on", True)
auto_upload_mins = settings.get("auto_upload_mins", 10)
upload_on_stop = settings.get("upload_on_stop", True)
_ctrl_mode = settings.get("ctrl_mode", "Dashboard").strip().strip()
if _ctrl_mode.strip() in ("MC Ctrl", "MC Ctrl "):
    _ctrl_mode = "Dashboard"
if _theme_name not in THEMES:
    _theme_name = "Dark (Default)"
T = THEMES[_theme_name]
ctk.set_appearance_mode(T["a"])
ctk.set_default_color_theme("dark-blue")

server_proc, server_stdin, server_pid = None, None, None
perf_running, server_ready = False, False
player_count = 0
online_players = {}
auto_upload_timer = None
log_history = ""
chat_history = ""
playit_proc, playit_tunnel, playit_log_lines = None, None, []
_remote_proc, _loaded_addons = [None], {}
_players_refresh_id = None
perf = {"ram_used": "--", "ram_pct": "--", "ram_srv": "--", "cpu_sys": "--", "cpu_srv": "--",
        "tps": "--", "latency": "--", "players": "0 ", "uptime": "--", "threads": "--"}
server_start_time = None

CHAT_RE = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE = re.compile(r'^(\w+) joined the game', re.I)
LEAVE_RE = re.compile(r'^(\w+) (?:lost connection|left the game)', re.I)
DEATH_RE = re.compile(
    r'(\w+) (was |died|fell|drowned|burned|blew|got |hit |walked|withered|starved|suffocated)', re.I)
STRIP_RE = re.compile(r'^\[[\d:]+\]\s*\[?(?:INFO|WARN|ERROR)\]?:\s*', re.I)
DONE_RE = re.compile(r'Done ([\d.]+s)!', re.I)
SPARK_TPS = re.compile(r'TPS from last 1m[^:]:\s([\d.]+)', re.I)
TPS_RE2 = re.compile(r'Current TPS[:\s]+([\d.]+)', re.I)
PLAYER_RE = re.compile(r'There are (\d+) of a max of \d+ players', re.I)
LIST_NM_RE = re.compile(r'There are \d+[^:]:\s(.+)', re.I)
LAT_RE = re.compile(r'(\w+)\s+has\s+(?:a\s+ping\s+of\s+)?(\d+)\sms', re.I)
LAT_RE2 = re.compile(r'(\w+)\s((\d+)\s*ms)', re.I)


def parse_server_line(raw):
    global player_count, server_ready
    clean = STRIP_RE.sub('', raw).strip()
    if not clean:
        return None
    if "Done (" in clean and DONE_RE.search(clean):
        server_ready = True
        app.after(0, show_toast, "Server is ready! ", T["start"])
        return ('log', clean)
    if "TPS " in clean:
        tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
        if tps:
            perf["tps"] = tps.group(1)
            return None
    if "ms" in clean:
        lat = LAT_RE.search(clean) or LAT_RE2.search(clean)
        if lat:
            try:
                pings = [int(m[1]) for m in (
                    LAT_RE.findall(clean) or LAT_RE2.findall(clean))]
                if pings:
                    perf["latency"] = f"{sum(pings)//len(pings)} ms "
            except:
                pass
        return None
    if "There are " in clean:
        pl = PLAYER_RE.search(clean)
        if pl:
            player_count = int(pl.group(1))
            perf["players"] = str(player_count)
            nm = LIST_NM_RE.search(clean)
            if nm:
                raw_names = nm.group(1).strip()
                if raw_names:
                    names = [n.strip()
                             for n in raw_names.split(", ") if n.strip()]
                    now = datetime.now().strftime("%H:%M ")
                    for n in names:
                        if n not in online_players:
                            online_players[n] = now
                    for gone in [k for k in online_players if k not in names]:
                        online_players.pop(gone, None)
            return None
    if ' <' in clean:
        c = CHAT_RE.search(clean)
        if c:
            return ('chat', f"[CHAT] {c.group(1)}: {c.group(2)} ")
    if "joined the game " in clean:
        j = JOIN_RE.search(clean)
        if j:
            n = j.group(1)
            player_count += 1
            perf["players"] = str(player_count)
            online_players[n] = datetime.now().strftime("%H:%M ")
            return ('event', f" > > {n} joined ")
    if "left the game " in clean or "lost connection " in clean:
        lv = LEAVE_RE.search(clean)
        if lv:
            n = lv.group(1)
            player_count = max(0, player_count-1)
            perf["players"] = str(player_count)
            online_players.pop(n, None)
            return ('event', f" < < {n} left ")
    if any(w in clean for w in ("was slain", "died", "fell", "drowned", "burned", "blew up", "suffocated", "starved", "withered")):
        if DEATH_RE.search(clean):
            return ('event', f"[DEATH] {clean} ")
    return ('log', clean)


_log_buffer = []


def log(msg):
    global log_history
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}]  {msg}\n"
    log_history += line
    if len(log_history) > 200_000:
        log_history = log_history[-150_000:]
    try:
        log_box.configure(state="normal")
        log_box.insert("end", line)
        log_box.configure(state="disabled")
        log_box.see("end")
    except:
        _log_buffer.append(line)


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


def send_server_cmd(cmd):
    global server_stdin
    _stdin = server_stdin
    if _stdin is None:
        show_toast("Server not running! ", T["stop"])
        return
    try:
        _stdin.write(cmd + "\n")
        _stdin.flush()
        log(f" > > {cmd} ")
    except BrokenPipeError:
        server_stdin = None
        show_toast("Lost connection! ", T["stop"])
    except Exception as ex:
        log(f"Command failed: {ex} ")


def send_command():
    try:
        cmd = cmd_entry.get().strip()
    except:
        return
    if not cmd:
        return
    cmd_entry.delete(0, "end")
    send_server_cmd(cmd)


def run_cmd(cmd, cwd=None):
    log(f"$ {cmd}")
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd,
                           capture_output=True, text=True, creationflags=_NO_WIN)
        for line in p.stdout.strip().splitlines():
            log(f"  {line}")
        if p.returncode != 0:
            for line in p.stderr.strip().splitlines():
                log(f"  {line}")
        return p.returncode == 0
    except Exception as ex:
        log(str(ex))
        return False


def set_all_buttons(state):
    for b in [btn_start, btn_stop, btn_sync]:
        try:
            b.configure(state=state)
        except:
            pass


_remote_state_log_fn = [None]


def read_server_output(proc):
    for raw in iter(proc.stdout.readline, ''):
        if not raw:
            break
        parsed = parse_server_line(raw)
        if parsed is None:
            continue
        cat, text = parsed
        if _remote_state_log_fn[0]:
            try:
                _remote_state_log_fn[0](text)
            except:
                pass
        if cat in ('chat', 'event'):
            app.after(0, log_chat, text)
        else:
            app.after(0, log, text)


_toast_win = None


def show_toast(msg, color=None, ms=3000):
    global _toast_win
    if color is None:
        color = T["sync"]
    try:
        if _toast_win and _toast_win.winfo_exists():
            _toast_win.destroy()
    except:
        pass
    t = ctk.CTkToplevel(app)
    t.overrideredirect(True)
    t.attributes("-topmost", True)
    t.configure(fg_color=T["card"])
    _toast_win = t
    f = ctk.CTkFrame(
        t, fg_color=T["card"], border_color=color, border_width=2, corner_radius=10)
    f.pack(padx=2, pady=2)
    ctk.CTkLabel(f, text=msg, font=ctk.CTkFont(
        size=13, weight="bold"), text_color=color).pack(padx=18, pady=12)

    def _place():
        try:
            t.geometry(
                f"+{app.winfo_x()+app.winfo_width()-360}+{app.winfo_y()+app.winfo_height()-80}")
        except:
            pass
    app.after(10, _place)
    app.after(ms, lambda: t.destroy() if t.winfo_exists() else None)


def toggle_auto_upload():
    global auto_upload
    auto_upload = not auto_upload
    update_setting("auto_upload", auto_upload)
    if auto_upload:
        schedule_auto_upload()
    elif auto_upload_timer:
        try:
            auto_upload_timer.cancel()
        except:
            pass


def schedule_auto_upload():
    global auto_upload_timer
    if auto_upload_timer:
        try:
            auto_upload_timer.cancel()
        except:
            pass
    if not auto_upload:
        return
    auto_upload_timer = threading.Timer(auto_upload_mins * 60, _do_auto_upload)
    auto_upload_timer.daemon = True
    auto_upload_timer.start()


def _do_auto_upload():
    if not auto_upload:
        return
    s = load_settings()
    path = s.get("srv_path", _DEFAULT_SRV)
    repo = s.get("repo_url", REPO_URL)

    def _work():
        app.after(0, log, "-- Auto-upload ---")
        try:
            subprocess.run(
                f"git remote set-url origin {repo} ", shell=True, cwd=path, capture_output=True, creationflags=_NO_WIN)
            subprocess.run("git add . ", shell=True, cwd=path,
                           capture_output=True, creationflags=_NO_WIN)
            r = subprocess.run(f'git commit -m "Auto {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                               shell=True, cwd=path, capture_output=True, text=True, creationflags=_NO_WIN)
            if "nothing to commit " not in r.stdout and r.returncode == 0:
                push = subprocess.run("git push origin main ", shell=True, cwd=path,
                                      capture_output=True, text=True, creationflags=_NO_WIN)
                if push.returncode == 0:
                    app.after(0, log, "  Auto-upload done. ")
                    app.after(0, show_toast,
                              "Auto-upload complete! ", T["sync"])
        except Exception as ex:
            app.after(0, log, f"  Error: {ex} ")
        schedule_auto_upload()
    threading.Thread(target=_work, daemon=True).start()


perf_labels = {}


def find_java_proc():
    if not _PSUTIL:
        return None
    if server_pid:
        try:
            return psutil.Process(server_pid)
        except:
            pass
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'java' in p.info['name'].lower():
                if 'server.jar' in ' '.join(p.info['cmdline'] or []):
                    return p
        except:
            pass
    return None


def perf_loop():
    global perf_running
    if not _PSUTIL:
        return
    perf_running = True
    java_proc = None
    tick = 0
    psutil.cpu_percent(interval=None)
    while perf_running:
        try:
            vm = psutil.virtual_memory()
            perf["ram_used"] = f"{vm.used/1024**3:.1f} GB "
            perf["ram_pct"] = f"{vm.percent:.0f}% "
            perf["cpu_sys"] = f"{psutil.cpu_percent(interval=None):.0f}% "
            if java_proc is None:
                java_proc = find_java_proc()
            if java_proc:
                try:
                    perf["ram_srv"] = f"{java_proc.memory_info().rss/1024**2:.0f} MB "
                    perf["cpu_srv"] = f"{java_proc.cpu_percent(interval=None):.0f}% "
                    perf["threads"] = str(java_proc.num_threads())
                except:
                    java_proc = None
                    perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            if server_start_time:
                e = int((datetime.now()-server_start_time).total_seconds())
                h, r = divmod(e, 3600)
                m, s = divmod(r, 60)
                perf["uptime"] = f"{h:02d}:{m:02d}:{s:02d} "
            else:
                perf["uptime"] = "--"
            if server_ready and server_stdin:
                try:
                    if tick % 5 == 0:
                        server_stdin.write("tps\n")
                        server_stdin.flush()
                    if tick % 10 == 0:
                        server_stdin.write("list\n")
                        server_stdin.flush()
                except:
                    pass
            tick += 1
            app.after(0, update_perf_labels)
        except:
            pass
        time.sleep(2)


def update_perf_labels():
    for key, lbl in perf_labels.items():
        try:
            val = perf[key]
            if key == "tps":
                try:
                    v = float(val)
                    c = T["start"] if v >= 18 else T["hand"] if v >= 15 else T["stop"]
                except:
                    c = T["text"]
            elif key in ("cpu_sys", "cpu_srv", "ram_pct"):
                try:
                    n = float(str(val).replace("%", ""))
                    c = T["start"] if n < 60 else T["hand"] if n < 85 else T["stop"]
                except:
                    c = T["text"]
            else:
                c = T["text"]
            lbl.configure(text=val, text_color=c)
        except:
            pass


def apply_theme(name):
    global T, _theme_name
    _theme_name = name
    T = THEMES[name]
    update_setting("theme", name)
    ctk.set_appearance_mode(T["a"])
    app.configure(fg_color=T["bg"])
    rebuild_ui()


def _show_first_run_wizard():
    """First-launch setup wizard: pick server path, Java, RAM, theme."""
    win = ctk.CTkToplevel(app)
    win.title("Welcome to MC CTRL")
    win.geometry("580x560")
    win.configure(fg_color=T["bg"])
    win.grab_set()
    win.attributes("-topmost", True)
    try:
        ax = app.winfo_x()+(app.winfo_width()-580)//2
        ay = app.winfo_y()+(app.winfo_height()-560)//2
        win.geometry(f"580x560+{ax}+{ay}")
    except:
        pass
    ctk.CTkLabel(win, text="🎮 Welcome to MC CTRL", font=ctk.CTkFont(
        size=20, weight="bold"), text_color=T["start"]).pack(pady=(22, 4))
    ctk.CTkLabel(win, text="Let's set up your Minecraft server launcher",
                 font=ctk.CTkFont(size=12), text_color=T["muted"]).pack()
    f = ctk.CTkFrame(
        win, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
    f.pack(fill="x", padx=28, pady=14)

    def row(label):
        r = ctk.CTkFrame(f, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=5)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(
            size=12), text_color=T["text"], width=180, anchor="w").pack(side="left")
        return r
    # Server path
    r1 = row("Server folder")
    srv_var = ctk.StringVar(value=_DEFAULT_SRV)
    ctk.CTkEntry(r1, textvariable=srv_var, width=200, height=26, font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]).pack(side="left", padx=(0, 4))
    ctk.CTkButton(r1, text="Browse", width=60, height=26, fg_color="transparent", border_width=1, border_color=T["border"], text_color=T[
                  "muted"], hover_color=T["border"], command=lambda: srv_var.set(_tk_fd.askdirectory(title="Server folder") or srv_var.get())).pack(side="left")
    # Java path
    r2 = row("Java executable")
    java_var = ctk.StringVar(value=_DEFAULT_JAVA)
    ctk.CTkEntry(r2, textvariable=java_var, width=200, height=26, font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]).pack(side="left", padx=(0, 4))
    ctk.CTkButton(r2, text="Browse", width=60, height=26, fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: java_var.set(
        _tk_fd.askopenfilename(title="Java executable") or java_var.get())).pack(side="left")
    # RAM
    r3 = row("Server RAM (GB)")
    ram_var = ctk.IntVar(value=2)
    ram_lbl = ctk.CTkLabel(r3, text="2 GB", font=ctk.CTkFont(
        size=12, family="Consolas"), text_color=T["sync"], width=44)
    ram_lbl.pack(side="right")
    def _on_ram(v): iv = int(float(v)); ram_lbl.configure(text=f"{iv} GB")
    ctk.CTkSlider(r3, from_=1, to=16, number_of_steps=15, variable=ram_var, command=_on_ram,
                  button_color=T["sync"], progress_color=T["sync"], width=200).pack(side="left")
    # Theme
    r4 = row("Theme")
    theme_var = ctk.StringVar(value="Dark (Default)")
    ctk.CTkOptionMenu(r4, variable=theme_var, values=list(THEMES.keys()), width=200, height=26, font=ctk.CTkFont(
        size=11), fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"], text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"], dropdown_hover_color=T["border"]).pack(side="left")
    # Auto-create folders
    r5 = row("Auto-create folders")
    autocreate_var = ctk.BooleanVar(value=True)
    ctk.CTkSwitch(r5, text="", variable=autocreate_var,
                  button_color=T["sync"], progress_color=T["sync"]).pack(side="right")

    def _finish():
        path = srv_var.get().strip()
        if autocreate_var.get() and path:
            for sub in ["", "plugins", "mods", "world"]:
                try:
                    os.makedirs(os.path.join(path, sub), exist_ok=True)
                except:
                    pass
        update_setting("srv_path", path)
        update_setting("java_path", java_var.get().strip())
        update_setting("server_ram_gb", int(ram_var.get()))
        update_setting("theme", theme_var.get())
        update_setting("first_run_done", True)
        win.destroy()
        apply_theme(theme_var.get())
        show_toast("Setup complete! Ready to launch.", T["start"])
    ctk.CTkButton(win, text="✓ Finish Setup", height=38, fg_color=T["start"], hover_color=T["start"], text_color="#000", font=ctk.CTkFont(
        size=14, weight="bold"), command=_finish).pack(pady=(10, 4), padx=28, fill="x")
    ctk.CTkButton(win, text="Skip (configure later in Settings)", height=28, fg_color="transparent",
                  border_width=0, text_color=T["muted"], hover_color=T["border"], command=win.destroy).pack(pady=2)


def rebuild_ui():
    global log_history, chat_history
    _ip_footer_labels.clear()
    try:
        log_history = log_box.get("1.0", "end")
    except:
        pass
    try:
        chat_history = chat_box.get("1.0", "end")
    except:
        pass
    for w in app.winfo_children():
        w.destroy()
    build_ui()


def _check_eula(path):
    eula = os.path.join(path, "eula.txt")
    try:
        if "eula=true " in open(eula, encoding="utf-8").read().lower():
            return True
    except FileNotFoundError:
        pass
    result = [None]

    def _show():
        win = ctk.CTkToplevel(app)
        win.title("Minecraft EULA")
        win.resizable(False, False)
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        try:
            ax = app.winfo_x()+(app.winfo_width()-500)//2
            ay = app.winfo_y()+(app.winfo_height()-360)//2
            win.geometry(f"500x360+{ax}+{ay} ")
        except:
            win.geometry("500x360")
        ctk.CTkLabel(win, text="⚠ ", font=ctk.CTkFont(size=40),
                     text_color=T["hand"]).pack(pady=(20, 0))
        ctk.CTkLabel(win, text="Minecraft EULA", font=ctk.CTkFont(
            size=15, weight="bold"), text_color=T["text"]).pack()
        f = ctk.CTkFrame(
            win, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
        f.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(f, text="You must agree to the Minecraft EULA before starting.\nThis writes eula=true to eula.txt.\n\nhttps://aka.ms/MinecraftEULA",
                     font=ctk.CTkFont(size=12), text_color=T["muted"], justify="left").pack(padx=16, pady=12)
        br = ctk.CTkFrame(win, fg_color="transparent")
        br.pack(pady=8)

        def _acc():
            try:
                os.makedirs(path, exist_ok=True)
                with open(eula, "w", encoding="utf-8") as f2:
                    f2.write(
                        f"# Accepted {datetime.now().strftime('%Y-%m-%d %H:%M')}\n# https://aka.ms/MinecraftEULA\neula=true\n ")
            except Exception as ex:
                log(f"  EULA write error: {ex} ")
            result[0] = True
            win.destroy()
        ctk.CTkButton(br, text="Accept EULA ", width=160, height=34, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000", command=_acc).pack(side="left", padx=(0, 10))
        ctk.CTkButton(br, text="Decline ", width=90, height=34, font=ctk.CTkFont(size=13), fg_color="transparent", border_width=1,
                      border_color=T["stop"], text_color=T["stop"], hover_color=T["border"], command=lambda: (result.__setitem__(0, False), win.destroy())).pack(side="left")
        win.wait_window()
    app.after(0, _show)
    while result[0] is None:
        time.sleep(0.05)
    return result[0]


def start_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready, player_count
    set_all_buttons("disabled")
    s = load_settings()
    path = s.get("srv_path", _DEFAULT_SRV)
    java = s.get("java_path", _DEFAULT_JAVA)
    repo = s.get("repo_url", REPO_URL)
    if not _check_eula(path):
        log("  Cancelled — EULA not accepted. ")
        set_status("Stopped ", T["stop"])
        set_all_buttons("normal")
        return
    set_status("Starting... ", T["hand"])
    log("-- Start Server --")
    run_cmd(f"git remote set-url origin {repo} ", cwd=path)
    run_cmd("git pull origin main ", cwd=path)
    _ram_gb = s.get("server_ram_gb", 2)
    _ram_str = f"{_ram_gb}G "
    aikar = [f"-Xms{_ram_str} ", f"-Xmx{_ram_str} ", "-XX:+UseG1GC ", "-XX:+ParallelRefProcEnabled ", "-XX:MaxGCPauseMillis=200 ", "-XX:+UnlockExperimentalVMOptions ", "-XX:+DisableExplicitGC ", "-XX:G1NewSizePercent=30 ", "-XX:G1MaxNewSizePercent=40 ", "-XX:G1HeapRegionSize=8M ", "-XX:G1ReservePercent=20 ", "-XX:G1HeapWastePercent=5 ",
             "-XX:G1MixedGCCountTarget=4 ", "-XX:InitiatingHeapOccupancyPercent=15 ", "-XX:G1MixedGCLiveThresholdPercent=90 ", "-XX:G1RSetUpdatingPauseTimePercent=5 ", "-XX:SurvivorRatio=32 ", "-XX:+PerfDisableSharedMem ", "-XX:MaxTenuringThreshold=1 ", "-Dusing.aikars.flags=https://mcflags.emc.gs ", "-Daikars.new.flags=true "]
    cmd = [java] + aikar + ["-jar", "server.jar", "nogui"]
    kw = {"cwd": path, "stdin": subprocess.PIPE, "stdout": subprocess.PIPE,
          "stderr": subprocess.STDOUT, "text": True, "bufsize": 1}
    if IS_WIN:
        kw["creationflags"] = _NO_WIN
    try:
        server_proc = subprocess.Popen(cmd, **kw)
    except Exception as ex:
        log(f"  Failed to start: {ex} ")
        set_status("Stopped ", T["stop"])
        set_all_buttons("normal")
        return
    server_stdin = server_proc.stdin
    server_pid = server_proc.pid
    server_start_time = datetime.now()
    server_ready = False
    player_count = 0
    online_players.clear()
    perf["tps"] = perf["latency"] = "--"
    perf["players"] = "0 "
    threading.Thread(target=read_server_output, args=(
        server_proc,), daemon=True).start()
    if not perf_running:
        threading.Thread(target=perf_loop, daemon=True).start()
    set_status("Running ", T["start"])
    log(f"Server running (PID {server_proc.pid}) ")
    try:
        btn_stop.configure(state="normal")
    except:
        pass


def stop_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready
    set_status("Stopping... ", T["hand"])
    log("-- Stop Server --")
    if server_stdin:
        try:
            server_stdin.write("stop\n")
            server_stdin.flush()
        except:
            pass
    server_stdin = None
    r = _kill_java()
    log("  Killed. " if r.returncode == 0 else "  Not running. ")
    server_proc = server_pid = server_start_time = None
    server_ready = perf_running = False
    for k in ("tps", "latency", "players", "uptime", "ram_srv", "cpu_srv", "threads"):
        perf[k] = "--"
    if upload_on_stop and backup_upload_on:
        s = load_settings()
        path = s.get("srv_path", _DEFAULT_SRV)
        log("Pushing world to GitHub... ")
        run_cmd("git add world/ world_nether/ world_the_end/ ", cwd=path)
        c = subprocess.run(f'git commit -m "World update {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                           shell=True, cwd=path, capture_output=True, text=True, creationflags=_NO_WIN)
        if "nothing to commit " in (c.stdout or " "):
            log("  Nothing to commit. ")
        else:
            run_cmd("git push origin main ", cwd=path)
        app.after(0, show_toast, "World pushed to GitHub! ", T["sync"])
    if _remote_proc[0]:
        try:
            _remote_proc[0].terminate()
        except:
            pass
    _remote_proc[0] = None
    set_status("Stopped ", T["stop"])
    log("Done. ")
    set_all_buttons("normal")


def run_repair():
    """Repair mode: verify server files, re-accept EULA, re-pull git."""
    def _work():
        s = load_settings()
        path = s.get("srv_path", _DEFAULT_SRV)
        java = s.get("java_path", _DEFAULT_JAVA)
        app.after(0, log, "── Repair Mode ──")
        # Check server folder
        if not os.path.isdir(path):
            app.after(0, log, f"  ✗ Server folder not found: {path}")
            app.after(0, show_toast, "Server folder missing!", None)
            return
        app.after(0, log, f"  ✓ Server folder: {path}")
        # Check server.jar
        jar = os.path.join(path, "server.jar")
        if not os.path.exists(jar):
            app.after(0, log, "  ✗ server.jar missing — please download it")
            app.after(0, show_toast, "server.jar missing!", None)
        else:
            app.after(
                0, log, f"  ✓ server.jar found ({os.path.getsize(jar)//1024//1024} MB)")
        # Check Java
        try:
            r = subprocess.run([java, "-version"], capture_output=True,
                               text=True, timeout=5, creationflags=_NO_WIN)
            ver = (r.stderr or r.stdout or "").strip().splitlines()
            app.after(0, log, f"  ✓ Java: {ver[0] if ver else 'unknown'}")
        except Exception as ex:
            app.after(0, log, f"  ✗ Java not found: {ex}")
        # Re-write EULA
        eula_path = os.path.join(path, "eula.txt")
        try:
            with open(eula_path, "w", encoding="utf-8") as ef:
                ef.write(
                    f"# Repaired {datetime.now().strftime('%Y-%m-%d %H:%M')}\neula=true\n")
            app.after(0, log, "  ✓ eula.txt written")
        except Exception as ex:
            app.after(0, log, f"  ✗ EULA write failed: {ex}")
        # Git pull
        app.after(0, log, "  git pull…")
        run_cmd("git pull origin main", cwd=path)
        app.after(0, log, "── Repair complete ──")
        app.after(0, show_toast, "Repair complete!", None)
    threading.Thread(target=_work, daemon=True).start()


def run_uninstall_wizard():
    """Uninstall/cleanup wizard — removes settings and optionally server data."""
    win = ctk.CTkToplevel(app)
    win.title("Uninstall / Cleanup Wizard")
    win.geometry("480x380")
    win.configure(fg_color=T["bg"])
    win.grab_set()
    win.attributes("-topmost", True)
    try:
        ax = app.winfo_x()+(app.winfo_width()-480)//2
        ay = app.winfo_y()+(app.winfo_height()-380)//2
        win.geometry(f"480x380+{ax}+{ay}")
    except:
        pass
    ctk.CTkLabel(win, text="🗑 Uninstall / Cleanup", font=ctk.CTkFont(size=16,
                 weight="bold"), text_color=T["stop"]).pack(pady=(18, 4))
    ctk.CTkLabel(win, text="Choose what to remove:",
                 font=ctk.CTkFont(size=12), text_color=T["muted"]).pack()
    opts_frame = ctk.CTkFrame(win, fg_color="transparent")
    opts_frame.pack(padx=24, pady=10, fill="x")
    v_settings = ctk.BooleanVar(value=True)
    v_addons = ctk.BooleanVar(value=False)
    v_server = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(opts_frame, text="Launcher settings (settings.json)", variable=v_settings,
                    text_color=T["text"], fg_color=T["stop"], hover_color=T["stop"]).pack(anchor="w", pady=4)
    ctk.CTkCheckBox(opts_frame, text="Addons folder", variable=v_addons,
                    text_color=T["text"], fg_color=T["stop"], hover_color=T["stop"]).pack(anchor="w", pady=4)
    ctk.CTkCheckBox(opts_frame, text="⚠ Server data folder (DESTRUCTIVE)", variable=v_server,
                    text_color=T["stop"], fg_color=T["stop"], hover_color=T["stop"]).pack(anchor="w", pady=4)

    def _do():
        base = os.path.dirname(os.path.abspath(__file__))
        removed = []
        if v_settings.get():
            try:
                os.remove(SETTINGS_FILE)
                removed.append("settings.json")
            except:
                pass
        if v_addons.get():
            adir = os.path.join(base, "addons")
            try:
                shutil.rmtree(adir)
                removed.append("addons/")
            except:
                pass
        if v_server.get():
            s = load_settings()
            spath = s.get("srv_path", _DEFAULT_SRV)
            if os.path.isdir(spath):
                try:
                    shutil.rmtree(spath)
                    removed.append(spath)
                except Exception as ex:
                    log(f"  Could not remove server folder: {ex}")
        win.destroy()
        show_toast(
            f"Removed: {', '.join(removed) if removed else 'nothing'}", T["stop"])
        if v_settings.get():
            app.after(500, rebuild_ui)
    ctk.CTkButton(win, text="⚠ Confirm Removal", height=36, fg_color=T["stop"], hover_color=T["stop"], text_color="#fff", font=ctk.CTkFont(
        size=13, weight="bold"), command=_do).pack(pady=(8, 4), padx=24, fill="x")
    ctk.CTkButton(win, text="Cancel", height=32, fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=win.destroy).pack(pady=4, padx=24, fill="x")


def sync_git():
    set_all_buttons("disabled")
    s = load_settings()
    path = s.get("srv_path", _DEFAULT_SRV)
    repo = s.get("repo_url", REPO_URL)
    set_status("Syncing... ", T["hand"])
    log("-- Sync & Upload --")
    run_cmd(f"git remote set-url origin {repo} ", cwd=path)
    run_cmd("git add . ", cwd=path)
    run_cmd('git commit -m "Manual Sync "', cwd=path)
    ok = run_cmd("git push origin main ", cwd=path)
    if ok:
        app.after(0, show_toast, "Sync complete! ", T["sync"])
    set_status("Stopped ", T["stop"])
    set_all_buttons("normal")


def _load_addon(path):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "setup"):
            mod.setup({"app": app, "T ": T, "log": log, "show_toast": show_toast,
                      "send_server_cmd": send_server_cmd, "load_settings": load_settings})
        _loaded_addons[name] = mod
        log(f"  Addon: {name} ")
    except Exception as ex:
        log(f"  Addon error [{name}]: {ex} ")


def _load_all_addons():
    addon_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)
    try:
        for s in sorted(os.listdir(addon_dir)):
            if s.endswith(".py"):
                _load_addon(os.path.join(addon_dir, s))
    except:
        pass


_cached_local_ip, _cached_ext_ip, _ip_footer_labels = ["…"], ["…"], []


def _refresh_ip_footers():
    for local_lbl, ext_lbl in _ip_footer_labels:
        try:
            local_lbl.configure(text=f"LAN {_cached_local_ip[0]}")
        except:
            pass
        try:
            ext_lbl.configure(text=f"EXT {_cached_ext_ip[0]}")
        except:
            pass


def _start_ip_detection():
    import socket

    def _work():
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s2.connect(("8.8.8.8", 80))
            lip = s2.getsockname()[0]
            s2.close()
        except:
            lip = "127.0.0.1 "
        port = load_settings().get("server_port", "25565 ")
        _cached_local_ip[0] = f"{lip}:{port} "
        app.after(0, _refresh_ip_footers)
        try:
            eip = urllib.request.urlopen(
                "https://api.ipify.org", timeout=6).read().decode().strip()
            _cached_ext_ip[0] = f"{eip}:{port} "
        except:
            _cached_ext_ip[0] = "unavailable"
        app.after(0, _refresh_ip_footers)
    threading.Thread(target=_work, daemon=True).start()


def _build_ip_footer(parent):
    bar = ctk.CTkFrame(
        parent, fg_color=T["bg"], corner_radius=0, border_color=T["border"], border_width=1)
    bar.pack(side="bottom", fill="x")
    bar.columnconfigure(2, weight=1)
    ctk.CTkLabel(bar, text="⬡ ", font=ctk.CTkFont(size=11),
                 text_color=T["border"]).pack(side="left", padx=(10, 4), pady=5)
    local_lbl = ctk.CTkLabel(bar, text=f"LAN {_cached_local_ip[0]} ", font=ctk.CTkFont(
        size=11, family="Consolas", weight="bold"), text_color=T["start"])
    local_lbl.pack(side="left", padx=(0, 16))
    ext_lbl = ctk.CTkLabel(bar, text=f"EXT {_cached_ext_ip[0]} ", font=ctk.CTkFont(
        size=11, family="Consolas", weight="bold"), text_color=T["sync"])
    ext_lbl.pack(side="left")
    ctk.CTkButton(bar, text="⎘ LAN ", width=56, height=20, font=ctk.CTkFont(size=9), fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["start"], hover_color=T["border"], command=lambda: (
        app.clipboard_clear(), app.clipboard_append(_cached_local_ip[0]), show_toast(f"Copied: {_cached_local_ip[0]} ", T["start"]))).pack(side="left", padx=(8, 2), pady=4)
    ctk.CTkButton(bar, text="⎘ EXT ", width=56, height=20, font=ctk.CTkFont(size=9), fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["sync"], hover_color=T["border"], command=lambda: (
        app.clipboard_clear(), app.clipboard_append(_cached_ext_ip[0]), show_toast(f"Copied: {_cached_ext_ip[0]} ", T["sync"]))).pack(side="left", padx=2, pady=4)
    ctk.CTkButton(bar, text="↺ ", width=30, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_start_ip_detection).pack(side="left", padx=2, pady=4)
    _ip_footer_labels.append((local_lbl, ext_lbl))
    return bar


def _build_loading_overlay(parent, text="Loading… ", detail=" "):
    overlay = ctk.CTkFrame(parent, fg_color=T["bg"], corner_radius=0)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()
    _spin_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    _spin_idx = [0]
    spin_lbl = ctk.CTkLabel(overlay, text=_spin_chars[0], font=ctk.CTkFont(
        size=22), text_color=T["sync"])
    spin_lbl.place(relx=0.5, rely=0.38, anchor="center")
    title_lbl = ctk.CTkLabel(overlay, text=text, font=ctk.CTkFont(
        size=15, weight="bold"), text_color=T["text"])
    title_lbl.place(relx=0.5, rely=0.47, anchor="center")
    detail_lbl = ctk.CTkLabel(overlay, text=detail,
                              font=ctk.CTkFont(size=11), text_color=T["muted"])
    detail_lbl.place(relx=0.5, rely=0.54, anchor="center")
    bar = ctk.CTkProgressBar(overlay, width=220, height=3,
                             fg_color=T["border"], progress_color=T["sync"])
    bar.place(relx=0.5, rely=0.61, anchor="center")
    bar.set(0)
    bar.start()
    _running = [True]

    def _tick():
        if not _running[0]:
            return
        _spin_idx[0] = (_spin_idx[0] + 1) % len(_spin_chars)
        try:
            spin_lbl.configure(text=_spin_chars[_spin_idx[0]])
        except:
            return
        overlay.after(80, _tick)
    overlay.after(80, _tick)

    def _dismiss():
        _running[0] = False
        try:
            bar.stop()
            overlay.destroy()
        except:
            pass
    return _dismiss


app = ctk.CTk()
app.title("MC CTRL")
app.geometry("1100x740")
app.resizable(True, True)
app.configure(fg_color=T["bg"])
_set_taskbar_id()
try:
    _set_win_icon(app, os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "icon.ico"))
except:
    pass
if fullscreen:
    app.after(100, lambda: app.attributes("-fullscreen", True))


def build_ui():
    global status_dot, status_lbl, btn_start, btn_stop, btn_sync, cmd_entry, log_box, chat_box, chat_toggle_btn
    top = ctk.CTkFrame(app, fg_color=T["card"], corner_radius=0)
    top.pack(fill="x")
    ctk.CTkLabel(top, text="MC CTRL ", font=ctk.CTkFont(
        size=15, weight="bold"), text_color=T["text"]).pack(side="left", padx=14, pady=8)
    plat = "🐧 Linux " if IS_LIN else ("🍎 Mac " if IS_MAC else "🪟 Windows ")
    ctk.CTkLabel(top, text=plat, font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(0, 8))
    _gpu_lbl = ctk.CTkLabel(top, text="GPU: detecting… ",
                            font=ctk.CTkFont(size=10), text_color=T["muted"])
    _gpu_lbl.pack(side="left", padx=(0, 8))

    def _detect_gpu():
        import queue as _q
        result_q = _q.Queue()
        gpu = " "

        def _try():
            try:
                if IS_WIN:
                    r = subprocess.run("wmic path win32_VideoController get Name /value ", shell=True,
                                       capture_output=True, text=True, timeout=4, creationflags=_NO_WIN)
                    for line in r.stdout.splitlines():
                        if "Name=" in line:
                            v = line.split("=", 1)[1].strip()
                            result_q.put(v) if v else result_q.put(" ")
                            return
                elif IS_LIN:
                    r = subprocess.run(
                        "lspci | grep -i vga ", shell=True, capture_output=True, text=True, timeout=4)
                    if r.stdout:
                        result_q.put(r.stdout.strip().split(
                            ": ")[-1].strip()[:48])
                        return
                elif IS_MAC:
                    r = subprocess.run("system_profiler SPDisplaysDataType | grep Chipset ",
                                       shell=True, capture_output=True, text=True, timeout=4)
                    if r.stdout:
                        result_q.put(r.stdout.strip().split(": ")[-1].strip())
                        return
            except:
                pass
            result_q.put(" ")
        _t = threading.Thread(target=_try, daemon=True)
        _t.start()
        _t.join(timeout=4.5)
        try:
            gpu = result_q.get_nowait()
        except:
            pass
        if not gpu:
            try:
                if IS_WIN:
                    r2 = subprocess.run("wmic cpu get Name /value ", shell=True,
                                        capture_output=True, text=True, timeout=3, creationflags=_NO_WIN)
                    for line in r2.stdout.splitlines():
                        if "Name=" in line:
                            gpu = "CPU: " + line.split("=", 1)[1].strip()[:36]
                            break
                elif IS_LIN:
                    r2 = subprocess.run("cat /proc/cpuinfo | grep 'model name' | head -1 ",
                                        shell=True, capture_output=True, text=True, timeout=3)
                    if r2.stdout:
                        gpu = "CPU: " + r2.stdout.split(": ")[-1].strip()[:36]
            except:
                pass
        label = ("🖥 " + gpu[:48]) if gpu else "🖥 GPU/CPU: unknown "
        try:
            app.after(0, _gpu_lbl.configure, {"text": label})
        except:
            pass
    threading.Thread(target=_detect_gpu, daemon=True).start()

    _theme_btn_lbl = ctk.StringVar(value=f"🎨 {_theme_name} ")

    def _open_theme_picker():
        win = ctk.CTkToplevel(app)
        win.title("Theme Picker ")
        win.geometry("780x540")
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        try:
            ax = app.winfo_x()+(app.winfo_width()-780)//2
            ay = app.winfo_y()+(app.winfo_height()-540)//2
            win.geometry(f"780x540+{ax}+{ay} ")
        except:
            pass
        win.rowconfigure(1, weight=1)
        win.columnconfigure(0, weight=1)
        sf = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=0)
        sf.grid(row=0, column=0, sticky="ew")
        sf.columnconfigure(1, weight=1)
        ctk.CTkLabel(sf, text="🔍 ", font=ctk.CTkFont(
            size=14), text_color=T["muted"]).grid(row=0, column=0, padx=(10, 4), pady=8)
        search_var = ctk.StringVar()
        se = ctk.CTkEntry(sf, textvariable=search_var, placeholder_text="Search themes… ", height=30, font=ctk.CTkFont(
            size=12), fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
        se.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        se.focus()
        _filt = ctk.StringVar(value="All ")
        fbf = ctk.CTkFrame(sf, fg_color="transparent")
        fbf.grid(row=0, column=2, padx=(0, 8))
        for lbl, val in [("All ", "All "), ("Dark ", "dark"), ("Light ", "light")]:
            ctk.CTkButton(fbf, text=lbl, width=52, height=26, font=ctk.CTkFont(size=10), fg_color=T["sync"] if val == "All " else T["bg"], border_width=1, border_color=T[
                          "border"], text_color="#000" if val == "All " else T["muted"], hover_color=T["border"], command=lambda v=val: (_filt.set(v), _refresh_grid())).pack(side="left", padx=2)
        grid_scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        grid_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        _cards = []

        def _pick(name):
            _theme_btn_lbl.set(f"🎨 {name} ")
            apply_theme(name)
            win.destroy()
            app.after(10, rebuild_ui)

        def _refresh_grid():
            for w in grid_scroll.winfo_children():
                w.destroy()
            q = search_var.get().lower()
            filt = _filt.get()
            results = [(n, t) for n, t in THEMES.items() if (q in n.lower() or q in t.get(
                "bg", "") or q in t.get("start", "")) and (filt == "All " or t.get("a ", "dark") == filt)]
            COLS = 4
            for i, (name, t) in enumerate(results):
                row_i, col_i = i//COLS, i % COLS
                card = ctk.CTkFrame(grid_scroll, fg_color=t["card"], border_color=t["border"] if name ==
                                    _theme_name else t["card"], border_width=2, corner_radius=10, cursor="hand2")
                card.grid(row=row_i, column=col_i, padx=4, pady=4, sticky="ew")
                grid_scroll.columnconfigure(col_i, weight=1)
                sw = ctk.CTkFrame(card, fg_color="transparent")
                sw.pack(padx=8, pady=(8, 4))
                for hex_c in [t["bg"], t["card"], t["border"], t["start"], t["stop"], t["sync"]]:
                    try:
                        c = ctk.CTkLabel(
                            sw, text=" ", width=18, height=18, corner_radius=4, fg_color=hex_c)
                        c.pack(side="left", padx=1)
                    except:
                        pass
                ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=t["text"], wraplength=150, justify="center").pack(padx=6, pady=(0, 6))
                card.bind("<Button-1>", lambda e, n=name: _pick(n))
                for child in card.winfo_children():
                    child.bind("<Button-1>", lambda e, n=name: _pick(n))
            if not results:
                ctk.CTkLabel(grid_scroll, text="No themes match. ", font=ctk.CTkFont(
                    size=13), text_color=T["muted"]).grid(row=0, column=0, pady=40)
        search_var.trace_add("write", lambda *_: _refresh_grid())
        _refresh_grid()
    ctk.CTkButton(top, textvariable=_theme_btn_lbl, width=160, height=26, font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_open_theme_picker).pack(side="left", padx=(0, 6), pady=6)

    def _open_settings():
        win = ctk.CTkToplevel(app)
        win.title("Settings ")
        win.geometry("720x700")
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.attributes("-topmost", True)
        try:
            ax = app.winfo_x()+(app.winfo_width()-720)//2
            ay = app.winfo_y()+(app.winfo_height()-700)//2
            win.geometry(f"720x700+{ax}+{ay} ")
        except:
            pass
        build_settings_window(win)

    ctk.CTkButton(top, text="⚙ Settings ", width=90, height=26, font=ctk.CTkFont(size=11), corner_radius=6,
                  fg_color=T["bg"], border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_open_settings).pack(side="left", padx=(0, 8), pady=6)

    status_dot = ctk.CTkLabel(
        top, text="● ", font=ctk.CTkFont(size=13), text_color=T["stop"])
    status_dot.pack(side="right", padx=(0, 12))
    status_lbl = ctk.CTkLabel(top, text="Stopped ",
                              font=ctk.CTkFont(size=12), text_color=T["muted"])
    status_lbl.pack(side="right", padx=(0, 4))

    tab_bar = ctk.CTkFrame(
        app, fg_color=T["card"], corner_radius=0, border_color=T["border"], border_width=1)
    tab_bar.pack(fill="x")
    tab_content = ctk.CTkFrame(app, fg_color="transparent")
    tab_content.pack(fill="both", expand=True)
    tab_frames = {k: ctk.CTkFrame(tab_content, fg_color="transparent") for k in [
        "dash", "info", "docker", "mods"]}
    _built = set()
    tab_btns = {}

    def show_tab(name):
        for f in tab_frames.values():
            f.pack_forget()
        for n, b in tab_btns.items():
            b.configure(fg_color="transparent", text_color=T["muted"])
        tab_frames[name].pack(fill="both", expand=True)
        tab_btns[name].configure(fg_color=T["sync"], text_color="#000")
        if name not in _built:
            _built.add(name)
            _TAB_LOAD_INFO = {"dash": ("Building Dashboard ", "Server controls, quick commands, log… "), "info": ("Building Server Info ", "Players, plugins, properties, backups… "), "docker": (
                "Building Docker ", "Container config, compose, controls… "), "mods": ("Building Modpacks ", "Modrinth search, installer, browser… ")}
            _lt, _ld = _TAB_LOAD_INFO.get(name, ("Loading… ", " "))
            _dismiss = _build_loading_overlay(tab_frames[name], _lt, _ld)

            def _build_and_dismiss(n=name, dismiss=_dismiss):
                try:
                    {"dash": lambda: build_dashboard(tab_frames["dash"], fullscreen), "info": lambda: build_server_info_tab(
                        tab_frames["info"]), "docker": lambda: build_docker_tab(tab_frames["docker"]), "mods": lambda: build_modpack_tab(tab_frames["mods"])}[n]()
                except Exception as _e:
                    log(f"Tab build error [{n}]: {_e} ")
                finally:
                    dismiss()
            app.after(60, _build_and_dismiss)
    TABS = [("dash", "Dashboard"), ("info", "Server Info "),
            ("docker", "Docker "), ("mods", "📦 Modpacks ")]
    for key, label in TABS:
        b = ctk.CTkButton(tab_bar, text=label, width=120, height=28, font=ctk.CTkFont(size=11), corner_radius=5,
                          fg_color="transparent", text_color=T["muted"], hover_color=T["border"], command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=(6 if key == "dash" else 2, 2), pady=5)
        tab_btns[key] = b
    show_tab("dash")


def build_dashboard(parent, is_fs):
    _build_ip_footer(parent)
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(side="top", fill="both", expand=True)
    _build_mode_dashboard(f, is_fs)


def _build_mode_dashboard(parent, is_fs):
    global btn_start, btn_stop, btn_sync, log_box, chat_box, cmd_entry, chat_toggle_btn
    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="both", expand=True)
    bar = ctk.CTkFrame(
        outer, fg_color=T["card"], corner_radius=0, border_color=T["border"], border_width=1)
    bar.pack(side="top", fill="x")
    _slot = [None]
    _active = [None]
    dsub_btns = {}
    BUILDERS = {"control": _build_dsub_control, "playit": _build_mode_playit,
                "remote": _build_mode_remote, "multi": _build_dsub_multi}

    def show_dsub(name):
        if name == _active[0]:
            return
        _active[0] = name
        for n, b in dsub_btns.items():
            b.configure(fg_color=T["sync"] if n == name else "transparent",
                        text_color="#000" if n == name else T["muted"])
        if _slot[0] is not None:
            try:
                _slot[0].destroy()
            except:
                pass
        frame = ctk.CTkFrame(outer, fg_color="transparent")
        frame.pack(side="top", fill="both", expand=True)
        _slot[0] = frame
        try:
            BUILDERS[name](frame)
        except Exception as e:
            import traceback
            ctk.CTkLabel(frame, text=f"Error: {e} ", text_color=T["stop"], font=ctk.CTkFont(
                size=12)).pack(pady=20)
            traceback.print_exc()
    DSUBS = [("control", "⚙ Control "), ("playit", "🚇 playit.gg "),
             ("remote", "📱 Remote "), ("multi", "⊞ Multi ")]
    for key, label in DSUBS:
        b = ctk.CTkButton(bar, text=label, height=28, width=100, font=ctk.CTkFont(size=10, weight="bold"), corner_radius=0,
                          fg_color="transparent", text_color=T["muted"], hover_color=T["border"], command=lambda k=key: show_dsub(k))
        b.pack(side="left", padx=1, pady=4)
        dsub_btns[key] = b
    show_dsub("control")
    globals()["_dsub_goto_remote"] = lambda: show_dsub("remote")


def _build_dsub_control(parent):
    global btn_start, btn_stop, btn_sync, log_box, chat_box, cmd_entry, chat_toggle_btn
    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="both", expand=True)
    outer.rowconfigure(0, weight=1)   # BODY (top/expand)
    outer.rowconfigure(1, weight=0)   # STATS (bottom/fixed)
    outer.columnconfigure(0, weight=1)

    # BODY
    body_frame = ctk.CTkScrollableFrame(
        outer, fg_color="transparent", border_width=0)
    body_frame.grid(row=0, column=0, sticky="nsew")
    body = ctk.CTkFrame(body_frame, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=16, pady=10)
    ctrl_col = 1 if log_left else 0
    log_col = 0 if log_left else 1
    body.columnconfigure(ctrl_col, weight=0, minsize=310)
    body.columnconfigure(log_col, weight=1)
    body.rowconfigure(0, weight=1)

    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=ctrl_col, sticky="nsew",
              padx=(8, 0) if log_left else (0, 8))

    def make_btn(par, text, desc, color, cmd):
        f = ctk.CTkFrame(
            par, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
        f.pack(fill="x", pady=3)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        top_r = ctk.CTkFrame(inner, fg_color="transparent")
        top_r.pack(fill="x")
        ctk.CTkLabel(top_r, text=text, font=ctk.CTkFont(
            size=12, weight="bold"), text_color=color, anchor="w").pack(side="left")
        b = ctk.CTkButton(top_r, text="Run ", width=64, height=26, font=ctk.CTkFont(
            size=11), fg_color=color, hover_color=color, text_color="#000", command=cmd)
        b.pack(side="right")
        ctk.CTkLabel(inner, text=desc, font=ctk.CTkFont(
            size=10), text_color=T["muted"], anchor="w", wraplength=250, justify="left").pack(anchor="w", pady=(2, 0))
        return b
    btn_start = make_btn(left, "Start Server ", "Git pull then launch with Aikar JVM flags ",
                         T["start"], lambda: threading.Thread(target=start_server, daemon=True).start())
    btn_stop = make_btn(left, "Stop Server ", "Kill Java process then push world to GitHub ",
                        T["stop"], lambda: threading.Thread(target=stop_server,  daemon=True).start())
    btn_sync = make_btn(left, "Sync & Upload ", "Git add all, commit Manual Sync, push ",
                        T["sync"], lambda: threading.Thread(target=sync_git,      daemon=True).start())
    qf = ctk.CTkFrame(
        left, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
    qf.pack(fill="x", pady=(8, 3))
    ctk.CTkLabel(qf, text="QUICK COMMANDS ", font=ctk.CTkFont(
        size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8, 4))
    ctk.CTkFrame(qf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    qgrid = ctk.CTkFrame(qf, fg_color="transparent")
    qgrid.pack(fill="x", padx=10, pady=8)
    QUICK_CMDS = [("Save World ", "save-all ", T["sync"]), ("Player List ", "list", T["sync"]), ("Check TPS ", "tps", T["sync"]), ("Set Day ", "time set day ", T["hand"]), ("Set Night ", "time set night ", T["hand"]),
                  ("Clear Weather ", "weather clear ", T["hand"]), ("Hard Mode ", "difficulty hard ", T["stop"]), ("Peaceful ", "difficulty peaceful ", T["start"]), ("Safe Stop ", "stop", T["stop"]), ("Reload ", "reload", T["muted"])]
    for i, (label, cmd_txt, color) in enumerate(QUICK_CMDS):
        ri, ci = i // 2, i % 2
        ctk.CTkButton(qgrid, text=label, width=130, height=26, font=ctk.CTkFont(size=10), corner_radius=6, fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=color, hover_color=T["border"], command=lambda c=cmd_txt: send_server_cmd(c)).grid(row=ri, column=ci, padx=3, pady=2, sticky="ew")
        qgrid.columnconfigure(ci, weight=1)
    wf = ctk.CTkFrame(left, fg_color="transparent")
    wf.pack(fill="x", pady=(6, 0))
    _wlbl = ctk.CTkLabel(wf, text="Size: calculating… ",
                         font=ctk.CTkFont(size=10), text_color=T["muted"])
    _wlbl.pack(side="left")
    _blbl = ctk.CTkLabel(wf, text=" ", font=ctk.CTkFont(
        size=10), text_color=T["muted"])
    _blbl.pack(side="right")
    _bkup_next_ts = [None]

    def _calc_world():
        try:
            s2 = load_settings()
            path = s2.get("srv_path", _DEFAULT_SRV)
            dirs = [os.path.join(path, d) for d in (
                "world", "world_nether", "world_the_end") if os.path.isdir(os.path.join(path, d))]
            total = sum(sum(os.path.getsize(os.path.join(r, fn))
                        for r, _, fs in os.walk(d) for fn in fs) for d in dirs)
            mb = total/1048576
            app.after(0, _wlbl.configure, {"text": (
                "Size: %.0f MB " % mb) if mb < 1024 else ("Size: %.2f GB " % (mb/1024))})
        except:
            app.after(0, _wlbl.configure, {"text": "Size: --"})

    def _tick_bkp():
        try:
            if _bkup_next_ts[0]:
                rem = max(0, int(_bkup_next_ts[0]-time.time()))
                m2, s3 = divmod(rem, 60)
                _blbl.configure(text="Backup in %02d:%02d " % (
                    m2, s3), text_color=T["sync"] if rem < 300 else T["muted"])
            _blbl.after(5000, _tick_bkp)
        except:
            pass
    globals()["_dashboard_set_backup_ts"] = lambda ts: _bkup_next_ts.__setitem__(
        0, ts)
    threading.Thread(target=_calc_world, daemon=True).start()
    app.after(1000, _tick_bkp)

    right = ctk.CTkFrame(body, fg_color="transparent")
    right.grid(row=0, column=log_col, sticky="nsew")
    right.rowconfigure(0, weight=1)
    right.rowconfigure(1, weight=0)
    right.rowconfigure(2, weight=0)
    right.columnconfigure(0, weight=1)
    lf = ctk.CTkFrame(
        right, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
    lf.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
    lt = ctk.CTkFrame(lf, fg_color="transparent")
    lt.pack(fill="x", padx=12, pady=(8, 0))
    ctk.CTkLabel(lt, text="ACTIVITY LOG ", font=ctk.CTkFont(
        size=10, weight="bold"), text_color=T["muted"]).pack(side="left")
    for txt2, fn in [("Swap ", lambda: _toggle_log_left()), ("Copy ", lambda: (app.clipboard_clear(), app.clipboard_append(log_box.get("1.0", "end")), show_toast("Copied! ", T["sync"]))), ("Clear ", lambda: (log_box.configure(state="normal"), log_box.delete("1.0", "end"), log_box.configure(state="disabled")))]:
        ctk.CTkButton(lt, text=txt2, width=44, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=fn).pack(side="right", padx=2)
    ctk.CTkFrame(lf, height=1, fg_color=T["border"]).pack(fill="x", padx=10)
    log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),
                             wrap="word", state="disabled", fg_color="transparent", text_color=T["text"])
    log_box.pack(fill="both", expand=True, padx=6, pady=(3, 6))
    log_box.configure(state="normal")
    log_box.insert("1.0", log_history)
    log_box.configure(state="disabled")
    log_box.see("end")

    cf = ctk.CTkFrame(
        right, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
    cf.grid(row=1, column=0, sticky="ew", pady=(0, 5))
    ct = ctk.CTkFrame(cf, fg_color="transparent")
    ct.pack(fill="x", padx=12, pady=(8, 0))
    ctk.CTkLabel(ct, text="SERVER CHAT & EVENTS ", font=ctk.CTkFont(
        size=10, weight="bold"), text_color=T["muted"]).pack(side="left")
    chat_toggle_btn = ctk.CTkButton(ct, text="Hide " if show_chat else "Show ", width=44, height=20, font=ctk.CTkFont(
        size=10), fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_toggle_chat)
    chat_toggle_btn.pack(side="right")
    ctk.CTkButton(ct, text="Clear ", width=44, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: (
        chat_box.configure(state="normal"), chat_box.delete("1.0", "end"), chat_box.configure(state="disabled"))).pack(side="right", padx=(0, 4))
    chat_box = ctk.CTkTextbox(cf, font=ctk.CTkFont(size=11, family="Consolas"), wrap="word",
                              state="disabled", fg_color="transparent", text_color=T["text"], height=100)
    if show_chat:
        chat_box.pack(fill="x", padx=6, pady=(3, 6))
    if chat_history.strip():
        chat_box.configure(state="normal")
        chat_box.insert("1.0", chat_history)
        chat_box.configure(state="disabled")
        chat_box.see("end")

    cmdf = ctk.CTkFrame(
        right, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
    cmdf.grid(row=2, column=0, sticky="ew")
    ci = ctk.CTkFrame(cmdf, fg_color="transparent")
    ci.pack(fill="x", padx=12, pady=8)
    ctk.CTkLabel(ci, text="/ ", font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=T["muted"], width=14).pack(side="left")
    cmd_entry = ctk.CTkEntry(ci, font=ctk.CTkFont(size=12, family="Consolas"),
                             fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text="command or chat message... ", height=32)
    cmd_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
    cmd_entry.bind("<Return>", lambda e: send_command())
    ctk.CTkButton(ci, text="Send ", width=60, height=32, font=ctk.CTkFont(
        size=12), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=send_command).pack(side="left")

    # STATS BAR MOVED TO BOTTOM (row 1)
    stats_bar = ctk.CTkFrame(
        outer, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0)
    stats_bar.grid(row=1, column=0, sticky="ew")
    for _ci in range(8):
        stats_bar.columnconfigure(_ci, weight=1)
    _stat_lbls = {}
    STAT_DEFS = [("players", "Players", T["sync"], "👥"), ("tps", "TPS", T["start"], "⚡"), ("ram_srv", "Srv RAM", T["hand"], "💾"), ("ram_pct", "RAM%", T["hand"], "📊"),
                 ("cpu_srv", "Srv CPU", T["stop"], "🖥"), ("cpu_sys", "Sys CPU", T["stop"], "⚙"), ("uptime", "Uptime", T["muted"], "⏱"), ("threads", "Threads", T["muted"], "🧵")]
    for col_i, (key, label, color, icon) in enumerate(STAT_DEFS):
        cell = ctk.CTkFrame(stats_bar, fg_color="transparent")
        cell.grid(row=0, column=col_i, sticky="nsew", padx=0, pady=0)
        if col_i > 0:
            ctk.CTkFrame(cell, width=1, fg_color=T["border"]).pack(
                side="left", fill="y", pady=6)
        inner = ctk.CTkFrame(cell, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        ctk.CTkLabel(inner, text=f"{icon} {label}", font=ctk.CTkFont(
            size=9), text_color=T["muted"], anchor="w").pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=perf.get(
            key, "--"), font=ctk.CTkFont(size=20, weight="bold"), text_color=color, anchor="w")
        val_lbl.pack(anchor="w", pady=(1, 0))
        _stat_lbls[key] = val_lbl

    def _tick():
        for k, lbl in _stat_lbls.items():
            try:
                val = perf.get(k, "--")
                if k == "tps":
                    try:
                        v = float(str(val).strip())
                        c = T["start"] if v >= 18 else T["hand"] if v >= 15 else T["stop"]
                    except:
                        c = T["muted"]
                elif k in ("cpu_sys", "cpu_srv", "ram_pct"):
                    try:
                        n = float(str(val).replace("%", "").strip())
                        c = T["start"] if n < 60 else T["hand"] if n < 85 else T["stop"]
                    except:
                        c = T["muted"]
                else:
                    c = None
                lbl.configure(text=val, **({"text_color": c} if c else {}))
            except:
                return
        try:
            list(_stat_lbls.values())[0].after(2000, _tick)
        except:
            pass
    _tick()


def _build_mode_playit(parent):
    global playit_proc, playit_tunnel, playit_log_lines
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

    def card(title, sub=None):
        f = ctk.CTkFrame(
            scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        f.pack(fill="x", padx=18, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(
            size=12, weight="bold"), text_color=T["text"]).pack(side="left")
        if sub:
            ctk.CTkLabel(h, text=sub, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=12, pady=(8, 10))
        return b, h
    ab, _ = card("About playit.gg ")
    ctk.CTkLabel(ab, text="playit.gg is a free tunnel that gives your server a public address without port forwarding.\nFriends connect via a .ply.gg address. Free plan supports up to 3 tunnels.",
                 font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    sb, _ = card("Setup ")
    s = load_settings()
    pt_var = ctk.StringVar(value=s.get("playit_path", " "))
    pt_var.trace_add(
        "write", lambda *_: update_setting("playit_path", pt_var.get()))
    pt_st = ctk.CTkLabel(sb, text=" ", font=ctk.CTkFont(
        size=11), text_color=T["muted"])

    def _browse_pt(): p = _tk_fd.askopenfilename(title="Select playit binary",
                                                 filetypes=[("All", "*.*")]); p and pt_var.set(p)

    def _dl_pt():
        fname = "playit-windows.exe" if IS_WIN else (
            "playit-darwin" if IS_MAC else "playit-linux-amd64")
        dest_name = "playit.exe" if IS_WIN else "playit"
        dest = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), dest_name)
        pt_st.configure(text="Downloading…", text_color=T["sync"])

        def _do():
            url = f"https://github.com/playit-cloud/playit-agent/releases/latest/download/{fname}"
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "MC-CTRL/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    with open(dest, "wb") as f2:
                        f2.write(r.read())
                if not IS_WIN:
                    os.chmod(dest, 0o755)
                pt_var.set(dest)
                app.after(0, pt_st.configure, {
                          "text": "Downloaded!", "text_color": T["start"]})
            except Exception as ex:
                app.after(0, pt_st.configure, {
                          "text": f"Failed: {ex}", "text_color": T["stop"]})
        threading.Thread(target=_do, daemon=True).start()
    pr = ctk.CTkFrame(sb, fg_color="transparent")
    pr.pack(fill="x", pady=(0, 4))
    ctk.CTkEntry(pr, textvariable=pt_var, height=28, font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text="path/to/playit").pack(side="left", fill="x", expand=True, padx=(0, 6))
    ctk.CTkButton(pr, text="Browse ", width=66, height=28, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_browse_pt).pack(side="left", padx=(0, 5))
    ctk.CTkButton(pr, text="Auto-Download ", height=28, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=_dl_pt).pack(side="left")
    pt_st.pack(anchor="w", pady=(4, 0))
    cb, ch = card("Tunnel Control ")
    tun_st = ctk.CTkLabel(cb, text="● Stopped ", font=ctk.CTkFont(
        size=13, weight="bold"), text_color=T["stop"])
    tun_st.pack(side="left")
    tun_addr = ctk.CTkLabel(cb, text=" ", font=ctk.CTkFont(
        size=13, family="Consolas"), text_color=T["start"])
    tun_addr.pack(side="left", padx=(12, 0))
    def _set_tst(txt, col): tun_st.configure(text=txt, text_color=col)

    def _set_addr(addr):
        global playit_tunnel
        playit_tunnel = addr
        tun_addr.configure(text=addr or " ")
        if addr:
            app.after(0, show_toast, f"Tunnel: {addr}", T["start"])
    _PT_Q, _PT_FL = [], [False]

    def _flush_pt():
        _PT_FL[0] = False
        if not _PT_Q:
            return
        batch, _PT_Q[:] = _PT_Q[:], []
        try:
            pt_log.configure(state="normal")
            pt_log.insert("end", "\n".join(batch)+"\n")
            total = int(pt_log.index("end-1c").split(".")[0])
            if total > 300:
                pt_log.delete("1.0", f"{total-300}.0")
            pt_log.configure(state="disabled")
            pt_log.see("end")
        except:
            pass

    def _qlog(line): _PT_Q.append(line); _PT_FL[0] or app.after(120, _flush_pt)
    _ANSI_RE = re.compile(
        r'\x1b(?:\[[0-9;]*[mABCDEFGHJKSTfhilmnprsuu]|\][^\x07]*\x07|[()][AB012]|[=>])')
    _ADDR_RE = re.compile(
        r'((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg|joinmc\.link|mc\.gg)(?::\d+)?)', re.I)
    _CLAIM_RE = re.compile(
        r'(https?://[^\s]+(?:playit|claim|tunnel)[^\s]*)', re.I)

    def _handle(raw):
        try:
            line = raw.decode("utf-8", errors="replace").rstrip()
        except:
            line = repr(raw)
        clean = _ANSI_RE.sub("", line).strip()
        if not clean:
            return
        playit_log_lines.append(clean)
        if len(playit_log_lines) > 300:
            del playit_log_lines[:150]
        m = _ADDR_RE.search(clean)
        if m:
            app.after(0, _set_addr, m.group(1))
        cm = _CLAIM_RE.search(clean)
        if cm:
            _qlog(f"[MC CTRL] CLAIM URL: {cm.group(1)}")
            app.after(0, show_toast, "Open claim URL!", T["hand"], 8000)
        _qlog(clean)

    def _read_pt(proc):
        for raw in iter(proc.stdout.readline, b""):
            _handle(raw) if raw else None
        app.after(0, _qlog, f"[MC CTRL] Exited with code {proc.wait()}. ")
        app.after(0, _set_tst, "● Stopped ", T["stop"])

    def _start_pt():
        global playit_proc
        exe = pt_var.get().strip()
        if not exe or not os.path.exists(exe):
            show_toast("Set playit path first!", T["stop"])
            return
        if playit_proc and playit_proc.poll() is None:
            show_toast("Already running.", T["muted"])
            return
        try:
            kw = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
                  "stdin": subprocess.DEVNULL, "text": False, "bufsize": 0}
            if IS_WIN:
                kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | _NO_WIN
            playit_proc = subprocess.Popen([exe], **kw)
            _set_tst("● Running ", T["start"])
            threading.Thread(target=_read_pt, args=(
                playit_proc,), daemon=True).start()

            def _stderr_reader(p=playit_proc):
                for l in iter(p.stderr.readline, b""):
                    _handle(l)
            threading.Thread(target=_stderr_reader, daemon=True).start()
        except Exception as ex:
            show_toast(f"Failed: {ex}", T["stop"])
            _set_tst("● Error ", T["stop"])

    def _stop_pt():
        global playit_proc, playit_tunnel
        if playit_proc:
            try:
                playit_proc.terminate()
            except:
                pass
        playit_proc = playit_tunnel = None
        _set_addr("")
        _set_tst("● Stopped ", T["stop"])
    br = ctk.CTkFrame(ch, fg_color="transparent")
    br.pack(side="right")
    for txt, cmd, fc, tc in [("▶ Start ", _start_pt, T["start"], "#000"), ("■ Stop ", _stop_pt, T["stop"], "#fff")]:
        ctk.CTkButton(br, text=txt, width=74, height=26, font=ctk.CTkFont(
            size=11), fg_color=fc, hover_color=fc, text_color=tc, command=cmd).pack(side="left", padx=(0, 4))
    ctk.CTkButton(br, text="Copy Address ", width=100, height=26, font=ctk.CTkFont(size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=lambda: (
        app.clipboard_clear(), app.clipboard_append(tun_addr.cget("text")), show_toast(f"Copied: {tun_addr.cget('text')}", T["sync"]))).pack(side="left")
    ctk.CTkButton(br, text="📱 Remote Server ", width=120, height=26, font=ctk.CTkFont(
        size=11), fg_color=T["hand"], hover_color=T["hand"], text_color="#000", command=lambda: globals().get("_dsub_goto_remote", lambda: None)()).pack(side="left", padx=(6, 0))
    lb, lh = card("Agent Log ")
    pt_log = ctk.CTkTextbox(lb, font=ctk.CTkFont(size=11, family="Consolas"), wrap="word",
                            state="disabled", height=180, fg_color=T["bg"], text_color=T["text"])
    pt_log.pack(fill="x")
    if playit_log_lines:
        pt_log.configure(state="normal")
        [pt_log.insert("end", l+"\n") for l in playit_log_lines]
        pt_log.configure(state="disabled")
        pt_log.see("end")
    if playit_tunnel:
        _set_addr(playit_tunnel)
    ctk.CTkButton(lh, text="Clear ", width=50, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1, border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: (
        playit_log_lines.clear(), pt_log.configure(state="normal"), pt_log.delete("1.0", "end"), pt_log.configure(state="disabled"))).pack(side="right")
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()


def _build_mode_remote(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

    def card(title):
        f = ctk.CTkFrame(
            scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        f.pack(fill="x", padx=18, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(
            size=12, weight="bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=12, pady=(8, 10))
        return b, h
    ab, _ = card("About Remote Dashboard")
    ctk.CTkLabel(ab, text="Starts a lightweight web server so you can control Minecraft from your phone.\nOpen http://<your-local-ip>:<port> in any browser — no app required.\nFeatures: start/stop, live log, commands, player list, TPS/RAM stats.",
                 font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    s = load_settings()
    port_var = ctk.StringVar(value=str(s.get("remote_port", 5000)))
    pass_var = ctk.StringVar(value=s.get("remote_password", ""))
    def _save_rd(*_): update_setting("remote_port", port_var.get()
                                     ); update_setting("remote_password", pass_var.get())
    cb, _ = card("Configuration")
    r0 = ctk.CTkFrame(cb, fg_color="transparent")
    r0.pack(fill="x", pady=3)
    ctk.CTkLabel(r0, text="Port", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    pe = ctk.CTkEntry(r0, textvariable=port_var, width=80, height=26, font=ctk.CTkFont(
        size=12, family="Consolas"), fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
    pe.pack(side="left")
    pe.bind("<FocusOut>", _save_rd)
    pe.bind("<Return>", _save_rd)
    r1 = ctk.CTkFrame(cb, fg_color="transparent")
    r1.pack(fill="x", pady=3)
    ctk.CTkLabel(r1, text="Password (optional)", font=ctk.CTkFont(
        size=12), text_color=T["text"], width=180, anchor="w").pack(side="left")
    pwe = ctk.CTkEntry(r1, textvariable=pass_var, width=200, height=26, show="•", font=ctk.CTkFont(
        size=12, family="Consolas"), fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text="blank = no auth")
    pwe.pack(side="left", padx=(0, 6))
    pwe.bind("<FocusOut>", _save_rd)
    ctk.CTkButton(r1, text="Show", width=48, height=26, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: pwe.configure(show="" if pwe.cget("show") == "•" else "•")).pack(side="left")
    ctrl_b, ctrl_h = card("Dashboard Control")
    rd_st = ctk.CTkLabel(ctrl_b, text="● Stopped", font=ctk.CTkFont(
        size=13, weight="bold"), text_color=T["stop"])
    rd_st.pack(side="left")
    rd_url = ctk.CTkLabel(ctrl_b, text=" ", font=ctk.CTkFont(
        size=12, family="Consolas"), text_color=T["sync"])
    rd_url.pack(side="left", padx=(12, 0))
    _cur_url = [""]
    def _set_st(txt, col): rd_st.configure(text=txt, text_color=col)
    def _set_url(url): _cur_url[0] = url; rd_url.configure(text=url)
    _state_file = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "_mc_ctrl_state.json")
    _state_log_buf, _state_log_lock = [], threading.Lock()

    def _append_state_log(line):
        with _state_log_lock:
            _state_log_buf.append(line)
            if len(_state_log_buf) > 200:
                del _state_log_buf[:100]

    def _write_state():
        try:
            with _state_log_lock:
                new_lines = _state_log_buf[-30:] if _state_log_buf else []
            state = {"running": server_proc is not None and server_proc.poll() is None, "tps": perf.get("tps", "--"), "players": perf.get("players", "0"), "player_list": list(online_players.keys()), "ram_srv": perf.get("ram_srv", "--"), "ram_pct": perf.get(
                "ram_pct", "--"), "ram_used": perf.get("ram_used", "--"), "cpu_srv": perf.get("cpu_srv", "--"), "cpu_sys": perf.get("cpu_sys", "--"), "uptime": perf.get("uptime", "--"), "threads": perf.get("threads", "--"), "latency": perf.get("latency", "--"), "log": new_lines}
            try:
                with open(_state_file) as _sf2:
                    existing = json.loads(_sf2.read())
                if existing.get("pending_action"):
                    act = existing.pop("pending_action")
                    {"start": start_server, "stop": stop_server}.get(
                        act, lambda: None)()
                if existing.get("pending_cmd"):
                    send_server_cmd(existing.pop("pending_cmd"))
            except:
                pass
            with open(_state_file, "w") as _sf:
                _sf.write(json.dumps(state))
        except:
            pass

    def _sync_loop():
        while _remote_proc[0] and _remote_proc[0].poll() is None:
            app.after(0, _write_state)
            time.sleep(2)

    def _write_flask():
        # Copy the uploaded _mc_ctrl_remote.py next to launcher if present, else write a full-featured version
        launcher_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(launcher_dir, "_mc_ctrl_remote.py")
        # If the file already exists beside the launcher (user placed it there), keep it
        if os.path.exists(path):
            return path
        code = r'''import sys,json,os,threading,time
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

# Serve remoteCTRL.html if present beside this script, otherwise use built-in HTML
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(_SCRIPT_DIR, "remoteCTRL.html")

BUILTIN_HTML="""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>MC CTRL Remote</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#080808;--card:#111;--card2:#161616;--border:#1f1f1f;--border2:#2a2a2a;--text:#e8e8e8;--muted:#555;--muted2:#888;--green:#22c55e;--red:#ef4444;--blue:#60a5fa;--amber:#f59e0b;--glow:rgba(34,197,94,0.12)}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:14px;line-height:1.5}
.topbar{background:var(--card);border-bottom:1px solid var(--border);padding:12px 18px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:10}
.topbar-logo{font-size:13px;font-weight:700;letter-spacing:.08em;color:var(--green)}
.topbar-logo span{color:var(--muted2);font-weight:400}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}
.dot-green{background:var(--green);box-shadow:0 0 8px var(--green)}.dot-red{background:var(--red)}
#srv-status-text{font-size:13px;font-weight:500}
.spacer{flex:1}
.page{padding:16px 14px 32px;max-width:520px;margin:0 auto;display:flex;flex-direction:column;gap:10px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.card-hdr{padding:12px 16px 10px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.card-title{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted2)}
.card-body{padding:14px 16px}
.hero-num{font-size:52px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--green);transition:color .4s}
.hero-num.off{color:var(--muted)}
.hero-label{font-size:11px;color:var(--muted2);margin-top:4px;text-transform:uppercase;letter-spacing:.08em}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border)}
.stat-cell{background:var(--card);padding:12px 14px}
.stat-row-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;display:flex;align-items:center;gap:5px}
.stat-val{font-size:20px;font-weight:600;font-family:'JetBrains Mono',monospace;color:var(--text)}
.btn-row{display:flex;gap:8px;flex-wrap:wrap}
button{border:none;border-radius:8px;cursor:pointer;font-family:'Inter',sans-serif;font-weight:600;font-size:13px;padding:10px 18px;transition:opacity .15s,transform .1s;display:inline-flex;align-items:center;gap:6px}
button:active{transform:scale(.97)}
.btn-start{background:var(--green);color:#000}.btn-stop{background:var(--red);color:#fff}
.btn-outline{background:transparent;border:1px solid var(--border2);color:var(--muted2);font-size:11px;padding:7px 12px}
.btn-outline:hover{border-color:var(--muted);color:var(--text)}
.cmd-wrap{display:flex;gap:8px;margin-bottom:10px}
.cmd-input{flex:1;background:var(--card2);border:1px solid var(--border2);border-radius:8px;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;padding:10px 12px;outline:none}
.cmd-input:focus{border-color:var(--muted)}
.quick-btns{display:flex;flex-wrap:wrap;gap:6px}
.log-box{background:var(--bg);border-radius:8px;border:1px solid var(--border);font-family:'JetBrains Mono',monospace;font-size:11px;color:#666;padding:10px 12px;height:200px;overflow-y:auto;white-space:pre-wrap;line-height:1.6}
.log-box::-webkit-scrollbar{width:4px}.log-box::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
.log-line-event{color:var(--blue)}.log-line-warn{color:var(--amber)}
.player-row{display:flex;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);gap:10px}
.player-row:last-child{border-bottom:none}
.player-name{font-size:13px;font-weight:500;flex:1}
.no-players{color:var(--muted);font-size:12px;padding:10px 0;text-align:center}
</style></head><body>
<div class="topbar">
  <div class="topbar-logo">MC CTRL <span>remote</span></div>
  <span class="dot" id="status-dot" style="background:var(--red)"></span>
  <span id="srv-status-text">Connecting...</span>
  <div class="spacer"></div>
  <span style="font-size:10px;color:var(--muted)" id="poll-time"></span>
</div>
<div class="page">
  <div class="card">
    <div class="card-hdr"><span class="card-title">Server Health</span></div>
    <div class="card-body" style="display:flex;align-items:flex-end;gap:20px;padding-bottom:18px">
      <div><div class="hero-num off" id="hero-pct">--</div><div class="hero-label">TPS</div></div>
      <div style="flex:1">
        <div class="stat-grid" style="border-radius:8px;overflow:hidden;border:1px solid var(--border);grid-template-columns:1fr 1fr 1fr">
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-ram"></span>Srv RAM</div><div class="stat-val" id="h-ram">--</div></div>
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-rampct"></span>RAM %</div><div class="stat-val" id="h-rampct">--</div></div>
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-cpu"></span>Srv CPU</div><div class="stat-val" id="h-cpu">--</div></div>
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-cpusys"></span>Sys CPU</div><div class="stat-val" id="h-cpusys">--</div></div>
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-up"></span>Uptime</div><div class="stat-val" id="h-up" style="font-size:14px">--</div></div>
          <div class="stat-cell"><div class="stat-row-label"><span class="dot" id="dot-pl"></span>Players</div><div class="stat-val" id="h-pl">--</div></div>
        </div>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-hdr"><span class="card-title">Server Control</span></div>
    <div class="card-body">
      <div class="btn-row" style="margin-bottom:12px">
        <button class="btn-start" onclick="act('start')">&#9654; Start</button>
        <button class="btn-stop" onclick="act('stop')">&#9632; Stop</button>
      </div>
      <div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:4px 0 8px">Quick Commands</div>
      <div class="quick-btns">
        <button class="btn-outline" onclick="sv('list')">list</button>
        <button class="btn-outline" onclick="sv('tps')">tps</button>
        <button class="btn-outline" onclick="sv('save-all')">save</button>
        <button class="btn-outline" onclick="sv('time set day')">set day</button>
        <button class="btn-outline" onclick="sv('weather clear')">clear weather</button>
        <button class="btn-outline" onclick="sv('difficulty peaceful')">peaceful</button>
        <button class="btn-outline" onclick="sv('difficulty hard')">hard mode</button>
        <button class="btn-outline" onclick="sv('stop')">safe stop</button>
      </div>
    </div>
  </div>
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
  <div class="card">
    <div class="card-hdr"><span class="card-title">Online Players</span><div style="flex:1"></div><span style="font-size:11px;color:var(--muted)" id="player-count">0 online</span></div>
    <div class="card-body" style="padding-top:4px;padding-bottom:4px">
      <div id="player-list"><div class="no-players">No players online</div></div>
    </div>
  </div>
</div>
<script>
async function api(p,b){try{const r=await fetch(p,{method:b?"POST":"GET",headers:b?{"Content-Type":"application/json"}:{},body:b?JSON.stringify(b):undefined});return await r.json()}catch(e){return null}}
async function act(a){await api("/api/action",{action:a})}
async function sc(){var v=document.getElementById("cmd").value.trim();if(!v)return;appendLog(">> "+v,"");await api("/api/cmd",{cmd:v});document.getElementById("cmd").value=""}
function sv(v){document.getElementById("cmd").value=v;sc()}
document.getElementById("cmd").addEventListener("keydown",function(e){if(e.key==="Enter")sc()});
function dc(val,type){if(val==="--"||val==null)return"#333";if(type==="tps"){var n=parseFloat(val);return n>=18?"#22c55e":n>=15?"#f59e0b":"#ef4444"}if(type==="pct"){var n=parseFloat(val);return n<60?"#22c55e":n<85?"#f59e0b":"#ef4444"}return"#22c55e"}
function appendLog(line,cls){var el=document.getElementById("log");var div=document.createElement("div");if(cls)div.className="log-line-"+cls;div.textContent=line;el.appendChild(div);if(el.children.length>200)el.removeChild(el.firstChild);el.scrollTop=el.scrollHeight}
async function poll(){
  var d=await api("/api/state");if(!d){setTimeout(poll,3000);return}
  var on=d.running;
  document.getElementById("status-dot").style.background=on?"var(--green)":"var(--red)";
  document.getElementById("status-dot").style.boxShadow=on?"0 0 8px var(--green)":"none";
  document.getElementById("srv-status-text").textContent=on?"Running":"Stopped";
  document.getElementById("poll-time").textContent=new Date().toLocaleTimeString();
  var tps=d.tps||"--";document.getElementById("hero-pct").textContent=tps;document.getElementById("hero-pct").className="hero-num"+(on?"":"off");
  document.getElementById("dot-ram").style.background=dc(d.ram_srv,"pct");document.getElementById("dot-rampct").style.background=dc(d.ram_pct,"pct");
  document.getElementById("dot-cpu").style.background=dc(d.cpu_srv,"pct");document.getElementById("dot-cpusys").style.background=dc(d.cpu_sys,"pct");
  document.getElementById("dot-up").style.background=on?"var(--green)":"#333";document.getElementById("dot-pl").style.background=on?"var(--blue)":"#333";
  document.getElementById("h-ram").textContent=d.ram_srv||"--";document.getElementById("h-rampct").textContent=d.ram_pct||"--";
  document.getElementById("h-cpu").textContent=d.cpu_srv||"--";document.getElementById("h-cpusys").textContent=d.cpu_sys||"--";
  document.getElementById("h-up").textContent=d.uptime||"--";document.getElementById("h-pl").textContent=d.players||"0";
  var pl=d.player_list||[];document.getElementById("player-count").textContent=(d.players||"0")+" online";
  var plEl=document.getElementById("player-list");
  if(pl.length===0){plEl.innerHTML='<div class="no-players">No players online</div>'}
  else{plEl.innerHTML=pl.map(function(nm){return'<div class="player-row"><span style="font-size:18px">👤</span><span class="player-name">'+nm+'</span><span class="dot dot-green"></span></div>'}).join("")}
  if(d.log&&d.log.length){d.log.forEach(function(l){var cls=l.startsWith(">>")||l.startsWith("<<")?"event":(l.toLowerCase().includes("warn")?"warn":"");appendLog(l,cls)})}
  setTimeout(poll,2000)
}
poll();
</script></body></html>"""

@app.route("/")
def index():
    if os.path.exists(HTML_PATH):
        try:
            with open(HTML_PATH, encoding="utf-8") as f: return f.read()
        except: pass
    return BUILTIN_HTML

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
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return path

    def _start_remote():
        if _remote_proc[0] and _remote_proc[0].poll() is None:
            show_toast("Already running.", T["muted"])
            return
        try:
            if importlib.util.find_spec("flask") is None:
                _set_st("Installing Flask…", T["hand"])
                subprocess.run([sys.executable, "-m", "pip", "install",
                               "flask", "--quiet"], creationflags=_NO_WIN)
        except:
            pass
        script = _write_flask()
        port = port_var.get().strip() or "5000"
        _remote_state_log_fn[0] = _append_state_log
        try:
            proc = subprocess.Popen([sys.executable, script, port, _state_file],
                                    creationflags=_NO_WIN, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            _remote_proc[0] = proc
            import socket
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s2.connect(("8.8.8.8", 80))
            lip = s2.getsockname()[0]
            s2.close()
            url = f"http://{lip}:{port}"
            _set_st("● Running", T["start"])
            _set_url(url)
            show_toast(f"Dashboard: {url}", T["start"], 5000)
            threading.Thread(target=_sync_loop, daemon=True).start()
        except Exception as ex:
            show_toast(f"Failed: {ex}", T["stop"])
            _set_st("● Error", T["stop"])

    def _stop_remote():
        if _remote_proc[0]:
            try:
                _remote_proc[0].terminate()
            except:
                pass
        _remote_proc[0] = _remote_state_log_fn[0] = None
        _set_st("● Stopped", T["stop"])
        _set_url("")
    br = ctk.CTkFrame(ctrl_h, fg_color="transparent")
    br.pack(side="right")
    ctk.CTkButton(br, text="▶ Start", width=74, height=26, font=ctk.CTkFont(
        size=11), fg_color=T["start"], hover_color=T["start"], text_color="#000", command=_start_remote).pack(side="left", padx=(0, 4))
    ctk.CTkButton(br, text="■ Stop", width=74, height=26, font=ctk.CTkFont(
        size=11), fg_color=T["stop"], hover_color=T["stop"], text_color="#fff", command=_stop_remote).pack(side="left", padx=(0, 4))
    ctk.CTkButton(br, text="Copy URL", width=78, height=26, font=ctk.CTkFont(size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=lambda: (
        app.clipboard_clear(), app.clipboard_append(_cur_url[0]), show_toast(f"Copied: {_cur_url[0]}", T["sync"]))).pack(side="left")
    gb, _ = card("How to use from your phone")
    ctk.CTkLabel(gb, text="1. Start Remote Dashboard above.\n2. Ensure your phone is on the same WiFi as this PC.\n3. Open the URL shown in your phone's browser.\n4. Use the web UI to start/stop, send commands, watch live logs.\n\nFor outside access, use Tailscale or playit.gg — don't expose port 5000 directly.",
                 font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()


def _build_dsub_multi(parent):
    MAX = 3
    slots = {}
    for i in range(MAX):
        slots[i] = {"proc": None, "stdin": None, "path_var": ctk.StringVar(
            value=" "), "log_box": None, "status": None, "running": False}
    _mc_wrap = ctk.CTkFrame(parent, fg_color="transparent")
    _mc_wrap.pack(side="top", fill="both", expand=True)
    parent = _mc_wrap
    parent.rowconfigure(0, weight=0)
    parent.rowconfigure(1, weight=1)
    parent.rowconfigure(2, weight=0)
    parent.columnconfigure(0, weight=1)
    tb = ctk.CTkFrame(
        parent, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0)
    tb.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(tb, text="⊞ MULTI SERVER CONTROL", font=ctk.CTkFont(
        size=13, weight="bold"), text_color=T["hand"]).pack(side="left", padx=12, pady=7)
    ctk.CTkLabel(tb, text="— up to 3 servers simultaneously", font=ctk.CTkFont(
        size=10), text_color=T["muted"]).pack(side="left")

    def _open_remote_tab(): show_toast(
        "Switch to Dashboard → Remote tab to open it.", T["sync"])
    ctk.CTkButton(tb, text="📱 Remote Dashboard", width=130, height=26, font=ctk.CTkFont(
        size=10), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=_open_remote_tab).pack(side="right", padx=8)
    ca = ctk.CTkFrame(parent, fg_color="transparent")
    ca.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
    for i in range(MAX):
        ca.columnconfigure(i, weight=1, uniform="col")
        ca.rowconfigure(0, weight=1)

    def _mclog(slot, msg): lb = slots[slot]["log_box"]; lb and lb.configure(
        state="normal") and lb.insert("end", msg+"\n") and lb.configure(state="disabled") and lb.see("end")

    def _mcst(slot, txt, col): slots[slot]["status"] and slots[slot]["status"].configure(
        text=txt, text_color=col)

    def _read_mc(slot, proc):
        for raw in iter(proc.stdout.readline, ""):
            raw and app.after(0, _mclog, slot, raw.rstrip())
        app.after(0, _mcst, slot, "● Stopped", T["stop"])
        slots[slot].update({"running": False, "proc": None, "stdin": None})

    def _start_mc(slot):
        path = slots[slot]["path_var"].get().strip()
        if not path or not os.path.isdir(path):
            show_toast(f"Server {slot+1}: invalid folder.", T["stop"])
            return
        if slots[slot]["running"]:
            show_toast(f"Server {slot+1} already running.", T["muted"])
            return
        s = load_settings()
        java = s.get("java_path", _DEFAULT_JAVA)
        jar = os.path.join(path, "server.jar")
        if not os.path.exists(jar):
            show_toast(f"Server {slot+1}: no server.jar.", T["stop"])
            return
        if not _check_eula(path):
            return
        try:
            kw = {"cwd": path, "stdin": subprocess.PIPE, "stdout": subprocess.PIPE,
                  "stderr": subprocess.STDOUT, "text": True, "bufsize": 1}
            if IS_WIN:
                kw["creationflags"] = _NO_WIN
            proc = subprocess.Popen(
                [java, "-Xms512M", "-Xmx2G", "-XX:+UseG1GC", "-jar", jar, "--nogui"], **kw)
            slots[slot].update(
                {"proc": proc, "stdin": proc.stdin, "running": True})
            _mcst(slot, "● Running", T["start"])
            threading.Thread(target=_read_mc, args=(
                slot, proc), daemon=True).start()
        except Exception as ex:
            show_toast(f"Server {slot+1} failed: {ex}", T["stop"])

    def _stop_mc(slot):
        proc = slots[slot]["proc"]
        if proc:
            try:
                slots[slot]["stdin"].write("stop\n")
                slots[slot]["stdin"].flush()
            except:
                pass
            app.after(3000, lambda p=proc: p.terminate()
                      if p.poll() is None else None)
        slots[slot].update({"running": False, "proc": None, "stdin": None})
        _mcst(slot, "● Stopped", T["stop"])
    for i in range(MAX):
        col = ctk.CTkFrame(
            ca, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
        col.grid(row=0, column=i, sticky="nsew", padx=3, pady=0)
        col.rowconfigure(2, weight=1)
        col.columnconfigure(0, weight=1)
        hdr = ctk.CTkFrame(col, fg_color=T["bg"], corner_radius=6)
        hdr.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 3))
        ctk.CTkLabel(hdr, text=f"Server {i+1}", font=ctk.CTkFont(
            size=12, weight="bold"), text_color=T["text"]).pack(side="left", padx=8, pady=5)
        st = ctk.CTkLabel(hdr, text="● Stopped", font=ctk.CTkFont(
            size=10, weight="bold"), text_color=T["stop"])
        st.pack(side="right", padx=8)
        slots[i]["status"] = st
        pf = ctk.CTkFrame(col, fg_color="transparent")
        pf.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 3))
        pf.columnconfigure(0, weight=1)
        ctk.CTkEntry(pf, textvariable=slots[i]["path_var"], height=26, font=ctk.CTkFont(size=10, family="Consolas"), fg_color=T["bg"],
                     border_color=T["border"], text_color=T["text"], placeholder_text=f"Server {i+1} folder…").grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ctk.CTkButton(pf, text="…", width=26, height=26, font=ctk.CTkFont(size=11), corner_radius=5, fg_color=T["bg"], border_width=1, border_color=T["border"], text_color=T[
                      "muted"], hover_color=T["border"], command=lambda s=i: slots[s]["path_var"].set(_tk_fd.askdirectory(title=f"Server {s+1}") or slots[s]["path_var"].get())).grid(row=0, column=1)
        br = ctk.CTkFrame(pf, fg_color="transparent")
        br.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        ctk.CTkButton(br, text="▶ Start", height=24, font=ctk.CTkFont(size=10), fg_color=T["start"], hover_color=T["start"], text_color="#000", command=lambda s=i: threading.Thread(
            target=_start_mc, args=(s,), daemon=True).start()).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ctk.CTkButton(br, text="■ Stop", height=24, font=ctk.CTkFont(
            size=10), fg_color=T["stop"], hover_color=T["stop"], text_color="#fff", command=lambda s=i: _stop_mc(s)).pack(side="left", expand=True, fill="x", padx=(2, 0))
        lb = ctk.CTkTextbox(col, font=ctk.CTkFont(size=10, family="Consolas"),
                            wrap="word", state="disabled", fg_color=T["bg"], text_color=T["text"])
        lb.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 6))
        slots[i]["log_box"] = lb
    chatbar = ctk.CTkFrame(
        parent, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0)
    chatbar.pack(fill="x")
    chatbar.columnconfigure(2, weight=1)
    tgt = ctk.StringVar(value="Server 1")
    ctk.CTkLabel(chatbar, text="Send to:", font=ctk.CTkFont(
        size=11), text_color=T["muted"]).grid(row=0, column=0, padx=(8, 4), pady=7)
    ctk.CTkOptionMenu(chatbar, values=["Server 1", "Server 2", "Server 3", "All Servers"], variable=tgt, font=ctk.CTkFont(size=11), width=110, height=28, fg_color=T["bg"], button_color=T["border"],
                      button_hover_color=T["muted"], text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"], dropdown_hover_color=T["border"]).grid(row=0, column=1, padx=(0, 5), pady=7)
    mc_cmd = ctk.CTkEntry(chatbar, height=28, font=ctk.CTkFont(
        size=12), fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text="command…")
    mc_cmd.grid(row=0, column=2, sticky="ew", padx=(0, 5), pady=7)

    def _mc_send(_e=None):
        cmd = mc_cmd.get().strip()
        if not cmd:
            return
        t = tgt.get()
        targets = list(range(MAX)) if t == "All Servers" else [
            int(t.split()[-1])-1]
        for s in targets:
            si = slots[s]["stdin"]
            if si:
                try:
                    si.write(cmd+"\n")
                    si.flush()
                    app.after(0, _mclog, s, f" > > {cmd}")
                except Exception as ex:
                    app.after(0, _mclog, s, f"[error] {ex}")
            else:
                app.after(0, _mclog, s, f"[Server {s+1} not running]")
        mc_cmd.delete(0, "end")
    mc_cmd.bind("<Return>", _mc_send)
    ctk.CTkButton(chatbar, text="Send", width=66, height=28, font=ctk.CTkFont(
        size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=_mc_send).grid(row=0, column=3, padx=(0, 8), pady=7)


def build_server_info_tab(parent):
    _build_ip_footer(parent)
    sub_bar = ctk.CTkFrame(
        parent, fg_color=T["card"], corner_radius=0, border_color=T["border"], border_width=1)
    sub_bar.pack(side="top", fill="x")
    sub_content = ctk.CTkFrame(parent, fg_color="transparent")
    sub_content.pack(side="top", fill="both", expand=True)
    SUB_TABS = [("players", "👥 Players"), ("plugins", "🔌 Plugins"),
                ("props", "⚙ Properties"), ("backup", "💾 Backup")]
    sub_frames = {k: ctk.CTkFrame(
        sub_content, fg_color="transparent") for k, _ in SUB_TABS}
    _sub_built = set()
    sub_btns = {}

    def show_sub(name):
        for f in sub_frames.values():
            f.pack_forget()
        for n, b in sub_btns.items():
            b.configure(fg_color=T["sync"] if n == name else "transparent",
                        text_color="#000" if n == name else T["muted"])
        if name not in _sub_built:
            _sub_built.add(name)
            {"players": lambda: _build_players_sub(sub_frames["players"]), "plugins": lambda: _build_plugins_sub(
                sub_frames["plugins"]), "props": lambda: _build_props_sub(sub_frames["props"]), "backup": lambda: _build_backup_sub(sub_frames["backup"])}[name]()
        sub_frames[name].pack(fill="both", expand=True)
    for key, label in SUB_TABS:
        b = ctk.CTkButton(sub_bar, text=label, width=110, height=26, font=ctk.CTkFont(size=11), corner_radius=5,
                          fg_color="transparent", text_color=T["muted"], hover_color=T["border"], command=lambda k=key: show_sub(k))
        b.pack(side="left", padx=(6 if key == "players" else 2, 2), pady=4)
        sub_btns[key] = b
    show_sub("players")


def _build_players_sub(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    hf = ctk.CTkFrame(
        scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12, 0))
    hdr = ctk.CTkFrame(hf, fg_color="transparent")
    hdr.pack(fill="x", padx=12, pady=(10, 4))
    ctk.CTkLabel(hdr, text="Online Players", font=ctk.CTkFont(
        size=12, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkButton(hdr, text="Refresh", width=66, height=22, font=ctk.CTkFont(
        size=10), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=lambda: send_server_cmd("list")).pack(side="right")
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    pf = ctk.CTkFrame(
        hf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8)
    pf.pack(fill="x", padx=12, pady=(6, 10))
    _head_cache = {}

    def _fetch_head(name, lbl):
        if name in _head_cache:
            try:
                app.after(0, lbl.configure, {
                          "image": _head_cache[name], "text": " "})
            except:
                return
        try:
            from PIL import Image
            import io
            url = f"https://mc-heads.net/avatar/{name}/32"
            with urllib.request.urlopen(url, timeout=4) as resp:
                img = Image.open(io.BytesIO(resp.read())).resize(
                    (28, 28), Image.Resampling.NEAREST)
                photo = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(28, 28))
                _head_cache[name] = photo
                app.after(0, lbl.configure, {"image": photo, "text": " "})
        except:
            pass

    def refresh_players():
        for w in pf.winfo_children():
            w.destroy()
        names = list(online_players.keys())
        if not names:
            ctk.CTkLabel(pf, text="No players online.", font=ctk.CTkFont(
                size=12), text_color=T["muted"]).pack(padx=12, pady=8)
        else:
            for nm in sorted(names):
                r = ctk.CTkFrame(pf, fg_color="transparent")
                r.pack(fill="x", padx=8, pady=4)
                head_lbl = ctk.CTkLabel(
                    r, text="👤", font=ctk.CTkFont(size=20), width=32)
                head_lbl.pack(side="left", padx=(0, 8))
                threading.Thread(target=_fetch_head, args=(
                    nm, head_lbl), daemon=True).start()
                info = ctk.CTkFrame(r, fg_color="transparent")
                info.pack(side="left", fill="y")
                ctk.CTkLabel(info, text=nm, font=ctk.CTkFont(
                    size=13, weight="bold"), text_color=T["text"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(info, text=f"joined {online_players.get(nm, '?')}", font=ctk.CTkFont(
                    size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
                ctk.CTkButton(r, text="Kick", width=48, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                              border_color=T["stop"], text_color=T["stop"], hover_color=T["border"], command=lambda n=nm: send_server_cmd(f"kick {n}")).pack(side="right")
                ctk.CTkButton(r, text="Msg", width=40, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                              border_color=T["sync"], text_color=T["sync"], hover_color=T["border"], command=lambda n=nm: send_server_cmd(f"msg {n} Hello!")).pack(side="right", padx=(0, 4))

    def _auto_refresh():
        global _players_refresh_id
        try:
            if not pf.winfo_exists():
                _players_refresh_id = None
                return
            refresh_players()
        except:
            return
        _players_refresh_id = app.after(2000, _auto_refresh)
    _auto_refresh()


def _build_plugins_sub(parent):
    import zipfile
    import json as _json
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    hf = ctk.CTkFrame(
        scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(12, 0))
    hdr = ctk.CTkFrame(hf, fg_color="transparent")
    hdr.pack(fill="x", padx=12, pady=(10, 4))
    ctk.CTkLabel(hdr, text="Plugins & Mods", font=ctk.CTkFont(
        size=12, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
    plf = ctk.CTkFrame(
        hf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8)
    plf.pack(fill="x", padx=12, pady=(6, 10))
    detail_frame = ctk.CTkFrame(
        scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)

    def _read_jar_meta(jar_path):
        info = {"name": os.path.basename(jar_path).replace(
            ".jar", ""), "version": "", "description": "", "author": "", "icon": None}
        try:
            with zipfile.ZipFile(jar_path, "r") as z:
                names = z.namelist()
                for yml_name in ("plugin.yml", "bungee.yml"):
                    if yml_name in names:
                        raw = z.read(yml_name).decode("utf-8", errors="ignore")
                        for line in raw.splitlines():
                            if ": " in line:
                                k, _, v = line.partition(": ")
                                k, v = k.strip(), v.strip().strip('\'"').strip()
                            if k == "name":
                                info["name"] = v
                            if k == "version":
                                info["version"] = v
                            if k == "description":
                                info["description"] = v
                            if k in ("author", "authors"):
                                info["author"] = v
                        break
                if "fabric.mod.json" in names:
                    try:
                        d = _json.loads(z.read("fabric.mod.json").decode(
                            "utf-8", errors="ignore"))
                        info["name"] = d.get("name", info["name"])
                        info["version"] = d.get("version", "")
                        info["description"] = d.get("description", "")
                        info["author"] = d.get("authors", [""])[0]
                        icon_path = d.get("icon", "")
                        info["icon"] = z.read(
                            icon_path) if icon_path in names else info["icon"]
                    except:
                        pass
        except:
            pass
        return info

    def _show_detail(jar_path, meta):
        for w in detail_frame.winfo_children():
            w.destroy()
        detail_frame.pack(fill="x", padx=18, pady=(8, 0))
        dh = ctk.CTkFrame(detail_frame, fg_color="transparent")
        dh.pack(fill="x", padx=12, pady=(10, 4))
        if meta["icon"]:
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(meta["icon"])).resize(
                    (48, 48), Image.Resampling.NEAREST).convert("RGBA")
                photo = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(48, 48))
                ctk.CTkLabel(dh, image=photo, text=" ").pack(
                    side="left", padx=(0, 12))
            except:
                ctk.CTkLabel(dh, text="🔌", font=ctk.CTkFont(
                    size=32)).pack(side="left", padx=(0, 12))
        else:
            ctk.CTkLabel(dh, text="🔌", font=ctk.CTkFont(
                size=32)).pack(side="left", padx=(0, 12))
        info_col = ctk.CTkFrame(dh, fg_color="transparent")
        info_col.pack(side="left", fill="y")
        ctk.CTkLabel(info_col, text=meta["name"], font=ctk.CTkFont(
            size=14, weight="bold"), text_color=T["text"], anchor="w").pack(anchor="w")
        meta["version"] and ctk.CTkLabel(info_col, text=f"v{meta['version']}", font=ctk.CTkFont(
            size=10), text_color=T["sync"], anchor="w").pack(anchor="w")
        meta["author"] and ctk.CTkLabel(info_col, text=f"by {meta['author']}", font=ctk.CTkFont(
            size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
        ctk.CTkButton(dh, text="✕", width=28, height=28, font=ctk.CTkFont(size=12), fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: detail_frame.pack_forget()).pack(side="right")
        ctk.CTkFrame(detail_frame, height=1,
                     fg_color=T["border"]).pack(fill="x", padx=12)
        ctk.CTkLabel(detail_frame, text=meta["description"] or "No description available.", font=ctk.CTkFont(
            size=12), text_color=T["muted"], wraplength=760, justify="left", anchor="w").pack(anchor="w", padx=14, pady=(8, 4))

    def refresh_plugins():
        for w in plf.winfo_children():
            w.destroy()
        detail_frame.pack_forget()
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        jars = []
        for sub in ("plugins", "mods"):
            d = os.path.join(path, sub)
            os.path.isdir(d) and jars.extend(
                [(sub, j) for j in sorted(os.listdir(d)) if j.endswith(".jar")])
        if not jars:
            ctk.CTkLabel(plf, text="No plugins or mods found.", font=ctk.CTkFont(
                size=12), text_color=T["muted"]).pack(padx=12, pady=8)
            return

        def _build_rows():
            for sub, j in jars:
                jar_path = os.path.join(path, sub, j)
                meta = _read_jar_meta(jar_path)
                icon_bytes = meta.get("icon")
                row = ctk.CTkFrame(plf, fg_color="transparent", cursor="hand2")
                row.pack(fill="x", padx=6, pady=2)
                ctk.CTkFrame(
                    row, height=1, fg_color=T["border"]).pack(fill="x")
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=4, pady=4)
                if icon_bytes:
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(icon_bytes)).resize(
                            (32, 32), Image.Resampling.NEAREST).convert("RGBA")
                        photo = ctk.CTkImage(
                            light_image=img, dark_image=img, size=(32, 32))
                        ctk.CTkLabel(inner, image=photo, text=" ").pack(
                            side="left", padx=(0, 10))
                    except:
                        ctk.CTkLabel(inner, text="🔌", font=ctk.CTkFont(
                            size=24)).pack(side="left", padx=(0, 10))
                else:
                    ctk.CTkLabel(inner, text="🔌", font=ctk.CTkFont(
                        size=24)).pack(side="left", padx=(0, 10))
                txt_col = ctk.CTkFrame(inner, fg_color="transparent")
                txt_col.pack(side="left", fill="y", expand=True)
                ctk.CTkLabel(txt_col, text=meta["name"], font=ctk.CTkFont(
                    size=12, weight="bold"), text_color=T["text"], anchor="w").pack(anchor="w")
                desc_short = (meta["description"][:80]+"…") if len(
                    meta.get("description", "")) > 80 else meta.get("description", f"{sub}/{j}")
                ctk.CTkLabel(txt_col, text=desc_short, font=ctk.CTkFont(
                    size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
                meta["version"] and ctk.CTkLabel(inner, text=f"v{meta['version']}", font=ctk.CTkFont(
                    size=9), text_color=T["sync"], fg_color=T["bg"], corner_radius=4, width=50).pack(side="right", padx=4)
                for w in (inner, txt_col, txt_col.winfo_children()):
                    w and w.bind("<Button-1>", lambda e,
                                 jp=jar_path, m=meta: _show_detail(jp, m))
        threading.Thread(target=_build_rows, daemon=True).start()
    refresh_plugins()
    ctk.CTkButton(hdr, text="Refresh", width=66, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=refresh_plugins).pack(side="right")


def _build_props_sub(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

    # ── Server Icon card ──────────────────────────────────
    icon_card = ctk.CTkFrame(
        scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
    icon_card.pack(fill="x", padx=18, pady=(12, 0))
    icon_hdr = ctk.CTkFrame(icon_card, fg_color="transparent")
    icon_hdr.pack(fill="x", padx=12, pady=(10, 4))
    ctk.CTkLabel(icon_hdr, text="Server Icon", font=ctk.CTkFont(
        size=12, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkFrame(icon_card, height=1, fg_color=T["border"]).pack(
        fill="x", padx=12)
    icon_body = ctk.CTkFrame(icon_card, fg_color="transparent")
    icon_body.pack(fill="x", padx=12, pady=(10, 12))
    # Preview + controls side by side
    _icon_preview = ctk.CTkLabel(icon_body, text="🖼", font=ctk.CTkFont(
        size=40), width=72, height=72, fg_color=T["bg"], corner_radius=8)
    _icon_preview.pack(side="left", padx=(0, 14))
    icon_info = ctk.CTkFrame(icon_body, fg_color="transparent")
    icon_info.pack(side="left", fill="y")
    _logo_lbl = ctk.CTkLabel(icon_info, text="No server-icon.png",
                             font=ctk.CTkFont(size=11), text_color=T["muted"])
    _logo_lbl.pack(anchor="w")
    ctk.CTkLabel(icon_info, text="64×64 PNG — shown in the Minecraft server list",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(2, 8))
    btn_row_icon = ctk.CTkFrame(icon_info, fg_color="transparent")
    btn_row_icon.pack(anchor="w")

    def _refresh_icon_preview():
        srv_path2 = load_settings().get("srv_path", _DEFAULT_SRV)
        icon_path = os.path.join(srv_path2, "server-icon.png")
        if os.path.exists(icon_path):
            try:
                from PIL import Image
                img = Image.open(icon_path).convert("RGBA").resize(
                    (64, 64), Image.Resampling.NEAREST)
                photo = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(64, 64))
                _icon_preview.configure(image=photo, text="")
                _logo_lbl.configure(text="✅ server-icon.png",
                                    text_color=T["start"])
            except:
                _logo_lbl.configure(
                    text="⚠ Icon unreadable", text_color=T["hand"])
        else:
            _logo_lbl.configure(text="No server-icon.png",
                                text_color=T["muted"])

    def _set_server_icon():
        path = _tk_fd.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg")], title="Select Server Icon")
        if not path:
            return
        srv_path = load_settings().get("srv_path", _DEFAULT_SRV)
        try:
            from PIL import Image
            img = Image.open(path).convert("RGBA").resize(
                (64, 64), Image.Resampling.LANCZOS)
            out = os.path.join(srv_path, "server-icon.png")
            img.save(out, "PNG")
            show_toast("Server icon saved!", T["start"])
            _refresh_icon_preview()
        except Exception as ex:
            show_toast(f"Icon failed: {ex}", T["stop"])

    def _clear_server_icon():
        srv_path = load_settings().get("srv_path", _DEFAULT_SRV)
        icon_path = os.path.join(srv_path, "server-icon.png")
        try:
            os.remove(icon_path)
            show_toast("Icon removed.", T["muted"])
            _refresh_icon_preview()
        except:
            show_toast("No icon to remove.", T["muted"])
    ctk.CTkButton(btn_row_icon, text="Change Icon", width=100, height=28, font=ctk.CTkFont(
        size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=_set_server_icon).pack(side="left", padx=(0, 6))
    ctk.CTkButton(btn_row_icon, text="Remove", width=70, height=28, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["stop"], text_color=T["stop"], hover_color=T["border"], command=_clear_server_icon).pack(side="left")
    _refresh_icon_preview()

    # ── Properties card ───────────────────────────────────
    hf = ctk.CTkFrame(
        scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
    hf.pack(fill="x", padx=18, pady=(10, 0))
    props_hdr = ctk.CTkFrame(hf, fg_color="transparent")
    props_hdr.pack(fill="x", padx=12, pady=(10, 4))
    ctk.CTkLabel(props_hdr, text="server.properties", font=ctk.CTkFont(
        size=12, weight="bold"), text_color=T["text"]).pack(side="left")
    ctk.CTkFrame(hf, height=1, fg_color=T["border"]).pack(fill="x", padx=12)

    # Categorised properties
    PROP_GROUPS = [
        ("🌍 World", [
            ("level-name",       "World Name",        "world"),
            ("level-seed",       "Seed",               ""),
            ("level-type",       "World Type",         "minecraft:default"),
            ("gamemode",         "Default Gamemode",   "survival"),
            ("difficulty",       "Difficulty",         "easy"),
            ("allow-nether",     "Allow Nether",       "true"),
            ("allow-flight",     "Allow Flight",       "false"),
            ("spawn-monsters",   "Spawn Monsters",     "true"),
            ("spawn-animals",    "Spawn Animals",      "true"),
            ("spawn-npcs",       "Spawn NPCs (Villagers)", "true"),
        ]),
        ("👥 Players", [
            ("max-players",      "Max Players",        "20"),
            ("online-mode",      "Online Mode",        "true"),
            ("pvp",              "PvP",                "true"),
            ("white-list",       "Whitelist",          "false"),
            ("enforce-whitelist", "Enforce Whitelist",  "false"),
            ("op-permission-level", "Op Permission Level", "4"),
            ("player-idle-timeout", "Idle Timeout (min)", "0"),
        ]),
        ("🌐 Network", [
            ("server-port",      "Port",               "25565"),
            ("server-ip",        "Bind IP",            ""),
            ("motd",             "MOTD",               "A Minecraft Server"),
            ("resource-pack",    "Resource Pack URL",  ""),
            ("resource-pack-sha1", "Resource Pack SHA1", ""),
            ("enable-status",    "Show in Server List", "true"),
            ("query.port",       "Query Port",         "25565"),
            ("enable-query",     "Enable Query",       "false"),
            ("enable-rcon",      "Enable RCON",        "false"),
            ("rcon.port",        "RCON Port",          "25575"),
            ("rcon.password",    "RCON Password",      ""),
        ]),
        ("⚙ Performance", [
            ("view-distance",    "View Distance",      "10"),
            ("simulation-distance", "Simulation Distance", "4"),
            ("spawn-protection", "Spawn Protection Radius", "16"),
            ("max-build-height", "Max Build Height",   "320"),
            ("max-tick-time",    "Max Tick Time (ms)", "60000"),
            ("max-world-size",   "Max World Size",     "29999984"),
            ("entity-broadcast-range-percentage", "Entity Broadcast %", "100"),
            ("network-compression-threshold", "Compression Threshold", "256"),
            ("use-native-transport", "Native Transport", "true"),
        ]),
        ("🔧 Advanced", [
            ("enable-command-block", "Command Blocks",  "false"),
            ("force-gamemode",   "Force Gamemode",     "false"),
            ("hardcore",         "Hardcore Mode",      "false"),
            ("generate-structures", "Generate Structures", "true"),
            ("snooper-enabled",  "Snooper",            "false"),
            ("broadcast-rcon-to-ops", "Broadcast RCON to Ops", "true"),
            ("log-ips",          "Log Player IPs",     "true"),
            ("hide-online-players", "Hide Online Players", "false"),
            ("previews-chat",    "Preview Chat",       "false"),
            ("sync-chunk-writes", "Sync Chunk Writes",  "true"),
        ]),
    ]

    props_vars = {}

    def load_props():
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        kv = {}
        try:
            with open(os.path.join(path, "server.properties"), encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        kv[k.strip()] = v.strip()
        except:
            pass
        return kv

    def save_props():
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        pfile = os.path.join(path, "server.properties")
        try:
            try:
                lines = open(pfile, encoding="utf-8",
                             errors="ignore").readlines()
            except:
                lines = []
            updated = set()
            new_lines = []
            for line in lines:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k = s.partition("=")[0].strip()
                    new_lines.append(
                        f"{k}={props_vars[k].get()}\n" if k in props_vars else line)
                    if k in props_vars:
                        updated.add(k)
                else:
                    new_lines.append(line)
            for k in props_vars:
                if k not in updated:
                    new_lines.append(f"{k}={props_vars[k].get()}\n")
            with open(pfile, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)
            show_toast("Saved! Restart server to apply.", T["start"])
        except Exception as ex:
            show_toast(f"Save failed: {ex}", T["stop"])

    kv = load_props()

    # Active group tab
    _active_grp = [0]
    grp_frames = []
    tab_btns = []

    grp_tab_bar = ctk.CTkFrame(hf, fg_color="transparent")
    grp_tab_bar.pack(fill="x", padx=12, pady=(6, 0))
    grp_content = ctk.CTkFrame(hf, fg_color="transparent")
    grp_content.pack(fill="x", padx=12, pady=(4, 8))

    def show_grp(idx):
        _active_grp[0] = idx
        for i, (frame, btn) in enumerate(zip(grp_frames, tab_btns)):
            frame.pack_forget()
            btn.configure(fg_color=T["sync"] if i == idx else "transparent",
                          text_color="#000" if i == idx else T["muted"])
        grp_frames[idx].pack(fill="x")

    for gi, (group_name, props) in enumerate(PROP_GROUPS):
        # Tab button
        tb = ctk.CTkButton(grp_tab_bar, text=group_name, height=24, width=100,
                           font=ctk.CTkFont(size=10), corner_radius=6,
                           fg_color=T["sync"] if gi == 0 else "transparent",
                           text_color="#000" if gi == 0 else T["muted"],
                           hover_color=T["border"], command=lambda i=gi: show_grp(i))
        tb.pack(side="left", padx=(0, 4))
        tab_btns.append(tb)
        # Grid frame for this group
        gf = ctk.CTkFrame(grp_content, fg_color="transparent")
        grp_frames.append(gf)
        gf.columnconfigure((0, 1, 2), weight=1)
        for pi, (key, label, default) in enumerate(props):
            var = ctk.StringVar(value=kv.get(key, default))
            props_vars[key] = var
            cell = ctk.CTkFrame(gf, fg_color="transparent")
            cell.grid(row=pi//3, column=pi % 3, padx=3, pady=2, sticky="ew")
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(
                size=10), text_color=T["muted"], anchor="w").pack(anchor="w")
            ctk.CTkEntry(cell, textvariable=var, height=26, font=ctk.CTkFont(size=11, family="Consolas"),
                         fg_color=T["card"], border_color=T["border"], text_color=T["text"]).pack(fill="x")

    show_grp(0)

    # Save + reload button row
    save_row = ctk.CTkFrame(hf, fg_color="transparent")
    save_row.pack(fill="x", padx=12, pady=(4, 12))
    ctk.CTkButton(save_row, text="💾 Save server.properties", height=32, corner_radius=8,
                  font=ctk.CTkFont(size=12, weight="bold"), fg_color=T["start"], hover_color=T["start"],
                  text_color="#000", command=save_props).pack(side="left")
    ctk.CTkButton(save_row, text="↺ Reload from file", height=32, corner_radius=8,
                  font=ctk.CTkFont(size=12), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                  command=lambda: [v.set(load_props().get(k, d)) for _, props in PROP_GROUPS for k, _, d in props for v in [props_vars[k]] if k in props_vars] or show_toast("Reloaded from file", T["sync"])).pack(side="left", padx=8)
    ctk.CTkButton(save_row, text="📂 Open File", height=32, corner_radius=8,
                  font=ctk.CTkFont(size=12), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                  command=lambda: _open_folder(load_settings().get("srv_path", _DEFAULT_SRV))).pack(side="left")
    ctk.CTkLabel(save_row, text="⚠ Restart server to apply changes",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="right")


def _build_backup_sub(parent):
    import zipfile
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    s = load_settings()
    bdir_var = ctk.StringVar(value=s.get("backup_dir", ""))
    keep_var = ctk.StringVar(value=str(s.get("backup_keep", 10)))
    auto_var = ctk.BooleanVar(value=s.get("backup_auto", False))
    mins_var = ctk.StringVar(value=str(s.get("backup_interval_mins", 30)))
    _btimer = [None]

    def card(title):
        f = ctk.CTkFrame(
            scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        f.pack(fill="x", padx=18, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(
            size=12, weight="bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=12, pady=(8, 10))
        return b, h
    tb, _ = card("📖 How to use Backups")
    tutorial = "Backups create a .zip snapshot of your world folders.\nQuick start:\n1. Set Destination (leave blank for server/backups/)\n2. Set 'Keep last N'\n3. Click 'Create Backup Now'\n4. Toggle auto-backup + set interval.\nRestore: Stop server → Extract backup → Replace world/ folders → Start."
    ctk.CTkLabel(tb, text=tutorial, font=ctk.CTkFont(
        size=11), text_color=T["muted"], justify="left", wraplength=820).pack(anchor="w")
    sb, _ = card("Backup Settings")
    r0 = ctk.CTkFrame(sb, fg_color="transparent")
    r0.pack(fill="x", pady=3)
    ctk.CTkLabel(r0, text="Destination", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkEntry(r0, textvariable=bdir_var, height=26, font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text="blank = server/backups/").pack(side="left", fill="x", expand=True, padx=(0, 6))
    ctk.CTkButton(r0, text="Browse", width=64, height=26, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: (bdir_var.set(_tk_fd.askdirectory(title="Backup destination")))).pack(side="left")
    for label, var in [("Keep last N", keep_var), ("Interval (mins)", mins_var)]:
        r = ctk.CTkFrame(sb, fg_color="transparent")
        r.pack(fill="x", pady=3)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(
            size=12), text_color=T["text"], width=180, anchor="w").pack(side="left")
        e = ctk.CTkEntry(r, textvariable=var, width=80, height=26, font=ctk.CTkFont(
            size=12, family="Consolas"), fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
        e.pack(side="left")
        e.bind("<FocusOut>", lambda *_: update_setting("backup_keep",
               int(keep_var.get() or 10)))
        e.bind("<Return>", lambda *_: update_setting("backup_interval_mins",
               int(mins_var.get() or 30)))
    r2 = ctk.CTkFrame(sb, fg_color="transparent")
    r2.pack(fill="x", pady=3)
    ctk.CTkLabel(r2, text="Auto backup", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkSwitch(r2, text="", variable=auto_var, command=lambda: update_setting(
        "backup_auto", auto_var.get()), button_color=T["sync"], progress_color=T["sync"]).pack(side="left")

    def _get_dest(): custom = bdir_var.get().strip(); path = load_settings().get("srv_path", _DEFAULT_SRV); return custom if os.path.isdir(custom) else (
        os.path.join(path, "backups") if os.makedirs(os.path.join(path, "backups"), exist_ok=True) or True else os.path.join(path, "backups"))
    mb, _ = card("Create Backup")
    wrld_var = ctk.StringVar(value="world,world_nether,world_the_end")
    r4 = ctk.CTkFrame(mb, fg_color="transparent")
    r4.pack(fill="x", pady=3)
    ctk.CTkLabel(r4, text="Folders", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkEntry(r4, textvariable=wrld_var, height=26, font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]).pack(side="left", fill="x", expand=True)
    bk_st = ctk.CTkLabel(mb, text="", font=ctk.CTkFont(
        size=11), text_color=T["muted"])
    bk_st.pack(anchor="w", pady=(4, 0))
    bk_pg = ctk.CTkProgressBar(mb, height=5)
    bk_pg.set(0)

    def _do_backup(auto=False):
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        dest = _get_dest()
        folders = [f.strip() for f in wrld_var.get().split(",") if f.strip()]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zname = os.path.join(
            dest, f"backup_{'auto' if auto else 'manual'}_{ts}.zip")

        def _work():
            try:
                app.after(0, lambda: bk_st.configure(
                    text="Creating…", text_color=T["sync"]))
                app.after(0, lambda: (bk_pg.set(0),
                          bk_pg.pack(fill="x", pady=(4, 0))))
                total = sum(sum(1 for _ in os.walk(os.path.join(path, f)))
                            for f in folders if os.path.isdir(os.path.join(path, f)))
                done = [0]
                with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED) as zf:
                    for folder in folders:
                        src = os.path.join(path, folder)
                        if not os.path.isdir(src):
                            continue
                        for root2, dirs, files in os.walk(src):
                            for file in files:
                                fp = os.path.join(root2, file)
                                zf.write(fp, os.path.relpath(fp, path))
                                done[0] += 1
                                total and app.after(
                                    0, bk_pg.set, min(done[0]/total, 1.0))
                size_mb = os.path.getsize(zname)/1048576
                app.after(0, lambda: bk_st.configure(
                    text=f"Done! {size_mb:.1f} MB", text_color=T["start"]))
                app.after(0, bk_pg.set, 1.0)
                app.after(0, show_toast,
                          f"Backup done ({size_mb:.1f} MB)", T["start"])
                app.after(0, _refresh_bklist)
            except Exception as ex:
                app.after(0, lambda: bk_st.configure(
                    text=f"Failed: {ex}", text_color=T["stop"]))
        threading.Thread(target=_work, daemon=True).start()
    ctk.CTkButton(mb, text="Create Backup Now", height=32, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000", command=lambda: threading.Thread(target=_do_backup, daemon=True).start()).pack(anchor="w", pady=(6, 0))
    lb, lh = card("Saved Backups")
    blf = ctk.CTkScrollableFrame(
        lb, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=8, height=200)
    blf.pack(fill="x")

    def _refresh_bklist():
        for w in blf.winfo_children():
            w.destroy()
            dest = _get_dest()
        try:
            zips = sorted([f for f in os.listdir(dest) if f.endswith(
                ".zip")], key=lambda f: os.path.getmtime(os.path.join(dest, f)), reverse=True)
        except:
            zips = []
        if not zips:
            ctk.CTkLabel(blf, text="No backups found.", font=ctk.CTkFont(
                size=12), text_color=T["muted"]).pack(padx=12, pady=8)
            return
        for z in zips:
            full = os.path.join(dest, z)
            sz = os.path.getsize(full)/1048576
            mt = datetime.fromtimestamp(
                os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
            row = ctk.CTkFrame(blf, fg_color="transparent")
            row.pack(fill="x", padx=6, pady=2)
            ctk.CTkLabel(row, text=z, font=ctk.CTkFont(
                size=10, family="Consolas"), text_color=T["text"]).pack(side="left")
            ctk.CTkLabel(row, text=f"{sz:.1f}MB {mt}", font=ctk.CTkFont(
                size=10), text_color=T["muted"]).pack(side="left", padx=6)
            ctk.CTkButton(row, text="Delete", width=54, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1, border_color=T["stop"], text_color=T[
                          "stop"], hover_color=T["border"], command=lambda p=full, n=z: (os.remove(p), show_toast(f"Deleted {n}", T["stop"]), _refresh_bklist())).pack(side="right")
            ctk.CTkButton(row, text="Open", width=46, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                          border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda d=dest: _open_folder(d)).pack(side="right", padx=(0, 4))
    _refresh_bklist()
    ctk.CTkButton(lh, text="Refresh", width=66, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_refresh_bklist).pack(side="right")
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()


def build_docker_tab(parent):
    _build_ip_footer(parent)
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(side="top", fill="both", expand=True)

    def card(title): f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12); f.pack(fill="x", padx=18, pady=(10, 0)); h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=12, pady=(10, 4)); ctk.CTkLabel(
        h, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=T["text"]).pack(side="left"); ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12); b = ctk.CTkFrame(f, fg_color="transparent"); b.pack(fill="x", padx=12, pady=(8, 10)); return b, h
    ab, _ = card("Docker Support")
    dok = False
    try:
        dok = subprocess.run("docker version", shell=True, capture_output=True,
                             text=True, creationflags=_NO_WIN, timeout=5).returncode == 0
    except:
        pass
    ctk.CTkLabel(ab, text="Run Minecraft in Docker. No Java needed.\n`docker compose up` starts instantly.\nPersistent data mounted to server folder.",
                 font=ctk.CTkFont(size=12), text_color=T["muted"], wraplength=820, justify="left").pack(anchor="w")
    ctk.CTkLabel(ab, text="● Docker available" if dok else "● Docker not found", font=ctk.CTkFont(
        size=11, weight="bold"), text_color=T["start"] if dok else T["stop"]).pack(anchor="w", pady=(6, 0))
    s = load_settings()
    dc_image = ctk.StringVar(value=s.get(
        "docker_image", "itzg/minecraft-server"))
    dc_port = ctk.StringVar(value=s.get("docker_port", "25565"))
    dc_ram = ctk.StringVar(value=s.get("docker_ram", "2G"))
    dc_type = ctk.StringVar(value=s.get("docker_type", "PAPER"))
    dc_ver = ctk.StringVar(value=s.get("docker_version", "LATEST"))
    dc_name = ctk.StringVar(value=s.get("docker_name", "mc-server"))

    def _save_dc(*_):
        for k, v in [("docker_image", dc_image), ("docker_port", dc_port), ("docker_ram", dc_ram), ("docker_type", dc_type), ("docker_version", dc_ver), ("docker_name", dc_name)]:
            update_setting(k, v.get())
    cc, ch = card("Docker Compose Config")

    def row_e(parent, label, var, w=160, ph=""): r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", pady=2); ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12), text_color=T["text"], width=180, anchor="w").pack(side="left"); e = ctk.CTkEntry(
        r, textvariable=var, width=w, height=26, font=ctk.CTkFont(size=11, family="Consolas"), fg_color=T["bg"], border_color=T["border"], text_color=T["text"], placeholder_text=ph); e.pack(side="left"); e.bind("<FocusOut>", _save_dc); e.bind("<Return>", _save_dc)
    row_e(cc, "Container name", dc_name, ph="mc-server")
    row_e(cc, "Docker image", dc_image, w=280, ph="itzg/minecraft-server")
    row_e(cc, "Port", dc_port, ph="25565")
    row_e(cc, "RAM limit", dc_ram, ph="2G")
    rt = ctk.CTkFrame(cc, fg_color="transparent")
    rt.pack(fill="x", pady=2)
    ctk.CTkLabel(rt, text="Server type", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkOptionMenu(rt, values=["PAPER", "PURPUR", "VANILLA", "FABRIC", "FORGE", "SPIGOT"], variable=dc_type, command=lambda _: _save_dc(), font=ctk.CTkFont(size=12), width=130, height=26, fg_color=T["bg"],
                      button_color=T["border"], button_hover_color=T["muted"], text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"], dropdown_hover_color=T["border"]).pack(side="left", padx=(0, 10))
    row_e(cc, "MC version", dc_ver, w=100, ph="LATEST")
    pv_box = None

    def _gen():
        path = load_settings().get("srv_path", _DEFAULT_SRV)
        yaml = f"""version: "3.8"\nservices:\n  {dc_name.get()}:\n    image: {dc_image.get()}\n    container_name: {dc_name.get()}\n    environment:\n      EULA: "TRUE"\n      TYPE: "{dc_type.get()}"\n      VERSION: "{dc_ver.get()}"\n      MEMORY: "{dc_ram.get()}"\n      USE_AIKAR_FLAGS: "true"\n    ports:\n      - "{dc_port.get()}:{dc_port.get()}"\n    volumes:\n      - ./data:/data\n    restart: unless-stopped\n"""
        dest = os.path.join(path, "docker-compose.yml")
        try:
            with open(dest, "w") as f2:
                f2.write(yaml)
                show_toast("docker-compose.yml written!", T["start"])
            if pv_box:
                pv_box.configure(state="normal")
                pv_box.delete("1.0", "end")
                pv_box.insert("end", yaml)
                pv_box.configure(state="disabled")
        except Exception as ex:
            show_toast(f"Error: {ex}", T["stop"])
    ctk.CTkButton(ch, text="Generate compose", height=24, width=140, font=ctk.CTkFont(
        size=11), fg_color=T["start"], hover_color=T["start"], text_color="#000", command=_gen).pack(side="right")
    pb, _ = card("docker-compose.yml Preview")
    pv_box = ctk.CTkTextbox(pb, font=ctk.CTkFont(size=11, family="Consolas"),
                            height=160, fg_color=T["bg"], text_color=T["text"], state="disabled")
    pv_box.pack(fill="x")
    cp = os.path.join(load_settings().get(
        "srv_path", _DEFAULT_SRV), "docker-compose.yml")
    if os.path.exists(cp):
        try:
            pv_box.configure(state="normal")
            pv_box.insert("end", open(cp).read())
            pv_box.configure(state="disabled")
        except:
            pass
    ctrl_b, ctrl_h = card("Container Control")
    dc_st = ctk.CTkLabel(ctrl_b, text="● Unknown", font=ctk.CTkFont(
        size=13, weight="bold"), text_color=T["muted"])
    dc_st.pack(side="left")
    dc_log = ctk.CTkTextbox(ctrl_b, font=ctk.CTkFont(size=10, family="Consolas"),
                            height=110, fg_color=T["bg"], text_color=T["text"], state="disabled")

    def _dclog(msg): dc_log.configure(state="normal"); dc_log.insert(
        "end", msg+"\n"); dc_log.configure(state="disabled"); dc_log.see("end")

    def _dc_status():
        name = dc_name.get().strip() or "mc-server"
        try:
            r = subprocess.run(f"docker inspect --format={{{{.State.Status}}}} {name}",
                               shell=True, capture_output=True, text=True, creationflags=_NO_WIN, timeout=5)
            st = r.stdout.strip()
            dc_st.configure(text=f"● {st.capitalize() if st else 'Not created'}",
                            text_color=T["start"] if st == "running" else T["muted"] if st else T["stop"])
        except:
            dc_st.configure(text="● Docker unavailable", text_color=T["stop"])

    def _run_dc(cmd_str, label):
        path = load_settings().get("srv_path", _DEFAULT_SRV)

        def _w():
            app.after(0, _dclog, f"$ {cmd_str}")
            try:
                proc = subprocess.Popen(cmd_str, shell=True, cwd=path, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, creationflags=_NO_WIN)
                [app.after(0, _dclog, line.rstrip()) for line in proc.stdout]
                proc.wait()
                app.after(0, _dc_status)
                app.after(0, show_toast, f"{label} done", T["start"])
            except Exception as ex:
                app.after(0, _dclog, f"Error: {ex}")
        threading.Thread(target=_w, daemon=True).start()
    name = dc_name.get().strip() or "mc-server"
    br = ctk.CTkFrame(ctrl_h, fg_color="transparent")
    br.pack(side="right")
    for label, cmd, fc in [("▶ Up", "docker compose up -d", T["start"]), ("■ Down", "docker compose down", T["stop"]), ("↺ Restart", f"docker restart {name}", T["sync"]), ("Logs", f"docker logs --tail=50 {name}", T["muted"])]:
        ctk.CTkButton(br, text=label, width=74, height=26, font=ctk.CTkFont(size=11), fg_color=fc, hover_color=fc,
                      text_color="#000" if fc != T["stop"] else "#fff", command=lambda c=cmd, l=label: _run_dc(c, l)).pack(side="left", padx=(0, 3))
    ctk.CTkButton(br, text="Status", width=60, height=26, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=_dc_status).pack(side="left")
    ctk.CTkButton(br, text="Pull Image", width=80, height=26, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: _run_dc(f"docker pull {dc_image.get()}", "Pull")).pack(side="left", padx=(3, 0))
    dc_log.pack(fill="x", pady=(8, 0))
    app.after(500, _dc_status)
    def _auto_dc_status(): _dc_status(); dc_st.after(10000, _auto_dc_status)
    app.after(1000, _auto_dc_status)
    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()


def build_modpack_tab(parent):
    import urllib.parse
    import json as _json
    import io
    import http.client
    import ssl as _ssl
    import gzip as _gz
    import zlib as _zl
    import zipfile as _zipfile
    try:
        import brotli as _brotli
    except ImportError:
        try:
            import brotlicffi as _brotli
        except ImportError:
            _brotli = None

    _MODRINTH_API = "https://api.modrinth.com/v2"
    _API_HDR = {
        "User-Agent": "MC-CTRL/2.1 (github.com/GamerMahir07)", "Accept": "application/json"}
    _IMG_HDR = {"User-Agent": "Mozilla/5.0",
                "Accept": "image/*,*/*;q=0.8", "Referer": "https://modrinth.com/"}
    _icon_cache = {}

    def _http_get(url, headers=None, timeout=10, _depth=0):
        if _depth > 5:
            return b""
        headers = headers or _API_HDR
        try:
            p = urllib.parse.urlparse(url)
            ctx = _ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _ssl.CERT_NONE
            host = p.netloc
            if p.scheme == "https":
                raw_conn = http.client.HTTPSConnection(
                    host, timeout=timeout, context=ctx)
            else:
                raw_conn = http.client.HTTPConnection(host, timeout=timeout)
            path_q = (p.path or "/") + ("?" + p.query if p.query else "")
            raw_conn.request("GET", path_q, headers=dict(headers, Host=host))
            resp = raw_conn.getresponse()
            if resp.status in (301, 302, 303, 307, 308):
                loc = resp.getheader("Location", "")
                resp.read()
                raw_conn.close()
                return _http_get(loc, headers, timeout, _depth + 1) if loc else b""
            data = resp.read()
            raw_conn.close()
            enc = resp.getheader("Content-Encoding", "")
            if enc == "gzip":
                data = _gz.decompress(data)
            elif enc == "deflate":
                data = _zl.decompress(data)
            elif enc == "br" and _brotli:
                data = _brotli.decompress(data)
            return data
        except Exception:
            return b""

    def _api_get(path_or_url):
        url = path_or_url if path_or_url.startswith(
            "http") else _MODRINTH_API + path_or_url
        return _json.loads(_http_get(url, _API_HDR))

    def _fetch_icon_async(url, lbl, size=40):
        if not url:
            return
        if url in _icon_cache:
            try:
                app.after(0, lbl.configure, {
                          "image": _icon_cache[url], "text": " "})
            except:
                pass
            return

        def _work():
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(_http_get(url, _IMG_HDR))).convert(
                    "RGBA").resize((size, size), Image.Resampling.NEAREST)
                photo = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(size, size))
                _icon_cache[url] = photo
                app.after(0, lbl.configure, {"image": photo, "text": " "})
            except:
                pass
        threading.Thread(target=_work, daemon=True).start()

    def _strip_md(text):
        import re
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    _build_ip_footer(parent)
    shell = ctk.CTkFrame(parent, fg_color="transparent")
    shell.pack(side="top", fill="both", expand=True)
    shell.rowconfigure(0, weight=1)
    shell.columnconfigure(0, weight=0)  # sidebar
    shell.columnconfigure(1, weight=1)  # results
    shell.columnconfigure(2, weight=0)  # detail

    # ── SIDEBAR ───────────────────────────────────────────
    sidebar = ctk.CTkFrame(
        shell, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0, width=240)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.rowconfigure(2, weight=1)
    sidebar.columnconfigure(0, weight=1)

    shdr = ctk.CTkFrame(sidebar, fg_color=T["bg"], corner_radius=0)
    shdr.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(shdr, text="📦  Modrinth", font=ctk.CTkFont(
        size=13, weight="bold"), text_color=T["text"]).pack(side="left", padx=12, pady=9)

    type_bar = ctk.CTkFrame(sidebar, fg_color=T["bg"], corner_radius=0)
    type_bar.grid(row=1, column=0, sticky="ew")
    ctk.CTkFrame(type_bar, height=1, fg_color=T["border"]).pack(fill="x")
    type_var = ["modpack"]
    type_btns = {}
    tb_row = ctk.CTkFrame(type_bar, fg_color="transparent")
    tb_row.pack(fill="x", padx=6, pady=5)

    search_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    search_frame.grid(row=2, column=0, sticky="nsew")
    search_frame.rowconfigure(1, weight=1)
    search_frame.columnconfigure(0, weight=1)

    sq_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
    sq_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
    sq_frame.columnconfigure(0, weight=1)
    query_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(sq_frame, textvariable=query_var, height=28, font=ctk.CTkFont(size=12),
                                fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                                placeholder_text="Search Modrinth…")
    search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    search_btn = ctk.CTkButton(sq_frame, text="🔍", width=32, height=28, fg_color=T["sync"],
                               hover_color=T["sync"], text_color="#000", command=lambda: _do_search())
    search_btn.grid(row=0, column=1)
    search_entry.bind("<Return>", lambda e: _do_search())
    result_lbl = ctk.CTkLabel(
        sq_frame, text="", font=ctk.CTkFont(size=9), text_color=T["muted"])
    result_lbl.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

    results_scroll = ctk.CTkScrollableFrame(
        search_frame, fg_color="transparent")
    results_scroll.grid(row=1, column=0, sticky="nsew")
    results_scroll.columnconfigure(0, weight=1)

    page_footer = ctk.CTkFrame(search_frame, fg_color=T["bg"], corner_radius=0)
    page_footer.grid(row=2, column=0, sticky="ew")
    ctk.CTkFrame(page_footer, height=1, fg_color=T["border"]).pack(fill="x")
    pg_row = ctk.CTkFrame(page_footer, fg_color="transparent")
    pg_row.pack(fill="x", padx=8, pady=5)
    pg_lbl = ctk.CTkLabel(pg_row, text="", font=ctk.CTkFont(
        size=10), text_color=T["muted"])
    pg_lbl.pack(side="left")
    _page = [0]
    _total = [0]
    PER_PAGE = 20

    def _prev_page():
        if _page[0] > 0:
            _page[0] -= 1
            _do_search(paginate=True)

    def _next_page():
        if (_page[0]+1)*PER_PAGE < _total[0]:
            _page[0] += 1
            _do_search(paginate=True)

    for txt, cmd in [("◀", _prev_page), ("▶", _next_page)]:
        ctk.CTkButton(pg_row, text=txt, width=32, height=24, fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                      command=cmd).pack(side="right", padx=2)

    # Type filter buttons
    def _set_type(t, key):
        type_var[0] = t
        for k, b in type_btns.items():
            b.configure(fg_color=T["sync"] if k == key else "transparent",
                        text_color="#000" if k == key else T["muted"])
        _do_search()
    for key, label, ftype in [("packs", "Modpacks", "modpack"), ("mods", "Mods", "mod"), ("plugins", "Plugins", "plugin"), ("local", "💾 Local", "installed")]:
        b = ctk.CTkButton(tb_row, text=label, height=26, width=60, font=ctk.CTkFont(size=10),
                          fg_color=T["sync"] if key == "packs" else "transparent",
                          text_color="#000" if key == "packs" else T["muted"],
                          hover_color=T["border"], corner_radius=6,
                          command=lambda f=ftype, k=key: _set_type(f, k))
        b.pack(side="left", padx=2)
        type_btns[key] = b

    # ── CENTER (results) ──────────────────────────────────
    center = ctk.CTkFrame(shell, fg_color="transparent")
    center.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
    center.rowconfigure(1, weight=1)
    center.columnconfigure(0, weight=1)

    cbar = ctk.CTkFrame(
        center, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0)
    cbar.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(cbar, text="Sort", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(10, 4), pady=6)
    sort_var = ctk.StringVar(value="relevance")
    ctk.CTkOptionMenu(cbar, values=["relevance", "downloads", "follows", "newest", "updated"],
                      variable=sort_var, width=110, height=24, font=ctk.CTkFont(size=10),
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"], command=lambda _: _do_search()).pack(side="left", padx=(0, 8), pady=6)
    ctk.CTkLabel(cbar, text="Loader", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(0, 4))
    loader_var = ctk.StringVar(value="any")
    ctk.CTkOptionMenu(cbar, values=["any", "paper", "spigot", "fabric", "forge", "neoforge", "quilt", "bukkit"],
                      variable=loader_var, width=100, height=24, font=ctk.CTkFont(size=10),
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"], command=lambda _: _do_search()).pack(side="left", padx=(0, 8), pady=6)
    ctk.CTkLabel(cbar, text="Version", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left", padx=(0, 4))
    ver_filt = ctk.StringVar(value="any")
    ctk.CTkOptionMenu(cbar, values=["any", "1.21", "1.20.6", "1.20.4", "1.20.1", "1.20", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.12.2", "1.8.9"],
                      variable=ver_filt, width=90, height=24, font=ctk.CTkFont(size=10),
                      fg_color=T["bg"], button_color=T["border"], button_hover_color=T["muted"],
                      text_color=T["text"], dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"], command=lambda _: _do_search()).pack(side="left", padx=(0, 8), pady=6)
    _res_lbl = ctk.CTkLabel(cbar, text="", font=ctk.CTkFont(
        size=10), text_color=T["muted"])
    _res_lbl.pack(side="right", padx=10)

    clist = ctk.CTkScrollableFrame(center, fg_color="transparent")
    clist.grid(row=1, column=0, sticky="nsew")
    clist.columnconfigure(0, weight=1)

    # ── DETAIL PANEL ──────────────────────────────────────
    detail_panel = ctk.CTkFrame(
        shell, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0, width=360)
    detail_panel.grid(row=0, column=2, sticky="nsew")
    detail_panel.grid_propagate(False)
    detail_panel.rowconfigure(0, weight=1)
    detail_panel.columnconfigure(0, weight=1)
    dscroll = ctk.CTkScrollableFrame(detail_panel, fg_color="transparent")
    dscroll.grid(row=0, column=0, sticky="nsew")
    dscroll.columnconfigure(0, weight=1)

    _sel_slug = [None]
    _result_btns = {}
    _searching = [False]
    _spin_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    _spin_idx = [0]
    _spin_id = [None]

    def _set_searching(on):
        _searching[0] = on
        search_btn.configure(state="disabled" if on else "normal")
        if on:
            def _spin():
                if not _searching[0]:
                    return
                try:
                    search_btn.configure(
                        text=_spin_chars[_spin_idx[0] % len(_spin_chars)])
                    _spin_idx[0] += 1
                    _spin_id[0] = app.after(120, _spin)
                except:
                    pass
            _spin()
        else:
            search_btn.configure(text="🔍")
            if _spin_id[0]:
                try:
                    app.after_cancel(_spin_id[0])
                except:
                    pass

    def _show_welcome():
        for w in dscroll.winfo_children():
            w.destroy()
        wrap = ctk.CTkFrame(dscroll, fg_color="transparent")
        wrap.pack(fill="both", expand=True, pady=60)
        ctk.CTkLabel(wrap, text="📦", font=ctk.CTkFont(size=52)).pack()
        ctk.CTkLabel(wrap, text="Modrinth Installer", font=ctk.CTkFont(
            size=18, weight="bold"), text_color=T["text"]).pack(pady=(8, 4))
        ctk.CTkLabel(wrap, text="Search for modpacks, mods, or plugins. Select a result to view details and install.",
                     font=ctk.CTkFont(size=12), text_color=T["muted"], justify="center").pack()
        ctk.CTkLabel(wrap, text="Powered by Modrinth API  ·  modrinth.com",
                     font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(pady=(10, 0))

    def _show_detail(project):
        for w in dscroll.winfo_children():
            w.destroy()
        slug = project.get("slug", "")
        title = project.get("title", "Unknown")
        desc = project.get("description", "")
        body = project.get("body", "")
        cats = project.get("categories", [])
        loaders = project.get("loaders", [])
        game_vs = project.get("game_versions", [])
        dls = project.get("downloads", 0)
        follows = project.get("followers", 0)
        lic = project.get("license", {}).get("id", "") if isinstance(
            project.get("license"), dict) else ""
        updated = project.get("updated", "")[:10]
        ptype = project.get("project_type", "modpack")
        icon_url = project.get("icon_url", "")

        # Header
        hcard = ctk.CTkFrame(
            dscroll, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=10)
        hcard.pack(fill="x", padx=10, pady=(10, 6))
        hinner = ctk.CTkFrame(hcard, fg_color="transparent")
        hinner.pack(fill="x", padx=10, pady=10)
        icon_lbl = ctk.CTkLabel(
            hinner, text="📦" if not icon_url else "", font=ctk.CTkFont(size=36), width=52)
        icon_lbl.pack(side="left", padx=(0, 10))
        icon_url and _fetch_icon_async(icon_url, icon_lbl, 48)
        info_col = ctk.CTkFrame(hinner, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)
        tr = ctk.CTkFrame(info_col, fg_color="transparent")
        tr.pack(fill="x")
        ctk.CTkLabel(tr, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T["text"], anchor="w", wraplength=240).pack(side="left")
        type_colors = {"modpack": T["sync"],
                       "mod": T["start"], "plugin": T["hand"]}
        tc = type_colors.get(ptype, T["muted"])
        ctk.CTkLabel(tr, text=ptype.upper(), font=ctk.CTkFont(size=8, weight="bold"), text_color=tc,
                     fg_color=T["border"], corner_radius=3, width=52, height=16).pack(side="right")
        project.get("author", "") and ctk.CTkLabel(info_col, text=f"by {project.get('author', '')} ", font=ctk.CTkFont(
            size=10), text_color=T["sync"], anchor="w").pack(anchor="w")

        # Stats chips
        sf = ctk.CTkFrame(dscroll, fg_color="transparent")
        sf.pack(fill="x", padx=10, pady=(0, 4))
        for lbl, val in [("⬇", f"{dls:,}"), ("♡", f"{follows:,}"), ("MC", ", ".join(sorted(game_vs, reverse=True)[:3]) or "?")]:
            if val:
                chip = ctk.CTkFrame(
                    sf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=6)
                chip.pack(side="left", padx=(0, 5))
                ctk.CTkLabel(chip, text=f"{lbl} {val}", font=ctk.CTkFont(
                    size=10), text_color=T["muted"]).pack(padx=7, pady=3)
        if loaders:
            chip2 = ctk.CTkFrame(
                sf, fg_color=T["bg"], border_color=T["border"], border_width=1, corner_radius=6)
            chip2.pack(side="left")
            ctk.CTkLabel(chip2, text=", ".join(loaders[:3]), font=ctk.CTkFont(
                size=10), text_color=T["muted"]).pack(padx=7, pady=3)
        if cats:
            cat_row = ctk.CTkFrame(dscroll, fg_color="transparent")
            cat_row.pack(fill="x", padx=10, pady=(0, 6))
            for c in cats[:6]:
                ctk.CTkLabel(cat_row, text=c, font=ctk.CTkFont(size=8), fg_color=T["border"], text_color=T["muted"],
                             corner_radius=3, width=54, height=16).pack(side="left", padx=(0, 3))

        ctk.CTkFrame(dscroll, height=1, fg_color=T["border"]).pack(
            fill="x", padx=10, pady=4)
        desc and ctk.CTkLabel(dscroll, text=desc, font=ctk.CTkFont(size=11), text_color=T["muted"],
                              wraplength=320, justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 8))

        # Install section
        icard = ctk.CTkFrame(
            dscroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
        icard.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(icard, text="Install", font=ctk.CTkFont(
            size=11, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkFrame(icard, height=1, fg_color=T["border"]).pack(
            fill="x", padx=12)
        ib = ctk.CTkFrame(icard, fg_color="transparent")
        ib.pack(fill="x", padx=12, pady=(10, 12))

        s2 = load_settings()
        srv_path_v = ctk.StringVar(value=s2.get("srv_path", _DEFAULT_SRV))
        mc_ver_v = ctk.StringVar(value="")
        loader_v = ctk.StringVar(value="")

        r0 = ctk.CTkFrame(ib, fg_color="transparent")
        r0.pack(fill="x", pady=3)
        ctk.CTkLabel(r0, text="Folder", font=ctk.CTkFont(
            size=11), text_color=T["muted"], width=52, anchor="w").pack(side="left")
        ctk.CTkEntry(r0, textvariable=srv_path_v, height=24, font=ctk.CTkFont(size=10, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"], text_color=T["text"]).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(r0, text="…", width=26, height=24, fg_color="transparent", border_width=1,
                      border_color=T["border"], text_color=T["muted"], hover_color=T["border"],
                      command=lambda: srv_path_v.set(_tk_fd.askdirectory(title="Install to") or srv_path_v.get())).pack(side="left")

        r1 = ctk.CTkFrame(ib, fg_color="transparent")
        r1.pack(fill="x", pady=3)
        ctk.CTkLabel(r1, text="MC ver", font=ctk.CTkFont(
            size=11), text_color=T["muted"], width=52, anchor="w").pack(side="left")
        ver_menu = ctk.CTkOptionMenu(r1, values=["Loading…"], variable=mc_ver_v, font=ctk.CTkFont(size=10),
                                     width=110, height=24, fg_color=T["bg"], button_color=T["border"],
                                     button_hover_color=T["muted"], text_color=T["text"],
                                     dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                                     dropdown_hover_color=T["border"])
        ver_menu.pack(side="left", padx=(0, 8))
        if loaders:
            ctk.CTkLabel(r1, text="Loader", font=ctk.CTkFont(
                size=11), text_color=T["muted"], width=48, anchor="w").pack(side="left")
            ctk.CTkOptionMenu(r1, values=loaders, variable=loader_v, font=ctk.CTkFont(size=10),
                              width=100, height=24, fg_color=T["bg"], button_color=T["border"],
                              button_hover_color=T["muted"], text_color=T["text"],
                              dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                              dropdown_hover_color=T["border"]).pack(side="left")
            if loaders:
                loader_v.set(loaders[0])

        def _load_ver_menu():
            try:
                vs = sorted(set(game_vs), reverse=True) if game_vs else []
                if vs:
                    app.after(0, lambda: (ver_menu.configure(
                        values=vs), mc_ver_v.set(vs[0])))
            except:
                pass
        threading.Thread(target=_load_ver_menu, daemon=True).start()

        inst_st = ctk.CTkLabel(ib, text="", font=ctk.CTkFont(
            size=11), text_color=T["muted"])
        inst_st.pack(anchor="w", pady=(4, 0))
        inst_pg = ctk.CTkProgressBar(ib, height=4)
        inst_pg.set(0)

        def _set_st(msg, color=None):
            try:
                inst_st.configure(text=msg, text_color=color or T["muted"])
            except:
                pass

        def _install_project():
            dest = srv_path_v.get().strip()
            ver = mc_ver_v.get()
            ldr = loader_v.get() if loaders else None
            if not dest or not os.path.isdir(dest):
                show_toast("Set a valid install folder!", T["stop"])
                return

            def _work():
                try:
                    _set_st("Fetching versions…", T["sync"])
                    app.after(0, lambda: (inst_pg.set(0),
                              inst_pg.pack(fill="x", pady=(4, 0))))
                    params = {}
                    if ver and ver not in ("Loading…", ""):
                        params["game_versions"] = f'["{ver}"]'
                    if ldr and ldr not in ("", "Loading…"):
                        params["loaders"] = f'["{ldr}"]'
                    pstr = "&".join(
                        f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
                    url = f"{_MODRINTH_API}/project/{project.get('id', '')}/version" + (
                        ("?" + pstr) if pstr else "")
                    versions = _json.loads(_http_get(url, _API_HDR))
                    if not versions:
                        _set_st("No compatible versions found.", T["stop"])
                        return
                    best = versions[0]
                    files = best.get("files", [])
                    if not files:
                        _set_st("No files in this version.", T["stop"])
                        return
                    primary = next(
                        (f for f in files if f.get("primary")), files[0])
                    dl_url = primary["url"]
                    fname = primary["filename"]
                    if ptype == "modpack":
                        tmp = os.path.join(dest, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        req2 = urllib.request.Request(dl_url, headers=_API_HDR)
                        with urllib.request.urlopen(req2, timeout=120) as r:
                            total = int(r.headers.get("Content-Length", 0))
                            done = 0
                            with open(tmp, "wb") as fout:
                                while True:
                                    chunk = r.read(65536)
                                    if not chunk:
                                        break
                                    fout.write(chunk)
                                    done += len(chunk)
                                    total and app.after(
                                        0, inst_pg.set, min(done/total*0.4, 0.4))
                        _set_st("Installing modpack…", T["sync"])
                        try:
                            with _zipfile.ZipFile(tmp, "r") as zf:
                                with zf.open("modrinth.index.json") as mf:
                                    manifest = _json.loads(mf.read())
                                overrides = [n for n in zf.namelist(
                                ) if n.startswith("overrides/")]
                                for i2, name2 in enumerate(overrides):
                                    rel = name2[len("overrides/"):]
                                    if not rel:
                                        continue
                                    out2 = os.path.join(dest, rel)
                                    os.makedirs(os.path.dirname(
                                        out2), exist_ok=True)
                                    with zf.open(name2) as src2, open(out2, "wb") as dst2:
                                        import shutil
                                        shutil.copyfileobj(src2, dst2)
                                    app.after(0, inst_pg.set, 0.4 +
                                              0.2*(i2/max(len(overrides), 1)))
                            pack_files = manifest.get("files", [])
                            n_files = len(pack_files)
                            _set_st(
                                f"Downloading {n_files} mod files…", T["sync"])
                            for i3, pf in enumerate(pack_files):
                                ppath = pf.get("path", "")
                                pdls = pf.get("downloads", [])
                                if not pdls:
                                    continue
                                pout = os.path.join(dest, ppath)
                                os.makedirs(os.path.dirname(
                                    pout), exist_ok=True)
                                for purl in pdls:
                                    try:
                                        with urllib.request.urlopen(purl, timeout=60) as pr:
                                            open(pout, "wb").write(pr.read())
                                            break
                                    except:
                                        continue
                                app.after(0, inst_pg.set, 0.6 +
                                          0.4*(i3/max(n_files, 1)))
                            try:
                                os.remove(tmp)
                            except:
                                pass
                            app.after(0, inst_pg.set, 1.0)
                            _set_st("Modpack installed!", T["start"])
                            show_toast("Modpack installed!", T["start"])
                        except Exception as ex2:
                            _set_st(
                                f"Modpack extract failed: {ex2}", T["stop"])
                    elif ptype == "mod":
                        mods_dir = os.path.join(dest, "mods")
                        os.makedirs(mods_dir, exist_ok=True)
                        out = os.path.join(mods_dir, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        req3 = urllib.request.Request(dl_url, headers=_API_HDR)
                        with urllib.request.urlopen(req3, timeout=60) as r:
                            open(out, "wb").write(r.read())
                        app.after(0, inst_pg.set, 1.0)
                        _set_st(f"Installed to mods/{fname}", T["start"])
                        show_toast(f"Mod installed: {fname}", T["start"])
                        log(f"  Installed mod: {fname}")
                    elif ptype == "plugin":
                        plug_dir = os.path.join(dest, "plugins")
                        os.makedirs(plug_dir, exist_ok=True)
                        out = os.path.join(plug_dir, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        req4 = urllib.request.Request(dl_url, headers=_API_HDR)
                        with urllib.request.urlopen(req4, timeout=60) as r:
                            open(out, "wb").write(r.read())
                        app.after(0, inst_pg.set, 1.0)
                        _set_st(f"Installed to plugins/{fname}", T["start"])
                        show_toast(f"Plugin installed: {fname}", T["start"])
                        log(f"  Installed plugin: {fname}")
                except Exception as ex:
                    _set_st(f"Failed: {ex}", T["stop"])
                    show_toast(f"Install failed: {ex}", T["stop"])
            threading.Thread(target=_work, daemon=True).start()

        btn_row = ctk.CTkFrame(ib, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(8, 0))
        ctk.CTkButton(btn_row, text=f"⬇  Install", height=32, font=ctk.CTkFont(size=12, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000",
                      command=_install_project).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="🌐 Modrinth", height=32, font=ctk.CTkFont(size=11),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: slug and __import__("webbrowser").open(
                          f"https://modrinth.com/{ptype}/{slug}")
                      ).pack(side="left")

        # Version list
        if body or True:
            vcard = ctk.CTkFrame(
                dscroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
            vcard.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(vcard, text="Available Versions", font=ctk.CTkFont(
                size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkFrame(vcard, height=1, fg_color=T["border"]).pack(
                fill="x", padx=12)
            vlist = ctk.CTkScrollableFrame(
                vcard, fg_color="transparent", height=140)
            vlist.pack(fill="x", padx=12, pady=(4, 8))
            vlist_lbl = ctk.CTkLabel(vlist, text="Loading…", font=ctk.CTkFont(
                size=10), text_color=T["muted"])
            vlist_lbl.pack(pady=6)

            def _pop_vlist():
                try:
                    vdata = _json.loads(_http_get(
                        f"{_MODRINTH_API}/project/{project.get('id', '')}/version", _API_HDR))[:25]

                    def _draw():
                        vlist_lbl.destroy()
                        for v2 in vdata:
                            vr = ctk.CTkFrame(vlist, fg_color="transparent")
                            vr.pack(fill="x", pady=1)
                            vname = v2.get("name", "?")[:40]
                            vnum = v2.get("version_number", "?")
                            vgvs = ", ".join(v2.get("game_versions", [])[:2])
                            vlds = ", ".join(v2.get("loaders", []))
                            ctk.CTkLabel(vr, text=vname, font=ctk.CTkFont(
                                size=10, weight="bold"), text_color=T["text"]).pack(side="left")
                            ctk.CTkLabel(vr, text=f"  {vnum}  {vgvs}  {vlds}", font=ctk.CTkFont(
                                size=9), text_color=T["muted"]).pack(side="left")
                            sz = sum(f2.get("size", 0)
                                     for f2 in v2.get("files", []))
                            sz and ctk.CTkLabel(vr, text=f"{sz/1048576:.1f}MB", font=ctk.CTkFont(
                                size=9), text_color=T["muted"]).pack(side="right")
                    app.after(0, _draw)
                except Exception as ex2:
                    app.after(0, lambda: vlist_lbl.configure(
                        text=f"Error: {ex2}", text_color=T["stop"]))
            threading.Thread(target=_pop_vlist, daemon=True).start()

        if body:
            bcard = ctk.CTkFrame(
                dscroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10)
            bcard.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(bcard, text="Description", font=ctk.CTkFont(
                size=10, weight="bold"), text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkFrame(bcard, height=1, fg_color=T["border"]).pack(
                fill="x", padx=12)
            plain = _strip_md(body)[:1200]
            ctk.CTkLabel(bcard, text=plain, font=ctk.CTkFont(size=10), text_color=T["text"],
                         justify="left", wraplength=320).pack(anchor="w", padx=12, pady=(8, 12))

    def _select_project(proj):
        slug = proj.get("slug", "")
        for s3, b in _result_btns.items():
            b.configure(fg_color=T["border"] if s3 == slug else T["bg"])
        _sel_slug[0] = slug
        _set_searching(False)

        def _fetch_full():
            try:
                full = _json.loads(
                    _http_get(f"{_MODRINTH_API}/project/{slug}", _API_HDR))
                app.after(0, lambda: _show_detail(full))
            except:
                app.after(0, lambda: _show_detail(proj))
        threading.Thread(target=_fetch_full, daemon=True).start()

    def _make_result_card(proj):
        slug = proj.get("slug", "")
        title = proj.get("title", "?")
        desc = (proj.get("description", "") or "")[:90]
        if len(proj.get("description", "")) > 90:
            desc += "…"
        dls = proj.get("downloads", 0)
        cats = proj.get("categories", [])[:3]
        pvs = sorted(proj.get("versions", []), reverse=True)[:2]
        ptype = proj.get("project_type", "modpack")
        icon_url = proj.get("icon_url", "")
        color_map = {"modpack": T["sync"],
                     "mod": T["start"], "plugin": T["hand"]}
        tc = color_map.get(ptype, T["muted"])

        btn = ctk.CTkButton(clist, text="", height=68, corner_radius=8,
                            fg_color=T["border"] if _sel_slug[0] == slug else T["bg"],
                            hover_color=T["border"], border_width=0,
                            command=lambda p=proj: _select_project(p))
        btn.pack(fill="x", padx=6, pady=2)
        _result_btns[slug] = btn

        inner = ctk.CTkFrame(btn, fg_color="transparent")
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        inner.bind("<Button-1>", lambda e, p=proj: _select_project(p))

        r1 = ctk.CTkFrame(inner, fg_color="transparent")
        r1.pack(fill="x", padx=(42, 10), pady=(8, 0))
        ctk.CTkLabel(r1, text=title, font=ctk.CTkFont(
            size=12, weight="bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(r1, text=f"⬇{dls:,}", font=ctk.CTkFont(
            size=9), text_color=T["muted"]).pack(side="right")

        icon_lbl = ctk.CTkLabel(
            inner, text="📦" if not icon_url else "", font=ctk.CTkFont(size=22), width=34)
        icon_lbl.place(x=6, rely=0.5, anchor="w")
        icon_url and _fetch_icon_async(icon_url, icon_lbl, 32)

        r2 = ctk.CTkFrame(inner, fg_color="transparent")
        r2.pack(fill="x", padx=(42, 10), pady=(1, 0))
        ctk.CTkLabel(r2, text=desc, font=ctk.CTkFont(
            size=10), text_color=T["muted"], anchor="w").pack(side="left", fill="x", expand=True)

        r3 = ctk.CTkFrame(inner, fg_color="transparent")
        r3.pack(fill="x", padx=(42, 10), pady=(0, 5))
        for cat in cats:
            ctk.CTkLabel(r3, text=cat, font=ctk.CTkFont(size=8), fg_color=T["border"], text_color=T["muted"],
                         corner_radius=3, width=50, height=14).pack(side="left", padx=(0, 3))
        if pvs:
            ctk.CTkLabel(r3, text=pvs[0], font=ctk.CTkFont(
                size=9), text_color=tc).pack(side="right")

    def _show_installed_local():
        for w in clist.winfo_children():
            w.destroy()
        _res_lbl.configure(text="local")
        _sel_slug[0] = None
        srv_path_l = load_settings().get("srv_path", _DEFAULT_SRV)
        jars = []
        for sub in ("plugins", "mods"):
            d = os.path.join(srv_path_l, sub)
            os.path.isdir(d) and jars.extend(
                [(sub, j) for j in sorted(os.listdir(d)) if j.endswith(".jar")])
        if not jars:
            ctk.CTkLabel(clist, text="No local mods/plugins found.",
                         font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(pady=40)
            return
        for sub, j in jars:
            jar_path = os.path.join(srv_path_l, sub, j)
            card2 = ctk.CTkFrame(
                clist, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=10, cursor="hand2")
            card2.pack(fill="x", padx=10, pady=4)
            card2.columnconfigure(0, weight=1)
            ctk.CTkLabel(card2, text=os.path.splitext(j)[0], font=ctk.CTkFont(
                size=12, weight="bold"), text_color=T["text"], anchor="w").grid(row=0, column=0, sticky="w", padx=(10, 4), pady=8)
            ctk.CTkButton(card2, text="🗑", width=30, height=24, fg_color="transparent", border_width=1, border_color=T["stop"],
                          text_color=T["stop"], hover_color=T["border"],
                          command=lambda p=jar_path: (os.remove(p), show_toast(f"Deleted {os.path.basename(p)}", T["stop"]), _show_installed_local())).grid(row=0, column=1, padx=(0, 4), pady=6)
            ctk.CTkButton(card2, text="📂", width=30, height=24, fg_color="transparent", border_width=1, border_color=T["border"],
                          text_color=T["muted"], hover_color=T["border"],
                          command=lambda p=jar_path: _open_folder(os.path.dirname(p))).grid(row=0, column=2, padx=(0, 6), pady=6)

    def _do_search(paginate=False):
        if not paginate:
            _page[0] = 0
        cat = type_var[0]
        if cat == "installed":
            _show_installed_local()
            _show_welcome()
            return
        q = query_var.get().strip() or "minecraft"
        _set_searching(True)

        def _work():
            try:
                facets = [["project_type:" + cat]]
                ldr = loader_var.get()
                vf = ver_filt.get()
                if ldr != "any":
                    facets.append(["categories:" + ldr])
                if vf != "any":
                    facets.append(["versions:" + vf])
                params = urllib.parse.urlencode({"query": q, "facets": _json.dumps(facets),
                                                 "index": sort_var.get(), "limit": PER_PAGE,
                                                 "offset": _page[0]*PER_PAGE})
                data = _json.loads(
                    _http_get(f"{_MODRINTH_API}/search?{params}", _API_HDR))
                hits = data.get("hits", [])
                total = data.get("total_hits", 0)
                _total[0] = total

                def _draw():
                    for w in clist.winfo_children():
                        w.destroy()
                    _result_btns.clear()
                    result_lbl.configure(text=f"{total:,} results")
                    pg_lbl.configure(
                        text=f"Page {_page[0]+1} / {max(1, (total+PER_PAGE-1)//PER_PAGE)}")
                    if not hits:
                        ctk.CTkLabel(clist, text="No results.", font=ctk.CTkFont(
                            size=12), text_color=T["muted"]).pack(pady=20)
                        _set_searching(False)
                        return
                    for proj in hits:
                        _make_result_card(proj)
                    _set_searching(False)
                app.after(0, _draw)
            except Exception as ex:
                app.after(0, lambda: (_set_searching(False),
                          result_lbl.configure(text=f"Error: {ex}")))
        threading.Thread(target=_work, daemon=True).start()

    _show_welcome()
    _do_search()


def _build_mode_mcctrl(parent): _build_mode_dashboard(parent, False)
def _build_log_area(right): pass


def _toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    update_setting("fullscreen", fullscreen)
    app.attributes("-fullscreen", fullscreen)
    not fullscreen and app.geometry("1100x740")
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
    show_chat = not show_chat
    update_setting("show_chat", show_chat)
    try:
        chat_toggle_btn.configure(text="Hide" if show_chat else "Show")
        if show_chat:
            chat_box.configure(height=80)
            chat_box.pack(fill="x", padx=6, pady=(3, 6))
        else:
            chat_box.pack_forget()
            chat_box.configure(height=0)
    except:
        pass


def _build_tools_settings(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=18, pady=10)

    def section(title, sub=None):
        f = ctk.CTkFrame(
            scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        f.pack(fill="x", pady=(0, 10))
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(
            size=11, weight="bold"), text_color=T["text"]).pack(side="left")
        if sub:
            ctk.CTkLabel(h, text=sub, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12)
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=12, pady=(8, 12))
        return b, h
    # Updates
    ub, uh = section("Updates", f"Current version: v{_APP_VERSION}")
    _uv_lbl = ctk.CTkLabel(ub, text="● Up to date" if not _update_info[0] else f"● Update available: v{_update_info[0]['version']}", font=ctk.CTkFont(
        size=12), text_color=T["start"] if not _update_info[0] else T["hand"])
    _uv_lbl.pack(side="left")

    def _chk():
        _uv_lbl.configure(text="Checking…", text_color=T["sync"])

        def _after():
            if _update_info[0]:
                _uv_lbl.configure(
                    text=f"● Update available: v{_update_info[0]['version']}", text_color=T["hand"])
            else:
                _uv_lbl.configure(text="● Up to date", text_color=T["start"])
        check_for_updates(silent=False)
        app.after(6000, _after)
    ctk.CTkButton(ub, text="Check Now", width=100, height=28,
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000", font=ctk.CTkFont(size=11), command=_chk).pack(side="right")
    # Repair
    rb, rh = section("Repair", "Verify files, re-write EULA, git pull")
    ctk.CTkLabel(rb, text="Re-checks Java, server.jar, EULA, then pulls latest from GitHub.", font=ctk.CTkFont(
        size=11), text_color=T["muted"], wraplength=560, justify="left").pack(anchor="w", pady=(0, 6))
    ctk.CTkButton(rb, text="🔧 Run Repair", height=32, fg_color=T["sync"], hover_color=T["sync"], text_color="#000", font=ctk.CTkFont(
        size=12, weight="bold"), command=run_repair).pack(anchor="w")
    # First-run wizard re-trigger
    wb, wh = section("Setup Wizard", "Re-run first-time configuration")
    ctk.CTkLabel(wb, text="Opens the setup wizard to reconfigure server path, Java, RAM, and theme.", font=ctk.CTkFont(
        size=11), text_color=T["muted"], wraplength=560, justify="left").pack(anchor="w", pady=(0, 6))
    ctk.CTkButton(wb, text="▶ Open Wizard", height=32, fg_color=T["start"], hover_color=T["start"], text_color="#000", font=ctk.CTkFont(
        size=12, weight="bold"), command=_show_first_run_wizard).pack(anchor="w")
    # Uninstall
    xb, xh = section("Uninstall / Cleanup", "Remove launcher data")
    ctk.CTkLabel(xb, text="Remove settings, addons, or the server data folder.", font=ctk.CTkFont(
        size=11), text_color=T["muted"], wraplength=560, justify="left").pack(anchor="w", pady=(0, 6))
    ctk.CTkButton(xb, text="🗑 Uninstall Wizard", height=32, fg_color="transparent", border_width=1,
                  border_color=T["stop"], text_color=T["stop"], hover_color=T["border"], font=ctk.CTkFont(size=12, weight="bold"), command=run_uninstall_wizard).pack(anchor="w")


def build_settings_window(parent):
    stab_bar = ctk.CTkFrame(
        parent, fg_color=T["card"], corner_radius=0, border_color=T["border"], border_width=1)
    stab_bar.pack(side="top", fill="x")
    stab_content = ctk.CTkFrame(parent, fg_color="transparent")
    stab_content.pack(side="top", fill="both", expand=True)
    STABS = [("general", "General"), ("addons",
                                      "🧩 Addons"), ("tools", "🔧 Tools")]
    stab_frames = {k: ctk.CTkFrame(
        stab_content, fg_color="transparent") for k, _ in STABS}
    _stab_built = set()
    stab_btns = {}

    def show_stab(name):
        for f in stab_frames.values():
            f.pack_forget()
        for n, b in stab_btns.items():
            b.configure(fg_color=T["sync"] if n == name else "transparent",
                        text_color="#000" if n == name else T["muted"])
        if name not in _stab_built:
            _stab_built.add(name)
            {"general": lambda: _build_general_settings(stab_frames["general"]), "addons": lambda: _build_addons_settings(
                stab_frames["addons"]), "tools": lambda: _build_tools_settings(stab_frames["tools"])}[name]()
        stab_frames[name].pack(fill="both", expand=True)
    for key, label in STABS:
        b = ctk.CTkButton(stab_bar, text=label, width=100, height=26, font=ctk.CTkFont(size=11), corner_radius=5,
                          fg_color="transparent", text_color=T["muted"], hover_color=T["border"], command=lambda k=key: show_stab(k))
        b.pack(side="left", padx=(6 if key == "general" else 2, 2), pady=4)
        stab_btns[key] = b
    show_stab("general")


def _build_general_settings(parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=18, pady=10)

    def section(title): f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12); f.pack(fill="x", pady=(0, 10)); ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=T["text"]).pack(
        anchor="w", padx=12, pady=(10, 4)); ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=12); b = ctk.CTkFrame(f, fg_color="transparent"); b.pack(fill="x", padx=12, pady=(6, 10)); return b

    def row_sw(parent, label, get_val, on_change): r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", pady=4); ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12), text_color=T["text"], width=280, anchor="w").pack(
        side="left"); var = ctk.BooleanVar(value=get_val()); ctk.CTkSwitch(r, text="", variable=var, command=lambda: on_change(var.get()), button_color=T["sync"], progress_color=T["sync"]).pack(side="right")

    def row_entry(parent, label, key, default):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", pady=4)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(
            size=12), text_color=T["text"], width=280, anchor="w").pack(side="left")
        e = ctk.CTkEntry(r, font=ctk.CTkFont(size=11, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"], text_color=T["text"], height=26)
        e.insert(0, load_settings().get(key, default))
        e.pack(side="left", fill="x", expand=True)
        def save(*_): update_setting(key, e.get())
        e.bind("<FocusOut>", save)
        e.bind("<Return>", save)
    b = section("Appearance")
    r = ctk.CTkFrame(b, fg_color="transparent")
    r.pack(fill="x", pady=4)
    ctk.CTkLabel(r, text="Theme", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=280, anchor="w").pack(side="left")
    _stm_lbl = ctk.CTkLabel(r, text=f"🎨 {_theme_name} (change via top bar picker)", font=ctk.CTkFont(
        size=11), text_color=T["muted"])
    _stm_lbl.pack(side="right")
    row_sw(b, "Fullscreen", lambda: fullscreen, lambda v: _toggle_fullscreen())
    row_sw(b, "Log on left", lambda: log_left, lambda v: _toggle_log_left())
    row_sw(b, "Show performance", lambda: show_perf, lambda v: _toggle_perf())
    row_sw(b, "Show chat", lambda: show_chat, lambda v: _toggle_chat())
    b = section("Server")
    row_entry(b, "Server path", "srv_path", _DEFAULT_SRV)
    row_entry(b, "GitHub repo", "repo_url", REPO_URL)
    row_entry(b, "Java path", "java_path", _DEFAULT_JAVA)
    java_ver_r = ctk.CTkFrame(b, fg_color="transparent")
    java_ver_r.pack(fill="x", pady=(0, 4))
    _jver_lbl = ctk.CTkLabel(java_ver_r, text="Java: detecting…", font=ctk.CTkFont(
        size=10, family="Consolas"), text_color=T["muted"])
    _jver_lbl.pack(side="left", padx=(0, 8))

    def _detect_java():
        s3 = load_settings()
        java_exe = s3.get("java_path", _DEFAULT_JAVA)
        try:
            r = subprocess.run([java_exe, "-version"], capture_output=True,
                               text=True, timeout=5, creationflags=_NO_WIN)
            out = (r.stderr or r.stdout or "").strip().splitlines()
            ver_line = out[0] if out else "unknown"
            app.after(0, _jver_lbl.configure, {
                      "text": f"Java: {ver_line}", "text_color": T["start"]})
        except Exception as ex:
            app.after(0, _jver_lbl.configure, {
                      "text": f"Java: not found ({ex})", "text_color": T["stop"]})
    ctk.CTkButton(java_ver_r, text="Detect", width=60, height=22, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: threading.Thread(target=_detect_java, daemon=True).start()).pack(side="left")
    threading.Thread(target=_detect_java, daemon=True).start()
    ram_r = ctk.CTkFrame(b, fg_color="transparent")
    ram_r.pack(fill="x", pady=4)
    ctk.CTkLabel(ram_r, text="Server RAM (GB)", font=ctk.CTkFont(
        size=12), text_color=T["text"], width=280, anchor="w").pack(side="left")
    _ram_gb = load_settings().get("server_ram_gb", 2)
    _ram_var = ctk.IntVar(value=_ram_gb)
    _ram_lbl = ctk.CTkLabel(ram_r, text=f"{_ram_gb} GB", font=ctk.CTkFont(
        size=12, family="Consolas"), text_color=T["sync"], width=44, anchor="e")
    _ram_lbl.pack(side="right")
    def _on_ram(v): iv = int(float(v)); _ram_lbl.configure(
        text=f"{iv} GB"); update_setting("server_ram_gb", iv)
    ctk.CTkSlider(ram_r, from_=1, to=16, number_of_steps=15, variable=_ram_var, command=_on_ram,
                  button_color=T["sync"], progress_color=T["sync"], width=160).pack(side="right", padx=(0, 8))
    b = section("Auto Upload")
    row_sw(b, "Enable auto upload", lambda: auto_upload,
           lambda v: toggle_auto_upload())
    row_sw(b, "Upload on server stop", lambda: upload_on_stop, lambda v: (
        globals().update({'upload_on_stop': v}), update_setting('upload_on_stop', v)))
    row_entry(b, "Upload interval (mins)",
              "auto_upload_mins", str(auto_upload_mins))
    ctk.CTkLabel(scroll, text=f"Settings: {SETTINGS_FILE}", font=ctk.CTkFont(
        size=10), text_color=T["muted"]).pack(anchor="w", pady=(4, 0))


def _build_addons_settings(parent):
    addon_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    root = ctk.CTkFrame(parent, fg_color="transparent")
    root.grid(row=0, column=0, sticky="nsew")
    root.rowconfigure(0, weight=1)
    root.columnconfigure((0, 1), weight=(0, 1))
    left = ctk.CTkFrame(
        root, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=0, width=240)
    left.grid(row=0, column=0, sticky="nsew")
    left.grid_propagate(False)
    left.rowconfigure(1, weight=1)
    left.columnconfigure(0, weight=1)
    lhdr = ctk.CTkFrame(left, fg_color=T["bg"], corner_radius=0)
    lhdr.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(lhdr, text="🧩 Addons", font=ctk.CTkFont(
        size=12, weight="bold"), text_color=T["text"]).pack(side="left", padx=12, pady=8)
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
    _sel = [None]
    _btns = {}

    def _get_meta(name): return (_loaded_addons.get(name).__meta__ if hasattr(_loaded_addons.get(name), "__meta__") else {
        "title": name.replace("_", "  ").title(), "version": "?", "author": "Unknown", "description": "No description available.", "settings": []})

    def _show_empty(): [w.destroy() for w in detail.winfo_children()]; empty = ctk.CTkFrame(detail, fg_color="transparent"); empty.grid(row=0, column=0, sticky="nsew"); inner = ctk.CTkFrame(empty, fg_color="transparent"); inner.place(relx=0.5, rely=0.4, anchor="center"); ctk.CTkLabel(
        inner, text="🧩", font=ctk.CTkFont(size=48)).pack(); ctk.CTkLabel(inner, text="Select an addon", font=ctk.CTkFont(size=16, weight="bold"), text_color=T["text"]).pack(pady=(8, 4)); ctk.CTkLabel(inner, text="Pick from list to view details.", font=ctk.CTkFont(size=12), text_color=T["muted"]).pack()

    def _show_detail(name):
        [w.destroy() for w in detail.winfo_children()]
        meta = _get_meta(name)
        loaded = name in _loaded_addons
        sc = ctk.CTkScrollableFrame(detail, fg_color="transparent")
        sc.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        sc.columnconfigure(0, weight=1)
        hc = ctk.CTkFrame(
            sc, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        hc.pack(fill="x", pady=(0, 8))
        hi = ctk.CTkFrame(hc, fg_color="transparent")
        hi.pack(fill="x", padx=14, pady=12)
        tr = ctk.CTkFrame(hi, fg_color="transparent")
        tr.pack(fill="x")
        ctk.CTkLabel(tr, text=meta.get("title", name), font=ctk.CTkFont(
            size=18, weight="bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(tr, text="● Loaded" if loaded else "○ Not loaded", font=ctk.CTkFont(
            size=11), text_color=T["start"] if loaded else T["muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hi, text=f"v{meta.get('version', '?')}  ·  by {meta.get('author', '?')}", font=ctk.CTkFont(
            size=11), text_color=T["muted"]).pack(anchor="w", pady=(2, 0))
        br = ctk.CTkFrame(hc, fg_color="transparent")
        br.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(br, text="↺ Reload", width=80, height=28, font=ctk.CTkFont(size=11), fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=lambda: (
            _load_addon(os.path.join(addon_dir, name+".py")), show_toast(f"{name} reloaded!", T["sync"]), _refresh_list(), _show_detail(name))).pack(side="left", padx=(0, 6))
        ctk.CTkButton(br, text="🗑 Remove", width=80, height=28, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1, border_color=T["stop"], text_color=T["stop"], hover_color=T["border"], command=lambda: (
            os.remove(os.path.join(addon_dir, name+".py")), _loaded_addons.pop(name, None), show_toast(f"{name} removed.", T["stop"]), _refresh_list(), _show_empty())).pack(side="left")
        dc = ctk.CTkFrame(
            sc, fg_color=T["card"], border_color=T["border"], border_width=1, corner_radius=12)
        dc.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(dc, text="About", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkFrame(dc, height=1, fg_color=T["border"]).pack(
            fill="x", padx=14)
        ctk.CTkLabel(dc, text=meta.get("description", "No description."), font=ctk.CTkFont(
            size=12), text_color=T["text"], justify="left", wraplength=420).pack(anchor="w", padx=14, pady=(8, 12))

    def _select(name):
        _sel[0] = name
        [b.configure(fg_color=T["border"] if n == name else T["bg"])
         for n, b in _btns.items()]
        _show_detail(name)

    def _refresh_list():
        [w.destroy() for w in list_scroll.winfo_children()]
        _btns.clear()
        try:
            scripts = sorted([os.path.splitext(x)[0]
                             for x in os.listdir(addon_dir) if x.endswith(".py")])
        except:
            scripts = []
        if not scripts:
            ctk.CTkLabel(list_scroll, text="No addons.\nClick + Install below.",
                         font=ctk.CTkFont(size=11), text_color=T["muted"], justify="center").pack(pady=30)
            return
        for name in scripts:
            loaded = name in _loaded_addons
            btn = ctk.CTkButton(list_scroll, text="", height=54, corner_radius=8, fg_color=T["border"] if _sel[
                                0] == name else T["bg"], hover_color=T["border"], border_width=0, command=lambda n=name: _select(n))
            btn.pack(fill="x", padx=6, pady=2)
            _btns[name] = btn
            inner = ctk.CTkFrame(btn, fg_color="transparent")
            inner.place(relx=0, rely=0, relwidth=1, relheight=1)
            inner.bind("<Button-1>", lambda e, n=name: _select(n))
            r1 = ctk.CTkFrame(inner, fg_color="transparent")
            r1.pack(fill="x", padx=10, pady=(7, 0))
            ctk.CTkLabel(r1, text="●" if loaded else "○", font=ctk.CTkFont(
                size=10), text_color=T["start"] if loaded else T["muted"], width=14).pack(side="left")
            ctk.CTkLabel(r1, text=name.replace("_", "  ").title(), font=ctk.CTkFont(
                size=12, weight="bold"), text_color=T["text"]).pack(side="left", padx=4)
            r2 = ctk.CTkFrame(inner, fg_color="transparent")
            r2.pack(fill="x", padx=10, pady=(2, 5))
            ctk.CTkLabel(r2, text="Loaded" if loaded else "Not loaded", font=ctk.CTkFont(
                size=10), text_color=T["muted"]).pack(anchor="w")

    def _install():
        paths = _tk_fd.askopenfilenames(title="Select Addon (.py)", filetypes=[
                                        ("Python", "*.py"), ("All", "*.*")])
        if not paths:
            return
        for p in paths:
            dest = os.path.join(addon_dir, os.path.basename(p))
            try:
                shutil.copy2(p, dest)
                _load_addon(dest)
            except Exception as ex:
                show_toast(f"Failed: {ex}", T["stop"])
        show_toast(f"{len(paths)} addon(s) installed!", T["start"])
        _refresh_list()
    ctk.CTkButton(lfooter, text="+ Install", height=30, font=ctk.CTkFont(size=11, weight="bold"),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000", command=_install).pack(side="left", padx=(8, 4), pady=6)
    ctk.CTkButton(lfooter, text="Open Folder", height=30, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                  border_color=T["border"], text_color=T["muted"], hover_color=T["border"], command=lambda: _open_folder(addon_dir)).pack(side="left", padx=(0, 8), pady=6)
    _refresh_list()
    _show_empty()


_splash = ctk.CTkFrame(app, fg_color=T["bg"])
_splash.place(relx=0, rely=0, relwidth=1, relheight=1)
ctk.CTkLabel(_splash, text="MC CTRL", font=ctk.CTkFont(size=48, weight="bold"),
             text_color=T["start"]).place(relx=0.5, rely=0.36, anchor="center")
ctk.CTkLabel(_splash, text="Minecraft Server Launcher", font=ctk.CTkFont(
    size=12), text_color=T["muted"]).place(relx=0.5, rely=0.445, anchor="center")
_splash_status = ctk.CTkLabel(
    _splash, text="Initializing…", font=ctk.CTkFont(size=11), text_color=T["sync"])
_splash_status.place(relx=0.5, rely=0.52, anchor="center")
_sbar = ctk.CTkProgressBar(
    _splash, width=260, height=4, fg_color=T["border"], progress_color=T["start"])
_sbar.place(relx=0.5, rely=0.585, anchor="center")
_sbar.set(0)
_sbar.start()
def _splash_msg(msg): _splash_status.configure(text=msg)


def _boot():
    _splash_msg("Loading settings…")
    app.update_idletasks()
    _splash_msg("Building UI…")
    app.update_idletasks()
    _sbar.stop()
    build_ui()
    _splash_msg("Starting services…")
    app.update_idletasks()
    _splash.destroy()
    auto_upload and schedule_auto_upload()
    _splash_msg("Detecting network…")
    _start_ip_detection()
    # First-run wizard
    _s = load_settings()
    if not _s.get("first_run_done", False):
        app.after(800, _show_first_run_wizard)
    # Auto-update check (silent on startup)
    app.after(3000, lambda: check_for_updates(silent=True))
    app.after(300, lambda: [log(l) for l in [" ", "  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗      ", "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║      ", "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║      ",
              "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║      ", "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗ ", "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ", f"  MC CTRL  ·  {datetime.now().strftime('%A %B %d %Y  %H:%M')} ", " "]])
    app.after(500, lambda: _load_all_addons())


app.after(80, _boot)
app.mainloop()
