"""
auto_update.py  —  MC CTRL Auto-Update Addon
Drop this file in the addons/ folder next to launcher.pyw.

What it does
------------
- Checks GitHub for a newer release tag on startup (background, silent)
- Shows a toast if an update is available
- Adds an "Updates" button to the top bar that opens a full update window
- Downloads, backs up old files, replaces them, prompts restart

Version tagging
---------------
Add this line near the top of launcher.pyw (after the imports):

    LAUNCHER_VERSION = "1.0.0"

Tag your GitHub releases as  v1.0.0  (with the v prefix).
Release ZIP asset must be named  mc_ctrl_release.zip  and contain
the updated .py files at the root level.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import urllib.error
import zipfile
from datetime import datetime
from pathlib import Path

GITHUB_API = "https://api.github.com"

# ── injected by setup() ───────────────────────────────────
_ctx   = {}
_app   = None
_T     = {}
_log   = print
_toast = print

# state
_latest_version   = None
_release_notes    = ""
_download_url     = None
_update_available = False
_checking         = False
_downloading      = False


def _parse_ver(v):
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0,)


def _current_version():
    # Try to read LAUNCHER_VERSION from the main module
    import sys as _sys
    main = _sys.modules.get("__main__") or _sys.modules.get("launcher")
    if main:
        return getattr(main, "LAUNCHER_VERSION", "0.0.0")
    return "0.0.0"


def _repo():
    s = _ctx["load_settings"]()
    return s.get("repo_url", "").replace("https://github.com/", "").replace(".git", "").strip("/")


# ── Check ─────────────────────────────────────────────────

def _check(on_done=None):
    global _latest_version, _release_notes, _download_url, _update_available, _checking
    if _checking:
        return
    _checking = True

    def _run():
        global _latest_version, _release_notes, _download_url, _update_available, _checking
        repo = _repo()
        if not repo or "/" not in repo:
            _log("  [updater] No valid repo URL in settings — skipping update check.")
            _checking = False
            return
        try:
            url = f"{GITHUB_API}/repos/{repo}/releases/latest"
            req = urllib.request.Request(
                url, headers={"User-Agent": "MC-CTRL-Addon/1.0",
                              "Accept":     "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())

            tag = data.get("tag_name", "")
            _latest_version = tag.lstrip("v")
            _release_notes  = data.get("body", "No release notes.")
            _download_url   = None

            for asset in data.get("assets", []):
                if asset["name"].endswith(".zip"):
                    _download_url = asset["browser_download_url"]
                    break
            if not _download_url:
                _download_url = data.get("zipball_url")

            cur = _parse_ver(_current_version())
            lat = _parse_ver(_latest_version)
            _update_available = lat > cur

            if _update_available:
                _log(f"  [updater] Update available: v{_current_version()} → v{_latest_version}")
                _app.after(0, _toast,
                           f"MC CTRL v{_latest_version} available — open Updates",
                           _T.get("sync", "#60a5fa"))
            else:
                _log(f"  [updater] Up to date (v{_current_version()}).")

        except urllib.error.URLError:
            _log("  [updater] Update check failed — no connection.")
        except Exception as ex:
            _log(f"  [updater] Check error: {ex}")
        finally:
            _checking = False
            if on_done:
                _app.after(0, on_done)

    threading.Thread(target=_run, daemon=True).start()


# ── Install ───────────────────────────────────────────────

def _install(progress_cb=None):
    global _downloading

    def _prog(f, msg):
        if progress_cb:
            try:
                _app.after(0, progress_cb, f, msg)
            except Exception:
                pass

    if _downloading or not _download_url:
        return
    _downloading = True

    def _run():
        global _downloading
        _prog(0.05, "Downloading…")
        app_dir = Path(os.path.dirname(os.path.abspath(
            sys.modules["__main__"].__file__
            if hasattr(sys.modules.get("__main__", object()), "__file__")
            else __file__)))
        try:
            tmp = Path(tempfile.mkdtemp())
            zip_path = tmp / "mc_ctrl_update.zip"

            req = urllib.request.Request(
                _download_url,
                headers={"User-Agent": "MC-CTRL-Addon/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                total = int(r.headers.get("Content-Length", 0))
                done  = 0
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            _prog(0.05 + 0.55 * done / total,
                                  f"Downloading… {done//1024}/{total//1024} KB")

            _prog(0.62, "Extracting…")
            extract_dir = tmp / "ex"
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)

            contents = list(extract_dir.iterdir())
            src_root = contents[0] if len(contents) == 1 and contents[0].is_dir() else extract_dir

            _prog(0.72, "Backing up current files…")
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            targets = ["launcher.pyw", "mc_backup.py", "auto_update.py"]
            for name in targets:
                cur = app_dir / name
                if cur.exists():
                    shutil.copy2(cur, app_dir / f"{name}.bak_{ts}")

            _prog(0.82, "Installing…")
            installed = []
            for name in targets:
                src = src_root / name
                if src.exists():
                    shutil.copy2(src, app_dir / name)
                    installed.append(name)
                    _log(f"  [updater] Installed: {name}")

            shutil.rmtree(tmp, ignore_errors=True)

            if not installed:
                _prog(0, "No files found in release ZIP.")
                _downloading = False
                return

            _prog(1.0, f"v{_latest_version} installed! Restart to apply.")
            _log(f"  [updater] Done: {', '.join(installed)}")
            _app.after(0, _toast,
                       f"Updated to v{_latest_version}! Restart MC CTRL.",
                       _T.get("start", "#22c55e"))
            _app.after(0, _show_restart_prompt)

        except Exception as ex:
            _log(f"  [updater] Install error: {ex}")
            _prog(0, f"Failed: {ex}")
            _app.after(0, _toast, f"Update failed: {ex}", _T.get("stop", "#ef4444"))
        finally:
            _downloading = False

    threading.Thread(target=_run, daemon=True).start()


def _show_restart_prompt():
    import customtkinter as ctk
    win = ctk.CTkToplevel(_app)
    win.title("Restart Required")
    win.resizable(False, False)
    win.configure(fg_color=_T.get("bg", "#0d0d0d"))
    win.grab_set()
    win.attributes("-topmost", True)
    try:
        ax = _app.winfo_x() + (_app.winfo_width()  - 420) // 2
        ay = _app.winfo_y() + (_app.winfo_height() - 200) // 2
        win.geometry(f"420x200+{ax}+{ay}")
    except Exception:
        win.geometry("420x200")

    ctk.CTkLabel(win, text="🔄  Update Installed",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=_T.get("start", "#22c55e")).pack(pady=(22, 4))
    ctk.CTkLabel(win,
                 text=f"MC CTRL v{_latest_version} is ready.\nRestart now to apply.",
                 font=ctk.CTkFont(size=12),
                 text_color=_T.get("muted", "#555")).pack()

    br = ctk.CTkFrame(win, fg_color="transparent"); br.pack(pady=18)

    def _restart():
        win.destroy()
        subprocess.Popen([sys.executable,
                          str(Path(os.path.abspath(
                              sys.modules["__main__"].__file__
                              if hasattr(sys.modules.get("__main__", object()), "__file__")
                              else __file__)))])
        _app.after(300, _app.destroy)

    ctk.CTkButton(br, text="Restart Now", width=130, height=34,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=_T.get("start", "#22c55e"),
                  hover_color=_T.get("start", "#22c55e"),
                  text_color="#000", command=_restart).pack(side="left", padx=(0, 10))
    ctk.CTkButton(br, text="Later", width=80, height=34,
                  font=ctk.CTkFont(size=12),
                  fg_color="transparent", border_width=1,
                  border_color=_T.get("border", "#2a2a2a"),
                  text_color=_T.get("muted", "#555"),
                  hover_color=_T.get("border", "#2a2a2a"),
                  command=win.destroy).pack(side="left")


# ── Update window ─────────────────────────────────────────

def _open_update_window():
    import customtkinter as ctk

    win = ctk.CTkToplevel(_app)
    win.title("MC CTRL — Updates")
    win.geometry("680x580")
    win.resizable(True, True)
    win.configure(fg_color=_T.get("bg", "#0d0d0d"))
    win.grab_set()
    win.attributes("-topmost", True)
    try:
        ax = _app.winfo_x() + (_app.winfo_width()  - 680) // 2
        ay = _app.winfo_y() + (_app.winfo_height() - 580) // 2
        win.geometry(f"680x580+{ax}+{ay}")
    except Exception:
        pass

    # ── scrollable body ───────────────────────────────────
    scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=16, pady=12)

    def _card(title):
        f = ctk.CTkFrame(scroll, fg_color=_T.get("card","#1a1a1a"),
                         border_color=_T.get("border","#2a2a2a"),
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=(0, 10))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(h, text=title,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=_T.get("text","#e0e0e0")).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=_T.get("border","#2a2a2a")).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8,12))
        return body, h

    # ── Version card ──────────────────────────────────────
    vb, vh = _card("Version")

    def _ver_row(label, value, color=None):
        r = ctk.CTkFrame(vb, fg_color="transparent"); r.pack(fill="x", pady=2)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=11),
                     text_color=_T.get("muted","#555"), width=160, anchor="w").pack(side="left")
        ctk.CTkLabel(r, text=value,
                     font=ctk.CTkFont(size=12, weight="bold", family="Consolas"),
                     text_color=color or _T.get("text","#e0e0e0")).pack(side="left")

    _ver_row("Current version:", f"v{_current_version()}")
    latest_lbl = ctk.CTkLabel(vb, text="v??? (checking…)",
                               font=ctk.CTkFont(size=12, weight="bold", family="Consolas"),
                               text_color=_T.get("muted","#555"))
    r2 = ctk.CTkFrame(vb, fg_color="transparent"); r2.pack(fill="x", pady=2)
    ctk.CTkLabel(r2, text="Latest version:", font=ctk.CTkFont(size=11),
                 text_color=_T.get("muted","#555"), width=160, anchor="w").pack(side="left")
    latest_lbl.pack(side="left") if False else r2.pack_forget()   # replaced below
    latest_lbl = ctk.CTkLabel(r2, text="checking…",
                               font=ctk.CTkFont(size=12, weight="bold", family="Consolas"),
                               text_color=_T.get("muted","#555"))
    latest_lbl.pack(side="left")

    status_lbl = ctk.CTkLabel(vb, text="",
                               font=ctk.CTkFont(size=12),
                               text_color=_T.get("muted","#555"))
    status_lbl.pack(anchor="w", pady=(4, 0))

    prog_var = ctk.DoubleVar(value=0)
    prog_bar = ctk.CTkProgressBar(vb, variable=prog_var, height=6)
    prog_msg = ctk.CTkLabel(vb, text="", font=ctk.CTkFont(size=11),
                             text_color=_T.get("muted","#555"))

    install_btn = ctk.CTkButton(vb, text="⬇ Install Update", height=34,
                                font=ctk.CTkFont(size=12, weight="bold"),
                                fg_color=_T.get("sync","#60a5fa"),
                                hover_color=_T.get("sync","#60a5fa"),
                                text_color="#000", state="disabled")
    install_btn.pack(anchor="w", pady=(8, 0))

    def _on_prog(f, msg):
        prog_var.set(f)
        prog_msg.configure(text=msg)
        if f > 0:
            prog_bar.pack(fill="x", pady=(4, 0))
            prog_msg.pack(anchor="w")
        if f >= 1.0:
            install_btn.configure(state="disabled",
                                  text="✓ Installed — restart to apply")

    def _refresh_ui():
        if _latest_version:
            c = _T.get("start","#22c55e") if _update_available else _T.get("text","#e0e0e0")
            latest_lbl.configure(text=f"v{_latest_version}", text_color=c)
            if _update_available:
                status_lbl.configure(
                    text=f"🔄  v{_current_version()} → v{_latest_version} available",
                    text_color=_T.get("start","#22c55e"))
                install_btn.configure(state="normal",
                                      command=lambda: _install(_on_prog))
            else:
                status_lbl.configure(text="✓  You're on the latest version.",
                                     text_color=_T.get("start","#22c55e"))
        else:
            latest_lbl.configure(text="Could not fetch.", text_color=_T.get("stop","#ef4444"))

    def _do_check():
        latest_lbl.configure(text="checking…", text_color=_T.get("muted","#555"))
        status_lbl.configure(text="")
        _check(on_done=_refresh_ui)

    ctk.CTkButton(vh, text="Check Now", width=80, height=22,
                  font=ctk.CTkFont(size=10), fg_color=_T.get("sync","#60a5fa"),
                  hover_color=_T.get("sync","#60a5fa"), text_color="#000",
                  command=_do_check).pack(side="right")

    _refresh_ui() if _latest_version else _do_check()

    # ── Release notes card ────────────────────────────────
    nb, _ = _card("Release Notes")
    notes_box = ctk.CTkTextbox(nb, height=140,
                                font=ctk.CTkFont(size=11, family="Consolas"),
                                wrap="word", state="disabled",
                                fg_color=_T.get("bg","#0d0d0d"),
                                text_color=_T.get("text","#e0e0e0"))
    notes_box.pack(fill="x")

    def _set_notes(txt):
        notes_box.configure(state="normal")
        notes_box.delete("1.0", "end")
        notes_box.insert("end", txt or "No notes.")
        notes_box.configure(state="disabled")

    if _release_notes:
        _set_notes(_release_notes)

    # ── Backup files card ─────────────────────────────────
    bb, _ = _card("Backup Files")
    ctk.CTkLabel(bb,
                 text="These are created automatically before each update:",
                 font=ctk.CTkFont(size=11),
                 text_color=_T.get("muted","#555")).pack(anchor="w", pady=(0,6))

    bak_frame = ctk.CTkFrame(bb, fg_color=_T.get("bg","#0d0d0d"),
                               border_color=_T.get("border","#2a2a2a"),
                               border_width=1, corner_radius=8)
    bak_frame.pack(fill="x")

    def _list_baks():
        for w in bak_frame.winfo_children(): w.destroy()
        app_dir = Path(os.path.dirname(os.path.abspath(
            sys.modules["__main__"].__file__
            if hasattr(sys.modules.get("__main__", object()), "__file__")
            else __file__)))
        baks = sorted(app_dir.glob("*.bak_*"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        if not baks:
            ctk.CTkLabel(bak_frame, text="No backup files yet.",
                         font=ctk.CTkFont(size=11),
                         text_color=_T.get("muted","#555")).pack(padx=14, pady=8)
            return
        for bak in baks[:10]:
            r = ctk.CTkFrame(bak_frame, fg_color="transparent"); r.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r, text=bak.name,
                         font=ctk.CTkFont(size=10, family="Consolas"),
                         text_color=_T.get("text","#e0e0e0")).pack(side="left")
            ctk.CTkLabel(r, text=f"{bak.stat().st_size//1024} KB",
                         font=ctk.CTkFont(size=10),
                         text_color=_T.get("muted","#555")).pack(side="left", padx=8)
            def _del(p=bak):
                try:
                    p.unlink()
                    _list_baks()
                except Exception: pass
            ctk.CTkButton(r, text="Delete", width=56, height=20,
                          font=ctk.CTkFont(size=9), fg_color="transparent",
                          border_width=1, border_color=_T.get("stop","#ef4444"),
                          text_color=_T.get("stop","#ef4444"),
                          hover_color=_T.get("border","#2a2a2a"),
                          command=_del).pack(side="right")

    _list_baks()


# ── Addon entry point ─────────────────────────────────────

def setup(ctx):
    global _ctx, _app, _T, _log, _toast
    _ctx   = ctx
    _app   = ctx["app"]
    _T     = ctx["T"]
    _log   = ctx["log"]
    _toast = ctx["show_toast"]

    # Add "Updates" button to the top bar
    try:
        import customtkinter as ctk
        # Find the top bar (first CTkFrame child of app)
        top_bar = None
        for child in _app.winfo_children():
            if type(child).__name__ == "CTkFrame":
                top_bar = child
                break
        if top_bar:
            ctk.CTkButton(
                top_bar, text="🔄 Updates", width=90, height=28,
                font=ctk.CTkFont(size=11), corner_radius=6,
                fg_color=_T.get("bg","#0d0d0d"), border_width=1,
                border_color=_T.get("border","#2a2a2a"),
                text_color=_T.get("muted","#555"),
                hover_color=_T.get("border","#2a2a2a"),
                command=_open_update_window
            ).pack(side="left", padx=(0, 6), pady=8)
    except Exception as ex:
        _log(f"  [updater] Could not add button: {ex}")

    _log("  [updater] Auto-update addon loaded.")
