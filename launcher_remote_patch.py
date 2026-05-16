"""
MC CTRL — Remote Dashboard Patcher
Run this once from the same folder as launcher.pyw:
    python launcher_remote_patch.py

It patches launcher.pyw in-place to add the 📱 Remote tab.
A backup is saved as launcher.pyw.bak before any changes.
"""

import os, sys, shutil

HERE      = os.path.dirname(os.path.abspath(__file__))
LAUNCHER  = os.path.join(HERE, "launcher.pyw")
BACKUP    = os.path.join(HERE, "launcher.pyw.bak")
REMOTE    = os.path.join(HERE, "remote_dashboard.py")

def fail(msg):
    print(f"\n  [ERROR] {msg}\n"); sys.exit(1)

def check(msg):
    print(f"  ✓  {msg}")

def warn(msg):
    print(f"  ⚠  {msg}")

# ── Preflight ─────────────────────────────────────────────
if not os.path.exists(LAUNCHER):
    fail("launcher.pyw not found in this folder.")
if not os.path.exists(REMOTE):
    fail("remote_dashboard.py not found in this folder.\n"
         "     Make sure both files are in the same directory.")

print("\n  MC CTRL — Remote Dashboard Patcher\n  " + "─"*38)

with open(LAUNCHER, encoding="utf-8") as f:
    src = f.read()

# Already patched?
if "_REMOTE_AVAILABLE" in src:
    warn("launcher.pyw already appears to be patched.")
    ans = input("  Re-apply anyway? [y/N]: ").strip().lower()
    if ans != "y":
        print("  Aborted.\n"); sys.exit(0)
    # Re-read without aborting
    with open(LAUNCHER, encoding="utf-8") as f:
        src = f.read()

# ── Backup ────────────────────────────────────────────────
shutil.copy2(LAUNCHER, BACKUP)
check(f"Backup saved → {BACKUP}")

errors = []

def patch(old, new, desc):
    global src
    if old not in src:
        errors.append(f"Could not find anchor for: {desc}")
        return False
    if new in src:
        warn(f"Already patched: {desc}")
        return True
    src = src.replace(old, new, 1)
    check(desc)
    return True

# ── Patch 1: import ───────────────────────────────────────
patch(
    "from datetime import datetime\ntry:\n    import tkinterdnd2 as dnd",
    "from datetime import datetime\ntry:\n    import remote_dashboard as _remote_mod\n    _REMOTE_AVAILABLE = True\nexcept ImportError:\n    _remote_mod = None\n    _REMOTE_AVAILABLE = False\ntry:\n    import tkinterdnd2 as dnd",
    "Add remote_dashboard import"
)

# ── Patch 2: expose log_box ref ───────────────────────────
patch(
    'log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),\n                             wrap="word", state="disabled",\n                             fg_color="transparent", text_color=T["text"])\n    log_box.pack(fill="both", expand=True, padx=8, pady=(4,8))',
    'log_box = ctk.CTkTextbox(lf, font=ctk.CTkFont(size=11, family="Consolas"),\n                             wrap="word", state="disabled",\n                             fg_color="transparent", text_color=T["text"])\n    log_box.pack(fill="both", expand=True, padx=8, pady=(4,8))\n    if _REMOTE_AVAILABLE and _remote_mod:\n        _remote_mod._state["log_box_ref"] = log_box',
    "Expose log_box ref to remote dashboard"
)

# ── Patch 3: sync running=True on start ───────────────────
patch(
    'set_status("Running", T["start"])\n    log(f"Server is running! (PID {server_proc.pid})")',
    'set_status("Running", T["start"])\n    log(f"Server is running! (PID {server_proc.pid})")\n    if _REMOTE_AVAILABLE and _remote_mod:\n        _remote_mod._state["server_running"] = True\n        _remote_mod._state["perf"] = perf\n        _remote_mod._state["online_players"] = online_players',
    "Sync server_running=True into remote state"
)

# ── Patch 4: sync running=False on stop ───────────────────
patch(
    'set_status("Stopped", T["stop"]); log("Done.")\n    set_all_buttons("normal")',
    'set_status("Stopped", T["stop"]); log("Done.")\n    set_all_buttons("normal")\n    if _REMOTE_AVAILABLE and _remote_mod:\n        _remote_mod._state["server_running"] = False',
    "Sync server_running=False into remote state"
)

# ── Patch 5: add remote_frame ─────────────────────────────
patch(
    '    multictrl_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")\n\n    all_frames = {\n        "dashboard":  dashboard_frame,\n        "network":    network_frame,\n        "serverinfo": serverinfo_frame,\n        "playit":     playit_frame,\n        "multictrl":  multictrl_frame,\n    }',
    '    multictrl_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")\n    remote_frame     = ctk.CTkFrame(tab_content, fg_color="transparent")\n\n    all_frames = {\n        "dashboard":  dashboard_frame,\n        "network":    network_frame,\n        "serverinfo": serverinfo_frame,\n        "playit":     playit_frame,\n        "remote":     remote_frame,\n        "multictrl":  multictrl_frame,\n    }',
    "Add remote_frame to all_frames"
)

# ── Patch 6: add Remote to TAB_DEFS ──────────────────────
patch(
    '    TAB_DEFS = [\n        ("dashboard",  "Dashboard"),\n        ("playit",     "playit.gg"),\n        ("serverinfo", "Server Info"),\n        ("network",    "Network & IPs"),\n        ("multictrl",  "⊞ MULTI CTRL"),\n    ]',
    '    TAB_DEFS = [\n        ("dashboard",  "Dashboard"),\n        ("playit",     "playit.gg"),\n        ("serverinfo", "Server Info"),\n        ("network",    "Network & IPs"),\n        ("remote",     "\U0001f4f1 Remote"),\n        ("multictrl",  "\u229e MULTI CTRL"),\n    ]',
    "Add 📱 Remote to tab bar"
)

# ── Patch 7: add remote builder to lazy builders ──────────
patch(
    '            builders = {\n                "dashboard":  lambda: build_dashboard(dashboard_frame, is_fs),\n                "network":    lambda: build_network_tab(network_frame),\n                "serverinfo": lambda: build_server_info_tab(serverinfo_frame),\n                "playit":     lambda: build_playit_tab(playit_frame),\n                "multictrl":  lambda: build_multictrl_tab(multictrl_frame),\n            }',
    '            builders = {\n                "dashboard":  lambda: build_dashboard(dashboard_frame, is_fs),\n                "network":    lambda: build_network_tab(network_frame),\n                "serverinfo": lambda: build_server_info_tab(serverinfo_frame),\n                "playit":     lambda: build_playit_tab(playit_frame),\n                "remote":     lambda: _build_remote_tab(remote_frame),\n                "multictrl":  lambda: build_multictrl_tab(multictrl_frame),\n            }',
    "Register _build_remote_tab in lazy builders"
)

# ── Patch 8: inject _build_remote_tab function ────────────
REMOTE_FN = '''
# ── Remote Dashboard tab ──────────────────────────────────────────────────
def _build_remote_tab(parent):
    if not _REMOTE_AVAILABLE or _remote_mod is None:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text="remote_dashboard.py not found",
                     font=ctk.CTkFont(size=14), text_color=T["stop"]).pack(expand=True)
        ctk.CTkLabel(
            f,
            text="Place remote_dashboard.py in the same folder as launcher.pyw",
            font=ctk.CTkFont(size=12), text_color=T["muted"]
        ).pack()
        return
    _remote_mod.build_remote_tab(parent, {
        "ctk":             ctk,
        "T":               T,
        "app":             app,
        "log":             log,
        "show_toast":      show_toast,
        "perf":            perf,
        "online_players":  online_players,
        "server_proc":     lambda: server_proc,
        "send_server_cmd": send_server_cmd,
        "start_server":    start_server,
        "stop_server":     stop_server,
        "sync_git":        sync_git,
    })

'''

patch(
    "# ── UI ────────────────────────────────────────────────────\ndef build_ui():",
    REMOTE_FN + "# ── UI ────────────────────────────────────────────────────\ndef build_ui():",
    "Inject _build_remote_tab function"
)

# ── Write result ──────────────────────────────────────────
if errors:
    print("\n  [FAILED] Some patches could not be applied:")
    for e in errors:
        print(f"    • {e}")
    print("\n  The launcher was NOT modified. Check that your launcher.pyw")
    print("  matches the expected version (GamerMahir07 MC CTRL).\n")
    sys.exit(1)

with open(LAUNCHER, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n  Done! launcher.pyw patched successfully.")
print(f"  Backup: {BACKUP}")
print(f"\n  To use:")
print(f"    1. Run launcher.pyw as normal")
print(f"    2. Click the '📱 Remote' tab")
print(f"    3. Set a port and click '▶ Start Web Server'")
print(f"    4. Open the shown URL on your phone\n")
