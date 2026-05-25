"""
mc_modpack.py — One-click Modpack Installer tab for MC CTRL
Powered by the Modrinth API (https://docs.modrinth.com)

Loaded dynamically by launcher.pyw — do NOT run standalone.
Entry point: build_modpack_tab(parent, T, show_toast, load_settings, DEFAULT_SRV)
"""

import os, sys, json, threading, urllib.request, urllib.parse, urllib.error, zipfile, shutil
import tkinter as tk
import customtkinter as ctk
from datetime import datetime

# ── Modrinth API ──────────────────────────────────────────
_API      = "https://api.modrinth.com/v2"
_HEADERS  = {"User-Agent": "MC-CTRL-Launcher/2.0 (github.com/GamerMahir07)"}
_FACETS_MOD  = '[["project_type:mod"]]'
_FACETS_PACK = '[["project_type:modpack"]]'
_FACETS_PLUG = '[["project_type:plugin"]]'

def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def _search(query, facets, limit=20, offset=0):
    q = urllib.parse.quote(query)
    url = f"{_API}/search?query={q}&facets={urllib.parse.quote(facets)}&limit={limit}&offset={offset}&index=relevance"
    return _get(url)

def _project(slug_or_id):
    return _get(f"{_API}/project/{slug_or_id}")

def _versions(project_id, game_version=None, loader=None):
    url = f"{_API}/project/{project_id}/version"
    params = []
    if game_version: params.append(f"game_versions=%5B%22{game_version}%22%5D")
    if loader:       params.append(f"loaders=%5B%22{loader}%22%5D")
    if params:       url += "?" + "&".join(params)
    return _get(url)

def _dl_file(url, dest_path, progress_cb=None):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length", 0))
        done  = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk: break
                f.write(chunk); done += len(chunk)
                if progress_cb and total: progress_cb(done / total)

# ══════════════════════════════════════════════════════════
# TAB BUILDER
# ══════════════════════════════════════════════════════════
def build_modpack_tab(parent, T, show_toast, load_settings, DEFAULT_SRV):
    """Build the full Modpacks / Mods / Plugins installer tab."""

    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)

    # ── Root layout: left list | right detail ─────────────
    root = ctk.CTkFrame(parent, fg_color="transparent")
    root.grid(row=0, column=0, sticky="nsew")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=0)  # left sidebar
    root.columnconfigure(1, weight=1)  # right content

    # ════════════════════════════════════════════════════
    # LEFT SIDEBAR
    # ════════════════════════════════════════════════════
    sidebar = ctk.CTkFrame(root, fg_color=T["card"], border_color=T["border"],
                            border_width=1, corner_radius=0, width=300)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.rowconfigure(2, weight=1)
    sidebar.columnconfigure(0, weight=1)

    # Header
    shdr = ctk.CTkFrame(sidebar, fg_color=T["bg"], corner_radius=0)
    shdr.grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(shdr, text="📦  Modrinth", font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=12, pady=9)

    # Type filter tabs
    type_bar = ctk.CTkFrame(sidebar, fg_color=T["bg"], corner_radius=0)
    type_bar.grid(row=1, column=0, sticky="ew")
    ctk.CTkFrame(type_bar, height=1, fg_color=T["border"]).pack(fill="x")
    type_btns = {}
    type_var   = [_FACETS_PACK]  # default: modpacks

    def _set_type(facets, key):
        type_var[0] = facets
        for k, b in type_btns.items():
            b.configure(fg_color=T["sync"] if k==key else "transparent",
                        text_color="#000" if k==key else T["muted"])
        _do_search()

    tb_row = ctk.CTkFrame(type_bar, fg_color="transparent"); tb_row.pack(fill="x", padx=6, pady=5)
    for key, label, facets in [
        ("packs",   "Modpacks", _FACETS_PACK),
        ("mods",    "Mods",     _FACETS_MOD),
        ("plugins", "Plugins",  _FACETS_PLUG),
    ]:
        b = ctk.CTkButton(tb_row, text=label, height=26, width=80,
                          font=ctk.CTkFont(size=11),
                          fg_color=T["sync"] if key=="packs" else "transparent",
                          text_color="#000" if key=="packs" else T["muted"],
                          hover_color=T["border"], corner_radius=6,
                          command=lambda f=facets, k=key: _set_type(f, k))
        b.pack(side="left", padx=2); type_btns[key] = b

    # Search bar
    search_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    search_frame.grid(row=2, column=0, sticky="nsew")
    search_frame.rowconfigure(1, weight=1)
    search_frame.columnconfigure(0, weight=1)

    sq_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
    sq_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
    sq_frame.columnconfigure(0, weight=1)

    query_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(sq_frame, textvariable=query_var, height=28,
                                 font=ctk.CTkFont(size=12),
                                 fg_color=T["bg"], border_color=T["border"],
                                 text_color=T["text"],
                                 placeholder_text="Search Modrinth…")
    search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    search_btn = ctk.CTkButton(sq_frame, text="🔍", width=32, height=28,
                                font=ctk.CTkFont(size=12),
                                fg_color=T["sync"], hover_color=T["sync"],
                                text_color="#000", command=lambda: _do_search())
    search_btn.grid(row=0, column=1)
    search_entry.bind("<Return>", lambda e: _do_search())

    result_lbl = ctk.CTkLabel(sq_frame, text="", font=ctk.CTkFont(size=9),
                               text_color=T["muted"])
    result_lbl.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

    # Results list
    results_scroll = ctk.CTkScrollableFrame(search_frame, fg_color="transparent")
    results_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
    results_scroll.columnconfigure(0, weight=1)

    # Pagination footer
    page_footer = ctk.CTkFrame(search_frame, fg_color=T["bg"], corner_radius=0)
    page_footer.grid(row=2, column=0, sticky="ew")
    ctk.CTkFrame(page_footer, height=1, fg_color=T["border"]).pack(fill="x")
    pg_row = ctk.CTkFrame(page_footer, fg_color="transparent"); pg_row.pack(fill="x", padx=8, pady=5)
    pg_lbl  = ctk.CTkLabel(pg_row, text="", font=ctk.CTkFont(size=10), text_color=T["muted"])
    pg_lbl.pack(side="left")
    _page   = [0]
    _total  = [0]
    PER_PAGE = 20

    def _prev_page():
        if _page[0] > 0: _page[0] -= 1; _do_search(paginate=True)
    def _next_page():
        if (_page[0]+1)*PER_PAGE < _total[0]: _page[0] += 1; _do_search(paginate=True)

    ctk.CTkButton(pg_row, text="◀", width=32, height=24, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_prev_page).pack(side="right", padx=(2, 0))
    ctk.CTkButton(pg_row, text="▶", width=32, height=24, font=ctk.CTkFont(size=11),
                  fg_color="transparent", border_width=1, border_color=T["border"],
                  text_color=T["muted"], hover_color=T["border"],
                  command=_next_page).pack(side="right", padx=(0, 2))

    # ════════════════════════════════════════════════════
    # RIGHT DETAIL PANE
    # ════════════════════════════════════════════════════
    detail_frame = ctk.CTkFrame(root, fg_color="transparent")
    detail_frame.grid(row=0, column=1, sticky="nsew")
    detail_frame.rowconfigure(0, weight=1)
    detail_frame.columnconfigure(0, weight=1)

    _sel_project = [None]   # currently selected project dict
    _result_btns = {}       # slug -> button widget

    # ── Empty / welcome state ─────────────────────────────
    def _show_welcome():
        for w in detail_frame.winfo_children(): w.destroy()
        wrap = ctk.CTkFrame(detail_frame, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.rowconfigure(0, weight=1); wrap.columnconfigure(0, weight=1)
        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.place(relx=0.5, rely=0.38, anchor="center")
        ctk.CTkLabel(inner, text="📦", font=ctk.CTkFont(size=52)).pack()
        ctk.CTkLabel(inner, text="Modrinth Installer",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=T["text"]).pack(pady=(8, 4))
        ctk.CTkLabel(inner, text=(
            "Search for modpacks, mods, or plugins on the left.\n"
            "Select a result to view details and install."
        ), font=ctk.CTkFont(size=12), text_color=T["muted"], justify="center").pack()
        ctk.CTkLabel(inner, text="Powered by Modrinth API  ·  modrinth.com",
                     font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(pady=(12, 0))

    # ── Detail view ───────────────────────────────────────
    def _show_detail(project):
        for w in detail_frame.winfo_children(): w.destroy()
        _sel_project[0] = project

        scroll = ctk.CTkScrollableFrame(detail_frame, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        scroll.columnconfigure(0, weight=1)

        slug     = project.get("slug","")
        title    = project.get("title","Unknown")
        desc     = project.get("description","")
        body     = project.get("body","")
        cats     = project.get("categories",[])
        loaders  = project.get("loaders",[])
        game_vs  = project.get("game_versions",[])
        dls      = project.get("downloads", 0)
        follows  = project.get("followers", 0)
        lic      = project.get("license",{}).get("id","?")
        updated  = project.get("updated","")[:10]
        ptype    = project.get("project_type","modpack")
        icon_url = project.get("icon_url","")
        source   = project.get("source_url","")
        issues   = project.get("issues_url","")

        # Header card
        hcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["sync"],
                              border_width=2, corner_radius=12)
        hcard.pack(fill="x", pady=(0, 8))

        hinner = ctk.CTkFrame(hcard, fg_color="transparent")
        hinner.pack(fill="x", padx=16, pady=14)

        # Title row
        tr = ctk.CTkFrame(hinner, fg_color="transparent"); tr.pack(fill="x")
        ctk.CTkLabel(tr, text=title, font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        type_colors = {"modpack": T["sync"], "mod": T["start"], "plugin": T["hand"]}
        tc = type_colors.get(ptype, T["muted"])
        ctk.CTkLabel(tr, text=ptype.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=tc, fg_color=T["bg"],
                     corner_radius=5, width=60, height=20).pack(side="left", padx=8)

        # Description
        ctk.CTkLabel(hinner, text=desc, font=ctk.CTkFont(size=12),
                     text_color=T["muted"], wraplength=620,
                     justify="left").pack(anchor="w", pady=(4, 0))

        # Stats row
        stats_row = ctk.CTkFrame(hinner, fg_color="transparent"); stats_row.pack(anchor="w", pady=(8, 0))
        for label, val in [("⬇ Downloads", f"{dls:,}"), ("♡ Followers", f"{follows:,}"),
                            ("License", lic), ("Updated", updated)]:
            chip = ctk.CTkFrame(stats_row, fg_color=T["bg"], border_color=T["border"],
                                 border_width=1, corner_radius=6)
            chip.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(chip, text=f"{label}: {val}", font=ctk.CTkFont(size=10),
                         text_color=T["muted"]).pack(padx=8, pady=4)

        # Game versions / loaders
        if game_vs or loaders:
            meta_row = ctk.CTkFrame(hinner, fg_color="transparent"); meta_row.pack(anchor="w", pady=(5, 0))
            if game_vs:
                recent = ", ".join(sorted(game_vs, reverse=True)[:6])
                ctk.CTkLabel(meta_row, text=f"MC: {recent}", font=ctk.CTkFont(size=10),
                             text_color=T["muted"]).pack(side="left", padx=(0, 10))
            if loaders:
                ctk.CTkLabel(meta_row, text=f"Loaders: {', '.join(loaders)}",
                             font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

        # Categories
        if cats:
            cat_row = ctk.CTkFrame(hinner, fg_color="transparent"); cat_row.pack(anchor="w", pady=(4, 0))
            for c in cats[:8]:
                ctk.CTkLabel(cat_row, text=c, font=ctk.CTkFont(size=9),
                             fg_color=T["border"], text_color=T["muted"],
                             corner_radius=4, width=60, height=18).pack(side="left", padx=(0, 4))

        # Install card
        icard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                              border_width=1, corner_radius=12)
        icard.pack(fill="x", pady=(0, 8))
        ih = ctk.CTkFrame(icard, fg_color="transparent"); ih.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(ih, text="Install", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkFrame(icard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)

        ib = ctk.CTkFrame(icard, fg_color="transparent")
        ib.pack(fill="x", padx=16, pady=(10, 14))

        s = load_settings()
        srv_path = ctk.StringVar(value=s.get("srv_path", DEFAULT_SRV))
        mc_ver   = ctk.StringVar(value="")
        loader_v = ctk.StringVar(value="")

        r0 = ctk.CTkFrame(ib, fg_color="transparent"); r0.pack(fill="x", pady=3)
        ctk.CTkLabel(r0, text="Install to folder", font=ctk.CTkFont(size=12),
                     text_color=T["text"], width=140, anchor="w").pack(side="left")
        ctk.CTkEntry(r0, textvariable=srv_path, height=26,
                     font=ctk.CTkFont(size=11, family="Consolas"),
                     fg_color=T["bg"], border_color=T["border"],
                     text_color=T["text"]).pack(side="left", fill="x", expand=True, padx=(0, 6))
        import tkinter.filedialog as _fd
        ctk.CTkButton(r0, text="Browse", width=64, height=26, font=ctk.CTkFont(size=11),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: srv_path.set(_fd.askdirectory(title="Install destination") or srv_path.get())
                      ).pack(side="left")

        # Version selector — loaded async
        r1 = ctk.CTkFrame(ib, fg_color="transparent"); r1.pack(fill="x", pady=3)
        ctk.CTkLabel(r1, text="MC version", font=ctk.CTkFont(size=12),
                     text_color=T["text"], width=140, anchor="w").pack(side="left")
        ver_menu = ctk.CTkOptionMenu(r1, values=["Loading…"], variable=mc_ver,
                                      font=ctk.CTkFont(size=11), width=120, height=26,
                                      fg_color=T["bg"], button_color=T["border"],
                                      button_hover_color=T["muted"], text_color=T["text"],
                                      dropdown_fg_color=T["card"],
                                      dropdown_text_color=T["text"],
                                      dropdown_hover_color=T["border"])
        ver_menu.pack(side="left", padx=(0, 8))

        if loaders:
            ctk.CTkLabel(r1, text="Loader", font=ctk.CTkFont(size=12),
                         text_color=T["text"], width=60, anchor="w").pack(side="left")
            ctk.CTkOptionMenu(r1, values=loaders, variable=loader_v,
                               font=ctk.CTkFont(size=11), width=110, height=26,
                               fg_color=T["bg"], button_color=T["border"],
                               button_hover_color=T["muted"], text_color=T["text"],
                               dropdown_fg_color=T["card"],
                               dropdown_text_color=T["text"],
                               dropdown_hover_color=T["border"]).pack(side="left")
            if loaders: loader_v.set(loaders[0])

        # Populate game versions async
        def _load_versions():
            try:
                vs = sorted(set(game_vs), reverse=True) if game_vs else []
                if vs:
                    parent_app = scroll.winfo_toplevel()
                    parent_app.after(0, lambda: (ver_menu.configure(values=vs), mc_ver.set(vs[0])))
            except: pass
        threading.Thread(target=_load_versions, daemon=True).start()

        # Progress / status
        inst_st  = ctk.CTkLabel(ib, text="", font=ctk.CTkFont(size=11), text_color=T["muted"])
        inst_st.pack(anchor="w", pady=(4, 0))
        inst_pg  = ctk.CTkProgressBar(ib, height=5); inst_pg.set(0)

        def _set_st(msg, color=None):
            try: inst_st.configure(text=msg, text_color=color or T["muted"])
            except: pass

        def _install_project():
            dest  = srv_path.get().strip()
            ver   = mc_ver.get()
            ldr   = loader_v.get() if loaders else None

            if not dest or not os.path.isdir(dest):
                show_toast("Set a valid install folder!", T["stop"]); return

            def _work():
                try:
                    _set_st("Fetching version list…", T["sync"])
                    app_root = scroll.winfo_toplevel()
                    app_root.after(0, lambda: (inst_pg.set(0), inst_pg.pack(fill="x", pady=(4, 0))))

                    versions = _versions(project.get("id",""), game_version=ver if ver not in ("Loading…","") else None,
                                          loader=ldr if ldr and ldr not in ("","Loading…") else None)
                    if not versions:
                        _set_st("No compatible versions found.", T["stop"]); return

                    # Pick best version (first = latest compatible)
                    best = versions[0]
                    files = best.get("files", [])
                    if not files:
                        _set_st("No files in this version.", T["stop"]); return

                    # Prefer the primary file
                    primary = next((f for f in files if f.get("primary")), files[0])
                    dl_url  = primary["url"]
                    fname   = primary["filename"]

                    # Where to put it
                    if ptype == "modpack":
                        # Modpacks: download .mrpack then extract/install
                        tmp = os.path.join(dest, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        _dl_file(dl_url, tmp, lambda p: app_root.after(0, inst_pg.set, p))
                        _install_mrpack(tmp, dest, _set_st, app_root, inst_pg, show_toast, T)
                    elif ptype == "mod":
                        # Mods: copy .jar to /mods
                        mods_dir = os.path.join(dest, "mods")
                        os.makedirs(mods_dir, exist_ok=True)
                        out = os.path.join(mods_dir, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        _dl_file(dl_url, out, lambda p: app_root.after(0, inst_pg.set, p))
                        app_root.after(0, inst_pg.set, 1.0)
                        _set_st(f"Installed to mods/{fname}", T["start"])
                        show_toast(f"Mod installed: {fname}", T["start"])
                    elif ptype == "plugin":
                        # Plugins: copy .jar to /plugins
                        plug_dir = os.path.join(dest, "plugins")
                        os.makedirs(plug_dir, exist_ok=True)
                        out = os.path.join(plug_dir, fname)
                        _set_st(f"Downloading {fname}…", T["sync"])
                        _dl_file(dl_url, out, lambda p: app_root.after(0, inst_pg.set, p))
                        app_root.after(0, inst_pg.set, 1.0)
                        _set_st(f"Installed to plugins/{fname}", T["start"])
                        show_toast(f"Plugin installed: {fname}", T["start"])
                except Exception as ex:
                    _set_st(f"Failed: {ex}", T["stop"])
                    show_toast(f"Install failed: {ex}", T["stop"])

            threading.Thread(target=_work, daemon=True).start()

        btn_row = ctk.CTkFrame(ib, fg_color="transparent"); btn_row.pack(anchor="w", pady=(8, 0))
        ctk.CTkButton(btn_row, text=f"⬇  Install {ptype.capitalize()}", height=34,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T["start"], hover_color=T["start"], text_color="#000",
                      command=_install_project).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="🌐 View on Modrinth", height=34,
                      font=ctk.CTkFont(size=12),
                      fg_color="transparent", border_width=1, border_color=T["border"],
                      text_color=T["muted"], hover_color=T["border"],
                      command=lambda: _open_url(f"https://modrinth.com/{ptype}/{slug}")
                      ).pack(side="left")

        # Body / description card
        if body:
            bcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                                  border_width=1, corner_radius=12)
            bcard.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(bcard, text="Description", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=T["muted"]).pack(anchor="w", padx=16, pady=(10, 4))
            ctk.CTkFrame(bcard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)
            # Strip markdown roughly
            plain = _strip_md(body)[:1200]
            ctk.CTkLabel(bcard, text=plain, font=ctk.CTkFont(size=11),
                         text_color=T["text"], justify="left",
                         wraplength=620).pack(anchor="w", padx=16, pady=(8, 14))

        # Version list card
        vcard = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                              border_width=1, corner_radius=12)
        vcard.pack(fill="x", pady=(0, 8))
        vh = ctk.CTkFrame(vcard, fg_color="transparent"); vh.pack(fill="x", padx=16, pady=(10, 4))
        ctk.CTkLabel(vh, text="Available Versions", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=T["muted"]).pack(side="left")
        ctk.CTkFrame(vcard, height=1, fg_color=T["border"]).pack(fill="x", padx=16)
        vlist = ctk.CTkScrollableFrame(vcard, fg_color="transparent", height=160)
        vlist.pack(fill="x", padx=16, pady=(6, 12))
        vlist_lbl = ctk.CTkLabel(vlist, text="Loading versions…",
                                  font=ctk.CTkFont(size=11), text_color=T["muted"])
        vlist_lbl.pack(pady=8)

        def _populate_vlist():
            try:
                vdata = _versions(project.get("id",""))[:30]
                def _draw():
                    vlist_lbl.destroy()
                    for v in vdata:
                        vr = ctk.CTkFrame(vlist, fg_color="transparent"); vr.pack(fill="x", pady=2)
                        vname = v.get("name","?")[:50]; vnum = v.get("version_number","?")
                        vgvs  = ", ".join(v.get("game_versions",[])[:3])
                        vlds  = ", ".join(v.get("loaders",[]))
                        ctk.CTkLabel(vr, text=vname, font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color=T["text"]).pack(side="left")
                        ctk.CTkLabel(vr, text=f"  {vnum}  |  MC: {vgvs}  |  {vlds}",
                                     font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left", padx=4)
                        sz = sum(f.get("size",0) for f in v.get("files",[]))
                        ctk.CTkLabel(vr, text=f"{sz/1048576:.1f} MB",
                                     font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="right", padx=(0, 4))
                scroll.winfo_toplevel().after(0, _draw)
            except Exception as ex:
                scroll.winfo_toplevel().after(0, lambda: vlist_lbl.configure(text=f"Error: {ex}", text_color=T["stop"]))
        threading.Thread(target=_populate_vlist, daemon=True).start()

    # ── Result card renderer ──────────────────────────────
    def _make_result_card(proj):
        slug  = proj.get("slug","")
        title = proj.get("title","?")
        desc  = (proj.get("description","") or "")[:80]
        if len(proj.get("description","")) > 80: desc += "…"
        dls   = proj.get("downloads", 0)
        cats  = proj.get("categories",[])[:3]
        pvs   = sorted(proj.get("versions",[]), reverse=True)[:3]
        ptype = proj.get("project_type","modpack")
        color_map = {"modpack": T["sync"], "mod": T["start"], "plugin": T["hand"]}
        tc    = color_map.get(ptype, T["muted"])

        btn = ctk.CTkButton(results_scroll, text="", height=72, corner_radius=8,
                             fg_color=T["border"] if _sel_project[0] and _sel_project[0].get("slug")==slug else T["bg"],
                             hover_color=T["border"], border_width=0,
                             command=lambda p=proj: _select_project(p))
        btn.pack(fill="x", padx=6, pady=2)
        _result_btns[slug] = btn

        inner = ctk.CTkFrame(btn, fg_color="transparent"); inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        inner.bind("<Button-1>", lambda e, p=proj: _select_project(p))

        r1 = ctk.CTkFrame(inner, fg_color="transparent"); r1.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(r1, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(r1, text=f"⬇{dls:,}", font=ctk.CTkFont(size=9),
                     text_color=T["muted"]).pack(side="right")

        r2 = ctk.CTkFrame(inner, fg_color="transparent"); r2.pack(fill="x", padx=10, pady=(1, 4))
        ctk.CTkLabel(r2, text=desc, font=ctk.CTkFont(size=10),
                     text_color=T["muted"], anchor="w").pack(side="left", fill="x", expand=True)

        r3 = ctk.CTkFrame(inner, fg_color="transparent"); r3.pack(fill="x", padx=10, pady=(0, 6))
        for cat in cats:
            ctk.CTkLabel(r3, text=cat, font=ctk.CTkFont(size=8),
                         fg_color=T["border"], text_color=T["muted"],
                         corner_radius=3, width=50, height=14).pack(side="left", padx=(0, 3))
        if pvs:
            ctk.CTkLabel(r3, text=pvs[0], font=ctk.CTkFont(size=9),
                         text_color=tc).pack(side="right")

    def _select_project(proj):
        # Highlight selected button
        for s, b in _result_btns.items():
            b.configure(fg_color=T["border"] if s==proj.get("slug","") else T["bg"])
        _set_st_searching(False)

        # Fetch full project details async
        def _fetch():
            try:
                full = _project(proj.get("slug",""))
                scroll.winfo_toplevel().after(0, lambda: _show_detail(full))
            except Exception as ex:
                scroll.winfo_toplevel().after(0, lambda: _show_detail(proj))
        threading.Thread(target=_fetch, daemon=True).start()

    # ── Search state ──────────────────────────────────────
    _searching = [False]
    spin_chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    _spin_idx  = [0]
    _spin_id   = [None]

    def _set_st_searching(on):
        _searching[0] = on
        search_btn.configure(state="disabled" if on else "normal")
        if on:
            def _spin():
                if not _searching[0]: return
                try:
                    search_btn.configure(text=spin_chars[_spin_idx[0] % len(spin_chars)])
                    _spin_idx[0] += 1
                    _spin_id[0] = results_scroll.winfo_toplevel().after(120, _spin)
                except: pass
            _spin()
        else:
            search_btn.configure(text="🔍")
            if _spin_id[0]:
                try: results_scroll.winfo_toplevel().after_cancel(_spin_id[0])
                except: pass

    def _do_search(paginate=False):
        if not paginate: _page[0] = 0
        q = query_var.get().strip() or "minecraft"
        _set_st_searching(True)

        def _work():
            try:
                data = _search(q, type_var[0], limit=PER_PAGE, offset=_page[0]*PER_PAGE)
                hits = data.get("hits", [])
                total = data.get("total_hits", 0)
                _total[0] = total

                def _draw():
                    for w in results_scroll.winfo_children(): w.destroy()
                    _result_btns.clear()
                    result_lbl.configure(text=f"{total:,} results")
                    pg_lbl.configure(text=f"Page {_page[0]+1} / {max(1,(total+PER_PAGE-1)//PER_PAGE)}")
                    if not hits:
                        ctk.CTkLabel(results_scroll, text="No results found.",
                                     font=ctk.CTkFont(size=12), text_color=T["muted"]).pack(pady=20)
                        return
                    for proj in hits:
                        _make_result_card(proj)
                    _set_st_searching(False)

                results_scroll.winfo_toplevel().after(0, _draw)
            except Exception as ex:
                results_scroll.winfo_toplevel().after(0, lambda: (
                    _set_st_searching(False),
                    result_lbl.configure(text=f"Error: {ex}"),
                ))
        threading.Thread(target=_work, daemon=True).start()

    # ── Init ──────────────────────────────────────────────
    _show_welcome()
    _do_search()   # load popular modpacks on open


# ── .mrpack installer ─────────────────────────────────────
def _install_mrpack(mrpack_path, dest, set_st, app_root, prog, show_toast, T):
    """
    Install a Modrinth .mrpack file.
    .mrpack is a ZIP containing:
      - modrinth.index.json  (manifest with download list)
      - overrides/           (files to copy directly)
    """
    try:
        set_st("Reading modpack manifest…", T["sync"])
        with zipfile.ZipFile(mrpack_path, "r") as zf:
            # Read manifest
            with zf.open("modrinth.index.json") as mf:
                manifest = json.loads(mf.read())

            # Extract overrides
            overrides = [n for n in zf.namelist() if n.startswith("overrides/")]
            for i, name in enumerate(overrides):
                rel  = name[len("overrides/"):]
                if not rel: continue
                out  = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with zf.open(name) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                app_root.after(0, prog.set, 0.1 + 0.2 * (i / max(len(overrides),1)))

        # Download mod files from manifest
        files = manifest.get("files", [])
        total = len(files)
        set_st(f"Downloading {total} mod files…", T["sync"])

        for i, f in enumerate(files):
            path_in_pack = f.get("path","")
            downloads    = f.get("downloads", [])
            if not downloads: continue

            out = os.path.join(dest, path_in_pack)
            os.makedirs(os.path.dirname(out), exist_ok=True)

            # Try each mirror URL
            downloaded = False
            for url in downloads:
                try:
                    _dl_file(url, out)
                    downloaded = True; break
                except: continue
            if not downloaded:
                set_st(f"Warning: could not download {os.path.basename(path_in_pack)}", T["hand"])

            app_root.after(0, prog.set, 0.3 + 0.7 * (i / max(total, 1)))

        # Clean up tmp file
        try: os.remove(mrpack_path)
        except: pass

        app_root.after(0, prog.set, 1.0)
        set_st("Modpack installed successfully!", T["start"])
        show_toast("Modpack installed!", T["start"])

    except Exception as ex:
        set_st(f"Modpack install failed: {ex}", T["stop"])
        show_toast(f"Failed: {ex}", T["stop"])


# ── Helpers ───────────────────────────────────────────────
def _strip_md(text):
    """Very basic markdown stripper for display."""
    import re
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)   # images
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    text = re.sub(r'#{1,6}\s*', '', text)          # headers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.+?)\*',   r'\1', text)     # italic
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text) # code
    text = re.sub(r'<[^>]+>', '', text)             # HTML tags
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _open_url(url):
    try:
        import webbrowser; webbrowser.open(url)
    except: pass
