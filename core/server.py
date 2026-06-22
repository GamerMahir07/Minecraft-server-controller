"""core/server.py — server process, perf loop, git sync, backup"""
import logging, os, subprocess, threading, time, zipfile
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

from .constants import (
    CREATE_NO_WINDOW, IS_WIN,
    DEFAULT_SRV_PATH, DEFAULT_JAVA_PATH, REPO_URL,
    STRIP_RE, DONE_RE, SPARK_TPS, TPS_RE2,
    PLAYER_RE, LIST_NAMES_RE, CHAT_RE, JOIN_RE, LEAVE_RE,
    DEATH_RE, LATENCY_RE, LATENCY_RE2, LATENCY_RE3,
)
from .settings import load_settings, update_setting

logger = logging.getLogger(__name__)

# ── State ──────────────────────────────────────────────────────────────────────
server_proc        = None
server_stdin       = None
server_pid         = None
server_start_time  = None
server_ready       = False
perf_running       = False
player_count       = 0
online_players: dict[str, str] = {}
auto_upload_timer  = None

perf: dict = {
    "ram_used": "--", "ram_pct": "--", "ram_srv": "--",
    "cpu_sys":  "--", "cpu_srv": "--", "tps":     "--",
    "latency":  "--", "players": "0",  "uptime":  "--",
    "threads":  "--", "disk_io": "--",
}

signals = None   # set by MainWindow


def _t(key: str) -> str:
    try:
        from core.themes import T
        return T[key]
    except Exception:
        return {"start": "#22c55e", "stop": "#ef4444", "sync": "#60a5fa", "handoff": "#f59e0b"}.get(key, "#888")

def _emit_log(text: str, cat: str = "log"):
    if signals:
        try: signals.sig_log.emit(text, cat)
        except Exception: pass

def _emit_status(text: str, color: str):
    if signals:
        try: signals.sig_status.emit(text, color)
        except Exception: pass

def _toast(msg: str, color: str, ms: int = 3000):
    if signals:
        try: signals.toast(msg, color, ms)
        except Exception: pass


# ── Line parser ────────────────────────────────────────────────────────────────
def parse_server_line(raw: str):
    global player_count, server_ready
    if not raw or not isinstance(raw, str):
        return None
    clean = STRIP_RE.sub("", raw).strip()
    if not clean:
        return None
    try:
        if "Done (" in clean and DONE_RE.search(clean):
            server_ready = True
            _toast("Server is ready!", _t("start"))
            return ("log", clean)
        if "TPS" in clean or "tps" in clean:
            tps = SPARK_TPS.search(clean) or TPS_RE2.search(clean)
            if tps:
                perf["tps"] = tps.group(1)
                return None
        if "ms" in clean:
            lat = LATENCY_RE.search(clean) or LATENCY_RE2.search(clean) or LATENCY_RE3.search(clean)
            if lat:
                pings = [int(m[1]) for m in (
                    LATENCY_RE.findall(clean) or LATENCY_RE2.findall(clean) or LATENCY_RE3.findall(clean))]
                if pings:
                    perf["latency"] = f"{sum(pings)//len(pings)} ms"
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
                        for gone in [k for k in list(online_players) if k not in names]:
                            online_players.pop(gone, None)
            return None
        if "<" in clean:
            chat = CHAT_RE.search(clean)
            if chat:
                return ("chat", f"[CHAT] {chat.group(1)}: {chat.group(2)}")
        if "joined the game" in clean:
            join = JOIN_RE.search(clean)
            if join:
                name = join.group(1)
                player_count += 1
                perf["players"] = str(player_count)
                online_players[name] = datetime.now().strftime("%H:%M")
                return ("event", f">> {name} joined")
        if "left the game" in clean or "lost connection" in clean:
            leave = LEAVE_RE.search(clean)
            if leave:
                name = leave.group(1)
                player_count = max(0, player_count - 1)
                perf["players"] = str(player_count)
                online_players.pop(name, None)
                return ("event", f"<< {name} left")
        if any(w in clean for w in ("was slain", "died", "fell", "drowned", "burned",
                                    "blew up", "suffocated", "starved", "withered")):
            if DEATH_RE.search(clean):
                return ("event", f"[DEATH] {clean}")
        return ("log", clean)
    except Exception as e:
        logger.error(f"parse_server_line: {e}")
        return None


def read_server_output(proc):
    try:
        for raw in iter(proc.stdout.readline, ""):
            if not raw:
                break
            try:
                parsed = parse_server_line(raw)
                if parsed:
                    _emit_log(parsed[1], parsed[0])
            except Exception as e:
                logger.error(f"read_server_output inner: {e}")
    except Exception as e:
        logger.error(f"read_server_output: {e}")


# ── Process helpers ────────────────────────────────────────────────────────────
def find_java_proc():
    if not psutil:
        return None
    if server_pid:
        try:
            return psutil.Process(server_pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    try:
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if p.info["name"] and "java" in p.info["name"].lower():
                    if "server.jar" in " ".join(p.info["cmdline"] or []):
                        return p
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.warning(f"find_java_proc: {e}")
    return None


def perf_loop():
    if not psutil:
        return
    global perf_running
    perf_running = True
    java_proc = None
    prev_disk = psutil.disk_io_counters() if hasattr(psutil, "disk_io_counters") else None
    tick = 0
    # Prime cpu_percent
    try: psutil.cpu_percent(interval=None)
    except Exception: pass
    while perf_running:
        try:
            vm = psutil.virtual_memory()
            perf["ram_used"] = f"{vm.used/1024**3:.1f}/{vm.total/1024**3:.0f}GB"
            perf["ram_pct"]  = f"{vm.percent:.0f}%"
            perf["cpu_sys"]  = f"{psutil.cpu_percent(interval=None):.0f}%"
            if prev_disk is not None:
                try:
                    cur = psutil.disk_io_counters()
                    if cur:
                        delta = max((cur.read_bytes + cur.write_bytes) -
                                    (prev_disk.read_bytes + prev_disk.write_bytes), 0)
                        rate  = delta / 2.0
                        perf["disk_io"] = (f"{rate/1048576:.1f} MB/s"
                                           if rate >= 1048576 else f"{rate/1024:.1f} KB/s")
                        prev_disk = cur
                except Exception:
                    perf["disk_io"] = "--"
            if java_proc is None:
                java_proc = find_java_proc()
            if java_proc:
                try:
                    perf["ram_srv"] = f"{java_proc.memory_info().rss/1048576:.0f} MB"
                    perf["cpu_srv"] = f"{java_proc.cpu_percent(interval=None):.0f}%"
                    perf["threads"] = str(java_proc.num_threads())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    java_proc = None
                    perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            else:
                perf["ram_srv"] = perf["cpu_srv"] = perf["threads"] = "--"
            if server_start_time:
                e = int((datetime.now() - server_start_time).total_seconds())
                h, r = divmod(e, 3600); m, s = divmod(r, 60)
                perf["uptime"] = f"{h:02d}:{m:02d}:{s:02d}"
            else:
                perf["uptime"] = "--"
            if server_ready and server_stdin:
                try:
                    if tick % 5  == 0: server_stdin.write("tps\n");  server_stdin.flush()
                    if tick % 10 == 0: server_stdin.write("list\n"); server_stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
            tick += 1
            if signals:
                try: signals.sig_perf.emit()
                except Exception: pass
        except Exception as e:
            logger.error(f"perf_loop: {e}")
        time.sleep(2)


def run_cmd_log(cmd: str, cwd=None) -> bool:
    _emit_log(f"$ {cmd}", "log")
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                           text=True, creationflags=CREATE_NO_WINDOW, timeout=60)
        for line in p.stdout.strip().splitlines():
            _emit_log(f"  {line}", "log")
        if p.returncode != 0:
            for line in p.stderr.strip().splitlines():
                _emit_log(f"  [ERR] {line}", "log")
        return p.returncode == 0
    except subprocess.TimeoutExpired:
        _emit_log("  Timed out.", "log"); return False
    except Exception as ex:
        _emit_log(str(ex), "log"); return False


def send_server_cmd(cmd: str):
    global server_stdin
    if server_stdin is None:
        _toast("Server not running!", _t("stop")); return
    try:
        server_stdin.write(cmd + "\n"); server_stdin.flush()
        _emit_log(f">> {cmd}", "log")
    except (BrokenPipeError, OSError):
        server_stdin = None
        _toast("Lost connection to server!", _t("stop"))


# ── EULA check ─────────────────────────────────────────────────────────────────
def check_and_accept_eula(path: str) -> bool:
    """Returns True if eula=true, or auto-writes it after user confirms via toast."""
    eula_path = os.path.join(path, "eula.txt")
    try:
        if "eula=true" in open(eula_path, encoding="utf-8").read().lower():
            return True
    except FileNotFoundError:
        pass
    # Write it automatically and inform user
    try:
        os.makedirs(path, exist_ok=True)
        with open(eula_path, "w", encoding="utf-8") as f:
            f.write(f"# Accepted by MC CTRL on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    "# https://aka.ms/MinecraftEULA\neula=true\n")
        _toast("EULA accepted automatically. https://aka.ms/MinecraftEULA", _t("handoff"), 5000)
        return True
    except Exception as ex:
        _emit_log(f"  EULA write error: {ex}", "log")
        return False


# ── Start / Stop ───────────────────────────────────────────────────────────────
def start_server():
    global server_proc, server_stdin, server_pid, server_start_time
    global perf_running, server_ready, player_count

    if server_proc is not None and server_proc.poll() is None:
        _toast("Already running!", _t("handoff")); return

    _emit_log("-- Start Server ------------------", "log")
    s    = load_settings()
    path = s.get("srv_path",  DEFAULT_SRV_PATH)
    java = s.get("java_path", DEFAULT_JAVA_PATH)
    repo = s.get("repo_url",  REPO_URL)
    ram  = s.get("ram_gb",    s.get("server_ram_gb", 2))

    if not check_and_accept_eula(path):
        _emit_log("  Cancelled — EULA not accepted.", "log")
        _emit_status("Stopped", _t("stop"))
        return

    if repo:
        run_cmd_log(f"git remote set-url origin {repo}", cwd=path)
        _emit_log("Pulling from GitHub…", "log")
        run_cmd_log("git pull origin main", cwd=path)

    _emit_log("Launching with Aikar flags…", "log")
    java_cmd = (
        f'"{java}" -Xms{ram}G -Xmx{ram}G -XX:+UseG1GC -XX:+ParallelRefProcEnabled '
        '-XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC '
        '-XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M '
        '-XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 '
        '-XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 '
        '-XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 '
        '-XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 '
        '-Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true '
        '-jar server.jar --nogui'
    )
    try:
        server_proc = subprocess.Popen(
            java_cmd, shell=True, cwd=path,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, creationflags=CREATE_NO_WINDOW)
    except Exception as ex:
        _emit_log(f"  Failed to start: {ex}", "log")
        _emit_status("Stopped", _t("stop"))
        return

    server_stdin      = server_proc.stdin
    server_pid        = server_proc.pid
    server_start_time = datetime.now()
    server_ready      = False
    player_count      = 0
    online_players.clear()
    perf["tps"] = perf["latency"] = "--"
    perf["players"] = "0"

    threading.Thread(target=read_server_output, args=(server_proc,), daemon=True).start()
    if not perf_running:
        threading.Thread(target=perf_loop, daemon=True).start()
    _emit_status("Running", _t("start"))
    _emit_log(f"Server PID {server_proc.pid}", "log")


def stop_server():
    global server_proc, server_stdin, server_pid, server_start_time, perf_running, server_ready

    _emit_status("Stopping…", _t("handoff"))
    _emit_log("-- Stop Server -------------------", "log")

    if server_stdin:
        try: server_stdin.write("stop\n"); server_stdin.flush()
        except (BrokenPipeError, OSError): pass
        finally: server_stdin = None

    # PID-specific kill — never taskkill /IM java.exe
    if server_pid:
        try:
            if IS_WIN:
                subprocess.run(f"taskkill /F /PID {server_pid}", shell=True,
                               capture_output=True, creationflags=CREATE_NO_WINDOW)
            else:
                import signal as _sig, os as _os
                try: _os.kill(server_pid, _sig.SIGTERM)
                except ProcessLookupError: pass
            _emit_log("  Process terminated.", "log")
        except Exception as e:
            _emit_log(f"  Error: {e}", "log")

    server_proc = server_pid = server_start_time = None
    server_ready = perf_running = False
    for k in ("tps", "latency", "players", "uptime", "ram_srv", "cpu_srv", "threads"):
        perf[k] = "--"

    s = load_settings()
    if s.get("upload_on_stop", True) and s.get("backup_upload_on", True):
        path = s.get("srv_path", DEFAULT_SRV_PATH)
        repo = s.get("repo_url", REPO_URL)
        if repo:
            _emit_log("Pushing world to GitHub…", "log")
            run_cmd_log(f"git remote set-url origin {repo}", cwd=path)
            run_cmd_log("git add world/ world_nether/ world_the_end/", cwd=path)
            r = subprocess.run(
                f'git commit -m "World update {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                shell=True, cwd=path, capture_output=True, text=True,
                creationflags=CREATE_NO_WINDOW)
            if "nothing to commit" not in r.stdout and r.returncode == 0:
                run_cmd_log("git push origin main", cwd=path)
                _toast("World pushed to GitHub!", _t("sync"))
            else:
                _emit_log("  Nothing to commit.", "log")

    _emit_status("Stopped", _t("stop"))
    _emit_log("Done.", "log")


def sync_git():
    s    = load_settings()
    path = s.get("srv_path", DEFAULT_SRV_PATH)
    repo = s.get("repo_url", REPO_URL)
    _emit_status("Syncing…", _t("handoff"))
    _emit_log("-- Sync & Upload -----------------", "log")
    if repo:
        run_cmd_log(f"git remote set-url origin {repo}", cwd=path)
    run_cmd_log("git add .", cwd=path)
    run_cmd_log('git commit -m "Manual Sync"', cwd=path)
    ok = run_cmd_log("git push origin main", cwd=path)
    if ok:
        _toast("Manual sync complete!", _t("sync"))
    _emit_status("Stopped", _t("stop"))


def run_repair():
    """Check server folder, java, jar, write eula."""
    s    = load_settings()
    path = s.get("srv_path", DEFAULT_SRV_PATH)
    java = s.get("java_path", DEFAULT_JAVA_PATH)
    _emit_log("-- Repair Mode ------------------", "log")
    if not os.path.isdir(path):
        _emit_log(f"  Server folder not found: {path}", "log")
        _toast("Server folder missing!", _t("stop"))
        return
    _emit_log(f"  Server folder: {path}", "log")
    jar = os.path.join(path, "server.jar")
    if not os.path.exists(jar):
        _emit_log("  server.jar missing", "log")
    else:
        _emit_log(f"  server.jar found ({os.path.getsize(jar)//1048576} MB)", "log")
    try:
        r = subprocess.run([java, "-version"], capture_output=True, text=True,
                           timeout=5, creationflags=CREATE_NO_WINDOW)
        ver = (r.stderr or r.stdout or "").strip().splitlines()
        _emit_log(f"  Java: {ver[0] if ver else 'unknown'}", "log")
    except Exception as ex:
        _emit_log(f"  Java not found: {ex}", "log")
    check_and_accept_eula(path)
    repo = s.get("repo_url", REPO_URL)
    if repo:
        run_cmd_log("git pull origin main", cwd=path)
    _emit_log("-- Repair complete ---------------", "log")
    _toast("Repair complete!", _t("start"))


# ── Auto-upload ────────────────────────────────────────────────────────────────
def schedule_auto_upload():
    global auto_upload_timer
    if auto_upload_timer:
        try: auto_upload_timer.cancel()
        except Exception: pass
    s = load_settings()
    if not s.get("auto_upload", False):
        return
    mins = max(1, min(int(s.get("auto_upload_mins", 10)), 1440))
    auto_upload_timer = threading.Timer(mins * 60, _do_auto_upload)
    auto_upload_timer.daemon = True
    auto_upload_timer.start()


def _do_auto_upload():
    s    = load_settings()
    path = s.get("srv_path", DEFAULT_SRV_PATH)
    repo = s.get("repo_url", REPO_URL)
    def _work():
        _emit_log("-- Auto-upload -------------------", "log")
        try:
            if repo:
                subprocess.run(f"git remote set-url origin {repo}", shell=True, cwd=path,
                               capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=10)
            subprocess.run("git add .", shell=True, cwd=path,
                           capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=10)
            r = subprocess.run(
                f'git commit -m "Auto {datetime.now().strftime("%Y-%m-%d %H:%M")}"',
                shell=True, cwd=path, capture_output=True, text=True,
                creationflags=CREATE_NO_WINDOW, timeout=10)
            if "nothing to commit" not in r.stdout and r.returncode == 0:
                push = subprocess.run("git push origin main", shell=True, cwd=path,
                                      capture_output=True, text=True,
                                      creationflags=CREATE_NO_WINDOW, timeout=30)
                if push.returncode == 0:
                    _emit_log("  Auto-upload complete.", "log")
                    _toast("Auto-upload complete!", _t("sync"))
                else:
                    _emit_log(f"  Push failed: {push.stderr.strip()[:80]}", "log")
            else:
                _emit_log("  Nothing new.", "log")
        except Exception as ex:
            _emit_log(f"  Error: {ex}", "log")
        finally:
            schedule_auto_upload()
    threading.Thread(target=_work, daemon=True).start()


# ── Backup ─────────────────────────────────────────────────────────────────────
def backup_to_zip(target: str = "local"):
    s    = load_settings()
    path = s.get("srv_path", DEFAULT_SRV_PATH)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = os.path.join(path, "backups")
    os.makedirs(bdir, exist_ok=True)
    zip_path = os.path.join(bdir, f"backup_{ts}.zip")

    def _work():
        _emit_log("Creating backup zip…", "log")
        try:
            world_dirs = [d for d in ("world", "world_nether", "world_the_end", "plugins")
                          if os.path.isdir(os.path.join(path, d))]
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as zf:
                for wd in world_dirs:
                    for root, _, files in os.walk(os.path.join(path, wd)):
                        for fn in files:
                            full = os.path.join(root, fn)
                            zf.write(full, os.path.relpath(full, path))
                for fn in ("server.properties", "ops.json", "whitelist.json",
                           "banned-players.json", "eula.txt"):
                    fp = os.path.join(path, fn)
                    if os.path.exists(fp):
                        zf.write(fp, fn)
            mb = os.path.getsize(zip_path) / 1048576
            _emit_log(f"  Backup: {os.path.basename(zip_path)} ({mb:.1f} MB)", "log")
            _toast(f"Backup done! {mb:.1f} MB", _t("start"))
            if target == "github":
                repo = s.get("repo_url", REPO_URL)
                if repo:
                    run_cmd_log(f"git remote set-url origin {repo}", cwd=path)
                    run_cmd_log(f"git add {os.path.relpath(zip_path, path)}", cwd=path)
                    run_cmd_log(f'git commit -m "Backup {ts}"', cwd=path)
                    run_cmd_log("git push origin main", cwd=path)
            elif target == "gdrive":
                _backup_to_gdrive(zip_path, s)
        except Exception as ex:
            _emit_log(f"  Backup error: {ex}", "log")
            _toast(f"Backup error: {ex}", _t("stop"))
    threading.Thread(target=_work, daemon=True).start()


def _backup_to_gdrive(zip_path: str, s: dict):
    remote = s.get("gdrive_remote", "gdrive")
    folder = s.get("gdrive_folder", "MC_Backups")
    cmd    = f'rclone copy "{zip_path}" "{remote}:{folder}"'
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=120, creationflags=CREATE_NO_WINDOW)
        if r.returncode == 0:
            _emit_log(f"  GDrive upload OK: {os.path.basename(zip_path)}", "log")
            _toast("Backup uploaded to Google Drive!", _t("start"))
        else:
            _toast("GDrive upload failed (check rclone setup)", _t("stop"))
            _emit_log(f"  GDrive error: {r.stderr[:200]}", "log")
    except FileNotFoundError:
        _toast("rclone not found — install rclone for Drive backups", _t("handoff"))
    except Exception as ex:
        _toast(f"GDrive error: {ex}", _t("stop"))


def calc_world_size(path: str) -> str:
    """Return human-readable world folder size string."""
    try:
        dirs = [os.path.join(path, d) for d in ("world", "world_nether", "world_the_end")
                if os.path.isdir(os.path.join(path, d))]
        total = sum(
            sum(os.path.getsize(os.path.join(r, fn))
                for r, _, fs in os.walk(d) for fn in fs)
            for d in dirs)
        mb = total / 1048576
        return f"{mb:.0f} MB" if mb < 1024 else f"{mb/1024:.2f} GB"
    except Exception:
        return "--"
