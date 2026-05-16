"""
MC CTRL INTEGRATION PATCH
==========================
This file describes the EXACT changes to make to launcher.pyw.
All new function bodies are in launcher_additions.py — copy them into launcher.pyw.

STEP 1 — Replace the TAB_DEFS list (search for TAB_DEFS in build_ui)
----------------------------------------------------------------------
Replace this:
    TAB_DEFS = [
        ("dashboard",  "Dashboard"),
        ("playit",     "playit.gg"),
        ("serverinfo", "Server Info"),
        ("network",    "Network & IPs"),
        ("multictrl",  "⊞ MULTI CTRL"),
    ]

With this:
    TAB_DEFS = [
        ("dashboard",  "Dashboard"),
        ("playit",     "playit.gg"),
        ("serverinfo", "Server Info"),
        ("network",    "Network & IPs"),
        ("addons",     "Addons"),
        ("backups",    "Backups"),
        ("remote",     "Remote"),
        ("docker",     "Docker"),
        ("multictrl",  "⊞ MULTI CTRL"),
    ]


STEP 2 — Add new frame declarations (right after multictrl_frame = ... line)
------------------------------------------------------------------------------
Add:
    addons_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")
    backups_frame = ctk.CTkFrame(tab_content, fg_color="transparent")
    remote_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")
    docker_frame  = ctk.CTkFrame(tab_content, fg_color="transparent")


STEP 3 — Add new frames to all_frames dict
-------------------------------------------
In the all_frames dict, add:
        "addons":     addons_frame,
        "backups":    backups_frame,
        "remote":     remote_frame,
        "docker":     docker_frame,


STEP 4 — Add builders to the builders dict inside show_tab()
-------------------------------------------------------------
In the builders dict (inside show_tab), add:
        "addons":     lambda: build_addons_tab(addons_frame),
        "backups":    lambda: build_backups_tab(backups_frame),
        "remote":     lambda: build_remote_dashboard_tab(remote_frame),
        "docker":     lambda: build_docker_tab(docker_frame),


STEP 5 — Replace build_addons_tab (or add it)
----------------------------------------------
The old addon UI was inside build_settings_tab. The new standalone tab
function is build_addons_tab() in launcher_additions.py.
Copy build_addons_tab(), build_backups_tab(), build_remote_dashboard_tab(),
and build_docker_tab() from launcher_additions.py into launcher.pyw
(anywhere before build_ui, e.g. right after build_multictrl_tab).


STEP 6 — Remove addon section from Settings window (optional cleanup)
----------------------------------------------------------------------
In build_settings_tab(), you can remove the entire
    b = section("MC CTRL App Addons")
block since addons now have their own dedicated tab.
Keep or remove — it's duplicate UI, not a bug either way.


STEP 7 — Add to stop_server() cleanup (optional)
-------------------------------------------------
When the server stops, also stop the remote dashboard if running:
    if _remote_server_proc[0]:
        try: _remote_server_proc[0].terminate()
        except: pass
        _remote_server_proc[0] = None

Add this right before the final set_status("Stopped", ...) line.


THAT'S IT — no other changes needed.
Flask is auto-installed the first time Remote Dashboard is started.
Docker tab works without Docker installed (shows a status indicator).
"""
