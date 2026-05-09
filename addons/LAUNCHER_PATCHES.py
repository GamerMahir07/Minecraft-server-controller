"""
MC CTRL — launcher.pyw PATCH NOTES
====================================
This file documents every change made to launcher.pyw.
Apply each section in order, or use the theme_creator.py addon
in addons/ for zero-edit installation of the theme creator.

Changes:
  1. Animation & glow utilities (add near top, after globals)
  2. Glow on active tab buttons
  3. Animated button press feedback  
  4. Heartbeat status dot
  5. Custom themes loaded from settings on boot
  6. ✏ Create Theme button in top bar (if not using addon)
  7. Splash animation enhancement
"""

# ══════════════════════════════════════════════════════════
# PATCH 1 — Animation & Glow utilities
# Add this block after the line:   CREATE_NO_WINDOW = 0x08000000
# ══════════════════════════════════════════════════════════

ANIMATION_PATCH = '''
# ── Animation & Glow utilities ────────────────────────────

def _glow_pulse(widget, color, steps=12, duration_ms=600):
    """Pulse border_color from transparent → color → transparent."""
    c = color.lstrip("#")
    if len(c) == 3: c = "".join(x*2 for x in c)
    try: tr,tg,tb = int(c[0:2],16),int(c[2:4],16),int(c[4:6],16)
    except: return
    half = steps // 2
    delay = max(1, duration_ms // steps)
    def _step(i):
        try:
            alpha = (i/half) if i<=half else ((steps-i)/half)
            r,g,b = int(tr*alpha),int(tg*alpha),int(tb*alpha)
            widget.configure(border_color=f"#{r:02x}{g:02x}{b:02x}")
            if i < steps: app.after(delay, lambda: _step(i+1))
            else: widget.configure(border_color=T["border"])
        except Exception: pass
    _step(0)

def _flash_button(widget, color):
    """Briefly darken a button on press for tactile feedback."""
    try:
        orig = widget.cget("fg_color")
        c = color.lstrip("#")
        if len(c)==3: c="".join(x*2 for x in c)
        r,g,b = int(int(c[0:2],16)*0.6),int(int(c[2:4],16)*0.6),int(int(c[4:6],16)*0.6)
        dark = f"#{r:02x}{g:02x}{b:02x}"
        widget.configure(fg_color=dark)
        app.after(130, lambda: _safe_cfg(widget, fg_color=orig))
    except Exception: pass

def _safe_cfg(widget, **kwargs):
    try: widget.configure(**kwargs)
    except Exception: pass

def _start_heartbeat():
    """Pulse status dot while server is running — call once after build_ui."""
    def _beat():
        try:
            if server_proc and server_proc.poll() is None:
                status_dot.configure(text_color="#ffffff")
                app.after(220, lambda: _safe_cfg(status_dot, text_color=T["start"]))
        except Exception: pass
        app.after(3000, _beat)
    app.after(3000, _beat)
'''

# ══════════════════════════════════════════════════════════
# PATCH 2 — Call _start_heartbeat() after build_ui() boots
# Find the line:   app.after(50, _finish_boot)
# Change _finish_boot to also call _start_heartbeat:
# ══════════════════════════════════════════════════════════

HEARTBEAT_PATCH = '''
def _finish_boot():
    global _splash_frame
    _splash_bar.stop()
    build_ui()
    _splash_frame.destroy()
    if auto_upload: schedule_auto_upload()
    app.after(800, _start_heartbeat)   # <-- ADD THIS LINE
'''

# ══════════════════════════════════════════════════════════
# PATCH 3 — Glow on active tab button
# In show_tab(), replace the tab_btns[name].configure line:
# ══════════════════════════════════════════════════════════

TAB_GLOW_PATCH = '''
# In show_tab(name):
# BEFORE:
#   tab_btns[name].configure(fg_color=T["sync"], text_color="#000")
# AFTER:
    tab_btns[name].configure(fg_color=T["sync"], text_color="#000")
    _glow_pulse(tab_btns[name], T["sync"], steps=10, duration_ms=400)
'''

# ══════════════════════════════════════════════════════════
# PATCH 4 — Animated Start/Stop/Sync buttons
# In make_btn() inside build_dashboard():
# Wrap the command with flash animation:
# ══════════════════════════════════════════════════════════

BUTTON_FLASH_PATCH = '''
# In make_btn(), change the button command to:
def _wrapped_cmd(b=b, c=color, fn=cmd):
    _flash_button(b, c)
    fn()
b.configure(command=_wrapped_cmd)
# (Apply after the button b is created, before returning b)
'''

# ══════════════════════════════════════════════════════════
# PATCH 5 — Load custom themes from settings on boot
# Add inside load_settings() or right after _settings_cache is loaded:
# ══════════════════════════════════════════════════════════

CUSTOM_THEMES_PATCH = '''
# After:   settings = load_settings()
# Add:
def _restore_custom_themes():
    customs = settings.get("custom_themes", {})
    for name, td in customs.items():
        if name not in THEMES:
            THEMES[name] = td
_restore_custom_themes()
'''

# ══════════════════════════════════════════════════════════
# PATCH 6 — ✏ Create Theme button in top bar
# (Only needed if NOT using the addon. The addon handles this.)
# In build_ui(), after the theme_btn is packed, add:
# ══════════════════════════════════════════════════════════

CREATE_THEME_BTN_PATCH = '''
# After theme_btn.pack(...)  in build_ui():
from addons.theme_creator import open_theme_creator as _open_tc
ctk.CTkButton(top, text="✏  Create Theme", width=130, height=28,
              font=ctk.CTkFont(size=11), corner_radius=6,
              fg_color=T["bg"], border_width=1,
              border_color=T["handoff"], text_color=T["handoff"],
              hover_color=T["border"],
              command=_open_tc).pack(side="left", padx=(0,6), pady=8)
'''

# ══════════════════════════════════════════════════════════
# PATCH 7 — Splash bar animation enhancement
# The existing splash already has a progress bar.
# Optionally add a fade-in label animation by changing:
# ══════════════════════════════════════════════════════════

SPLASH_PATCH = '''
# After _splash_bar.start(), add:
_splash_colors = [T["start"], T["sync"], T["handoff"], T["start"]]
_splash_idx = [0]
def _cycle_splash_color():
    try:
        _splash_lbl.configure(text_color=_splash_colors[_splash_idx[0] % len(_splash_colors)])
        _splash_idx[0] += 1
        app.after(180, _cycle_splash_color)
    except Exception: pass
app.after(100, _cycle_splash_color)
'''

# ══════════════════════════════════════════════════════════
# SUMMARY — Quickest way to get everything:
# 1. Copy addons/theme_creator.py into your addons/ folder
# 2. Launch MC CTRL — the addon loads automatically
# 3. Click "✏ Create Theme" in the top bar
#
# For the glow + heartbeat animations in the main UI,
# apply PATCH 1 and PATCH 2 above to launcher.pyw.
# The tab glow (PATCH 3) and button flash (PATCH 4)
# are cosmetic extras — apply if desired.
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("This is a patch reference file, not an executable.")
    print("See addons/theme_creator.py for the theme creator addon.")
    print("Apply the PATCH_* strings above to launcher.pyw for animations.")
