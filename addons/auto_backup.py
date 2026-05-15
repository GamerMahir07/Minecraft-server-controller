"""
auto_backup.py  —  MC CTRL Auto-Backup Addon
Drop this file in the addons/ folder next to launcher.pyw.

What it does
------------
- Zips world folders on a configurable timer
- Zips world folders when the server stops
- Keeps the last N backups (deletes older ones automatically)
- Adds a "Backups" button to the top bar → opens full backup window
- Supports manual backup + restore from the UI

Settings (saved to settings.json automatically)
--------
backup_enabled        true/false   enable scheduled backups
backup_interval_mins  int          how often (default 30)
backup_on_stop        true/false   zip when server stops (default true)
backup_keep_count     int          max backups to keep (default 10)
backup_dir            str          where to save ZIPs (default ./backups/)
backup_world_folders  str          comma-separated folder names (blank = auto)
"""

import os
import re
import shutil
import tempfile
import threading
import zipfile
from datetime import datetime
from pathlib import Path

# ── injected by setup() ───────────────────────────────────
_ctx      = {}
_app      = None
_T        = {}
_log      = print
_toast    = print

_timer    = None
_lock     = threading.Lock()
_busy     = False    # True while a backup is running


# ── Settings shortcuts ────────────────────────────────────

def _s():
    return _ctx["load_settings"]()

def _enabled():      return _s().get("backup_enabled", False)
def _interval():     return max(1, int(_s().get("backup_interval_mins", 30)))
def _on_stop():      return _s().get("backup_on_stop", True)
def _keep():         return max(1, int(_s().get("backup_keep_count", 10)))
def _srv_path():     return Path(_s().get("srv_path", ""))

def _backup_dir():
    d = _s().get("backup_dir", "")
    return Path(d) if d else Path(os.path.dirname(
        os.path.abspath(__file__))).parent / "backups"

def _world_folders():
    raw = _s().get("backup_world_folders", "")
    if isinstance(raw, list):
        return [f.strip() for f in raw if f.strip()]
    return [f.strip() for f in raw.split(",") if f.strip()] if raw else []


# ── Scheduler ─────────────────────────────────────────────

def _schedule():
    global _timer
    _cancel()
    if not _enabled():
        return
    _timer = threading.Timer(_interval() * 60, _scheduled_run)
    _timer.daemon = True
    _timer.start()

def _cancel():
    global _timer
    if _timer:
        try: _timer.cancel()
        except Exception: pass
        _timer = None

def _scheduled_run():
    run_backup("scheduled")
    _schedule()


# ── Core backup ───────────────────────────────────────────

def run_backup(reason="manual", progress_cb=None):
    """Thread-safe. Runs in a background thread."""
    threading.Thread(target=_do_backup, args=(reason, progress_cb),
                     daemon=True).start()

def _prog(cb, f, msg):
    if cb:
        try: _app.after(0, cb, f, msg)
        except Exception: pass

def _do_backup(reason, progress_cb):
    global _busy
    with _lock:
        if _busy:
            _log("  [backup] Already running — skipped.")
            return
        _busy = True
    try:
        srv = _srv_path()
        if not srv or not srv.is_dir():
            _log("  [backup] Server path not set — skipped.")
            return

        dest = _backup_dir()
        dest.mkdir(parents=True, exist_ok=True)

        ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"mcworld_{reason}_{ts}.zip"
        out  = dest / name

        # Decide folders to zip
        folders = _world_folders()
        if not folders:
            folders = []
            for entry in srv.iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    if (entry / "level.dat").exists():
                        folders.append(entry.name)
            if not folders:
                folders = ["world", "world_nether", "world_the_end"]

        # Collect files
        all_files = []
        for fn in folders:
            fp = srv / fn
            if not fp.is_dir():
                continue
            for f in fp.rglob("*"):
                if f.is_file():
                    all_files.append((f, str(Path(fn) / f.relative_to(fp))))

        if not all_files:
            _log("  [backup] No world files found.")
            return

        _log(f"-- Backup [{reason}]: {name} ({len(all_files)} files) --")
        _prog(progress_cb, 0.1, f"Zipping {len(all_files)} files…")

        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for i, (src, arc) in enumerate(all_files):
                try: zf.write(src, arc)
                except Exception: pass
                if i % 300 == 0:
                    _prog(progress_cb, 0.1 + 0.7 * i / len(all_files),
                          f"Zipping… {i}/{len(all_files)}")

        size_mb = out.stat().st_size / 1_048_576
        _log(f"  [backup] Done: {name}  ({size_mb:.1f} MB)")
        _prog(progress_cb, 0.85, f"Done ({size_mb:.1f} MB). Pruning…")

        _prune(dest)
        _prog(progress_cb, 1.0, "Backup complete!")
        _app.after(0, _toast, f"Backup done! ({size_mb:.1f} MB)",
                   _T.get("start","#22c55e"))

    except Exception as ex:
        _log(f"  [backup] Error: {ex}")
        _prog(progress_cb, 0, f"Backup failed: {ex}")
    finally:
        with _lock:
            _busy = False


def _prune(dest):
    zips = sorted(dest.glob("mcworld_*.zip"),
                  key=lambda p: p.stat().st_mtime)
    for old in zips[: max(0, len(zips) - _keep())]:
        try:
            old.unlink()
            _log(f"  [backup] Pruned: {old.name}")
        except Exception: pass


def list_backups():
    try:
        zips = sorted(_backup_dir().glob("mcworld_*.zip"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        return [{"name": p.name, "path": str(p),
                 "size_mb": round(p.stat().st_size / 1_048_576, 1),
                 "mtime": datetime.fromtimestamp(
                     p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")}
                for p in zips]
    except Exception:
        return []


def restore_backup(zip_path, progress_cb=None):
    threading.Thread(target=_do_restore, args=(zip_path, progress_cb),
                     daemon=True).start()

def _do_restore(zip_path, progress_cb):
    def _prog2(f, msg): _prog(progress_cb, f, msg)
    srv = _srv_path()
    if not srv.is_dir(): return
    zp = Path(zip_path)
    if not zp.exists(): return

    _prog2(0.05, "Backing up current world…")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with zipfile.ZipFile(zp) as zf:
        top_dirs = {Path(n).parts[0] for n in zf.namelist()
                    if len(Path(n).parts) > 1}
    for td in top_dirs:
        cur = srv / td
        if cur.is_dir():
            try: shutil.copytree(cur, srv / f"{td}_pre_restore_{ts}")
            except Exception as ex: _log(f"  [backup] Pre-restore backup failed: {ex}")

    _prog2(0.2, "Extracting…")
    try:
        with zipfile.ZipFile(zp) as zf:
            members = zf.namelist()
            for i, m in enumerate(members):
                zf.extract(m, srv)
                if i % 500 == 0:
                    _prog2(0.2 + 0.75 * i / len(members),
                           f"Restoring… {i}/{len(members)}")
        _prog2(1.0, "Restore complete!")
        _log(f"  [backup] Restored: {zp.name}")
        _app.after(0, _toast, "World restored from backup!", _T.get("start","#22c55e"))
    except Exception as ex:
        _log(f"  [backup] Restore error: {ex}")
        _prog2(0, f"Restore failed: {ex}")


# ── Backup window ─────────────────────────────────────────

def _open_backup_window():
    import customtkinter as ctk

    win = ctk.CTkToplevel(_app)
    win.title("MC CTRL — Backups")
    win.geometry("700x620")
    win.resizable(True, True)
    win.configure(fg_color=_T.get("bg","#0d0d0d"))
    win.grab_set()
    win.attributes("-topmost", True)
    try:
        ax = _app.winfo_x() + (_app.winfo_width()  - 700) // 2
        ay = _app.winfo_y() + (_app.winfo_height() - 620) // 2
        win.geometry(f"700x620+{ax}+{ay}")
    except Exception:
        pass

    scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=16, pady=12)

    def _card(title):
        f = ctk.CTkFrame(scroll, fg_color=_T.get("card","#1a1a1a"),
                         border_color=_T.get("border","#2a2a2a"),
                         border_width=1, corner_radius=10)
        f.pack(fill="x", pady=(0, 10))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10,4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=_T.get("text","#e0e0e0")).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=_T.get("border","#2a2a2a")).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8,12))
        return body, h

    # ── Quick backup ──────────────────────────────────────
    qb, _ = _card("Backup Now")
    prog_var = ctk.DoubleVar(value=0)
    prog_bar = ctk.CTkProgressBar(qb, variable=prog_var, height=6)
    st_lbl   = ctk.CTkLabel(qb, text="Ready.",
                              font=ctk.CTkFont(size=11),
                              text_color=_T.get("muted","#555"))

    def _on_prog(f, msg):
        prog_var.set(f)
        st_lbl.configure(text=msg)
        if f > 0: prog_bar.pack(fill="x", pady=(0,4))
        if f >= 1.0:
            _app.after(500, _refresh_list)

    def _do_now():
        prog_bar.pack(fill="x", pady=(0,4))
        st_lbl.configure(text="Starting…", text_color=_T.get("sync","#60a5fa"))
        run_backup("manual", _on_prog)

    ctk.CTkButton(qb, text="▶ Backup Now", height=34,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=_T.get("start","#22c55e"),
                  hover_color=_T.get("start","#22c55e"),
                  text_color="#000", command=_do_now).pack(anchor="w", pady=(0,8))
    st_lbl.pack(anchor="w")

    # ── Settings ──────────────────────────────────────────
    sb, _ = _card("Settings")

    def _sw_row(label, key, default=False):
        r = ctk.CTkFrame(sb, fg_color="transparent"); r.pack(fill="x", pady=3)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color=_T.get("text","#e0e0e0"),
                     width=240, anchor="w").pack(side="left")
        var = ctk.BooleanVar(value=_s().get(key, default))
        def _tog():
            _ctx["load_settings"]   # keep reference alive
            from mc_ctrl_addon_utils import update_setting  # type: ignore
        # use the launcher's update_setting via ctx workaround:
        import sys as _sys
        main = _sys.modules.get("__main__")
        _us  = getattr(main, "update_setting", lambda k,v: None)
        def _tog2():
            _us(key, var.get())
            if key == "backup_enabled": _schedule()
        ctk.CTkSwitch(r, text="", variable=var, command=_tog2,
                      button_color=_T.get("sync","#60a5fa"),
                      progress_color=_T.get("sync","#60a5fa")).pack(side="right")

    def _entry_row(label, key, default):
        import sys as _sys
        main = _sys.modules.get("__main__")
        _us  = getattr(main, "update_setting", lambda k,v: None)
        r = ctk.CTkFrame(sb, fg_color="transparent"); r.pack(fill="x", pady=3)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color=_T.get("text","#e0e0e0"),
                     width=240, anchor="w").pack(side="left")
        var = ctk.StringVar(value=str(_s().get(key, default)))
        e = ctk.CTkEntry(r, textvariable=var, width=120, height=28,
                         font=ctk.CTkFont(size=12, family="Consolas"),
                         fg_color=_T.get("bg","#0d0d0d"),
                         border_color=_T.get("border","#2a2a2a"),
                         text_color=_T.get("text","#e0e0e0"))
        e.pack(side="right")
        def _save(*_): _us(key, var.get())
        e.bind("<FocusOut>", _save); e.bind("<Return>", _save)

    _sw_row("Enable scheduled backups",  "backup_enabled",  False)
    _sw_row("Backup when server stops",  "backup_on_stop",  True)
    _entry_row("Interval (minutes)",     "backup_interval_mins", 30)
    _entry_row("Keep last N backups",    "backup_keep_count",    10)

    # Backup dir picker
    import sys as _sys_inner
    _us_inner = getattr(_sys_inner.modules.get("__main__"), "update_setting", lambda k,v: None)
    dr = ctk.CTkFrame(sb, fg_color="transparent"); dr.pack(fill="x", pady=3)
    ctk.CTkLabel(dr, text="Backup directory", font=ctk.CTkFont(size=12),
                 text_color=_T.get("text","#e0e0e0"),
                 width=240, anchor="w").pack(side="left")
    dv = ctk.StringVar(value=_s().get("backup_dir",""))
    de = ctk.CTkEntry(dr, textvariable=dv, height=28,
                      font=ctk.CTkFont(size=11, family="Consolas"),
                      fg_color=_T.get("bg","#0d0d0d"),
                      border_color=_T.get("border","#2a2a2a"),
                      text_color=_T.get("text","#e0e0e0"),
                      placeholder_text="(default: ./backups/)")
    de.pack(side="left", fill="x", expand=True, padx=(0,6))
    def _save_dir(*_): _us_inner("backup_dir", dv.get())
    de.bind("<FocusOut>", _save_dir); de.bind("<Return>", _save_dir)
    def _browse():
        import tkinter.filedialog as fd
        p = fd.askdirectory(title="Select Backup Directory")
        if p: dv.set(p); _us_inner("backup_dir", p)
    ctk.CTkButton(dr, text="…", width=30, height=28,
                  font=ctk.CTkFont(size=11), fg_color="transparent",
                  border_width=1, border_color=_T.get("border","#2a2a2a"),
                  text_color=_T.get("muted","#555"),
                  hover_color=_T.get("border","#2a2a2a"),
                  command=_browse).pack(side="left")

    # ── Local backup list ─────────────────────────────────
    lb, lh = _card("Local Backups")
    list_frame = ctk.CTkFrame(lb, fg_color=_T.get("bg","#0d0d0d"),
                               border_color=_T.get("border","#2a2a2a"),
                               border_width=1, corner_radius=8)
    list_frame.pack(fill="x")

    restore_prog_var = ctk.DoubleVar(value=0)
    restore_prog     = ctk.CTkProgressBar(lb, variable=restore_prog_var, height=6)
    restore_lbl      = ctk.CTkLabel(lb, text="", font=ctk.CTkFont(size=11),
                                     text_color=_T.get("muted","#555"))

    def _restore_prog_cb(f, msg):
        restore_prog_var.set(f)
        restore_lbl.configure(text=msg)
        if f > 0:
            restore_prog.pack(fill="x", pady=(4,0))
            restore_lbl.pack(anchor="w")

    def _do_restore(path):
        import sys as _sys2
        main2 = _sys2.modules.get("__main__")
        sp    = getattr(main2, "server_proc", None)
        if sp and sp.poll() is None:
            _app.after(0, _toast, "Stop the server first!", _T.get("stop","#ef4444"))
            return
        restore_backup(path, _restore_prog_cb)
        _app.after(2000, _refresh_list)

    def _refresh_list():
        for w in list_frame.winfo_children(): w.destroy()
        bks = list_backups()
        if not bks:
            ctk.CTkLabel(list_frame,
                         text="No backups yet. Click ▶ Backup Now above.",
                         font=ctk.CTkFont(size=11),
                         text_color=_T.get("muted","#555")).pack(padx=14, pady=10)
            return
        for bk in bks:
            r = ctk.CTkFrame(list_frame, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(r, text=bk["name"],
                         font=ctk.CTkFont(size=10, family="Consolas"),
                         text_color=_T.get("text","#e0e0e0")).pack(side="left")
            ctk.CTkLabel(r, text=f"  {bk['size_mb']} MB  •  {bk['mtime']}",
                         font=ctk.CTkFont(size=10),
                         text_color=_T.get("muted","#555")).pack(side="left")
            def _del(p=bk["path"], n=bk["name"]):
                try:
                    Path(p).unlink()
                    _app.after(0, _toast, f"Deleted {n}", _T.get("stop","#ef4444"))
                    _refresh_list()
                except Exception as ex:
                    _app.after(0, _toast, f"Error: {ex}", _T.get("stop","#ef4444"))
            ctk.CTkButton(r, text="Restore", width=66, height=22,
                          font=ctk.CTkFont(size=10),
                          fg_color=_T.get("handoff","#f59e0b"),
                          hover_color=_T.get("handoff","#f59e0b"),
                          text_color="#000",
                          command=lambda p=bk["path"]: _do_restore(p)
                          ).pack(side="right", padx=(4,0))
            ctk.CTkButton(r, text="Delete", width=56, height=22,
                          font=ctk.CTkFont(size=10), fg_color="transparent",
                          border_width=1, border_color=_T.get("stop","#ef4444"),
                          text_color=_T.get("stop","#ef4444"),
                          hover_color=_T.get("border","#2a2a2a"),
                          command=_del).pack(side="right")

        def _open_folder():
            try:
                import subprocess
                subprocess.Popen(f'explorer "{_backup_dir()}"', shell=True)
            except Exception: pass

        ctk.CTkButton(list_frame, text="Open Folder", height=26,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=_T.get("border","#2a2a2a"),
                      text_color=_T.get("muted","#555"),
                      hover_color=_T.get("border","#2a2a2a"),
                      command=_open_folder).pack(padx=10, pady=(6,10))

    _refresh_list()
    ctk.CTkButton(lh, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=_T.get("border","#2a2a2a"),
                  text_color=_T.get("muted","#555"),
                  hover_color=_T.get("border","#2a2a2a"),
                  command=_refresh_list).pack(side="right")


# ── Hook into server stop ─────────────────────────────────

def _patch_stop_server():
    """Monkey-patch the launcher's stop_server to trigger backup on stop."""
    import sys as _sys
    main = _sys.modules.get("__main__")
    if not main or not hasattr(main, "stop_server"):
        return
    _orig = main.stop_server

    def _patched():
        _orig()
        if _on_stop():
            _log("  [backup] Server stopped — triggering backup.")
            run_backup("on-stop")

    main.stop_server = _patched
    _log("  [backup] Hooked into stop_server.")


# ── Addon entry point ─────────────────────────────────────

def setup(ctx):
    global _ctx, _app, _T, _log, _toast
    _ctx   = ctx
    _app   = ctx["app"]
    _T     = ctx["T"]
    _log   = ctx["log"]
    _toast = ctx["show_toast"]

    # Add "Backups" button to top bar
    try:
        import customtkinter as ctk
        top_bar = None
        for child in _app.winfo_children():
            if type(child).__name__ == "CTkFrame":
                top_bar = child
                break
        if top_bar:
            ctk.CTkButton(
                top_bar, text="💾 Backups", width=90, height=28,
                font=ctk.CTkFont(size=11), corner_radius=6,
                fg_color=_T.get("bg","#0d0d0d"), border_width=1,
                border_color=_T.get("border","#2a2a2a"),
                text_color=_T.get("muted","#555"),
                hover_color=_T.get("border","#2a2a2a"),
                command=_open_backup_window
            ).pack(side="left", padx=(0, 6), pady=8)
    except Exception as ex:
        _log(f"  [backup] Could not add button: {ex}")

    _patch_stop_server()
    _schedule()
    _log("  [backup] Auto-backup addon loaded.")
