"""
MC CTRL — UI Enhancement Utilities
===================================
Drop these three utilities into launcher.pyw (or import this module).

1. DynamicLabel        — heading that scales its font with the widget width
2. FlexCardGrid        — card container that reflows columns based on available width
3. SnapScrollFrame     — canvas scroll area with per-section snap behaviour

Usage examples are at the bottom of this file.
"""

import tkinter as tk
import customtkinter as ctk
import threading


# ══════════════════════════════════════════════════════════════════════════════
# 1. DYNAMIC HEADING SIZE
# ══════════════════════════════════════════════════════════════════════════════

class DynamicLabel(ctk.CTkLabel):
    """
    A CTkLabel whose font size tracks the widget's width.

    Parameters
    ----------
    parent          : parent widget
    text            : label text
    min_size        : minimum font size in points  (default 10)
    max_size        : maximum font size in points  (default 48)
    weight          : "normal" | "bold"            (default "bold")
    chars_per_row   : how many characters fit at *max_size* before we start
                      shrinking.  Tune this to taste (default 20).
    **kwargs        : forwarded to CTkLabel (text_color, anchor, …)
    """

    def __init__(
        self,
        parent,
        text: str,
        min_size: int = 10,
        max_size: int = 48,
        weight: str = "bold",
        chars_per_row: int = 20,
        **kwargs,
    ):
        # Remove font kwarg if accidentally passed — we manage it ourselves
        kwargs.pop("font", None)
        super().__init__(parent, text=text, font=ctk.CTkFont(size=max_size, weight=weight), **kwargs)

        self._min_size      = min_size
        self._max_size      = max_size
        self._weight        = weight
        self._chars_per_row = chars_per_row
        self._last_width    = 0
        self._after_id      = None

        self.bind("<Configure>", self._on_configure)

    # ── internals ────────────────────────────────────────────────────────────

    def _on_configure(self, event):
        w = event.width
        if w == self._last_width or w < 2:
            return
        self._last_width = w
        # Debounce: skip rapid resize events
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(40, lambda: self._resize(w))

    def _resize(self, width: int):
        """
        Simple heuristic: assume each character is ~0.55× the font size wide.
        Target: text fits in `width` pixels.
        """
        char_count  = max(1, len(self.cget("text")))
        # pixels per char at max_size ≈ 0.55 * max_size
        px_per_char = 0.55 * self._max_size
        ideal_size  = int(width / (char_count * 0.55))
        size        = max(self._min_size, min(self._max_size, ideal_size))
        try:
            self.configure(font=ctk.CTkFont(size=size, weight=self._weight))
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# 2. FLEXIBLE CARD GRID
# ══════════════════════════════════════════════════════════════════════════════

class FlexCardGrid(ctk.CTkFrame):
    """
    A frame that lays out child "cards" in a responsive grid: the number of
    columns is recalculated whenever the container is resized, keeping each
    card at least `min_card_width` pixels wide.

    Usage
    -----
        grid = FlexCardGrid(parent, min_card_width=220, gap=10)
        grid.pack(fill="x", padx=20, pady=8)

        # Add cards with .add_card()
        card = grid.add_card()          # returns a CTkFrame to populate
        ctk.CTkLabel(card, text="Hello").pack(padx=8, pady=8)

    The grid re-flows automatically on resize — no manual column management.
    """

    def __init__(self, parent, min_card_width: int = 200, gap: int = 8, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(parent, **kwargs)

        self._min_card_width = min_card_width
        self._gap            = gap
        self._cards: list[ctk.CTkFrame] = []
        self._last_cols      = 0
        self._after_id       = None

        self.bind("<Configure>", self._on_configure)

    # ── public API ───────────────────────────────────────────────────────────

    def add_card(self, **kwargs) -> ctk.CTkFrame:
        """
        Create and return a new card frame inside the grid.
        Populate it however you like; the grid handles placement.
        """
        # Inherit theme colours from the root T dict if available
        try:
            from __main__ import T
            fg   = T["card"]
            bord = T["border"]
        except Exception:
            fg   = "#1a1a1a"
            bord = "#2a2a2a"

        kwargs.setdefault("fg_color",     fg)
        kwargs.setdefault("border_color", bord)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 10)

        card = ctk.CTkFrame(self, **kwargs)
        self._cards.append(card)
        self._layout()
        return card

    def clear(self):
        """Remove all cards."""
        for c in self._cards:
            try: c.destroy()
            except Exception: pass
        self._cards.clear()

    # ── internals ────────────────────────────────────────────────────────────

    def _on_configure(self, event):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(60, self._layout)

    def _layout(self):
        try:
            width = self.winfo_width()
        except Exception:
            return
        if width < 2:
            return

        cols = max(1, width // (self._min_card_width + self._gap))
        if cols == self._last_cols and all(c.winfo_manager() for c in self._cards):
            return  # nothing changed
        self._last_cols = cols

        # Ungrid everything first
        for c in self._cards:
            c.grid_forget()

        # Distribute column weights
        for ci in range(cols):
            self.columnconfigure(ci, weight=1, uniform="flexcard")

        # Place cards
        for idx, card in enumerate(self._cards):
            row = idx // cols
            col = idx % cols
            card.grid(
                row=row, column=col,
                padx=self._gap // 2,
                pady=self._gap // 2,
                sticky="nsew",
            )


# ══════════════════════════════════════════════════════════════════════════════
# 3. SNAP SCROLL FRAME
# ══════════════════════════════════════════════════════════════════════════════

class SnapScrollFrame(ctk.CTkFrame):
    """
    A vertically-scrollable frame whose scroll position *snaps* to registered
    section boundaries after the user stops scrolling.

    Usage
    -----
        scroll = SnapScrollFrame(parent, snap_delay_ms=180)
        scroll.pack(fill="both", expand=True)

        inner = scroll.inner          # pack children into this frame

        # Tell the scroller about each section so it can snap to it:
        scroll.register_snap_widget(section_frame)

    How it works
    ------------
    After each wheel event, a debounced timer fires.  When the timer
    expires (the user has stopped scrolling) the frame measures the
    canvas Y position of every registered widget and scrolls to whichever
    one is closest to the top of the viewport.
    """

    def __init__(self, parent, snap_delay_ms: int = 220, **kwargs):
        try:
            from __main__ import T
            bg = T["bg"]; border = T["border"]; muted = T["muted"]
        except Exception:
            bg = "#0d0d0d"; border = "#2a2a2a"; muted = "#555555"

        kwargs.setdefault("fg_color", "transparent")
        super().__init__(parent, **kwargs)

        self._snap_delay  = snap_delay_ms
        self._snap_widgets: list[tk.Widget] = []
        self._snap_timer  = None
        self._scrolling   = False
        self._bg          = bg

        # ── Canvas + scrollbar ────────────────────────────
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._vbar   = ctk.CTkScrollbar(
            self, orientation="vertical",
            command=self._canvas.yview,
            button_color=border,
            button_hover_color=muted,
        )
        self._vbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._canvas.configure(yscrollcommand=self._vbar.set)

        # ── Inner frame ───────────────────────────────────
        self.inner = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # ── Bindings ──────────────────────────────────────
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self.inner.bind("<Configure>",   self._on_inner_resize)
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self.inner.bind("<Map>", lambda e: self._bind_tree(self.inner))

    # ── public API ───────────────────────────────────────────────────────────

    def register_snap_widget(self, widget: tk.Widget):
        """Register a widget as a snap target.  Call after packing the widget."""
        if widget not in self._snap_widgets:
            self._snap_widgets.append(widget)

    def scroll_to(self, widget: tk.Widget, animate: bool = True):
        """Programmatically scroll so `widget` is at the top of the viewport."""
        frac = self._fraction_for(widget)
        if frac is not None:
            if animate:
                self._animate_to(frac)
            else:
                self._canvas.yview_moveto(frac)

    # ── internals ────────────────────────────────────────────────────────────

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._win_id, width=event.width)

    def _on_inner_resize(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_wheel(self, event):
        self._canvas.yview_scroll(int(-event.delta / 60), "units")
        # Reset snap timer on every wheel tick
        if self._snap_timer:
            self.after_cancel(self._snap_timer)
        self._snap_timer = self.after(self._snap_delay, self._do_snap)

    def _bind_tree(self, w):
        try:
            w.bind("<MouseWheel>", self._on_wheel)
            for child in w.winfo_children():
                self._bind_tree(child)
        except Exception:
            pass

    def _do_snap(self):
        """Find the closest registered widget to the current scroll top and snap to it."""
        if not self._snap_widgets:
            return

        # Current top of viewport in canvas units
        try:
            top_frac = self._canvas.yview()[0]
            canvas_h = self._canvas.winfo_height()
            total_h  = self._canvas.winfo_reqheight()
            if total_h < 1:
                total_h = max(1, int(self._canvas.cget("scrollregion").split()[3]))
            viewport_top_px = top_frac * total_h
        except Exception:
            return

        best_widget = None
        best_dist   = float("inf")

        for w in self._snap_widgets:
            frac = self._fraction_for(w)
            if frac is None:
                continue
            widget_top_px = frac * total_h
            dist = abs(widget_top_px - viewport_top_px)
            if dist < best_dist:
                best_dist   = dist
                best_widget = w

        if best_widget is not None:
            frac = self._fraction_for(best_widget)
            if frac is not None:
                self._animate_to(frac)

    def _fraction_for(self, widget: tk.Widget):
        """Return the yview fraction that puts `widget` at the top of the canvas."""
        try:
            # canvas coords of the widget
            cy = self._canvas.winfo_rooty()
            wy = widget.winfo_rooty()
            # Offset from canvas origin
            offset = wy - cy + self._canvas.yview()[0] * self._get_scroll_height()
            total  = self._get_scroll_height()
            if total < 1:
                return None
            frac = max(0.0, min(1.0, offset / total))
            return frac
        except Exception:
            return None

    def _get_scroll_height(self) -> float:
        try:
            bb = self._canvas.bbox("all")
            if bb:
                return float(bb[3] - bb[1])
        except Exception:
            pass
        return float(self._canvas.winfo_reqheight())

    def _animate_to(self, target_frac: float, steps: int = 8, delay_ms: int = 14):
        """Smooth eased scroll to target_frac."""
        try:
            current = self._canvas.yview()[0]
        except Exception:
            return
        delta = target_frac - current
        if abs(delta) < 0.001:
            return

        def _step(remaining, cur):
            if remaining <= 0:
                self._canvas.yview_moveto(target_frac)
                return
            # Ease-out: move a fraction of the remaining distance
            ease   = 0.35
            new    = cur + delta * ease * (steps - remaining + 1) / steps
            # Clamp
            new    = max(0.0, min(1.0, new))
            self._canvas.yview_moveto(new)
            self.after(delay_ms, lambda: _step(remaining - 1, new))

        _step(steps, current)


# ══════════════════════════════════════════════════════════════════════════════
# HOW TO INTEGRATE INTO launcher.pyw
# ══════════════════════════════════════════════════════════════════════════════
"""
──────────────────────────────────────────────────────────────────────────────
STEP 1 — Import (add near the top of launcher.pyw, after existing imports)
──────────────────────────────────────────────────────────────────────────────

    from ui_enhancements import DynamicLabel, FlexCardGrid, SnapScrollFrame


──────────────────────────────────────────────────────────────────────────────
STEP 2 — Dynamic headings
──────────────────────────────────────────────────────────────────────────────
Replace static CTkLabel headings with DynamicLabel anywhere you want the text
to scale with the window.  Example — in build_dashboard():

    # BEFORE:
    ctk.CTkLabel(top, text="MC CTRL",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=T["text"]).pack(side="left", padx=16, pady=10)

    # AFTER:
    DynamicLabel(top, text="MC CTRL",
                 min_size=11, max_size=22,
                 text_color=T["text"]).pack(side="left", padx=16, pady=10)

Works best on section titles inside cards, e.g.:

    DynamicLabel(card, text="ACTIVITY LOG",
                 min_size=9, max_size=14, weight="bold",
                 text_color=T["muted"]).pack(anchor="w", padx=12, pady=(8,0))


──────────────────────────────────────────────────────────────────────────────
STEP 3 — Flexible card grid  (example: perf stats panel)
──────────────────────────────────────────────────────────────────────────────
Replace the fixed 5-column stats grid in build_perf_panel() with a FlexCardGrid:

    # BEFORE (fixed 5-column grid):
    grid = ctk.CTkFrame(pf, fg_color="transparent")
    grid.pack(fill="x", padx=12, pady=(0,10))
    stats = [...]
    for i, (label, key) in enumerate(stats):
        col = i % 5; row = i // 5
        cell = ctk.CTkFrame(grid, ...)
        cell.grid(row=row, column=col, ...)

    # AFTER — min_card_width controls when columns collapse:
    flex = FlexCardGrid(pf, min_card_width=140, gap=8)
    flex.pack(fill="x", padx=12, pady=(0,10))
    for label, key in stats:
        cell = flex.add_card()
        ctk.CTkLabel(cell, text=label, ...).pack(pady=(6,0))
        lbl = ctk.CTkLabel(cell, text=perf[key], ...)
        lbl.pack(pady=(0,6))
        perf_labels[key] = lbl


──────────────────────────────────────────────────────────────────────────────
STEP 4 — Snap scroll  (example: Settings window)
──────────────────────────────────────────────────────────────────────────────
Replace make_scroll_frame() calls (or CTkScrollableFrame) in any tab with
SnapScrollFrame.  The API is the same — pack children into .inner:

    # In build_settings_tab(parent):
    scroll = SnapScrollFrame(parent, snap_delay_ms=200)
    scroll.pack(fill="both", expand=True)

    # For each section card:
    f = ctk.CTkFrame(scroll.inner, fg_color=T["card"], ...)
    f.pack(fill="x", padx=20, pady=(0,10))
    scroll.register_snap_widget(f)   # ← this makes it a snap target

The scroller will glide to the nearest section after you stop scrolling.
Use scroll.scroll_to(widget) to jump programmatically.
"""


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE DEMO  (run this file directly to see all three features)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    root.title("UI Enhancements Demo")
    root.geometry("900x650")
    root.configure(fg_color="#0d0d0d")

    # Fake theme dict
    class _T(dict):
        pass
    T = _T(
        bg="#0d0d0d", card="#1a1a1a", border="#2a2a2a",
        text="#e0e0e0", muted="#555555",
        start="#22c55e", stop="#ef4444", sync="#60a5fa", handoff="#f59e0b",
    )

    # ── Top: dynamic heading ──────────────────────────────
    hdr = ctk.CTkFrame(root, fg_color="#111111", corner_radius=0)
    hdr.pack(fill="x")
    DynamicLabel(
        hdr, text="MC CTRL — Dynamic Heading",
        min_size=11, max_size=36, weight="bold",
        text_color="#22c55e",
    ).pack(padx=20, pady=14, fill="x")

    # ── Middle: flex card grid ────────────────────────────
    mid = ctk.CTkFrame(root, fg_color="transparent")
    mid.pack(fill="x", padx=16, pady=(12, 0))
    ctk.CTkLabel(mid, text="FLEXIBLE CARD GRID — resize the window",
                 font=ctk.CTkFont(size=10), text_color="#555").pack(anchor="w", padx=4)

    flex = FlexCardGrid(mid, min_card_width=150, gap=10)
    flex.pack(fill="x", pady=(4, 0))

    STATS = [("TPS", "20.0"), ("Players", "4"), ("RAM", "1.2 GB"),
             ("CPU", "12%"), ("Uptime", "02:14:33"), ("Threads", "48"),
             ("Latency", "34 ms"), ("Chunks", "1 024"), ("Entities", "382")]
    for label, val in STATS:
        card = flex.add_card()
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=9),
                     text_color="#555").pack(pady=(8, 2))
        ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#e0e0e0").pack(pady=(0, 8))

    # ── Bottom: snap scroll ───────────────────────────────
    ctk.CTkLabel(root, text="SNAP SCROLL — scroll down, release, watch it snap",
                 font=ctk.CTkFont(size=10), text_color="#555").pack(anchor="w", padx=20, pady=(14, 2))

    snap = SnapScrollFrame(root, snap_delay_ms=200)
    snap.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    SECTIONS = [
        ("Dashboard",   "#22c55e", "Server controls, activity log, quick commands"),
        ("playit.gg",   "#60a5fa", "Tunnel setup, agent log, connection guide"),
        ("Server Info", "#f59e0b", "Players, plugins, resource packs, properties"),
        ("Network",     "#a78bfa", "Local IP, external IP, port forwarding guide"),
        ("Multi CTRL",  "#f472b6", "Run up to 3 servers simultaneously"),
        ("Settings",    "#fb923c", "Themes, paths, auto-upload, addon manager"),
    ]

    for title, color, desc in SECTIONS:
        sec = ctk.CTkFrame(snap.inner, fg_color="#1a1a1a",
                           border_color=color, border_width=2, corner_radius=12)
        sec.pack(fill="x", padx=8, pady=6)
        snap.register_snap_widget(sec)

        ctk.CTkLabel(sec, text=title, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=color).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(sec, text=desc, font=ctk.CTkFont(size=12),
                     text_color="#888").pack(anchor="w", padx=16)

        # Fake content so sections have height
        grid = FlexCardGrid(sec, min_card_width=160, gap=8)
        grid.pack(fill="x", padx=16, pady=(10, 16))
        for _ in range(random.randint(3, 6)):
            c = grid.add_card()
            ctk.CTkLabel(c, text=f"Card {random.randint(1,99)}",
                         font=ctk.CTkFont(size=11), text_color="#aaa").pack(padx=12, pady=10)

    root.mainloop()
