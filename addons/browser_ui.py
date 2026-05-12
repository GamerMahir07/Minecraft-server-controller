"""
MC CTRL Addon — Browser UI
===========================
Opens the MC CTRL web UI in your default browser.
Zero downloads. Uses only Python's built-in http.server.

Drop this in your addons/ folder.
A "🌐 Browser UI" button appears in Settings.
Click it → browser opens → use it alongside the Python launcher.

The browser UI can:
  ✓ View the live activity log (polls every 2 s)
  ✓ Send server commands
  ✓ View server status / uptime / TPS / players
  ✓ Change settings (paths, theme, upload toggles)
  ✓ View connection IPs

It cannot (Python launcher only):
  ✗ Start / stop the server directly (safety — do that from the Python UI)
  ✗ Control playit.gg
  ✗ Multi-server control
"""

import os
import sys
import json
import time
import threading
import webbrowser
import http.server
import urllib.parse
import re
from datetime import datetime

PORT        = 8765
_server     = None
_server_thr = None
_ctx        = {}
_app        = None

# ── Shared log ring-buffer (written by addon, read by browser) ────────────
_log_lines   = []          # list of {"t": timestamp, "msg": str, "cls": str}
_log_lock    = threading.Lock()
_MAX_LOG     = 600

def _classify(line):
    l = line.lower()
    if re.search(r'\[error\]|\berror\b', l): return "err"
    if re.search(r'done \(|joined the game', l): return "ok"
    if line.startswith(">>"): return "cmd"
    if re.search(r'left the game|\[warn\]|death', l): return "ev"
    return ""

def _push_log(line):
    with _log_lock:
        _log_lines.append({
            "t":   datetime.now().strftime("%H:%M:%S"),
            "msg": line,
            "cls": _classify(line),
        })
        if len(_log_lines) > _MAX_LOG:
            del _log_lines[:_MAX_LOG // 2]

# Hook into the launcher's log function so browser sees live output
def _hook_log(original_log):
    def _patched(msg):
        original_log(msg)
        _push_log(msg)
    return _patched

# ── HTTP request handler ───────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *_):
        pass   # suppress server access logs from cluttering the launcher log

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: bytes):
        self.send_response(200)
        self.send_header("Content-Type",  "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/" or path == "/index.html":
            html_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "browser_ui.html")
            if not os.path.exists(html_path):
                self._json({"error": "browser_ui.html not found next to addon"}, 404)
                return
            with open(html_path, "rb") as f:
                self._html(f.read())
            return

        if path == "/api/status":
            import sys as _sys
            main = _sys.modules.get("__main__")
            running = False
            uptime  = None
            tps     = "--"
            players = "0"
            if main:
                proc = getattr(main, "server_proc", None)
                running = bool(proc and proc.poll() is None)
                st = getattr(main, "server_start_time", None)
                if st:
                    uptime = int((datetime.now() - st).total_seconds())
                perf = getattr(main, "perf", {})
                tps     = perf.get("tps",     "--")
                players = perf.get("players", "0")
                ram_srv = perf.get("ram_srv", "--")
                cpu_srv = perf.get("cpu_srv", "--")
            self._json({
                "running": running,
                "uptime":  uptime,
                "tps":     tps,
                "players": players,
                "ram_srv": ram_srv if running else "--",
                "cpu_srv": cpu_srv if running else "--",
            })
            return

        if path == "/api/log":
            qs   = urllib.parse.parse_qs(self.path.split("?",1)[-1])
            since = int(qs.get("since", ["0"])[0])
            with _log_lock:
                lines = _log_lines[since:]
                total = len(_log_lines)
            self._json({"lines": lines, "total": total})
            return

        if path == "/api/settings":
            load = _ctx.get("load_settings", dict)
            self._json(load())
            return

        self._json({"error": "not found"}, 404)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        try:    data = json.loads(body) if body else {}
        except: data = {}

        path = self.path

        if path == "/api/command":
            cmd = data.get("cmd", "").strip()
            if not cmd:
                self._json({"ok": False, "error": "empty command"}); return
            send = _ctx.get("send_server_cmd")
            if send:
                send(cmd)
                _push_log(f">> {cmd}")
                self._json({"ok": True})
            else:
                self._json({"ok": False, "error": "send_server_cmd not available"})
            return

        if path == "/api/settings":
            import sys as _sys
            main = _sys.modules.get("__main__")
            if main and hasattr(main, "update_setting"):
                for k, v in data.items():
                    main.update_setting(k, v)
            self._json({"ok": True})
            return

        self._json({"error": "not found"}, 404)


# ── Server lifecycle ───────────────────────────────────────────────────────
def _start_server():
    global _server
    try:
        _server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
        _server.serve_forever()
    except OSError as e:
        _ctx.get("log", print)(f"  Browser UI server error: {e}")

def _ensure_server():
    global _server_thr, _server
    if _server_thr and _server_thr.is_alive():
        return True
    _server = None
    _server_thr = threading.Thread(target=_start_server, daemon=True)
    _server_thr.start()
    # Wait up to 1 s for it to bind
    for _ in range(20):
        if _server:
            return True
        time.sleep(0.05)
    return False

def _open_browser():
    T     = _ctx.get("T", {})
    log   = _ctx.get("log", print)
    toast = _ctx.get("show_toast", lambda m, c: None)

    ok = _ensure_server()
    if not ok:
        toast("Could not start local server.", T.get("stop", "#ef4444"))
        return

    url = f"http://localhost:{PORT}/"
    log(f"  Browser UI → {url}")
    toast("Opening Browser UI…", T.get("sync", "#60a5fa"))
    webbrowser.open(url)


# ── Inject button into Settings ────────────────────────────────────────────
def _inject():
    import customtkinter as ctk

    if not _app:
        return

    def _find_settings_btn(widget):
        for child in widget.winfo_children():
            try:
                if type(child).__name__ == "CTkButton" and "Settings" in child.cget("text"):
                    return child
            except Exception:
                pass
            found = _find_settings_btn(child)
            if found:
                return found
        return None

    btn = _find_settings_btn(_app)
    if not btn:
        return

    orig = btn.cget("command")

    def _patched():
        if orig: orig()
        _app.after(250, _inject_card)

    btn.configure(command=_patched)


def _inject_card():
    import customtkinter as ctk

    T = _ctx.get("T", {})

    tops = [w for w in _app.winfo_children()
            if type(w).__name__ == "CTkToplevel"]
    if not tops:
        return
    win = tops[-1]

    def _find_scroll(w):
        for child in w.winfo_children():
            if type(child).__name__ == "CTkScrollableFrame":
                return child
            found = _find_scroll(child)
            if found:
                return found
        return None

    scroll = _find_scroll(win)
    if not scroll:
        return

    # Guard against double inject
    for child in scroll.winfo_children():
        if getattr(child, "_browser_ui_card", False):
            return

    section = ctk.CTkFrame(scroll,
                            fg_color=T.get("card","#1a1a1a"),
                            border_color=T.get("border","#2a2a2a"),
                            border_width=1, corner_radius=10)
    section._browser_ui_card = True
    section.pack(fill="x", pady=(0,10))

    hdr = ctk.CTkFrame(section, fg_color="transparent")
    hdr.pack(fill="x", padx=14, pady=(10,4))
    ctk.CTkLabel(hdr, text="Browser UI  (zero install)",
                 font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=T.get("text","#e0e0e0")).pack(side="left")
    ctk.CTkFrame(section, height=1,
                 fg_color=T.get("border","#2a2a2a")).pack(fill="x", padx=14)

    body = ctk.CTkFrame(section, fg_color="transparent")
    body.pack(fill="x", padx=14, pady=(8,12))

    ctk.CTkLabel(body,
                 text="Opens the web UI in your browser. No downloads, no build step.\n"
                      "Uses Python's built-in server on localhost:8765.",
                 font=ctk.CTkFont(size=11),
                 text_color=T.get("muted","#555"),
                 wraplength=540, justify="left").pack(anchor="w", pady=(0,8))

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x")

    ctk.CTkButton(
        row, text="🌐  Open Browser UI",
        height=32, corner_radius=8,
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=T.get("sync","#60a5fa"),
        hover_color=T.get("sync","#60a5fa"),
        text_color="#000000",
        command=lambda: threading.Thread(target=_open_browser, daemon=True).start()
    ).pack(side="left")

    ctk.CTkLabel(row,
                 text=f"  localhost:{PORT}",
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 text_color=T.get("muted","#555")).pack(side="left", padx=(10,0))


# ── Addon entry point ──────────────────────────────────────────────────────
def setup(ctx: dict):
    global _ctx, _app
    _ctx = ctx
    _app = ctx.get("app")

    # Hook into the launcher's log so we capture live server output
    import sys as _sys
    main = _sys.modules.get("__main__")
    if main and hasattr(main, "log"):
        main.log = _hook_log(main.log)

    # Start the HTTP server immediately in the background
    _ensure_server()

    ctx.get("log", print)("Browser UI addon loaded — server running on localhost:8765")

    if _app:
        _app.after(600, _inject)
