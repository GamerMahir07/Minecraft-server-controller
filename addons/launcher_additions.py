# ═══════════════════════════════════════════════════════════════════════════════
# MC CTRL — ADDITIONS PATCH
# Drop these functions into launcher.pyw replacing the originals.
# New tabs: Addons (redesigned), Backups, Remote Dashboard, Docker
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. REDESIGNED ADDON TAB ───────────────────────────────────────────────────
# Left side: list of installed addons
# Right side: selected addon description + live settings/preview

BUILTIN_ADDON_META = {
    # name -> {description, settings_builder_fn (optional)}
}

def build_addons_tab(parent):
    """
    Left panel  — addon list (installed + available builtins)
    Right panel — selected addon details, description, settings
    """
    parent.columnconfigure(0, weight=0, minsize=260)
    parent.columnconfigure(1, weight=1)
    parent.rowconfigure(0, weight=1)

    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "addons")
    os.makedirs(addon_dir, exist_ok=True)

    # ── Left: addon list ──────────────────────────────────
    left = ctk.CTkFrame(parent, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=10)
    left.grid(row=0, column=0, sticky="nsew", padx=(12, 4), pady=12)
    left.columnconfigure(0, weight=1)
    left.rowconfigure(1, weight=1)

    lhdr = ctk.CTkFrame(left, fg_color="transparent")
    lhdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
    ctk.CTkLabel(lhdr, text="ADDONS", font=ctk.CTkFont(size=10),
                 text_color=T["muted"]).pack(side="left")

    def _inst_addon_btn():
        paths = _tk_fd.askopenfilenames(
            title="Select MC CTRL Addon (.py)",
            filetypes=[("Python", "*.py"), ("All", "*.*")])
        if not paths: return
        for p in paths:
            dest = os.path.join(addon_dir, os.path.basename(p))
            try: shutil.copy2(p, dest); _load_addon(dest)
            except Exception as ex: show_toast(f"Failed: {ex}", T["stop"])
        show_toast(f"{len(paths)} addon(s) installed!", T["start"])
        _refresh_list()

    ctk.CTkButton(lhdr, text="+ Install", width=64, height=22,
                  font=ctk.CTkFont(size=10), fg_color=T["sync"],
                  hover_color=T["sync"], text_color="#000",
                  command=_inst_addon_btn).pack(side="right")

    ctk.CTkFrame(left, height=1, fg_color=T["border"]).grid(
        row=0, column=0, sticky="ew", padx=0, pady=(36, 0))

    list_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
    list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    # ── Right: detail panel ───────────────────────────────
    right = ctk.CTkFrame(parent, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew", padx=(4, 12), pady=12)
    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)

    detail_frame = ctk.CTkFrame(right, fg_color=T["card"],
                                border_color=T["border"], border_width=1,
                                corner_radius=10)
    detail_frame.grid(row=0, column=0, sticky="nsew")

    # Placeholder when nothing selected
    _placeholder = ctk.CTkLabel(detail_frame,
                                 text="Select an addon to view details",
                                 font=ctk.CTkFont(size=13),
                                 text_color=T["muted"])
    _placeholder.place(relx=0.5, rely=0.5, anchor="center")

    selected = [None]   # currently selected name
    btn_refs  = {}      # name -> button widget

    def _show_detail(name):
        selected[0] = name
        for w in detail_frame.winfo_children():
            w.destroy()

        # Highlight selected in list
        for n, b in btn_refs.items():
            b.configure(fg_color=T["sync"] if n == name else "transparent",
                        text_color="#000" if n == name else T["text"])

        is_loaded = name in _loaded_addons
        mod = _loaded_addons.get(name)

        # ── Header ────────────────────────────────────────
        hdr = ctk.CTkFrame(detail_frame, fg_color=T["bg"], corner_radius=8)
        hdr.pack(fill="x", padx=14, pady=(14, 0))

        name_row = ctk.CTkFrame(hdr, fg_color="transparent")
        name_row.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(name_row, text=name,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=T["text"]).pack(side="left")

        st_color = T["start"] if is_loaded else T["muted"]
        ctk.CTkLabel(name_row,
                     text="● loaded" if is_loaded else "○ not loaded",
                     font=ctk.CTkFont(size=11),
                     text_color=st_color).pack(side="left", padx=10)

        # Action buttons
        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        def _reload():
            _load_addon(os.path.join(addon_dir, name + ".py"))
            _show_detail(name)
            show_toast(f"Reloaded {name}", T["sync"])

        def _remove():
            try:
                os.remove(os.path.join(addon_dir, name + ".py"))
                _loaded_addons.pop(name, None)
                show_toast(f"Removed {name}", T["stop"])
            except Exception as ex:
                show_toast(f"Error: {ex}", T["stop"])
            _refresh_list()
            for w in detail_frame.winfo_children(): w.destroy()
            _placeholder2 = ctk.CTkLabel(detail_frame,
                                          text="Select an addon to view details",
                                          font=ctk.CTkFont(size=13),
                                          text_color=T["muted"])
            _placeholder2.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(btn_row, text="Reload", width=80, height=26,
                      font=ctk.CTkFont(size=11), fg_color=T["sync"],
                      hover_color=T["sync"], text_color="#000",
                      command=_reload).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Open Folder", width=90, height=26,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: os.startfile(addon_dir)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Remove", width=72, height=26,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color=T["stop"],
                      text_color=T["stop"], hover_color=T["border"],
                      command=_remove).pack(side="left")

        ctk.CTkFrame(detail_frame, height=1, fg_color=T["border"]).pack(fill="x", padx=14, pady=(10, 0))

        # ── Description ───────────────────────────────────
        scroll_right = ctk.CTkScrollableFrame(detail_frame, fg_color="transparent")
        scroll_right.pack(fill="both", expand=True, padx=14, pady=8)

        # Try to get docstring or __addon_meta__ from the module
        desc = "(No description provided.)"
        author = ""
        version = ""
        if mod:
            if hasattr(mod, "__addon_meta__"):
                meta = mod.__addon_meta__
                desc    = meta.get("description", desc)
                author  = meta.get("author", "")
                version = meta.get("version", "")
            elif mod.__doc__:
                desc = mod.__doc__.strip()

        # Meta row
        meta_row = ctk.CTkFrame(scroll_right, fg_color="transparent")
        meta_row.pack(fill="x", pady=(0, 8))
        if version:
            ctk.CTkLabel(meta_row, text=f"v{version}",
                         font=ctk.CTkFont(size=10),
                         text_color=T["muted"],
                         fg_color=T["bg"], corner_radius=4).pack(side="left", padx=(0, 6))
        if author:
            ctk.CTkLabel(meta_row, text=f"by {author}",
                         font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left")

        ctk.CTkLabel(scroll_right, text="Description",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll_right, text=desc,
                     font=ctk.CTkFont(size=12),
                     text_color=T["muted"],
                     wraplength=480, justify="left").pack(anchor="w")

        ctk.CTkFrame(scroll_right, height=1, fg_color=T["border"]).pack(fill="x", pady=12)

        # ── Live settings / preview ────────────────────────
        ctk.CTkLabel(scroll_right, text="Settings & Preview",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["text"]).pack(anchor="w", pady=(0, 8))

        settings_area = ctk.CTkFrame(scroll_right, fg_color=T["bg"],
                                     border_color=T["border"], border_width=1,
                                     corner_radius=8)
        settings_area.pack(fill="x")

        # If the addon exposes a settings_ui(parent, ctx) function, call it
        if mod and hasattr(mod, "settings_ui"):
            ctx = {"app": app, "T": T, "log": log, "show_toast": show_toast,
                   "send_server_cmd": send_server_cmd, "load_settings": load_settings}
            try:
                mod.settings_ui(settings_area, ctx)
            except Exception as ex:
                ctk.CTkLabel(settings_area, text=f"Settings UI error: {ex}",
                             font=ctk.CTkFont(size=11),
                             text_color=T["stop"]).pack(padx=12, pady=8)
        else:
            ctk.CTkLabel(settings_area,
                         text="This addon has no configurable settings.\n"
                              "Add a settings_ui(parent, ctx) function to your addon to enable this.",
                         font=ctk.CTkFont(size=11),
                         text_color=T["muted"],
                         justify="left").pack(padx=12, pady=12)

        # ── Addon API hint ─────────────────────────────────
        ctk.CTkFrame(scroll_right, height=1, fg_color=T["border"]).pack(fill="x", pady=12)
        api_f = ctk.CTkFrame(scroll_right, fg_color=T["bg"],
                              border_color=T["border"], border_width=1, corner_radius=8)
        api_f.pack(fill="x")
        ctk.CTkLabel(api_f, text="Addon API",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=T["muted"]).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(api_f,
                     text=(
                         "def setup(ctx): ...           # called on load\n"
                         "def settings_ui(parent, ctx): # optional settings panel\n"
                         "__addon_meta__ = {            # optional metadata\n"
                         "    'description': '...',\n"
                         "    'author': '...',\n"
                         "    'version': '1.0',\n"
                         "}"
                     ),
                     font=ctk.CTkFont(size=10, family="Consolas"),
                     text_color=T["muted"],
                     justify="left").pack(anchor="w", padx=10, pady=(0, 10))

    def _refresh_list():
        for w in list_scroll.winfo_children(): w.destroy()
        btn_refs.clear()

        try:
            scripts = sorted([x for x in os.listdir(addon_dir) if x.endswith(".py")])
        except:
            scripts = []

        if not scripts:
            ctk.CTkLabel(list_scroll,
                         text="No addons installed.\nClick + Install to add one.",
                         font=ctk.CTkFont(size=11),
                         text_color=T["muted"],
                         justify="center").pack(pady=20)
            return

        for s in scripts:
            name = s.replace(".py", "")
            is_loaded = name in _loaded_addons

            row_frame = ctk.CTkFrame(list_scroll, fg_color="transparent",
                                     corner_radius=6)
            row_frame.pack(fill="x", pady=1)

            is_sel = (name == selected[0])
            btn = ctk.CTkButton(row_frame, text=name,
                                height=34, anchor="w",
                                font=ctk.CTkFont(size=12),
                                fg_color=T["sync"] if is_sel else "transparent",
                                text_color="#000" if is_sel else T["text"],
                                hover_color=T["border"],
                                border_spacing=0,
                                command=lambda n=name: _show_detail(n))
            btn.pack(fill="x", padx=4, pady=1)
            btn_refs[name] = btn

            # Status dot overlay (right side of button)
            dot_color = T["start"] if is_loaded else T["muted"]
            ctk.CTkLabel(row_frame, text="●", font=ctk.CTkFont(size=9),
                         text_color=dot_color,
                         fg_color="transparent").place(relx=1.0, rely=0.5,
                                                        anchor="e", x=-10)

        # Open folder link at bottom
        ctk.CTkFrame(list_scroll, height=1, fg_color=T["border"]).pack(fill="x", pady=(8, 4))
        ctk.CTkButton(list_scroll, text="Open addons/", height=26,
                      font=ctk.CTkFont(size=10), fg_color="transparent",
                      border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: os.startfile(addon_dir)).pack(fill="x", padx=4)

    _refresh_list()

    # Refresh button in header
    ctk.CTkButton(lhdr, text="↺", width=28, height=22,
                  font=ctk.CTkFont(size=12), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_refresh_list).pack(side="right", padx=(0, 4))


# ── 2. BACKUPS TAB ────────────────────────────────────────────────────────────

def build_backups_tab(parent):
    import zipfile, glob

    scroll = make_scroll_frame(parent, fg_color="transparent")

    def _card(title, subtitle=None):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8, 12))
        return body, h

    # ── Settings ──────────────────────────────────────────
    sb, sh = _card("Backup Settings")
    s = load_settings()

    backup_dir_var    = ctk.StringVar(value=s.get("backup_dir", ""))
    backup_keep_var   = ctk.StringVar(value=str(s.get("backup_keep", 10)))
    backup_auto_var   = ctk.BooleanVar(value=s.get("backup_auto", False))
    backup_mins_var   = ctk.StringVar(value=str(s.get("backup_interval_mins", 30)))
    _backup_timer     = [None]

    def _save_bs(*_):
        update_setting("backup_dir",           backup_dir_var.get())
        update_setting("backup_keep",          int(backup_keep_var.get() or 10))
        update_setting("backup_interval_mins", int(backup_mins_var.get() or 30))

    def _browse_backup_dir():
        import tkinter.filedialog as fd
        p = fd.askdirectory(title="Select Backup Destination Folder")
        if p: backup_dir_var.set(p); _save_bs()

    r0 = ctk.CTkFrame(sb, fg_color="transparent"); r0.pack(fill="x", pady=3)
    ctk.CTkLabel(r0, text="Backup destination", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkEntry(r0, textvariable=backup_dir_var, height=28,
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="Leave blank to use <server>/backups/"
                 ).pack(side="left", fill="x", expand=True, padx=(0, 6))
    ctk.CTkButton(r0, text="Browse", width=66, height=28, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_browse_backup_dir).pack(side="left")

    r1 = ctk.CTkFrame(sb, fg_color="transparent"); r1.pack(fill="x", pady=3)
    ctk.CTkLabel(r1, text="Keep last N backups", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ke = ctk.CTkEntry(r1, textvariable=backup_keep_var, width=60, height=28,
                      font=ctk.CTkFont(size=12, family="Consolas"),
                      fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
    ke.pack(side="left", padx=(0, 8))
    ke.bind("<FocusOut>", _save_bs); ke.bind("<Return>", _save_bs)

    r2 = ctk.CTkFrame(sb, fg_color="transparent"); r2.pack(fill="x", pady=3)
    ctk.CTkLabel(r2, text="Auto backup while running", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")

    def _toggle_auto_backup(v):
        update_setting("backup_auto", v)
        if v: _schedule_backup()
        else:
            if _backup_timer[0]:
                try: _backup_timer[0].cancel()
                except: pass

    ctk.CTkSwitch(r2, text="", variable=backup_auto_var,
                  command=lambda: _toggle_auto_backup(backup_auto_var.get()),
                  button_color=T["sync"], progress_color=T["sync"]).pack(side="left")

    r3 = ctk.CTkFrame(sb, fg_color="transparent"); r3.pack(fill="x", pady=3)
    ctk.CTkLabel(r3, text="Auto interval (minutes)", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    me = ctk.CTkEntry(r3, textvariable=backup_mins_var, width=60, height=28,
                      font=ctk.CTkFont(size=12, family="Consolas"),
                      fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
    me.pack(side="left")
    me.bind("<FocusOut>", _save_bs); me.bind("<Return>", _save_bs)

    # ── Manual backup ──────────────────────────────────────
    mb, mh = _card("Create Backup")
    backup_status = ctk.CTkLabel(mb, text="", font=ctk.CTkFont(size=11), text_color=T["muted"])
    backup_prog   = ctk.CTkProgressBar(mb, height=6); backup_prog.set(0)

    worlds_to_back = ctk.StringVar(value="world,world_nether,world_the_end")
    r4 = ctk.CTkFrame(mb, fg_color="transparent"); r4.pack(fill="x", pady=3)
    ctk.CTkLabel(r4, text="Folders to backup (comma-separated)",
                 font=ctk.CTkFont(size=12), text_color=T["text"],
                 width=280, anchor="w").pack(side="left")
    ctk.CTkEntry(r4, textvariable=worlds_to_back, height=28,
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"],
                 text_color=T["text"]).pack(side="left", fill="x", expand=True)

    def _get_backup_dest():
        custom = backup_dir_var.get().strip()
        if custom and os.path.isdir(custom): return custom
        path = load_settings().get("srv_path", SRV_PATH)
        dest = os.path.join(path, "backups")
        os.makedirs(dest, exist_ok=True)
        return dest

    def _prune_old(dest, keep):
        zips = sorted(
            [os.path.join(dest, f) for f in os.listdir(dest) if f.endswith(".zip")],
            key=os.path.getmtime)
        while len(zips) > keep:
            try: os.remove(zips.pop(0))
            except: pass

    def _do_backup(auto=False):
        import zipfile
        s2 = load_settings()
        path = s2.get("srv_path", SRV_PATH)
        dest = _get_backup_dest()
        folders = [f.strip() for f in worlds_to_back.get().split(",") if f.strip()]
        keep    = int(backup_keep_var.get() or 10)

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag  = "auto" if auto else "manual"
        zname = os.path.join(dest, f"backup_{tag}_{ts}.zip")

        def _work():
            try:
                app.after(0, lambda: backup_status.configure(
                    text="Creating backup...", text_color=T["sync"]))
                app.after(0, lambda: (backup_prog.set(0),
                                       backup_prog.pack(fill="x", pady=(6, 0))))
                total_files = sum(
                    sum(1 for _ in os.walk(os.path.join(path, f)))
                    for f in folders if os.path.isdir(os.path.join(path, f)))
                done = [0]
                with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED) as zf:
                    for folder in folders:
                        src = os.path.join(path, folder)
                        if not os.path.isdir(src): continue
                        for root, dirs, files in os.walk(src):
                            for file in files:
                                fp = os.path.join(root, file)
                                arcname = os.path.relpath(fp, path)
                                zf.write(fp, arcname)
                                done[0] += 1
                                if total_files:
                                    p = done[0] / total_files
                                    app.after(0, backup_prog.set, min(p, 1.0))
                size_mb = os.path.getsize(zname) / 1048576
                _prune_old(dest, keep)
                app.after(0, lambda: backup_status.configure(
                    text=f"Backup complete! {size_mb:.1f} MB — {zname}",
                    text_color=T["start"]))
                app.after(0, backup_prog.set, 1.0)
                app.after(0, show_toast, f"Backup done ({size_mb:.1f} MB)", T["start"])
                app.after(0, _refresh_backup_list)
                log(f"  Backup created: {os.path.basename(zname)} ({size_mb:.1f} MB)")
            except Exception as ex:
                app.after(0, lambda: backup_status.configure(
                    text=f"Backup failed: {ex}", text_color=T["stop"]))
                log(f"  Backup error: {ex}")

        threading.Thread(target=_work, daemon=True).start()

    def _schedule_backup():
        if _backup_timer[0]:
            try: _backup_timer[0].cancel()
            except: pass
        if not backup_auto_var.get(): return
        mins = int(backup_mins_var.get() or 30)
        def _fire():
            _do_backup(auto=True)
            _schedule_backup()
        _backup_timer[0] = threading.Timer(mins * 60, _fire)
        _backup_timer[0].daemon = True
        _backup_timer[0].start()

    backup_status.pack(anchor="w", pady=(6, 0))

    ctk.CTkButton(mb, text="Create Backup Now", height=34, corner_radius=8,
                  font=ctk.CTkFont(size=12, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=lambda: threading.Thread(
                      target=_do_backup, daemon=True).start()
                  ).pack(anchor="w", pady=(8, 0))

    # ── Backup list ────────────────────────────────────────
    lb, lh = _card("Saved Backups")
    backup_list_frame = ctk.CTkScrollableFrame(lb, fg_color=T["bg"],
                                               border_color=T["border"],
                                               border_width=1, corner_radius=8,
                                               height=220)
    backup_list_frame.pack(fill="x")

    def _refresh_backup_list():
        for w in backup_list_frame.winfo_children(): w.destroy()
        dest = _get_backup_dest()
        try:
            zips = sorted(
                [f for f in os.listdir(dest) if f.endswith(".zip")],
                key=lambda f: os.path.getmtime(os.path.join(dest, f)),
                reverse=True)
        except: zips = []

        if not zips:
            ctk.CTkLabel(backup_list_frame, text="No backups found.",
                         font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(padx=14, pady=10)
            return

        for z in zips:
            full = os.path.join(dest, z)
            size_mb = os.path.getsize(full) / 1048576
            mtime   = datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
            tag_color = T["sync"] if "manual" in z else T["muted"]

            row = ctk.CTkFrame(backup_list_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)

            ctk.CTkLabel(row, text=z, font=ctk.CTkFont(size=11, family="Consolas"),
                         text_color=T["text"]).pack(side="left")
            ctk.CTkLabel(row, text=f"{size_mb:.1f} MB",
                         font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=mtime,
                         font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

            def _open_folder(p=dest): os.startfile(p)
            def _delete_backup(p=full, n=z):
                try:
                    os.remove(p)
                    show_toast(f"Deleted {n}", T["stop"])
                    _refresh_backup_list()
                except Exception as ex:
                    show_toast(f"Error: {ex}", T["stop"])

            ctk.CTkButton(row, text="Delete", width=58, height=22,
                          font=ctk.CTkFont(size=10), fg_color="transparent",
                          border_width=1, border_color=T["stop"],
                          text_color=T["stop"], hover_color=T["border"],
                          command=_delete_backup).pack(side="right")
            ctk.CTkButton(row, text="Open", width=52, height=22,
                          font=ctk.CTkFont(size=10), fg_color="transparent",
                          border_width=1, border_color=T["border"],
                          text_color=T["muted"], hover_color=T["border"],
                          command=_open_folder).pack(side="right", padx=(0, 4))

    _refresh_backup_list()
    ctk.CTkButton(lh, text="Refresh", width=70, height=22,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_refresh_backup_list).pack(side="right")

    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()

    if backup_auto_var.get(): _schedule_backup()


# ── 3. REMOTE DASHBOARD TAB ───────────────────────────────────────────────────

_remote_server_proc = [None]   # Flask subprocess

def build_remote_dashboard_tab(parent):
    scroll = make_scroll_frame(parent, fg_color="transparent")

    def _card(title, subtitle=None):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8, 12))
        return body, h

    ab, _ = _card("What is this?")
    ctk.CTkLabel(ab, text=(
        "Starts a lightweight web server on your PC so you can control the Minecraft server\n"
        "from your phone, tablet, or another computer on the same network.\n\n"
        "Open  http://<your-local-ip>:<port>  in any browser — no app install needed.\n"
        "Features: start/stop server, live log, send commands, player list, TPS/RAM stats."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       wraplength=840, justify="left").pack(anchor="w")

    # ── Config ────────────────────────────────────────────
    cb, _ = _card("Configuration")
    s = load_settings()
    rd_port_var = ctk.StringVar(value=str(s.get("remote_port", 5000)))
    rd_pass_var = ctk.StringVar(value=s.get("remote_password", ""))

    def _save_rd(*_):
        update_setting("remote_port",     rd_port_var.get())
        update_setting("remote_password", rd_pass_var.get())

    r0 = ctk.CTkFrame(cb, fg_color="transparent"); r0.pack(fill="x", pady=3)
    ctk.CTkLabel(r0, text="Dashboard port", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    pe = ctk.CTkEntry(r0, textvariable=rd_port_var, width=80, height=28,
                      font=ctk.CTkFont(size=12, family="Consolas"),
                      fg_color=T["bg"], border_color=T["border"], text_color=T["text"])
    pe.pack(side="left")
    pe.bind("<FocusOut>", _save_rd); pe.bind("<Return>", _save_rd)

    r1 = ctk.CTkFrame(cb, fg_color="transparent"); r1.pack(fill="x", pady=3)
    ctk.CTkLabel(r1, text="Password (optional)", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    passentry = ctk.CTkEntry(r1, textvariable=rd_pass_var, width=200, height=28, show="•",
                              font=ctk.CTkFont(size=12, family="Consolas"),
                              fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                              placeholder_text="leave blank = no auth")
    passentry.pack(side="left", padx=(0, 8))
    def _toggle_pass_vis():
        passentry.configure(show="" if passentry.cget("show") == "•" else "•")
    ctk.CTkButton(r1, text="Show", width=52, height=28,
                  font=ctk.CTkFont(size=10), fg_color="transparent",
                  border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_toggle_pass_vis).pack(side="left")
    passentry.bind("<FocusOut>", _save_rd)

    ctk.CTkLabel(cb,
                 text="Keep the dashboard on your home network only — don't forward this port to the internet.",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", pady=(6, 0))

    # ── Control ───────────────────────────────────────────
    ctrl_b, ctrl_h = _card("Dashboard Control")
    rd_status = ctk.CTkLabel(ctrl_b, text="● Stopped",
                              font=ctk.CTkFont(size=13, weight="bold"),
                              text_color=T["stop"])
    rd_status.pack(side="left")
    rd_url_lbl = ctk.CTkLabel(ctrl_b, text="",
                               font=ctk.CTkFont(size=12, family="Consolas"),
                               text_color=T["sync"])
    rd_url_lbl.pack(side="left", padx=(14, 0))

    def _set_rd_status(txt, color):
        try: rd_status.configure(text=txt, text_color=color)
        except: pass
    def _set_rd_url(url):
        try: rd_url_lbl.configure(text=url)
        except: pass

    def _write_flask_server():
        """Write the Flask dashboard script to a temp file and return its path."""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "_mc_ctrl_remote.py")
        flask_code = r'''
import sys, json, threading, time, os, queue
from datetime import datetime

try:
    from flask import Flask, request, jsonify, render_template_string, session, redirect
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "--quiet"])
    from flask import Flask, request, jsonify, render_template_string, session, redirect

PORT     = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else ""
STATE_FILE = sys.argv[3] if len(sys.argv) > 3 else ""

app = Flask(__name__)
app.secret_key = os.urandom(24)

LOG_LINES = []
LOG_LOCK  = threading.Lock()

def read_state():
    try:
        if STATE_FILE and os.path.exists(STATE_FILE):
            return json.loads(open(STATE_FILE).read())
    except: pass
    return {}

HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MC CTRL Remote</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d0d0d; color: #e0e0e0; font-family: system-ui, sans-serif; padding: 12px; }
h1 { color: #22c55e; font-size: 20px; margin-bottom: 12px; }
.card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
button { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 13px; font-weight: bold; }
.btn-start { background: #22c55e; color: #000; }
.btn-stop  { background: #ef4444; color: #fff; }
.btn-send  { background: #60a5fa; color: #000; }
.btn-cmd   { background: transparent; border: 1px solid #2a2a2a; color: #888; font-size: 11px; padding: 5px 10px; }
input[type=text], input[type=password] {
  width: 100%; padding: 8px; background: #111; border: 1px solid #333;
  border-radius: 6px; color: #e0e0e0; font-size: 13px; margin-bottom: 8px;
}
.stat { display: inline-block; background: #111; border-radius: 6px; padding: 6px 12px; margin: 3px; font-size: 12px; }
.stat span { font-size: 18px; font-weight: bold; color: #22c55e; display: block; }
#log { background: #050505; border-radius: 6px; padding: 8px; height: 220px; overflow-y: auto;
       font-family: monospace; font-size: 11px; color: #aaa; white-space: pre-wrap; }
.dot-on { color: #22c55e; } .dot-off { color: #ef4444; }
</style>
</head>
<body>
<h1>⛏ MC CTRL Remote</h1>
<div class="card" id="status-card">
  <div class="row">
    <span id="status-dot" class="dot-off">●</span>
    <strong id="status-text">Loading...</strong>
  </div>
  <div class="row">
    <div class="stat">TPS<span id="s-tps">--</span></div>
    <div class="stat">Players<span id="s-players">--</span></div>
    <div class="stat">RAM<span id="s-ram">--</span></div>
    <div class="stat">CPU<span id="s-cpu">--</span></div>
    <div class="stat">Uptime<span id="s-uptime">--</span></div>
  </div>
  <div class="row">
    <button class="btn-start" onclick="action('start')">▶ Start</button>
    <button class="btn-stop"  onclick="action('stop')">■ Stop</button>
  </div>
</div>
<div class="card">
  <b style="font-size:12px;color:#555">COMMAND</b>
  <input type="text" id="cmd" placeholder="say Hello / time set day / etc" />
  <div class="row">
    <button class="btn-send" onclick="sendCmd()">Send</button>
    <button class="btn-cmd" onclick="sendCmdVal('list')">list</button>
    <button class="btn-cmd" onclick="sendCmdVal('tps')">tps</button>
    <button class="btn-cmd" onclick="sendCmdVal('save-all')">save-all</button>
    <button class="btn-cmd" onclick="sendCmdVal('time set day')">day</button>
    <button class="btn-cmd" onclick="sendCmdVal('weather clear')">clear weather</button>
  </div>
</div>
<div class="card">
  <b style="font-size:12px;color:#555">LIVE LOG</b>
  <div id="log"></div>
</div>
<script>
async function api(path, body) {
  const r = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? {"Content-Type":"application/json"} : {},
    body: body ? JSON.stringify(body) : undefined
  });
  return r.json();
}
async function action(a) {
  await api("/api/action", {action: a});
}
async function sendCmd() {
  const v = document.getElementById("cmd").value.trim();
  if (!v) return;
  await api("/api/cmd", {cmd: v});
  document.getElementById("cmd").value = "";
}
function sendCmdVal(v) {
  document.getElementById("cmd").value = v; sendCmd();
}
document.getElementById("cmd").addEventListener("keydown", e => { if(e.key==="Enter") sendCmd(); });
async function poll() {
  try {
    const d = await api("/api/state");
    const on = d.running;
    document.getElementById("status-dot").className = on ? "dot-on" : "dot-off";
    document.getElementById("status-text").textContent = on ? "Server Running" : "Server Stopped";
    document.getElementById("s-tps").textContent = d.tps || "--";
    document.getElementById("s-players").textContent = d.players || "0";
    document.getElementById("s-ram").textContent = d.ram_srv || "--";
    document.getElementById("s-cpu").textContent = d.cpu_srv || "--";
    document.getElementById("s-uptime").textContent = d.uptime || "--";
    const lg = document.getElementById("log");
    if (d.log && d.log.length) {
      d.log.forEach(l => { lg.textContent += l + "\n"; });
      lg.scrollTop = lg.scrollHeight;
    }
  } catch(e) {}
  setTimeout(poll, 2000);
}
poll();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/state")
def state():
    s = read_state()
    with LOG_LOCK:
        lines = list(LOG_LINES)
        LOG_LINES.clear()
    s["log"] = lines
    return jsonify(s)

@app.route("/api/action", methods=["POST"])
def do_action():
    data = request.get_json(force=True)
    act  = data.get("action","")
    s    = read_state()
    # Write action request to state file
    try:
        s["pending_action"] = act
        open(STATE_FILE, "w").write(json.dumps(s))
    except: pass
    return jsonify({"ok": True})

@app.route("/api/cmd", methods=["POST"])
def do_cmd():
    data = request.get_json(force=True)
    cmd  = data.get("cmd","")
    s    = read_state()
    try:
        s["pending_cmd"] = cmd
        open(STATE_FILE, "w").write(json.dumps(s))
    except: pass
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
'''
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(flask_code)
        return script_path

    # State file for bridge between Flask and main app
    _state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "_mc_ctrl_state.json")

    def _write_state():
        try:
            state = {
                "running":  server_proc is not None and server_proc.poll() is None,
                "tps":      perf.get("tps","--"),
                "players":  perf.get("players","0"),
                "ram_srv":  perf.get("ram_srv","--"),
                "cpu_srv":  perf.get("cpu_srv","--"),
                "uptime":   perf.get("uptime","--"),
            }
            # Check for pending actions from web dashboard
            try:
                existing = json.loads(open(_state_file).read())
                if existing.get("pending_action"):
                    act = existing.pop("pending_action")
                    if act == "start":
                        threading.Thread(target=start_server, daemon=True).start()
                    elif act == "stop":
                        threading.Thread(target=stop_server, daemon=True).start()
                if existing.get("pending_cmd"):
                    send_server_cmd(existing.pop("pending_cmd"))
            except: pass
            open(_state_file, "w").write(json.dumps(state))
        except: pass

    def _state_sync_loop():
        while _remote_server_proc[0] and _remote_server_proc[0].poll() is None:
            app.after(0, _write_state)
            time.sleep(2)

    def _start_remote():
        if _remote_server_proc[0] and _remote_server_proc[0].poll() is None:
            show_toast("Dashboard already running.", T["muted"]); return
        try:
            import importlib.util as _iu
            if _iu.find_spec("flask") is None:
                _set_rd_status("● Installing Flask...", T["handoff"])
                subprocess.run([sys.executable, "-m", "pip", "install", "flask", "--quiet"],
                               creationflags=CREATE_NO_WINDOW)
        except: pass

        script = _write_flask_server()
        port   = rd_port_var.get().strip() or "5000"
        pw     = rd_pass_var.get().strip()
        try:
            proc = subprocess.Popen(
                [sys.executable, script, port, pw, _state_file],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            _remote_server_proc[0] = proc
            import socket
            local_ip = "127.0.0.1"
            try:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s2.connect(("8.8.8.8", 80)); local_ip = s2.getsockname()[0]; s2.close()
            except: pass
            url = f"http://{local_ip}:{port}"
            _set_rd_status("● Running", T["start"])
            _set_rd_url(url)
            show_toast(f"Dashboard running at {url}", T["start"], 5000)
            log(f"-- Remote dashboard started: {url} --")
            threading.Thread(target=_state_sync_loop, daemon=True).start()
        except Exception as ex:
            show_toast(f"Failed: {ex}", T["stop"])
            _set_rd_status("● Error", T["stop"])

    def _stop_remote():
        if _remote_server_proc[0]:
            try: _remote_server_proc[0].terminate()
            except: pass
            _remote_server_proc[0] = None
        _set_rd_status("● Stopped", T["stop"])
        _set_rd_url("")
        log("-- Remote dashboard stopped --")

    def _copy_url():
        url = rd_url_lbl.cget("text")
        if url: app.clipboard_clear(); app.clipboard_append(url); show_toast(f"Copied: {url}", T["sync"])

    br = ctk.CTkFrame(ctrl_h, fg_color="transparent"); br.pack(side="right")
    ctk.CTkButton(br, text="▶ Start", width=74, height=26, font=ctk.CTkFont(size=11),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=_start_remote).pack(side="left", padx=(0, 4))
    ctk.CTkButton(br, text="■ Stop", width=74, height=26, font=ctk.CTkFont(size=11),
                  fg_color=T["stop"], hover_color=T["stop"], text_color="#fff",
                  command=_stop_remote).pack(side="left", padx=(0, 4))
    ctk.CTkButton(br, text="Copy URL", width=80, height=26, font=ctk.CTkFont(size=11),
                  fg_color=T["sync"], hover_color=T["sync"], text_color="#000",
                  command=_copy_url).pack(side="left")

    # ── Guide ──────────────────────────────────────────────
    gb, _ = _card("How to use from your phone")
    ctk.CTkLabel(gb, text=(
        "1. Start the Remote Dashboard above.\n"
        "2. Make sure your phone is on the same WiFi network as this PC.\n"
        "3. Open the URL shown above in your phone's browser.\n"
        "4. You can now start/stop the server, send commands, and watch the live log.\n\n"
        "To access from outside your home network, use a VPN (e.g. Tailscale) — "
        "do not expose port 5000 to the internet directly."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       wraplength=840, justify="left").pack(anchor="w")

    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()


# ── 4. DOCKER TAB ─────────────────────────────────────────────────────────────

def build_docker_tab(parent):
    scroll = make_scroll_frame(parent, fg_color="transparent")

    def _card(title, subtitle=None):
        f = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
        f.pack(fill="x", padx=20, pady=(10, 0))
        h = ctk.CTkFrame(f, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        if subtitle:
            ctk.CTkLabel(h, text=subtitle, font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(side="left", padx=8)
        ctk.CTkFrame(f, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
        body = ctk.CTkFrame(f, fg_color="transparent"); body.pack(fill="x", padx=14, pady=(8, 12))
        return body, h

    def _docker_available():
        try:
            r = subprocess.run("docker version", shell=True, capture_output=True,
                               text=True, creationflags=CREATE_NO_WINDOW, timeout=5)
            return r.returncode == 0
        except: return False

    ab, _ = _card("Docker Support")
    ctk.CTkLabel(ab, text=(
        "Run your Minecraft server inside a Docker container — portable, clean, easy to back up.\n"
        "No Java install needed on the host: it's bundled inside the container.\n\n"
        "  docker compose up  →  server starts instantly in a container\n"
        "  Persistent data    →  world files mount to your server folder\n"
        "  Resource limits    →  set RAM and CPU caps from this panel"
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       wraplength=840, justify="left").pack(anchor="w")

    # Docker status check
    docker_ok = _docker_available()
    dock_st_color = T["start"] if docker_ok else T["stop"]
    dock_st_text  = "● Docker available" if docker_ok else "● Docker not found"
    ctk.CTkLabel(ab, text=dock_st_text, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=dock_st_color).pack(anchor="w", pady=(8, 0))
    if not docker_ok:
        ctk.CTkLabel(ab, text="Install Docker Desktop from https://www.docker.com/products/docker-desktop/",
                     font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w")

    # ── Compose config ────────────────────────────────────
    cc, ch = _card("Docker Compose Config")
    s = load_settings()

    dc_image_var  = ctk.StringVar(value=s.get("docker_image",  "itzg/minecraft-server"))
    dc_port_var   = ctk.StringVar(value=s.get("docker_port",   "25565"))
    dc_ram_var    = ctk.StringVar(value=s.get("docker_ram",    "2G"))
    dc_type_var   = ctk.StringVar(value=s.get("docker_type",   "PAPER"))
    dc_ver_var    = ctk.StringVar(value=s.get("docker_version","LATEST"))
    dc_name_var   = ctk.StringVar(value=s.get("docker_name",   "mc-server"))

    def _save_dc(*_):
        for k, v in [("docker_image", dc_image_var), ("docker_port", dc_port_var),
                      ("docker_ram",  dc_ram_var),   ("docker_type", dc_type_var),
                      ("docker_version", dc_ver_var), ("docker_name", dc_name_var)]:
            update_setting(k, v.get())

    def row_entry(parent, label, var, width=160, placeholder=""):
        r = ctk.CTkFrame(parent, fg_color="transparent"); r.pack(fill="x", pady=3)
        ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=12),
                     text_color=T["text"], width=180, anchor="w").pack(side="left")
        e = ctk.CTkEntry(r, textvariable=var, width=width, height=28,
                         font=ctk.CTkFont(size=11, family="Consolas"),
                         fg_color=T["bg"], border_color=T["border"],
                         text_color=T["text"], placeholder_text=placeholder)
        e.pack(side="left")
        e.bind("<FocusOut>", _save_dc); e.bind("<Return>", _save_dc)

    row_entry(cc, "Container name",  dc_name_var,  placeholder="mc-server")
    row_entry(cc, "Docker image",    dc_image_var, width=280, placeholder="itzg/minecraft-server")
    row_entry(cc, "Port",            dc_port_var,  placeholder="25565")
    row_entry(cc, "RAM limit",       dc_ram_var,   placeholder="2G")

    r_type = ctk.CTkFrame(cc, fg_color="transparent"); r_type.pack(fill="x", pady=3)
    ctk.CTkLabel(r_type, text="Server type", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=180, anchor="w").pack(side="left")
    ctk.CTkOptionMenu(r_type,
                      values=["PAPER","PURPUR","VANILLA","FABRIC","FORGE","SPIGOT","BUKKIT"],
                      variable=dc_type_var, command=lambda _: _save_dc(),
                      font=ctk.CTkFont(size=12), width=140, height=28,
                      fg_color=T["bg"], button_color=T["border"],
                      button_hover_color=T["muted"], text_color=T["text"],
                      dropdown_fg_color=T["card"], dropdown_text_color=T["text"],
                      dropdown_hover_color=T["border"]).pack(side="left", padx=(0, 12))
    ctk.CTkLabel(r_type, text="MC version", font=ctk.CTkFont(size=12),
                 text_color=T["text"], width=90, anchor="w").pack(side="left")
    ctk.CTkEntry(r_type, textvariable=dc_ver_var, width=100, height=28,
                 font=ctk.CTkFont(size=11, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"],
                 placeholder_text="LATEST").pack(side="left")

    def _gen_compose():
        path = load_settings().get("srv_path", SRV_PATH)
        yaml = f"""version: "3.8"
services:
  {dc_name_var.get()}:
    image: {dc_image_var.get()}
    container_name: {dc_name_var.get()}
    environment:
      EULA: "TRUE"
      TYPE: "{dc_type_var.get()}"
      VERSION: "{dc_ver_var.get()}"
      MEMORY: "{dc_ram_var.get()}"
      USE_AIKAR_FLAGS: "true"
    ports:
      - "{dc_port_var.get()}:{dc_port_var.get()}"
    volumes:
      - ./data:/data
    restart: unless-stopped
    stdin_open: true
    tty: true
"""
        dest = os.path.join(path, "docker-compose.yml")
        try:
            with open(dest, "w") as f: f.write(yaml)
            show_toast("docker-compose.yml written!", T["start"])
            log(f"  docker-compose.yml written to {dest}")
            preview_box.configure(state="normal")
            preview_box.delete("1.0", "end")
            preview_box.insert("end", yaml)
            preview_box.configure(state="disabled")
        except Exception as ex:
            show_toast(f"Error: {ex}", T["stop"])

    ctk.CTkButton(ch, text="Generate compose file", height=26, width=160,
                  font=ctk.CTkFont(size=11), fg_color=T["start"],
                  hover_color=T["start"], text_color="#000",
                  command=_gen_compose).pack(side="right")

    # Compose file preview
    pb, ph = _card("docker-compose.yml Preview")
    preview_box = ctk.CTkTextbox(pb, font=ctk.CTkFont(size=11, family="Consolas"),
                                  height=180, fg_color=T["bg"], text_color=T["text"],
                                  state="disabled")
    preview_box.pack(fill="x")
    path = load_settings().get("srv_path", SRV_PATH)
    compose_path = os.path.join(path, "docker-compose.yml")
    if os.path.exists(compose_path):
        try:
            preview_box.configure(state="normal")
            preview_box.insert("end", open(compose_path).read())
            preview_box.configure(state="disabled")
        except: pass

    # ── Container control ──────────────────────────────────
    ctrl_b, ctrl_h = _card("Container Control")
    dc_status = ctk.CTkLabel(ctrl_b, text="● Unknown",
                              font=ctk.CTkFont(size=13, weight="bold"),
                              text_color=T["muted"])
    dc_status.pack(side="left")

    dc_log_box = ctk.CTkTextbox(ctrl_b, font=ctk.CTkFont(size=10, family="Consolas"),
                                 height=120, fg_color=T["bg"], text_color=T["text"],
                                 state="disabled")

    def _dc_log(msg):
        try:
            dc_log_box.configure(state="normal")
            dc_log_box.insert("end", msg + "\n")
            dc_log_box.configure(state="disabled")
            dc_log_box.see("end")
        except: pass

    def _dc_status():
        name = dc_name_var.get().strip() or "mc-server"
        try:
            r = subprocess.run(f"docker inspect --format={{{{.State.Status}}}} {name}",
                               shell=True, capture_output=True, text=True,
                               creationflags=CREATE_NO_WINDOW, timeout=5)
            st = r.stdout.strip()
            if st == "running":
                dc_status.configure(text="● Running", text_color=T["start"])
            elif st:
                dc_status.configure(text=f"● {st.capitalize()}", text_color=T["muted"])
            else:
                dc_status.configure(text="● Not created", text_color=T["stop"])
        except:
            dc_status.configure(text="● Docker unavailable", text_color=T["stop"])

    def _run_dc(cmd_str, label):
        path = load_settings().get("srv_path", SRV_PATH)
        def _work():
            app.after(0, _dc_log, f"$ {cmd_str}")
            try:
                proc = subprocess.Popen(cmd_str, shell=True, cwd=path,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, creationflags=CREATE_NO_WINDOW)
                for line in proc.stdout:
                    app.after(0, _dc_log, line.rstrip())
                proc.wait()
                app.after(0, _dc_status)
                app.after(0, show_toast, f"{label} done", T["start"])
            except Exception as ex:
                app.after(0, _dc_log, f"Error: {ex}")
        threading.Thread(target=_work, daemon=True).start()

    name = dc_name_var.get().strip() or "mc-server"
    br = ctk.CTkFrame(ctrl_h, fg_color="transparent"); br.pack(side="right")
    for label, cmd in [
        ("▶ Up",      "docker compose up -d"),
        ("■ Down",    "docker compose down"),
        ("↺ Restart", f"docker restart {name}"),
        ("Logs",      f"docker logs --tail=50 {name}"),
        ("Status",    None),
    ]:
        if label == "Status":
            ctk.CTkButton(br, text="Refresh", width=70, height=26,
                          font=ctk.CTkFont(size=11), fg_color="transparent",
                          border_width=1, border_color=T["border"],
                          text_color=T["muted"], hover_color=T["border"],
                          command=_dc_status).pack(side="left", padx=(0, 4))
        else:
            fc = T["start"] if "Up" in label else (T["stop"] if "Down" in label else T["sync"])
            ctk.CTkButton(br, text=label, width=74, height=26, font=ctk.CTkFont(size=11),
                          fg_color=fc, hover_color=fc,
                          text_color="#000" if fc != T["stop"] else "#fff",
                          command=lambda c=cmd, l=label: _run_dc(c, l)
                          ).pack(side="left", padx=(0, 4))

    dc_log_box.pack(fill="x", pady=(10, 0))
    _dc_status()

    ctk.CTkFrame(scroll, height=12, fg_color="transparent").pack()
