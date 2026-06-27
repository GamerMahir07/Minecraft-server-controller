"""ui/widgets.py — shared widget helpers"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QColor, QFont, QTextCharFormat

from core.themes import T
from core.server import perf
from core.constants import MONO_FONT

logger = logging.getLogger(__name__)


def make_scroll():
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    inner = QWidget()
    scroll.setWidget(inner)
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(8)
    return scroll, inner, lay


def card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setObjectName("card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(12, 10, 12, 10)
    lay.setSpacing(6)
    return f


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setObjectName("hline")
    return line


def lbl(text: str, muted: bool = False, header: bool = False) -> QLabel:
    l = QLabel(text)
    if header:
        l.setObjectName("header")
    elif muted:
        l.setObjectName("muted")
    l.setWordWrap(True)
    return l


def btn(text: str, obj_name: str = "", parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    if obj_name:
        b.setObjectName(obj_name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class LogWidget(QTextEdit):
    """Auto-scrolling, read-only log widget. Styled purely via QSS (no inline setStyleSheet)."""

    MAX_LINES = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setFont(QFont(MONO_FONT.split(",")[0], 10))
        self.setObjectName("log_widget")
        self._line_count = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def append_line(self, text: str, color: str | None = None):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color if color else T["text"]))
        cur.setCharFormat(fmt)
        cur.insertText(text.rstrip() + "\n")
        self._line_count += 1
        if self._line_count > self.MAX_LINES:
            self._trim()
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _trim(self):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.Start)
        cur.movePosition(
            QTextCursor.MoveOperation.Down,
            QTextCursor.MoveMode.KeepAnchor,
            self._line_count // 4,
        )
        cur.removeSelectedText()
        self._line_count = max(0, self._line_count - self._line_count // 4)


class PerfStrip(QFrame):
    """8-stat performance grid."""

    STATS = [
        ("tps",     "TPS"),
        ("players", "Players"),
        ("ram_srv", "Srv RAM"),
        ("ram_pct", "RAM %"),
        ("cpu_srv", "Srv CPU"),
        ("cpu_sys", "Sys CPU"),
        ("uptime",  "Uptime"),
        ("threads", "Threads"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("perf_strip")
        self.setFixedHeight(80)
        self._val_labels: dict[str, QLabel] = {}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        hdr = QLabel("PERFORMANCE")
        hdr.setObjectName("header")
        outer.addWidget(hdr)
        outer.addWidget(hline())

        grid = QGridLayout()
        grid.setSpacing(4)
        COLS = 4
        for i, (key, label) in enumerate(self.STATS):
            row, col = i // COLS, i % COLS
            cell = QFrame()
            cell.setObjectName("card")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(8, 5, 8, 5)
            cl.setSpacing(2)
            lbl_w = QLabel(label)
            lbl_w.setObjectName("muted")
            cl.addWidget(lbl_w)
            val_lbl = QLabel("--")
            val_lbl.setObjectName("perf_val")
            cl.addWidget(val_lbl)
            self._val_labels[key] = val_lbl
            grid.addWidget(cell, row, col)
        for c in range(COLS):
            grid.setColumnStretch(c, 1)
        outer.addLayout(grid)

    def update_perf(self):
        for key, lbl_w in self._val_labels.items():
            val = perf.get(key, "--")
            color = T["sync"]
            if key == "tps":
                try:
                    v = float(val)
                    color = T["start"] if v >= 18 else T["handoff"] if v >= 15 else T["stop"]
                except Exception:
                    color = T["muted"]
            elif key in ("cpu_sys", "cpu_srv", "ram_pct"):
                try:
                    n = float(str(val).replace("%", "").split()[0])
                    color = T["start"] if n < 60 else T["handoff"] if n < 85 else T["stop"]
                except Exception:
                    color = T["muted"]
            elif key in ("uptime", "threads"):
                color = T["muted"]
            elif key in ("ram_srv", "ram_used"):
                color = T["handoff"]
            lbl_w.setText(str(val))
            lbl_w.setStyleSheet(
                f"color:{color}; font-size:17px; font-weight:700; background:transparent;"
            )


class ToastWidget(QLabel):
    """Bottom-right toast notification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(46)
        self.setMinimumWidth(260)
        self.setMaximumWidth(500)
        self.setWordWrap(True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_msg(self, msg: str, color: str, ms: int = 3000):
        self.setText(msg)
        self.setStyleSheet(
            f"background:{T['card']}; color:{color}; font-weight:700; font-size:12px;"
            f" border:2px solid {color}; border-radius:10px; padding:6px 16px;"
        )
        self.adjustSize()
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            self.move(pw - self.width() - 20, ph - self.height() - 52)
        self.raise_()
        self.show()
        self._timer.stop()
        self._timer.start(ms)
