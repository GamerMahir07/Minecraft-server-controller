"""ui/main_window.py"""
import logging, os, sys, threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFrame, QApplication, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from core.constants import ICON_PATH, FIRST_RUN_FLAG, APP_VERSION, _ADDONS_DIR
from core.settings import load_settings, update_setting
import core.themes as _themes_mod
import core.server as _server_mod

logger = logging.getLogger(__name__)
WIN: "MainWindow | None" = None

# Windows: set a unique AppUserModelID before anything else so the taskbar
# groups under our icon instead of the generic Python icon.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            u"GamerMahir07.MCCTRL.App"
        )
    except Exception:
        pass


class ServerSignals(QObject):
    sig_log    = pyqtSignal(str, str)
    sig_perf   = pyqtSignal()
    sig_status = pyqtSignal(str, str)
    sig_toast  = pyqtSignal(str, str, int)
    sig_ips    = pyqtSignal(str, str)
    sig_set_addr = pyqtSignal(str)

    def toast(self, msg: str, color: str, ms: int = 3000):
        self.sig_toast.emit(msg, color, ms)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MC CTRL  v{APP_VERSION}")
        self.setMinimumSize(1000, 680)
        self.resize(1280, 820)
        if ICON_PATH and os.path.exists(ICON_PATH):
            icon = QIcon(ICON_PATH)
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
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0); main_lay.setSpacing(0)

        # Top bar
        topbar = QFrame(); topbar.setObjectName("topbar"); topbar.setFixedHeight(50)
        tb = QHBoxLayout(topbar); tb.setContentsMargins(14, 0, 14, 0); tb.setSpacing(8)

        title_lbl = QLabel("MC CTRL")
        tf = title_lbl.font(); tf.setPointSize(14); tf.setBold(True); title_lbl.setFont(tf)
        title_lbl.setStyleSheet(f"color:{_themes_mod.T['text']}; background:transparent;")
        tb.addWidget(title_lbl)

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet(f"color:{_themes_mod.T['muted']}; font-size:11px; background:transparent;")
        tb.addWidget(ver_lbl)
        tb.addStretch()

        self.status_dot = QLabel("●")
        sf = self.status_dot.font(); sf.setPointSize(14); self.status_dot.setFont(sf)
        self.status_dot.setStyleSheet(f"color:{_themes_mod.T['stop']}; background:transparent;")
        tb.addWidget(self.status_dot)

        self.status_lbl = QLabel("Stopped")
        self.status_lbl.setStyleSheet(f"color:{_themes_mod.T['stop']}; font-size:12px; font-weight:600; background:transparent;")
        tb.addWidget(self.status_lbl)
        tb.addSpacing(8)

        settings_btn = QPushButton("Settings")
        settings_btn.setFixedHeight(28)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{_themes_mod.T['muted']};"
            f" border:1px solid {_themes_mod.T['border']}; border-radius:6px; padding:0 10px; font-size:11px; }}"
            f"QPushButton:hover {{ background:{_themes_mod.T['border']}; color:{_themes_mod.T['text']}; }}")
        settings_btn.clicked.connect(self._open_settings)
        tb.addWidget(settings_btn)

        theme_btn = QPushButton(f"Theme: {_themes_mod.current_theme_name[:18]}")
        self._theme_btn = theme_btn
        theme_btn.setFixedHeight(28)
        theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{_themes_mod.T['muted']};"
            f" border:1px solid {_themes_mod.T['border']}; border-radius:6px; padding:0 10px; font-size:11px; }}"
            f"QPushButton:hover {{ background:{_themes_mod.T['border']}; color:{_themes_mod.T['text']}; }}")
        theme_btn.clicked.connect(self._open_theme_picker)
        tb.addWidget(theme_btn)
        main_lay.addWidget(topbar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        if load_settings().get("side_tabs", False):
            self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        main_lay.addWidget(self.tabs, 1)

        from .dashboard   import DashboardTab
        from .server_info import ServerInfoTab
        from .docker_tab  import DockerTab
        from .modpacks    import ModpacksTab
        from .settings_tab import SettingsTab

        self.dash_tab     = DashboardTab()
        self.srvinfo_tab  = ServerInfoTab()
        self.docker_tab   = DockerTab()
        self.modpacks_tab = ModpacksTab()
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.dash_tab,     "Dashboard")
        self.tabs.addTab(self.srvinfo_tab,  "Server Info")
        self.tabs.addTab(self.docker_tab,   "Docker")
        self.tabs.addTab(self.modpacks_tab, "Modpacks")
        self.tabs.addTab(self.settings_tab, "Settings")

        from .widgets import ToastWidget
        self._toast_widget = ToastWidget(central)

        # Status bar — IP footer
        sb = QStatusBar(); sb.setFixedHeight(24)
        sb.setStyleSheet(
            f"QStatusBar {{ background:{_themes_mod.T['card']};"
            f" color:{_themes_mod.T['muted']}; border-top:1px solid {_themes_mod.T['border']}; font-size:10px; }}")
        self.setStatusBar(sb)
        self._ip_lbl = QLabel("LAN: detecting...  |  EXT: detecting...")
        self._ip_lbl.setStyleSheet(f"color:{_themes_mod.T['muted']}; font-size:10px; padding:0 8px; background:transparent;")
        sb.addWidget(self._ip_lbl, 1)

        copy_lan = QPushButton("Copy LAN")
        copy_lan.setFixedHeight(18)
        copy_lan.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {_themes_mod.T['start']}; color:{_themes_mod.T['start']}; border-radius:4px; padding:0 6px; font-size:9px; }}")
        copy_lan.clicked.connect(lambda: (QApplication.clipboard().setText(self._lan_ip), self.toast(f"Copied: {self._lan_ip}", _themes_mod.T["start"])))
        sb.addPermanentWidget(copy_lan)

        copy_ext = QPushButton("Copy EXT")
        copy_ext.setFixedHeight(18)
        copy_ext.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {_themes_mod.T['sync']}; color:{_themes_mod.T['sync']}; border-radius:4px; padding:0 6px; font-size:9px; }}")
        copy_ext.clicked.connect(lambda: (QApplication.clipboard().setText(self._ext_ip), self.toast(f"Copied: {self._ext_ip}", _themes_mod.T["sync"])))
        sb.addPermanentWidget(copy_ext)

        self._lan_ip = "..."
        self._ext_ip = "..."
        self._start_ip_detection()

        # Perf tick
        self._perf_timer = QTimer(self)
        self._perf_timer.setInterval(2000)
        self._perf_timer.timeout.connect(self._tick_perf)
        self._perf_timer.start()

        # Update checker
        from core.updater import UpdateCheckerThread
        self._upd = UpdateCheckerThread()
        self._upd.update_found.connect(
            lambda v, u: self.toast(f"Update v{v} available -> {u}", _themes_mod.T["handoff"], 8000))
        self._upd.start()

        self.apply_theme(_themes_mod.current_theme_name, emit_toast=False)

    def toast(self, msg: str, color: str, ms: int = 3000):
        self._signals.sig_toast.emit(msg, color, ms)

    def apply_glossy(self, enabled: bool):
        update_setting("glossy_ui", enabled)
        self.apply_theme(_themes_mod.current_theme_name, emit_toast=False)
        self.toast("Glossy UI on" if enabled else "Glossy UI off", _themes_mod.T["sync"])

    def apply_side_tabs(self, enabled: bool):
        update_setting("side_tabs", enabled)
        pos = QTabWidget.TabPosition.West if enabled else QTabWidget.TabPosition.North
        self.tabs.setTabPosition(pos)
        self.apply_theme(_themes_mod.current_theme_name, emit_toast=False)
        self.toast("Tabs: left side" if enabled else "Tabs: top", _themes_mod.T["sync"])

    def apply_theme(self, name: str, emit_toast: bool = True):
        from core.themes import THEMES, _resolve_theme, _qss
        if name not in THEMES:
            return
        td = _resolve_theme(name)
        _themes_mod.T.clear(); _themes_mod.T.update(td)
        _themes_mod.current_theme_name = name
        update_setting("theme", name)
        s = load_settings()
        glossy = s.get("glossy_ui", False)
        side_tabs = s.get("side_tabs", False)
        QApplication.instance().setStyleSheet(_qss(td, glossy=glossy, side_tabs=side_tabs))
        self._theme_btn.setText(f"Theme: {name[:18]}")
        if emit_toast:
            self.toast(f"Theme: {name}", td["sync"])

    def _on_log(self, text: str, cat: str):
        self.dash_tab.log(text, cat)

    def _on_perf(self):
        self.dash_tab.update_perf()

    def _on_status(self, text: str, color: str):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600; background:transparent;")
        self.status_dot.setStyleSheet(f"color:{color}; font-size:14px; background:transparent;")

    def _show_toast(self, msg: str, color: str, ms: int):
        self._toast_widget.show_msg(msg, color, ms)

    def _on_ips(self, local: str, ext: str):
        self._lan_ip = local
        self._ext_ip = ext
        self._ip_lbl.setText(f"LAN: {local}  |  EXT: {ext}")

    def _on_set_addr(self, addr: str):
        self.dash_tab.set_playit_addr(addr)

    def _tick_perf(self):
        from core.server import perf_running, perf_loop, server_proc
        if server_proc is not None and server_proc.poll() is None:
            if not perf_running:
                threading.Thread(target=perf_loop, daemon=True).start()
        self._on_perf()

    def _open_theme_picker(self):
        from .theme_picker import ThemePickerDialog
        ThemePickerDialog(self).exec()

    def _open_settings(self):
        self.tabs.setCurrentWidget(self.settings_tab)

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
                ext_ip = urllib.request.urlopen("https://api.ipify.org", timeout=6).read().decode().strip()
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
            r = QMessageBox.question(self, "Server Running",
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
    app.setFont(QFont("Segoe UI", 10))

    if ICON_PATH and os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    if not os.path.exists(FIRST_RUN_FLAG):
        from .first_run import FirstRunWizard
        FirstRunWizard().exec()

    WIN = MainWindow()
    WIN.show()

    def _print_banner():
        banner = [
            " ",
            "  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗      ",
            "  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║      ",
            "  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║      ",
            "  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║      ",
            "  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗ ",
            "  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ",
            f"  MC CTRL  ·  v{APP_VERSION}  ·  {datetime.now().strftime('%A %B %d %Y  %H:%M')} ",
            " ",
        ]
        for line in banner:
            WIN._signals.sig_log.emit(line, "muted")

    def _deferred_init():
        """Everything that can wait until after the window is visible."""
        def _load_addons():
            from core.addons import _load_all_addons
            _load_all_addons()
        threading.Thread(target=_load_addons, daemon=True).start()

    # Defer so the window paints first, mirroring the legacy app.after(...) pattern.
    QTimer.singleShot(300, _print_banner)
    QTimer.singleShot(400, _deferred_init)

    sys.exit(app.exec())
