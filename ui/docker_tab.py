"""ui/docker_tab.py — Docker management: status, quick-config, compose editor, controls, containers"""
import os, subprocess, threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QScrollArea, QPlainTextEdit, QLineEdit,
    QComboBox, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.themes import T
from core.settings import load_settings, update_setting
from core.constants import DEFAULT_SRV_PATH, CREATE_NO_WINDOW
from .widgets import make_scroll, card, hline, lbl, LogWidget

def _win():
    from .main_window import WIN
    return WIN

def _toast(msg, color=None):
    w = _win()
    if w: w.toast(msg, color or T["sync"])


# ── Compose template ─────────────────────────────────────────────────────────
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
      ONLINE_MODE: "true"
    ports:
      - "25565:25565"
      - "25575:25575"
    volumes:
      - ./world:/data/world
      - ./world_nether:/data/world_nether
      - ./world_the_end:/data/world_the_end
      - ./plugins:/data/plugins
      - ./config:/data/config
    restart: unless-stopped
    tty: true
    stdin_open: true
    healthcheck:
      test: mc-monitor status --host localhost || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
"""


class DockerTab(QWidget):
    _containers_signal    = pyqtSignal(list, str)
    _log_signal           = pyqtSignal(str, object)   # text, color|None
    _docker_status_signal = pyqtSignal(bool, str, str) # ok, version, compose_ver

    def __init__(self, parent=None):
        super().__init__(parent)
        self._containers_signal.connect(self._on_containers)
        self._log_signal.connect(self._on_log)
        self._docker_status_signal.connect(self._on_docker_status)
        self._docker_ok = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        scroll, inner, lay = make_scroll()
        root.addWidget(scroll)

        lay.addWidget(self._build_status())
        lay.addWidget(self._build_quick_config())
        lay.addWidget(self._build_compose())
        lay.addWidget(self._build_controls())
        lay.addWidget(self._build_containers())
        lay.addStretch()

    # ── Status ────────────────────────────────────────────────────────────────
    def _build_status(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Docker Status", header=True)); hdr.addStretch()
        refresh_b = QPushButton("Refresh"); refresh_b.setFixedSize(66, 24)
        refresh_b.clicked.connect(self._check_docker)
        hdr.addWidget(refresh_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        self._status_lbl = lbl("Checking Docker...", muted=True)
        self._ver_lbl    = lbl("", muted=True)
        self._compose_ver_lbl = lbl("", muted=True)
        c.layout().addWidget(self._status_lbl)
        c.layout().addWidget(self._ver_lbl)
        c.layout().addWidget(self._compose_ver_lbl)
        threading.Thread(target=self._check_docker, daemon=True).start()
        return c

    def _check_docker(self):
        ok, ver, cver = False, "", ""
        try:
            r = subprocess.run(["docker", "--version"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                ok = True; ver = r.stdout.strip()
        except Exception:
            pass
        try:
            r2 = subprocess.run(["docker", "compose", "version"],
                                capture_output=True, text=True, timeout=5)
            if r2.returncode == 0:
                cver = r2.stdout.strip()
        except Exception:
            # Fallback: old docker-compose standalone
            try:
                r3 = subprocess.run(["docker-compose", "--version"],
                                    capture_output=True, text=True, timeout=5)
                if r3.returncode == 0:
                    cver = r3.stdout.strip() + " (standalone)"
            except Exception:
                cver = "docker compose not found"
        self._docker_status_signal.emit(ok, ver, cver)

    def _on_docker_status(self, ok: bool, ver: str, cver: str):
        self._docker_ok = ok
        if ok:
            self._status_lbl.setText("Docker available")
            self._status_lbl.setStyleSheet(f"color:{T['start']}; background:transparent;")
        else:
            self._status_lbl.setText("Docker not found — install Docker Desktop or docker CLI")
            self._status_lbl.setStyleSheet(f"color:{T['stop']}; background:transparent;")
        self._ver_lbl.setText(ver)
        self._compose_ver_lbl.setText(cver)

    # ── Quick-config ──────────────────────────────────────────────────────────
    def _build_quick_config(self):
        c = card()
        c.layout().addWidget(lbl("Quick Config", header=True))
        c.layout().addWidget(hline())

        grid = QGridLayout(); grid.setSpacing(6)
        fields = [
            ("Server Type",   "docker_type",    ["PAPER","SPIGOT","FABRIC","FORGE","VANILLA","PURPUR","NEOFORGE"]),
            ("MC Version",    "docker_version",  ["LATEST","1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4"]),
            ("Memory",        "docker_ram",      ["1G","2G","4G","6G","8G","12G","16G"]),
            ("Difficulty",    "docker_diff",     ["peaceful","easy","normal","hard"]),
            ("Max Players",   "docker_maxplay",  ["10","20","50","100"]),
            ("RCON Password", "docker_rcon_pw",  None),
            ("Port",          "docker_port",     ["25565","25566","25567","19132"]),
            ("Container Name","docker_name",     None),
        ]
        s = load_settings()
        self._qc_widgets: dict[str, QWidget] = {}
        for i, (label, key, opts) in enumerate(fields):
            row, col = divmod(i, 2)
            pair = QFrame()
            pl = QVBoxLayout(pair); pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(2)
            pl.addWidget(lbl(label, muted=True))
            if opts:
                w = QComboBox(); w.addItems(opts)
                cur = s.get(key, opts[0])
                idx = w.findText(cur)
                if idx >= 0: w.setCurrentIndex(idx)
                else: w.insertItem(0, cur); w.setCurrentIndex(0)
            else:
                w = QLineEdit(str(s.get(key, "")))
                if "password" in key.lower() or "pw" in key.lower():
                    w.setEchoMode(QLineEdit.EchoMode.Password)
            pl.addWidget(w)
            self._qc_widgets[key] = w
            grid.addWidget(pair, row, col)

        c.layout().addLayout(grid)

        btn_row = QHBoxLayout()
        apply_b = QPushButton("Apply → Compose"); apply_b.setFixedHeight(28)
        apply_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        apply_b.clicked.connect(self._apply_quick_config)
        btn_row.addWidget(apply_b); btn_row.addStretch()
        c.layout().addLayout(btn_row)
        return c

    def _apply_quick_config(self):
        """Save quick-config values and regenerate compose YAML."""
        s = load_settings()
        vals = {}
        for key, w in self._qc_widgets.items():
            vals[key] = w.currentText() if isinstance(w, QComboBox) else w.text().strip()
            update_setting(key, vals[key])

        ram  = vals.get("docker_ram", "2G")
        typ  = vals.get("docker_type", "PAPER")
        ver  = vals.get("docker_version", "LATEST")
        diff = vals.get("docker_diff", "normal")
        mp   = vals.get("docker_maxplay", "20")
        pw   = vals.get("docker_rcon_pw", "changeme") or "changeme"
        port = vals.get("docker_port", "25565")
        name = vals.get("docker_name", "mc_server") or "mc_server"

        yaml = f"""\
services:
  minecraft:
    image: itzg/minecraft-server
    container_name: {name}
    environment:
      EULA: "TRUE"
      MEMORY: "{ram}"
      TYPE: "{typ}"
      VERSION: "{ver}"
      DIFFICULTY: "{diff}"
      MAX_PLAYERS: "{mp}"
      MOTD: "MC CTRL Server"
      ENABLE_RCON: "true"
      RCON_PASSWORD: "{pw}"
      ONLINE_MODE: "true"
    ports:
      - "{port}:{port}"
      - "25575:25575"
    volumes:
      - ./world:/data/world
      - ./world_nether:/data/world_nether
      - ./world_the_end:/data/world_the_end
      - ./plugins:/data/plugins
      - ./config:/data/config
    restart: unless-stopped
    tty: true
    stdin_open: true
    healthcheck:
      test: mc-monitor status --host localhost || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
"""
        self._compose_edit.setPlainText(yaml)
        _toast("Compose updated from quick-config", T["sync"])

    # ── Compose editor ────────────────────────────────────────────────────────
    def _build_compose(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("docker-compose.yml", header=True)); hdr.addStretch()
        for label, fn in [("Save", self._save_compose), ("Reset", self._reset_compose)]:
            b = QPushButton(label); b.setFixedWidth(52)
            if label == "Save":
                b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; }}")
            b.clicked.connect(fn); hdr.addWidget(b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        self._compose_edit = QPlainTextEdit()
        self._compose_edit.setFixedHeight(260)
        self._compose_edit.setObjectName("log_widget")
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        try:
            txt = open(os.path.join(path, "docker-compose.yml"), encoding="utf-8").read()
        except Exception:
            txt = _COMPOSE_TEMPLATE
        self._compose_edit.setPlainText(txt)
        c.layout().addWidget(self._compose_edit)
        return c

    def _save_compose(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        try:
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, "docker-compose.yml"), "w", encoding="utf-8") as f:
                f.write(self._compose_edit.toPlainText())
            _toast("docker-compose.yml saved!", T["start"])
        except Exception as ex:
            _toast(f"Save failed: {ex}", T["stop"])

    def _reset_compose(self):
        self._compose_edit.setPlainText(_COMPOSE_TEMPLATE)

    # ── Controls ──────────────────────────────────────────────────────────────
    def _build_controls(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Container Controls", header=True)); hdr.addStretch()
        clr = QPushButton("Clear"); clr.setFixedWidth(52)
        clr.clicked.connect(lambda: self._ctrl_log.clear())
        hdr.addWidget(clr)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        # Determine docker-compose command (new plugin vs standalone)
        btn_row = QHBoxLayout(); btn_row.setSpacing(4)
        CMDS = [
            ("Up",       "docker compose up -d",              T["start"],   "#000"),
            ("Down",     "docker compose down",               T["stop"],    "#fff"),
            ("Restart",  "docker compose restart",            T["handoff"], "#000"),
            ("Pull",     "docker compose pull",               T["sync"],    "#000"),
            ("Logs",     "docker compose logs --tail=60 -f",  T["muted"],   "#fff"),
            ("Stats",    "docker stats --no-stream",          T["border"],  T["text"]),
        ]
        for label, cmd, fc, tc in CMDS:
            b = QPushButton(label); b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton {{ background:{fc}; color:{tc}; border:none; border-radius:6px; font-weight:700; }}")
            b.clicked.connect(lambda _, c2=cmd: self._run_cmd(c2))
            btn_row.addWidget(b)
        c.layout().addLayout(btn_row)

        # RCON command input
        rcon_row = QHBoxLayout()
        self._rcon_edit = QLineEdit(); self._rcon_edit.setPlaceholderText("RCON command (e.g. list, say hello)")
        self._rcon_edit.returnPressed.connect(self._send_rcon)
        rcon_row.addWidget(self._rcon_edit)
        send_b = QPushButton("Send"); send_b.setFixedWidth(52)
        send_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; }}")
        send_b.clicked.connect(self._send_rcon)
        rcon_row.addWidget(send_b)
        c.layout().addLayout(rcon_row)

        self._ctrl_log = LogWidget(); self._ctrl_log.setFixedHeight(140)
        c.layout().addWidget(self._ctrl_log)
        return c

    def _run_cmd(self, cmd: str):
        self._ctrl_log.append_line(f"$ {cmd}", T["muted"])
        cwd = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        def _work():
            try:
                p = subprocess.Popen(
                    cmd, shell=True, cwd=cwd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, creationflags=CREATE_NO_WINDOW)
                for line in iter(p.stdout.readline, ""):
                    if line.strip(): self._log_signal.emit(f"  {line.rstrip()}", None)
                p.wait()
            except Exception as ex:
                self._log_signal.emit(f"  ERROR: {ex}", T["stop"])
        threading.Thread(target=_work, daemon=True).start()

    def _send_rcon(self):
        s = load_settings()
        cmd = self._rcon_edit.text().strip()
        if not cmd: return
        pw   = s.get("docker_rcon_pw", s.get("remote_password", "changeme"))
        port = "25575"
        name = s.get("docker_name", "mc_server")
        rcon_cmd = f'docker exec {name} rcon-cli --password "{pw}" --port {port} {cmd}'
        self._ctrl_log.append_line(f">> {cmd}", T["sync"])
        self._rcon_edit.clear()
        self._run_cmd(rcon_cmd)

    def _on_log(self, text: str, color):
        self._ctrl_log.append_line(text, color)

    # ── Container list ────────────────────────────────────────────────────────
    def _build_containers(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Running Containers", header=True)); hdr.addStretch()
        ref_b = QPushButton("Refresh"); ref_b.setFixedWidth(64)
        ref_b.clicked.connect(self._refresh_containers)
        hdr.addWidget(ref_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        self._cnt_inner = QWidget()
        self._cnt_lay   = QVBoxLayout(self._cnt_inner)
        self._cnt_lay.setContentsMargins(0, 0, 0, 0); self._cnt_lay.setSpacing(3)
        cs = QScrollArea(); cs.setWidgetResizable(True); cs.setFixedHeight(120)
        cs.setFrameShape(QFrame.Shape.NoFrame); cs.setWidget(self._cnt_inner)
        c.layout().addWidget(cs)
        self._refresh_containers()
        return c

    def _refresh_containers(self):
        self._clear_layout(self._cnt_lay)
        self._cnt_lay.addWidget(lbl("Refreshing...", muted=True))
        def _work():
            try:
                r = subprocess.run(
                    ['docker', 'ps', '--format',
                     '{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}'],
                    capture_output=True, text=True, timeout=6,
                    creationflags=CREATE_NO_WINDOW)
                lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
                self._containers_signal.emit(lines, "")
            except Exception as ex:
                self._containers_signal.emit([], str(ex))
        threading.Thread(target=_work, daemon=True).start()

    def _on_containers(self, lines: list, error: str):
        self._clear_layout(self._cnt_lay)
        if error:
            self._cnt_lay.addWidget(lbl(f"Docker error: {error}", muted=True)); return
        if not lines:
            self._cnt_lay.addWidget(lbl("No running containers", muted=True)); return
        for line in lines:
            parts = line.split("\t")
            name   = parts[0] if len(parts) > 0 else "?"
            status = parts[1] if len(parts) > 1 else ""
            ports  = parts[2] if len(parts) > 2 else ""
            image  = parts[3] if len(parts) > 3 else ""

            row = QFrame(); row.setObjectName("card")
            rl  = QHBoxLayout(row); rl.setContentsMargins(8, 5, 8, 5); rl.setSpacing(6)

            nl = QLabel(name); nl.setStyleSheet(f"color:{T['start']}; font-weight:700; background:transparent;")
            rl.addWidget(nl)
            il = QLabel(image[:24]); il.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            rl.addWidget(il)
            sl = QLabel(status); sl.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            rl.addWidget(sl)
            pl = QLabel(self._fmt_ports(ports)); pl.setStyleSheet(f"color:{T['sync']}; font-size:9px; background:transparent;")
            rl.addWidget(pl); rl.addStretch()

            for label, cmd, color in [
                ("Restart", f"docker restart {name}", T["handoff"]),
                ("Logs",    f"docker logs --tail=40 -f {name}", T["sync"]),
                ("Stop",    f"docker stop {name}", T["stop"]),
            ]:
                b = QPushButton(label); b.setFixedSize(52, 22)
                b.setStyleSheet(f"QPushButton {{ background:transparent; color:{color}; border:1px solid {color}; border-radius:4px; font-size:9px; }}")
                b.clicked.connect(lambda _, c2=cmd: self._run_cmd(c2))
                rl.addWidget(b)
            self._cnt_lay.addWidget(row)

    @staticmethod
    def _fmt_ports(raw: str) -> str:
        """Shorten port string: '0.0.0.0:25565->25565/tcp' → '25565'"""
        parts = []
        for seg in raw.split(","):
            seg = seg.strip()
            if "->" in seg:
                host = seg.split("->")[0].rsplit(":", 1)[-1]
                parts.append(host)
        return "  ".join(parts) if parts else raw[:30]

    @staticmethod
    def _clear_layout(lay):
        while lay.count():
            item = lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
