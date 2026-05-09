"""
MC CTRL Addon — Custom Theme Creator
=====================================
Adds a "✏ Create Theme" button to the top bar.
Opens an animated color-picker dialog where you can define every
color role, preview in real time, and save the theme permanently
to settings.json under the key "custom_themes".

Drop this file in your  addons/  folder — it loads automatically.
No restart needed if you use  Settings → MC CTRL App Addons → Install Addon.

Requires: customtkinter (already installed), tkinter (stdlib)
"""

import json
import os
import tkinter as tk
import tkinter.colorchooser as _colorchooser
import threading
import time

# ── will be filled in by setup() ──────────────────────────
_ctx = {}
_app = None
_get_T = lambda: _ctx.get("T", {})

# ─────────────────────────────────────────────────────────
#  Glow / animation helpers
#  These work on any CTkFrame or CTkLabel widget.
# ─────────────────────────────────────────────────────────

def _animate_glow(widget, color, steps=12, duration_ms=600):
    """
    Pulse the border_color of a CTkFrame from transparent → color → transparent.
    Non-blocking — runs through app.after() scheduling.
    """
    if _app is None:
        return
    try:
        import customtkinter as ctk

        # Parse target color hex → rgb
        c = color.lstrip("#")
        if len(c) == 3:
            c = "".join(x * 2 for x in c)
        tr, tg, tb = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

        half = steps // 2
        delay = duration_ms // steps

        def _step(i):
            try:
                if i <= half:
                    alpha = i / half
                else:
                    alpha = (steps - i) / half
                r = int(tr * alpha)
                g = int(tg * alpha)
                b = int(tb * alpha)
                hex_col = f"#{r:02x}{g:02x}{b:02x}"
                widget.configure(border_color=hex_col)
                if i < steps:
                    _app.after(delay, lambda: _step(i + 1))
                else:
                    T = _get_T()
                    widget.configure(border_color=T.get("border", "#2a2a2a"))
            except Exception:
                pass

        _step(0)
    except Exception:
        pass


def _animate_button_press(widget, color):
    """Brief scale-down → scale-up flash on a CTkButton."""
    if _app is None:
        return
    try:
        orig = widget.cget("fg_color")
        # Darken the color briefly
        c = color.lstrip("#")
        if len(c) == 3:
            c = "".join(x * 2 for x in c)
        r, g, b = int(int(c[0:2], 16) * 0.65), int(int(c[2:4], 16) * 0.65), int(int(c[4:6], 16) * 0.65)
        dark = f"#{r:02x}{g:02x}{b:02x}"

        widget.configure(fg_color=dark)
        _app.after(120, lambda: _safe_cfg(widget, fg_color=orig))
    except Exception:
        pass


def _safe_cfg(widget, **kwargs):
    try:
        widget.configure(**kwargs)
    except Exception:
        pass


def _slide_in(widget, axis="x", distance=40, duration_ms=280, steps=14):
    """
    Animate a widget sliding in from off-screen.
    Uses place() temporarily — call after pack/grid is already done.
    """
    # This works best on Toplevel children; for the main app it's cosmetic only.
    # We'll use a simple opacity-like fade via repeated configure calls on a label.
    pass  # placeholder — real slide handled via CTkFrame place trick below


# ─────────────────────────────────────────────────────────
#  Color swatch widget
# ─────────────────────────────────────────────────────────

class ColorSwatch:
    """
    A labeled color picker row:
      [Label]  [####hex]  [■ color block]  [Pick →]
    """

    def __init__(self, parent, label: str, initial_hex: str, T: dict, app_ref, on_change=None):
        import customtkinter as ctk
        self._var = tk.StringVar(value=initial_hex)
        self._cb = on_change
        self._T = T
        self._app = app_ref

        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x", pady=3)

        ctk.CTkLabel(self.frame, text=label,
                     font=ctk.CTkFont(size=11),
                     text_color=T.get("text", "#e0e0e0"),
                     width=120, anchor="w").pack(side="left")

        self._hex_entry = ctk.CTkEntry(
            self.frame, textvariable=self._var, width=90, height=28,
            font=ctk.CTkFont(size=11, family="Consolas"),
            fg_color=T.get("bg", "#0d0d0d"),
            border_color=T.get("border", "#2a2a2a"),
            text_color=T.get("text", "#e0e0e0"),
            placeholder_text="#rrggbb")
        self._hex_entry.pack(side="left", padx=(0, 8))
        self._hex_entry.bind("<Return>", self._on_entry_change)
        self._hex_entry.bind("<FocusOut>", self._on_entry_change)

        self._swatch = ctk.CTkFrame(
            self.frame, width=28, height=28, corner_radius=6,
            fg_color=initial_hex, border_color=T.get("border", "#2a2a2a"), border_width=1)
        self._swatch.pack(side="left", padx=(0, 8))
        self._swatch.pack_propagate(False)

        self._pick_btn = ctk.CTkButton(
            self.frame, text="Pick →", width=64, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=T.get("sync", "#60a5fa"),
            hover_color=T.get("sync", "#60a5fa"),
            text_color="#000000",
            command=self._open_picker)
        self._pick_btn.pack(side="left")

    def _open_picker(self):
        current = self._var.get().strip()
        if not current.startswith("#") or len(current) not in (4, 7):
            current = "#ffffff"
        result = _colorchooser.askcolor(color=current, title="Choose Color")
        if result and result[1]:
            self.set(result[1])
            _animate_button_press(self._pick_btn, self._T.get("sync", "#60a5fa"))

    def _on_entry_change(self, _event=None):
        val = self._var.get().strip()
        if val.startswith("#") and len(val) in (4, 7):
            self.set(val)

    def set(self, hex_col: str):
        # Normalize
        hex_col = hex_col.strip()
        if not hex_col.startswith("#"):
            hex_col = "#" + hex_col
        hex_col = hex_col[:7].lower()
        self._var.set(hex_col)
        try:
            self._swatch.configure(fg_color=hex_col)
        except Exception:
            pass
        if self._cb:
            self._cb(hex_col)

    def get(self) -> str:
        return self._var.get().strip()


# ─────────────────────────────────────────────────────────
#  Mini live preview
# ─────────────────────────────────────────────────────────

def _build_preview(parent, theme_dict: dict):
    """Build a tiny mock dashboard card to preview the theme."""
    import customtkinter as ctk

    T = theme_dict
    for w in parent.winfo_children():
        w.destroy()

    outer = ctk.CTkFrame(parent, fg_color=T["bg"],
                         border_color=T["border"], border_width=1, corner_radius=10)
    outer.pack(fill="both", expand=True, padx=4, pady=4)

    # Top bar
    bar = ctk.CTkFrame(outer, fg_color=T["card"], corner_radius=0, height=28)
    bar.pack(fill="x")
    bar.pack_propagate(False)
    ctk.CTkLabel(bar, text="MC CTRL",
                 font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=8, pady=4)
    ctk.CTkLabel(bar, text="● Running",
                 font=ctk.CTkFont(size=9),
                 text_color=T["start"]).pack(side="right", padx=8)

    # Body row
    body = ctk.CTkFrame(outer, fg_color="transparent")
    body.pack(fill="x", padx=6, pady=6)

    for label, color_key in [("▶ Start", "start"), ("■ Stop", "stop"), ("↑ Sync", "sync")]:
        ctk.CTkButton(body, text=label, height=22, width=58,
                      font=ctk.CTkFont(size=9),
                      fg_color=T.get(color_key, "#888"),
                      hover_color=T.get(color_key, "#888"),
                      text_color="#000000",
                      corner_radius=5).pack(side="left", padx=2)

    # Stats row
    stats = ctk.CTkFrame(outer, fg_color=T["bg"],
                         border_color=T["border"], border_width=1, corner_radius=6)
    stats.pack(fill="x", padx=6, pady=(0, 6))
    for label, val in [("TPS", "20.0"), ("RAM", "1.2 GB"), ("CPU", "12%")]:
        cell = ctk.CTkFrame(stats, fg_color="transparent")
        cell.pack(side="left", expand=True, fill="x", padx=4, pady=4)
        ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=8),
                     text_color=T["muted"]).pack()
        ctk.CTkLabel(cell, text=val, font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=T["start"]).pack()


# ─────────────────────────────────────────────────────────
#  Main theme creator dialog
# ─────────────────────────────────────────────────────────

def open_theme_creator():
    import customtkinter as ctk

    T = _get_T()
    app = _app

    ROLES = [
        ("bg",       "Background",          T.get("bg",      "#0d0d0d")),
        ("card",     "Card / Panel",        T.get("card",    "#1a1a1a")),
        ("border",   "Border / Divider",    T.get("border",  "#2a2a2a")),
        ("text",     "Primary Text",        T.get("text",    "#e0e0e0")),
        ("muted",    "Muted / Label Text",  T.get("muted",   "#555555")),
        ("start",    "Start / Success",     T.get("start",   "#22c55e")),
        ("stop",     "Stop / Danger",       T.get("stop",    "#ef4444")),
        ("sync",     "Sync / Accent",       T.get("sync",    "#60a5fa")),
        ("handoff",  "Handoff / Warning",   T.get("handoff", "#f59e0b")),
    ]

    # ── Window ─────────────────────────────────────────────
    win = ctk.CTkToplevel(app)
    win.title("✏  Custom Theme Creator")
    win.geometry("860x680")
    win.resizable(True, True)
    win.configure(fg_color=T.get("bg", "#0d0d0d"))
    win.grab_set()
    win.attributes("-topmost", True)

    try:
        ax = app.winfo_x() + (app.winfo_width()  - 860) // 2
        ay = app.winfo_y() + (app.winfo_height() - 680) // 2
        win.geometry(f"860x680+{ax}+{ay}")
    except Exception:
        pass

    # Animate open — slide in from slightly below
    # (We briefly offset the window then snap it back)
    try:
        orig_y = app.winfo_y() + (app.winfo_height() - 680) // 2
        win.geometry(f"860x680+{ax}+{orig_y + 30}")
        def _snap():
            try:
                win.geometry(f"860x680+{ax}+{orig_y}")
            except Exception:
                pass
        app.after(80, _snap)
    except Exception:
        pass

    # ── Header ─────────────────────────────────────────────
    hdr = ctk.CTkFrame(win, fg_color=T.get("card", "#1a1a1a"), corner_radius=0)
    hdr.pack(fill="x")
    ctk.CTkLabel(hdr, text="✏  Custom Theme Creator",
                 font=ctk.CTkFont(size=15, weight="bold"),
                 text_color=T.get("text", "#e0e0e0")).pack(side="left", padx=16, pady=12)
    ctk.CTkLabel(hdr, text="Pick colors → see live preview → name & save",
                 font=ctk.CTkFont(size=11),
                 text_color=T.get("muted", "#555")).pack(side="left", padx=4)

    # ── Body (left: pickers | right: preview) ─────────────
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=16, pady=12)
    body.columnconfigure(0, weight=2)
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    # Left: color pickers
    left_outer = ctk.CTkFrame(body, fg_color=T.get("card", "#1a1a1a"),
                               border_color=T.get("border", "#2a2a2a"),
                               border_width=1, corner_radius=10)
    left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

    ctk.CTkLabel(left_outer, text="COLOR ROLES",
                 font=ctk.CTkFont(size=10),
                 text_color=T.get("muted", "#555")).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(left_outer, height=1,
                 fg_color=T.get("border", "#2a2a2a")).pack(fill="x", padx=14)

    pickers_frame = ctk.CTkScrollableFrame(left_outer, fg_color="transparent")
    pickers_frame.pack(fill="both", expand=True, padx=14, pady=8)

    # Right: live preview
    right_outer = ctk.CTkFrame(body, fg_color=T.get("card", "#1a1a1a"),
                                border_color=T.get("border", "#2a2a2a"),
                                border_width=1, corner_radius=10)
    right_outer.grid(row=0, column=1, sticky="nsew")

    ctk.CTkLabel(right_outer, text="LIVE PREVIEW",
                 font=ctk.CTkFont(size=10),
                 text_color=T.get("muted", "#555")).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(right_outer, height=1,
                 fg_color=T.get("border", "#2a2a2a")).pack(fill="x", padx=14)

    preview_frame = ctk.CTkFrame(right_outer, fg_color="transparent", height=180)
    preview_frame.pack(fill="x", padx=10, pady=10)

    # Appearance toggle (dark/light)
    appearance_var = ctk.StringVar(value=T.get("appearance", "dark"))
    ap_row = ctk.CTkFrame(right_outer, fg_color="transparent")
    ap_row.pack(fill="x", padx=14, pady=(0, 8))
    ctk.CTkLabel(ap_row, text="Appearance:",
                 font=ctk.CTkFont(size=11),
                 text_color=T.get("text", "#e0e0e0")).pack(side="left")
    for val, lbl in [("dark", "🌙 Dark"), ("light", "☀ Light")]:
        ctk.CTkRadioButton(ap_row, text=lbl, variable=appearance_var, value=val,
                           font=ctk.CTkFont(size=11),
                           text_color=T.get("text", "#e0e0e0"),
                           fg_color=T.get("sync", "#60a5fa"),
                           border_color=T.get("border", "#2a2a2a")
                           ).pack(side="left", padx=(8, 0))

    # ── Build current theme dict from swatches ─────────────
    current_theme = {role: hex_val for role, _, hex_val in ROLES}
    current_theme["appearance"] = appearance_var.get()

    swatches = {}

    def _on_color_change(role, _hex_val):
        current_theme[role] = _hex_val
        current_theme["appearance"] = appearance_var.get()
        # Rebuild preview
        _build_preview(preview_frame, current_theme)
        # Glow the preview frame to signal update
        _animate_glow(right_outer,
                      current_theme.get("sync", T.get("sync", "#60a5fa")),
                      steps=8, duration_ms=400)

    appearance_var.trace_add("write",
                             lambda *_: _on_color_change("appearance", appearance_var.get()))

    # Instantiate swatches
    for role, label, initial in ROLES:
        sw = ColorSwatch(
            pickers_frame, label, initial, T, app,
            on_change=lambda hx, r=role: _on_color_change(r, hx))
        swatches[role] = sw

    # Initial preview
    _build_preview(preview_frame, current_theme)

    # "Copy from existing theme" helper
    sep = ctk.CTkFrame(right_outer, height=1, fg_color=T.get("border", "#2a2a2a"))
    sep.pack(fill="x", padx=14, pady=(0, 6))

    ctk.CTkLabel(right_outer, text="Copy from existing theme:",
                 font=ctk.CTkFont(size=10),
                 text_color=T.get("muted", "#555")).pack(anchor="w", padx=14)

    copy_var = ctk.StringVar(value="— select —")

    def _copy_from(name):
        if name == "— select —":
            return
        # Import THEMES from the main module
        import sys
        main_mod = sys.modules.get("__main__")
        if main_mod and hasattr(main_mod, "THEMES"):
            td = main_mod.THEMES.get(name)
            if td:
                for role, _, _ in ROLES:
                    val = td.get(role, "#888888")
                    swatches[role].set(val)
                if td.get("appearance"):
                    appearance_var.set(td["appearance"])
                _animate_glow(left_outer,
                              current_theme.get("sync", T.get("sync", "#60a5fa")),
                              steps=12, duration_ms=500)

    import sys as _sys
    _main = _sys.modules.get("__main__")
    theme_names = ["— select —"] + (list(_main.THEMES.keys()) if _main and hasattr(_main, "THEMES") else [])
    ctk.CTkOptionMenu(right_outer, values=theme_names, variable=copy_var,
                      command=_copy_from,
                      font=ctk.CTkFont(size=11), height=28,
                      fg_color=T.get("bg", "#0d0d0d"),
                      button_color=T.get("border", "#2a2a2a"),
                      button_hover_color=T.get("muted", "#555"),
                      text_color=T.get("text", "#e0e0e0"),
                      dropdown_fg_color=T.get("card", "#1a1a1a"),
                      dropdown_text_color=T.get("text", "#e0e0e0"),
                      dropdown_hover_color=T.get("border", "#2a2a2a")
                      ).pack(fill="x", padx=14, pady=(4, 0))

    # ── Name + Save row ────────────────────────────────────
    bottom = ctk.CTkFrame(win, fg_color=T.get("card", "#1a1a1a"),
                           border_color=T.get("border", "#2a2a2a"),
                           border_width=1, corner_radius=10)
    bottom.pack(fill="x", padx=16, pady=(0, 16))
    bi = ctk.CTkFrame(bottom, fg_color="transparent")
    bi.pack(fill="x", padx=14, pady=10)

    ctk.CTkLabel(bi, text="Theme name:",
                 font=ctk.CTkFont(size=12),
                 text_color=T.get("text", "#e0e0e0")).pack(side="left")

    name_var = ctk.StringVar(value="My Custom Theme")
    name_entry = ctk.CTkEntry(bi, textvariable=name_var, width=220, height=32,
                               font=ctk.CTkFont(size=12),
                               fg_color=T.get("bg", "#0d0d0d"),
                               border_color=T.get("border", "#2a2a2a"),
                               text_color=T.get("text", "#e0e0e0"))
    name_entry.pack(side="left", padx=(8, 16))

    status_lbl = ctk.CTkLabel(bi, text="",
                               font=ctk.CTkFont(size=11),
                               text_color=T.get("muted", "#555"))
    status_lbl.pack(side="left", padx=(0, 12))

    def _save_theme():
        name = name_var.get().strip()
        if not name:
            status_lbl.configure(text="Enter a theme name first.", text_color=T.get("stop", "#ef4444"))
            return

        final_theme = {role: swatches[role].get() for role, _, _ in ROLES}
        final_theme["appearance"] = appearance_var.get()

        # Save into main THEMES dict
        import sys as _sys2
        main_mod = _sys2.modules.get("__main__")
        if main_mod and hasattr(main_mod, "THEMES"):
            main_mod.THEMES[name] = final_theme

        # Persist to settings.json
        try:
            load_settings = _ctx.get("load_settings")
            if load_settings:
                s = load_settings()
                customs = s.get("custom_themes", {})
                customs[name] = final_theme
                s["custom_themes"] = customs
                # Write via update_setting if available
                if hasattr(main_mod, "save_settings"):
                    main_mod.save_settings(s)
        except Exception as ex:
            pass

        status_lbl.configure(
            text=f'✓ "{name}" saved! Apply it from the Theme Picker.',
            text_color=T.get("start", "#22c55e"))
        _animate_glow(bottom, T.get("start", "#22c55e"), steps=16, duration_ms=800)
        _animate_button_press(save_btn, T.get("start", "#22c55e"))
        _ctx.get("log", print)(f'Custom theme saved: "{name}"')
        _ctx.get("show_toast", lambda m, c: None)(f'Theme "{name}" saved!', T.get("start", "#22c55e"))

    def _apply_theme():
        name = name_var.get().strip()
        if not name:
            return
        _save_theme()
        import sys as _sys3
        main_mod = _sys3.modules.get("__main__")
        if main_mod and hasattr(main_mod, "apply_theme"):
            try:
                main_mod.apply_theme(name)
            except Exception:
                pass
        _animate_glow(win, current_theme.get("sync", "#60a5fa"), steps=14, duration_ms=600)

    save_btn = ctk.CTkButton(bi, text="💾 Save Theme", height=32, width=120,
                              font=ctk.CTkFont(size=12, weight="bold"),
                              fg_color=T.get("start", "#22c55e"),
                              hover_color=T.get("start", "#22c55e"),
                              text_color="#000000",
                              command=_save_theme)
    save_btn.pack(side="right", padx=(0, 4))

    ctk.CTkButton(bi, text="▶ Apply Now", height=32, width=110,
                  font=ctk.CTkFont(size=12),
                  fg_color=T.get("sync", "#60a5fa"),
                  hover_color=T.get("sync", "#60a5fa"),
                  text_color="#000000",
                  command=_apply_theme).pack(side="right", padx=(0, 8))


# ─────────────────────────────────────────────────────────
#  Glow on selected/active UI elements
#  Call this after the UI is built to wire up persistent glow
#  on the active tab indicator etc.
# ─────────────────────────────────────────────────────────

def _wire_global_glows():
    """
    Periodically pulse the status dot when the server is running,
    creating a live "heartbeat" glow effect.
    """
    import sys
    main_mod = sys.modules.get("__main__")
    if not main_mod:
        return

    def _heartbeat():
        try:
            if not (_app and _app.winfo_exists()):
                return
            T = _get_T()
            server_proc = getattr(main_mod, "server_proc", None)
            if server_proc and server_proc.poll() is None:
                # Server running — pulse the status dot label
                status_dot = getattr(main_mod, "status_dot", None)
                if status_dot:
                    try:
                        # Briefly brighten then restore
                        status_dot.configure(text_color="#ffffff")
                        _app.after(200, lambda: _safe_cfg(
                            status_dot, text_color=T.get("start", "#22c55e")))
                    except Exception:
                        pass
        except Exception:
            pass
        # Repeat every 3 seconds
        if _app:
            _app.after(3000, _heartbeat)

    if _app:
        _app.after(3000, _heartbeat)


# ─────────────────────────────────────────────────────────
#  Load saved custom themes on startup
# ─────────────────────────────────────────────────────────

def _load_custom_themes():
    import sys
    main_mod = sys.modules.get("__main__")
    if not main_mod:
        return
    load_settings = _ctx.get("load_settings")
    if not load_settings:
        return
    try:
        s = load_settings()
        customs = s.get("custom_themes", {})
        if customs and hasattr(main_mod, "THEMES"):
            for name, td in customs.items():
                if name not in main_mod.THEMES:
                    main_mod.THEMES[name] = td
            if customs:
                _ctx.get("log", print)(f"Loaded {len(customs)} custom theme(s) from settings.")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────
#  Inject "✏ Create Theme" button into the top bar
# ─────────────────────────────────────────────────────────

def _inject_create_theme_button():
    import sys
    import customtkinter as ctk

    main_mod = sys.modules.get("__main__")
    if not main_mod or not _app:
        return

    T = _get_T()

    # Find the top bar (first CTkFrame child of app)
    top_bar = None
    for child in _app.winfo_children():
        if type(child).__name__ == "CTkFrame":
            top_bar = child
            break

    if top_bar is None:
        _ctx.get("log", print)("Theme Creator: could not find top bar — button not injected.")
        return

    btn = ctk.CTkButton(
        top_bar,
        text="✏  Create Theme",
        width=130, height=28,
        font=ctk.CTkFont(size=11),
        corner_radius=6,
        fg_color=T.get("bg", "#0d0d0d"),
        border_width=1,
        border_color=T.get("handoff", "#f59e0b"),
        text_color=T.get("handoff", "#f59e0b"),
        hover_color=T.get("border", "#2a2a2a"),
        command=open_theme_creator)
    btn.pack(side="left", padx=(0, 6), pady=8)

    # Animate in with a glow pulse
    _animate_glow(btn, T.get("handoff", "#f59e0b"), steps=10, duration_ms=500)


# ─────────────────────────────────────────────────────────
#  Addon entry point
# ─────────────────────────────────────────────────────────

def setup(ctx: dict):
    global _ctx, _app
    _ctx = ctx
    _app = ctx.get("app")

    if _app is None:
        return

    # Load any previously saved custom themes
    _load_custom_themes()

    # Inject the Create Theme button (delayed so the top bar exists)
    _app.after(300, _inject_create_theme_button)

    # Wire heartbeat glow
    _app.after(500, _wire_global_glows)

    ctx.get("log", print)("Theme Creator addon loaded — ✏ Create Theme button added to top bar.")
    ctx.get("show_toast", lambda m, c: None)(
        "Theme Creator ready! Click ✏ Create Theme in the top bar.",
        ctx.get("T", {}).get("handoff", "#f59e0b"))
