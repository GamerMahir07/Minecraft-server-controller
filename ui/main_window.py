"""ui/main_window.py"""
import logging, os, sys, threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QStatusBar,
    QMessageBox, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QPainter, QPainterPath

from core.constants import ICON_PATH, FIRST_RUN_FLAG, APP_VERSION
from core.settings import load_settings, update_setting
import core.themes as _themes_mod
import core.server as _server_mod

logger = logging.getLogger(__name__)
WIN: "MainWindow | None" = None

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "GamerMahir07.MCCTRL.App")
    except Exception:
        pass


# ── Signals ───────────────────────────────────────────────────────────────────
class ServerSignals(QObject):
    sig_log      = pyqtSignal(str, str)
    sig_perf     = pyqtSignal()
    sig_status   = pyqtSignal(str, str)
    sig_toast    = pyqtSignal(str, str, int)
    sig_ips      = pyqtSignal(str, str)
    sig_set_addr = pyqtSignal(str)

    def toast(self, msg: str, color: str, ms: int = 3000):
        self.sig_toast.emit(msg, color, ms)


# ── Sidebar nav button ────────────────────────────────────────────────────────
class _NavBtn(QPushButton):
    """Pill-style vertical nav item — no rotation, icon + label, optional badge."""

    def __init__(self, icon_char: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_char = icon_char
        self._label     = label
        self._badge     = 0
        self._selected  = False
        self.setCheckable(False)
        self.setFixedHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

    def set_selected(self, v: bool):
        self._selected = v
        self.update()

    def set_badge(self, n: int):
        self._badge = n
        self.update()

    def paintEvent(self, _):
        T = _themes_mod.T
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(6, 3, -6, -3)

        if self._selected:
            path = QPainterPath()
            path.addRoundedRect(r.x(), r.y(), r.width(), r.height(), 12, 12)
            p.fillPath(path, QColor(T["sync"] + "28"))
            p.setPen(QColor(T["sync"]))
        else:
            p.setPen(QColor(T["muted"]))

        # Icon
        f = QFont("Segoe UI", 11)
        p.setFont(f)
        p.drawText(r.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, self._icon_char)

        # Label
        f2 = QFont("Segoe UI", 10)
        if self._selected: f2.setWeight(QFont.Weight.Bold)
        p.setFont(f2)
        p.drawText(r.adjusted(34, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, self._label)

        # Badge
        if self._badge > 0:
            bx = r.right() - 6
            by = r.top() + 6
            br = 9
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#ef4444"))
            p.drawEllipse(int(bx - br), int(by - br), br * 2, br * 2)
            p.setPen(QColor("#ffffff"))
            f3 = QFont("Segoe UI", 7); f3.setBold(True); p.setFont(f3)
            p.drawText(int(bx - br), int(by - br), br * 2, br * 2,
                       Qt.AlignmentFlag.AlignCenter, str(self._badge))
        p.end()


# ── Sidebar ───────────────────────────────────────────────────────────────────
class _Sidebar(QFrame):
    tab_changed = pyqtSignal(int)

    _TABS = [
        ("⬡", "Dashboard"),
        ("☰", "Server Info"),
        ("⬡", "Docker"),
        ("⬡", "Modpacks"),
        ("⚙", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(150)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(4)

        # Branding
        brand = QLabel("MC CTRL")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(
            f"color:{_themes_mod.T['sync']}; font-size:13px; font-weight:700;"
            " background:transparent; padding:6px 0 10px 0;")
        lay.addWidget(brand)

        self._btns: list[_NavBtn] = []
        for i, (ic, lb) in enumerate(self._TABS):
            b = _NavBtn(ic, lb)
            b.clicked.connect(lambda _, idx=i: self._select(idx))
            lay.addWidget(b)
            self._btns.append(b)

        lay.addStretch()

        # Server status pill at bottom
        self._status_pill = QLabel("● Stopped")
        self._status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_pill.setFixedHeight(28)
        self._status_pill.setStyleSheet(
            f"color:{_themes_mod.T['stop']}; font-size:10px; font-weight:600;"
            f" background:{_themes_mod.T['card']}; border-radius:10px;"
            " border:none; padding:0 8px; background:transparent;")
        lay.addWidget(self._status_pill)

        self._select(0)

    def _select(self, idx: int):
        for i, b in enumerate(self._btns):
            b.set_selected(i == idx)
        self.tab_changed.emit(idx)

    def set_status(self, text: str, color: str):
        self._status_pill.setText(f"● {text}")
        self._status_pill.setStyleSheet(
            f"color:{color}; font-size:10px; font-weight:600; background:transparent;")

    def select(self, idx: int):
        self._select(idx)


# ── Main window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MC CTRL  v{APP_VERSION}")
        self.setMinimumSize(980, 660)
        self.resize(1300, 840)
        if ICON_PATH and os.path.exists(ICON_PATH):
            icon = QIcon(ICON_PATH)
            # On Linux/Mac also try loading the .png variant for better rendering
            from core.constants import IS_WIN, _ASSETS_DIR, _BASE_DIR
            if not IS_WIN:
                for _p in (os.path.join(_ASSETS_DIR,"icon.png"),
                            os.path.join(_BASE_DIR,"icon.png")):
                    if os.path.exists(_p):
                        icon = QIcon(_p); break
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)

        self._signals = ServerSignals()
        _server_mod.signals = self._signals
        self._signals.sig_log.connect(self._on_log)
        self._signals.sig_perf.connect(self._on_perf)
        self._signals.sig_status.connect(self._on_status)
        self._signals.sig_toast.connect(self._show_toast)
        self._signals.sig_ips.connect(self._on_ips)
        self._signals.sig_set_addr.connect(self._on_set_addr)

        central = QWidget(); central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = _Sidebar()
        root.addWidget(self._sidebar)

        # Sidebar/content separator
        sep = QFrame(); sep.setFixedWidth(1); sep.setObjectName("hline")
        root.addWidget(sep)

        # ── Content area ──────────────────────────────────────────────────────
        content_wrap = QWidget()
        cw_lay = QVBoxLayout(content_wrap)
        cw_lay.setContentsMargins(0, 0, 0, 0); cw_lay.setSpacing(0)
        root.addWidget(content_wrap, 1)

        # Top bar
        topbar = QFrame(); topbar.setObjectName("topbar"); topbar.setFixedHeight(46)
        tb = QHBoxLayout(topbar); tb.setContentsMargins(14, 0, 14, 0); tb.setSpacing(8)

        self._page_title = QLabel("Dashboard")
        f = self._page_title.font(); f.setPointSize(12); f.setBold(True)
        self._page_title.setFont(f)
        self._page_title.setStyleSheet(f"color:{_themes_mod.T['text']}; background:transparent;")
        tb.addWidget(self._page_title); tb.addStretch()

        self._ip_lbl = QLabel("LAN: --  |  EXT: --")
        self._ip_lbl.setStyleSheet(
            f"color:{_themes_mod.T['muted']}; font-size:10px; background:transparent;")
        tb.addWidget(self._ip_lbl)

        for label, attr in [("Copy LAN", "_copy_lan_btn"), ("Copy EXT", "_copy_ext_btn")]:
            b = QPushButton(label); b.setFixedHeight(22)
            b.setStyleSheet(
                f"QPushButton {{ background:transparent; border:1px solid {_themes_mod.T['border']};"
                f" color:{_themes_mod.T['muted']}; border-radius:5px; padding:0 6px; font-size:9px; }}"
                f"QPushButton:hover {{ border-color:{_themes_mod.T['sync']}; color:{_themes_mod.T['sync']}; }}")
            tb.addWidget(b); setattr(self, attr, b)

        self._copy_lan_btn.clicked.connect(
            lambda: (QApplication.clipboard().setText(self._lan_ip),
                     self.toast(f"Copied: {self._lan_ip}", _themes_mod.T["start"])))
        self._copy_ext_btn.clicked.connect(
            lambda: (QApplication.clipboard().setText(self._ext_ip),
                     self.toast(f"Copied: {self._ext_ip}", _themes_mod.T["sync"])))

        theme_btn = QPushButton(f"◑  {_themes_mod.current_theme_name[:16]}")
        self._theme_btn = theme_btn
        theme_btn.setFixedHeight(26)
        theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{_themes_mod.T['muted']};"
            f" border:1px solid {_themes_mod.T['border']}; border-radius:6px;"
            f" padding:0 10px; font-size:10px; }}"
            f"QPushButton:hover {{ color:{_themes_mod.T['text']};"
            f" border-color:{_themes_mod.T['sync']}; }}")
        theme_btn.clicked.connect(self._open_theme_picker)
        tb.addWidget(theme_btn)
        cw_lay.addWidget(topbar)

        # Stacked pages
        self._stack = QStackedWidget()
        cw_lay.addWidget(self._stack, 1)

        from .dashboard    import DashboardTab
        from .server_info  import ServerInfoTab
        from .docker_tab   import DockerTab
        from .modpacks     import ModpacksTab
        from .settings_tab import SettingsTab

        self.dash_tab     = DashboardTab()
        self.srvinfo_tab  = ServerInfoTab()
        self.docker_tab   = DockerTab()
        self.modpacks_tab = ModpacksTab()
        self.settings_tab = SettingsTab(self)

        self._pages = [
            ("Dashboard",   self.dash_tab),
            ("Server Info", self.srvinfo_tab),
            ("Docker",      self.docker_tab),
            ("Modpacks",    self.modpacks_tab),
            ("Settings",    self.settings_tab),
        ]
        for _, w in self._pages:
            self._stack.addWidget(w)

        self._sidebar.tab_changed.connect(self._on_tab_changed)

        # Toast
        from .widgets import ToastWidget, PerfStrip
        self._toast_widget = ToastWidget(central)

        # ── Bottom perf bar (permanent, full width) ───────────────────────
        self._perf_bar = PerfStrip()
        cw_lay.addWidget(self._perf_bar)

        # Status bar (very thin, below perf bar)
        sb = QStatusBar(); sb.setFixedHeight(20)
        self.setStatusBar(sb)
        self._sb_lbl = QLabel("")
        self._sb_lbl.setStyleSheet(
            f"color:{_themes_mod.T['muted']}; font-size:9px; padding:0 8px; background:transparent;")
        sb.addWidget(self._sb_lbl, 1)

        self._lan_ip = "..."
        self._ext_ip = "..."
        self._start_ip_detection()

        self._perf_timer = QTimer(self)
        self._perf_timer.setInterval(2000)
        self._perf_timer.timeout.connect(self._tick_perf)
        self._perf_timer.start()

        from core.updater import UpdateCheckerThread
        self._upd = UpdateCheckerThread()
        self._upd.update_found.connect(
            lambda v, u: self.toast(f"Update v{v} available → {u}",
                                    _themes_mod.T["handoff"], 8000))
        self._upd.start()

        self.apply_theme(_themes_mod.current_theme_name, emit_toast=False)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def toast(self, msg: str, color: str, ms: int = 3000):
        self._signals.sig_toast.emit(msg, color, ms)

    def apply_side_tabs(self, enabled: bool):
        """Side tabs are always on now (sidebar replaces QTabWidget). No-op kept for compat."""
        update_setting("side_tabs", enabled)

    def apply_theme(self, name: str, emit_toast: bool = True):
        from core.themes import THEMES, _resolve_theme, _qss
        if name not in THEMES:
            return
        td = _resolve_theme(name)
        _themes_mod.T.clear(); _themes_mod.T.update(td)
        _themes_mod.current_theme_name = name
        update_setting("theme", name)
        QApplication.instance().setStyleSheet(_qss(td))
        self._theme_btn.setText(f"◑  {name[:16]}")
        if emit_toast:
            self.toast(f"Theme: {name}", td["sync"])

    def _on_tab_changed(self, idx: int):
        self._stack.setCurrentIndex(idx)
        title = self._pages[idx][0]
        self._page_title.setText(title)

    def _on_log(self, text: str, cat: str):
        self.dash_tab.log(text, cat)

    def _on_perf(self):
        self.dash_tab.update_perf()

    def _on_status(self, text: str, color: str):
        self._sidebar.set_status(text, color)
        self._sb_lbl.setText(f"Server: {text}")

    def _show_toast(self, msg: str, color: str, ms: int):
        self._toast_widget.show_msg(msg, color, ms)

    def _on_ips(self, local: str, ext: str):
        self._lan_ip = local; self._ext_ip = ext
        self._ip_lbl.setText(f"LAN: {local}  |  EXT: {ext}")

    def _on_set_addr(self, addr: str):
        self.dash_tab.set_playit_addr(addr)

    def _tick_perf(self):
        from core.server import perf_running, perf_loop, server_proc
        if server_proc is not None and server_proc.poll() is None:
            if not perf_running:
                threading.Thread(target=perf_loop, daemon=True).start()
        self._on_perf()
        self._perf_bar.update_perf()

    def _open_theme_picker(self):
        from .theme_picker import ThemePickerDialog
        ThemePickerDialog(self).exec()

    def _open_settings(self):
        self._sidebar.select(4)

    def _start_ip_detection(self):
        import socket, urllib.request
        def _work():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80)); lip = s.getsockname()[0]; s.close()
            except Exception:
                lip = "127.0.0.1"
            port = load_settings().get("server_port", "25565")
            local = f"{lip}:{port}"
            self._signals.sig_ips.emit(local, "detecting...")
            try:
                ext_ip = urllib.request.urlopen(
                    "https://api.ipify.org", timeout=6).read().decode().strip()
                ext = f"{ext_ip}:{port}"
            except Exception:
                ext = "unavailable"
            self._signals.sig_ips.emit(local, ext)
        threading.Thread(target=_work, daemon=True).start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        tw = self._toast_widget
        if tw.isVisible():
            cw = self.centralWidget()
            tw.move(cw.width() - tw.width() - 20, cw.height() - tw.height() - 52)

    def closeEvent(self, e):
        from core.server import server_proc, stop_server
        if server_proc is not None and server_proc.poll() is None:
            r = QMessageBox.question(
                self, "Server Running",
                "The Minecraft server is still running.\nStop it before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                e.ignore(); return
            if r == QMessageBox.StandardButton.Yes:
                threading.Thread(target=stop_server, daemon=True).start()
        e.accept()


def main():
    global WIN
    import sys
    from datetime import datetime
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from core.constants import UI_FONT
    app.setFont(QFont(UI_FONT.split(",")[0], 10))
    if ICON_PATH and os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    if not os.path.exists(FIRST_RUN_FLAG):
        from .first_run import FirstRunWizard
        FirstRunWizard().exec()

    WIN = MainWindow()
    WIN.show()

    def _print_banner():
        for line in [
            " ",
            "  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗      ",
            "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║      ",
            "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║      ",
            "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║      ",
            "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗ ",
            "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ",
            f"  MC CTRL  ·  v{APP_VERSION}  ·  {datetime.now().strftime('%A %B %d %Y  %H:%M')} ",
            " ",
        ]:
            WIN._signals.sig_log.emit(line, "muted")

    def _deferred_init():
        def _load():
            from core.addons import _load_all_addons
            _load_all_addons()
        threading.Thread(target=_load, daemon=True).start()

    QTimer.singleShot(300, _print_banner)
    QTimer.singleShot(400, _deferred_init)
    sys.exit(app.exec())
