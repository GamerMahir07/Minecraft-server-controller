"""ui/theme_picker.py — ThemePickerDialog + CustomThemeDialog"""
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLineEdit, QLabel, QComboBox,
    QColorDialog, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.themes import T, THEMES, current_theme_name, _resolve_theme
from core.settings import load_settings, save_settings


class ThemePickerDialog(QDialog):
    CARD_W, CARD_H, GAP = 192, 94, 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Choose Theme  —  {len(THEMES)} available")
        self.resize(860, 580); self.setMinimumSize(640, 420)
        self._apply_style()

        root = QVBoxLayout(self); root.setContentsMargins(14,12,14,12); root.setSpacing(8)

        bar = QHBoxLayout(); bar.setSpacing(8)
        self._search = QLineEdit(); self._search.setPlaceholderText("Search...")
        self._search.textChanged.connect(self._rebuild); bar.addWidget(self._search, 1)
        self._mode = QComboBox()
        self._mode.addItems(["All","Dark","Light"]); self._mode.setFixedWidth(90)
        self._mode.currentIndexChanged.connect(self._rebuild); bar.addWidget(self._mode)
        cb = QPushButton("Create Custom"); cb.setFixedWidth(130)
        cb.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; padding:6px 10px; font-weight:700; }}")
        cb.clicked.connect(self._create_custom); bar.addWidget(cb)
        root.addLayout(bar)

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea {{ background:{T['bg']}; border:none; }}")
        self._container = QWidget(); self._container.setStyleSheet(f"background:{T['bg']};")
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

        self._all_cards: list[QFrame] = []
        for name, td in THEMES.items():
            self._all_cards.append(self._make_card(name, td))
        self._rebuild()

    def _apply_style(self):
        self.setStyleSheet(
            f"QDialog {{ background:{T['bg']}; }}"
            f"QWidget {{ background:{T['bg']}; color:{T['text']}; }}"
            f"QLineEdit {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:5px 10px; }}"
            f"QComboBox {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:4px 8px; }}"
            f"QComboBox QAbstractItemView {{ background:{T['card']}; color:{T['text']}; selection-background-color:{T['border']}; }}"
            f"QScrollBar:vertical {{ background:{T['bg']}; width:7px; border-radius:4px; }}"
            f"QScrollBar::handle:vertical {{ background:{T['border']}; border-radius:4px; min-height:20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}")

    def _make_card(self, name, td):
        active = (name == current_theme_name)
        f = QFrame(self._container)
        f.setFixedSize(self.CARD_W, self.CARD_H)
        f.setCursor(Qt.CursorShape.PointingHandCursor)
        f.setStyleSheet(
            f"QFrame {{ background:{td['card']}; border:2px solid {'#ffffff' if active else td['border']}; border-radius:9px; }}"
            f"QFrame:hover {{ border-color:{td['sync']}; }}")
        lay = QVBoxLayout(f); lay.setContentsMargins(10,8,10,6); lay.setSpacing(4)
        nl = QLabel(name)
        nl.setStyleSheet(f"color:{td['text']}; font-size:11px; font-weight:600; border:none; background:transparent;")
        nl.setWordWrap(True); lay.addWidget(nl)
        sr = QHBoxLayout(); sr.setSpacing(5); sr.setContentsMargins(0,0,0,0)
        for role in ("bg","start","stop","sync","handoff"):
            dot = QLabel(); dot.setFixedSize(13,13)
            dot.setStyleSheet(f"background:{td[role]}; border-radius:6px; border:1px solid rgba(0,0,0,.15);")
            sr.addWidget(dot)
        sr.addStretch()
        badge = QLabel("dark" if td.get("appearance","dark")=="dark" else "light")
        badge.setStyleSheet(f"color:{td['muted']}; font-size:9px; border:none; background:transparent;")
        sr.addWidget(badge); lay.addLayout(sr)
        if active:
            al = QLabel("  active")
            al.setStyleSheet(f"color:{td['start']}; font-size:9px; border:none; background:transparent;")
            lay.addWidget(al)
        f.mousePressEvent = lambda e, n=name: self._pick(n)
        f._theme_name = name; f._theme_data = td
        return f

    def _pick(self, name):
        p = self.parent()
        if p and hasattr(p, "apply_theme"):
            p.apply_theme(name)
        self.accept()

    def _rebuild(self):
        q    = self._search.text().strip().lower()
        mode = self._mode.currentIndex()
        visible = []
        for c in self._all_cards:
            td  = c._theme_data; app = td.get("appearance","dark")
            ok  = ((not q or q in c._theme_name.lower()) and
                   (mode==0 or (mode==1 and app=="dark") or (mode==2 and app=="light")))
            c.setVisible(ok)
            if ok: visible.append(c); c.setParent(self._container)
        vw   = self._scroll.viewport().width()
        cols = max(1, (vw - self.GAP) // (self.CARD_W + self.GAP))
        rows = max(1, -(-len(visible) // cols))
        h    = rows * (self.CARD_H + self.GAP) + self.GAP
        self._container.setMinimumHeight(h); self._container.setFixedHeight(h)
        for i, c in enumerate(visible):
            row, col = divmod(i, cols)
            c.move(self.GAP + col*(self.CARD_W+self.GAP),
                   self.GAP + row*(self.CARD_H+self.GAP))
            c.show()

    def resizeEvent(self, e):
        super().resizeEvent(e); self._rebuild()

    def _create_custom(self):
        dlg = CustomThemeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._all_cards = [self._make_card(n,td) for n,td in THEMES.items()]
            self._rebuild()
            p = self.parent()
            if p and hasattr(p,"toast"): p.toast("Custom theme created!", T["start"])


class CustomThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Custom Theme"); self.resize(440, 600)
        self.setStyleSheet(
            f"QDialog {{ background:{T['bg']}; }}"
            f"QWidget {{ background:{T['bg']}; color:{T['text']}; }}"
            f"QLabel  {{ background:transparent; }}"
            f"QLineEdit {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:5px 8px; }}"
            f"QPushButton {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:5px 12px; }}"
            f"QPushButton:hover {{ background:{T['border']}; }}")

        root = QVBoxLayout(self); root.setContentsMargins(20,20,20,20); root.setSpacing(10)
        nr = QHBoxLayout(); nr.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("My Custom Theme")
        nr.addWidget(self.name_edit); root.addLayout(nr)
        mr = QHBoxLayout(); mr.addWidget(QLabel("Mode:"))
        from PyQt6.QtWidgets import QComboBox
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["Dark","Light"])
        mr.addWidget(self.mode_combo); mr.addStretch(); root.addLayout(mr)

        self.color_btns: dict[str, QPushButton] = {}
        colors = [("bg","Background"),("card","Card"),("border","Border"),
                  ("text","Text"),("muted","Muted Text"),("start","Start / Green"),
                  ("stop","Stop / Red"),("sync","Sync / Blue"),("handoff","Handoff / Orange")]
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background:{T['bg']}; border:none; }}")
        cw = QWidget(); cw.setStyleSheet(f"background:{T['bg']};")
        cl = QVBoxLayout(cw); cl.setSpacing(8)
        for key, label in colors:
            r = QHBoxLayout(); r.setSpacing(10)
            cb = QPushButton(); cb.setFixedSize(30,30); cb.setCursor(Qt.CursorShape.PointingHandCursor)
            initial = T.get(key,"#ffffff")
            cb.setStyleSheet(f"QPushButton {{ background:{initial}; border:2px solid {T['border']}; border-radius:4px; }}")
            cb.clicked.connect(lambda _, k=key: self._pick(k))
            r.addWidget(cb); r.addWidget(QLabel(label)); r.addStretch()
            cl.addLayout(r); self.color_btns[key] = cb
        scroll.setWidget(cw); root.addWidget(scroll, 1)

        br = QHBoxLayout(); br.addStretch()
        cancel_b = QPushButton("Cancel"); cancel_b.clicked.connect(self.reject); br.addWidget(cancel_b)
        create_b = QPushButton("Create Theme")
        create_b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; font-weight:700; }}")
        create_b.clicked.connect(self._create); br.addWidget(create_b)
        root.addLayout(br)

    def _pick(self, key):
        style = self.color_btns[key].styleSheet()
        m = re.search(r'background:\s*([^;]+)', style)
        initial = m.group(1).strip() if m else "#ffffff"
        dlg = QColorDialog(QColor(initial), self)
        if dlg.exec() == QColorDialog.DialogCode.Accepted:
            hex_c = dlg.selectedColor().name()
            self.color_btns[key].setStyleSheet(
                f"QPushButton {{ background:{hex_c}; border:2px solid {T['border']}; border-radius:4px; }}")

    def _create(self):
        name = self.name_edit.text().strip()
        if not name: QMessageBox.warning(self,"Error","Enter a theme name."); return
        if name in THEMES: QMessageBox.warning(self,"Error","Name already exists."); return
        td: dict = {"appearance": "dark" if self.mode_combo.currentText()=="Dark" else "light"}
        for key, cb in self.color_btns.items():
            m = re.search(r'background:\s*([^;]+)', cb.styleSheet())
            td[key] = m.group(1).strip() if m else "#ffffff"
        THEMES[name] = td
        s = load_settings(); s.setdefault("custom_themes",{})[name] = td; save_settings(s)
        self.accept()
