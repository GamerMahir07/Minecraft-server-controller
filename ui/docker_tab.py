"""ui/docker_tab.py — Docker tab: status, compose editor, container controls, container list"""
import os, subprocess, threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QScrollArea, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from core.themes import T
from core.settings import load_settings
from core.constants import DEFAULT_SRV_PATH, CREATE_NO_WINDOW
from .widgets import make_scroll, card, hline, lbl, LogWidget

def _win():
    from .main_window import WIN
    return WIN


_COMPOSE_TEMPLATE = """\
services:
  minecraft:
    image: itzg/minecraft-server
    container_name: mc_server
    environment:
      EULA: "TRUE"
      MEMORY: "2G"
      TYPE: "PAPER"
      VERSION: "LATEST"
      DIFFICULTY: "normal"
      MAX_PLAYERS: "20"
      MOTD: "MC CTRL Server"
      ENABLE_RCON: "true"
      RCON_PASSWORD: "changeme"
    ports:
      - "25565:25565"
      - "25575:25575"
    volumes:
      - ./world:/data/world
      - ./world_nether:/data/world_nether
      - ./world_the_end:/data/world_the_end
      - ./plugins:/data/plugins
    restart: unless-stopped
    tty: true
    stdin_open: true
"""


class DockerTab(QWidget):
    _containers_signal = pyqtSignal(list, str)
    _log_signal = pyqtSignal(str, str, object)  # text, log_name ("status"|"ctrl"), color
    _docker_status_signal = pyqtSignal(bool, str)  # available, text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._containers_signal.connect(self._on_containers_result)
        self._log_signal.connect(self._on_log_signal)
        self._docker_status_signal.connect(self._on_docker_status)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll, inner, lay = make_scroll()
        root.addWidget(scroll)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)

        # Docker status (spans both columns)
        grid.addWidget(self._build_status(), 0, 0, 1, 2)

        # Compose editor (spans both columns)
        grid.addWidget(self._build_compose(), 1, 0, 1, 2)

        # Controls (spans both columns)
        grid.addWidget(self._build_controls(), 2, 0, 1, 2)

        # Running containers (spans both columns)
        grid.addWidget(self._build_containers(), 3, 0, 1, 2)

        lay.addStretch()

    def _build_status(self):
        c = card()
        c.layout().addWidget(lbl("Docker Status", header=True))
        c.layout().addWidget(hline())
        self._status_lbl = lbl("Checking Docker...", muted=True)
        c.layout().addWidget(self._status_lbl)
        self._ver_lbl = lbl("", muted=True)
        c.layout().addWidget(self._ver_lbl)
        threading.Thread(target=self._check_docker, daemon=True).start()
        return c

    def _check_docker(self):
        try:
            r = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                self._docker_status_signal.emit(True, r.stdout.strip())
            else:
                raise FileNotFoundError
        except Exception:
            self._docker_status_signal.emit(False, "")

    def _on_docker_status(self, available: bool, version_text: str):
        if available:
            self._status_lbl.setText("Docker available")
            self._status_lbl.setStyleSheet(f"color:{T['start']}; background:transparent;")
            self._ver_lbl.setText(version_text)
        else:
            self._status_lbl.setText("Docker not found - install Docker Desktop or docker CLI")
            self._status_lbl.setStyleSheet(f"color:{T['stop']}; background:transparent;")
            self._ver_lbl.setText("")

    def _build_compose(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("docker-compose.yml", header=True)); hdr.addStretch()
        save_b = QPushButton("Save")
        save_b.setFixedWidth(52)
        save_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; }}")
        save_b.clicked.connect(self._save_compose); hdr.addWidget(save_b)
        reset_b = QPushButton("Reset"); reset_b.setFixedWidth(52)
        reset_b.clicked.connect(self._reset_compose); hdr.addWidget(reset_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        self._compose_edit = QPlainTextEdit()
        self._compose_edit.setFixedHeight(240)
        self._compose_edit.setStyleSheet(
            f"background:{T['bg']}; color:{T['text']}; border:1px solid {T['border']};"
            f" border-radius:6px; font-family:Consolas,monospace; font-size:11px; padding:4px;"
        )
        # Load existing or template
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        compose_path = os.path.join(path, "docker-compose.yml")
        try:
            txt = open(compose_path, encoding="utf-8").read()
        except Exception:
            txt = _COMPOSE_TEMPLATE
        self._compose_edit.setPlainText(txt)
        c.layout().addWidget(self._compose_edit)
        return c

    def _save_compose(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        compose_path = os.path.join(path, "docker-compose.yml")
        try:
            os.makedirs(path, exist_ok=True)
            with open(compose_path, "w", encoding="utf-8") as f:
                f.write(self._compose_edit.toPlainText())
            w = _win()
            if w: w.toast("docker-compose.yml saved!", T["start"])
        except Exception as ex:
            w = _win()
            if w: w.toast(f"Save failed: {ex}", T["stop"])

    def _reset_compose(self):
        self._compose_edit.setPlainText(_COMPOSE_TEMPLATE)

    def _build_controls(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Container Controls", header=True)); hdr.addStretch()
        clear_b = QPushButton("Clear"); clear_b.setFixedWidth(52)
        clear_b.clicked.connect(lambda: self._ctrl_log.clear())
        hdr.addWidget(clear_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        btn_row = QHBoxLayout()
        CMDS = [
            ("Up",      "docker compose up -d",         T["start"],   "#000"),
            ("Down",    "docker compose down",           T["stop"],    "#fff"),
            ("Restart", "docker compose restart",        T["handoff"], "#000"),
            ("Logs",    "docker compose logs --tail=50", T["sync"],    "#000"),
            ("Stats",   "docker stats --no-stream",      T["muted"],   "#fff"),
        ]
        for label, cmd_txt, fc, tc in CMDS:
            b = QPushButton(label); b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton {{ background:{fc}; color:{tc}; border:none; border-radius:6px; font-weight:700; }}")
            b.clicked.connect(lambda _, c2=cmd_txt: self._run_docker_cmd(c2, load_settings().get("srv_path", DEFAULT_SRV_PATH)))
            btn_row.addWidget(b)
        c.layout().addLayout(btn_row)

        self._ctrl_log = LogWidget(); self._ctrl_log.setFixedHeight(120)
        c.layout().addWidget(self._ctrl_log)
        return c

    def _run_docker_cmd(self, cmd: str, cwd: str):
        self._ctrl_log.append_line(f"$ {cmd}", T["muted"])
        def _work():
            try:
                r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                                   text=True, timeout=120, creationflags=CREATE_NO_WINDOW)
                for line in (r.stdout + r.stderr).splitlines():
                    if line.strip(): self._log_signal.emit(f"  {line}", "ctrl", None)
            except Exception as ex:
                self._log_signal.emit(f"  ERROR: {ex}", "ctrl", T["stop"])
        threading.Thread(target=_work, daemon=True).start()

    def _on_log_signal(self, text: str, which: str, color):
        if which == "ctrl":
            self._ctrl_log.append_line(text, color)

    def _build_containers(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Running Containers", header=True)); hdr.addStretch()
        refresh_b = QPushButton("Refresh"); refresh_b.setFixedWidth(64)
        refresh_b.clicked.connect(self._refresh_containers)
        hdr.addWidget(refresh_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        self._cnt_list_w = QWidget(); self._cnt_lay = QVBoxLayout(self._cnt_list_w)
        self._cnt_lay.setContentsMargins(0, 0, 0, 0); self._cnt_lay.setSpacing(3)
        cs = QScrollArea(); cs.setWidgetResizable(True); cs.setFixedHeight(110)
        cs.setFrameShape(QFrame.Shape.NoFrame); cs.setWidget(self._cnt_list_w)
        c.layout().addWidget(cs)
        self._refresh_containers()
        return c

    def _refresh_containers(self):
        while self._cnt_lay.count():
            item = self._cnt_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._cnt_lay.addWidget(lbl("Refreshing...", muted=True))

        def _work():
            try:
                r = subprocess.run(
                    "docker ps --format \"{{.Names}}\t{{.Status}}\t{{.Ports}}\"",
                    shell=True, capture_output=True, text=True, timeout=5,
                    creationflags=CREATE_NO_WINDOW)
                lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
                self._containers_signal.emit(lines, "")
            except Exception as ex:
                self._containers_signal.emit([], str(ex))
        threading.Thread(target=_work, daemon=True).start()

    def _on_containers_result(self, lines, error: str):
        while self._cnt_lay.count():
            item = self._cnt_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if error:
            self._cnt_lay.addWidget(lbl(f"Docker error: {error}", muted=True))
            return
        if not lines:
            self._cnt_lay.addWidget(lbl("No running containers", muted=True))
            return
        for line in lines:
            parts = line.split("\t")
            name = parts[0] if parts else "?"
            status = parts[1] if len(parts) > 1 else ""
            ports = parts[2] if len(parts) > 2 else ""
            row = QFrame(); row.setObjectName("card")
            rl = QHBoxLayout(row); rl.setContentsMargins(8, 5, 8, 5)
            nl = QLabel(name); nl.setStyleSheet(f"color:{T['start']}; font-weight:700; background:transparent;")
            rl.addWidget(nl)
            sl = QLabel(status); sl.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            rl.addWidget(sl)
            pl = QLabel(ports[:40]); pl.setStyleSheet(f"color:{T['sync']}; font-size:9px; background:transparent;")
            rl.addWidget(pl); rl.addStretch()
            stop_b = QPushButton("Stop"); stop_b.setFixedSize(46, 22)
            stop_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:4px; font-size:9px; }}")
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            stop_b.clicked.connect(lambda _, n=name, p=path: self._run_docker_cmd(f"docker stop {n}", p))
            rl.addWidget(stop_b)
            self._cnt_lay.addWidget(row)
