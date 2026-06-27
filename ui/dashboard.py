"""ui/dashboard.py — Dashboard tab with Control / playit.gg / Remote / Multi-Server / Presets sub-tabs"""
import os, re, subprocess, threading, time
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QScrollArea, QGridLayout, QFileDialog, QSlider,
    QTabWidget, QApplication, QSizePolicy, QComboBox, QTextEdit,
    QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor

from core.themes import T
from core.server import start_server, stop_server, sync_git, send_server_cmd, backup_to_zip
from core.settings import load_settings, update_setting, load_presets, save_preset, delete_preset
from core.constants import CREATE_NO_WINDOW, PLAYIT_ADDR_RE, PLAYIT_CLAIM_RE, DEFAULT_SRV_PATH, DEFAULT_JAVA_PATH, IS_WIN, IS_MAC
from .widgets import make_scroll, card, hline, lbl, btn, LogWidget


def _win():
    from .main_window import WIN
    return WIN


# ── Control sub-tab ───────────────────────────────────────────────────────────
class _ControlTab(QWidget):
    _world_size_signal = pyqtSignal(str)
    _git_signal        = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._world_size_signal.connect(self._on_world_size)
        self._git_signal.connect(self._on_git_status)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        scroll, _, lay = make_scroll()
        root.addWidget(scroll, 1)

        main = QHBoxLayout(); main.setSpacing(8)
        lay.addLayout(main)

        # Left column
        left = QWidget(); left.setFixedWidth(340)
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(6)
        main.addWidget(left)

        def _action_card(label_text, desc, obj, color, fn):
            c = card(); c.layout().setSpacing(6)
            row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
            tl = QLabel(label_text)
            tl.setStyleSheet(f"color:{color}; font-weight:700; font-size:13px; background:transparent;")
            row.addWidget(tl); row.addStretch()
            b = QPushButton("Run"); b.setObjectName(obj); b.setFixedSize(70, 30)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda: threading.Thread(target=fn, daemon=True).start())
            row.addWidget(b)
            c.layout().addLayout(row)
            dl = QLabel(desc); dl.setWordWrap(True)
            dl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
            c.layout().addWidget(dl)
            return c, b

        # ── Server controls card (start/stop combined) ──────────────────────
        srv_card = card(); srv_card.layout().setSpacing(8)
        srv_card.layout().addWidget(lbl("SERVER CONTROLS", header=True))
        srv_card.layout().addWidget(hline())

        start_row = QHBoxLayout(); start_row.setContentsMargins(0, 0, 0, 0)
        self.btn_start = QPushButton("▶  Start Server")
        self.btn_start.setObjectName("start"); self.btn_start.setFixedHeight(36)
        self.btn_start.setStyleSheet(
            f"QPushButton {{ background:{T['start']}; color:#000; border:none;"
            f" border-radius:8px; font-weight:700; font-size:12px; }}"
            f"QPushButton:hover {{ background:{T['start']}cc; }}")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(
            lambda: threading.Thread(target=start_server, daemon=True).start())

        self.btn_stop = QPushButton("■  Stop Server")
        self.btn_stop.setObjectName("stop"); self.btn_stop.setFixedHeight(36)
        self.btn_stop.setStyleSheet(
            f"QPushButton {{ background:{T['stop']}; color:#fff; border:none;"
            f" border-radius:8px; font-weight:700; font-size:12px; }}"
            f"QPushButton:hover {{ background:{T['stop']}cc; }}")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(
            lambda: threading.Thread(target=stop_server, daemon=True).start())

        start_row.addWidget(self.btn_start, 1)
        start_row.addSpacing(6)
        start_row.addWidget(self.btn_stop, 1)
        srv_card.layout().addLayout(start_row)
        ll.addWidget(srv_card)

        # ── Sync & Upload card (improved) ───────────────────────────────────
        sync_card = card(); sync_card.layout().setSpacing(6)
        sync_hdr = QHBoxLayout(); sync_hdr.setContentsMargins(0, 0, 0, 0)
        sync_hdr.addWidget(lbl("SYNC & UPLOAD", header=True)); sync_hdr.addStretch()
        self._git_status_lbl = QLabel("●  unknown")
        self._git_status_lbl.setStyleSheet(
            f"color:{T['muted']}; font-size:10px; background:transparent;")
        sync_hdr.addWidget(self._git_status_lbl)
        sync_card.layout().addLayout(sync_hdr)
        sync_card.layout().addWidget(hline())

        # Git remote display
        self._git_remote_lbl = QLabel("")
        self._git_remote_lbl.setStyleSheet(
            f"color:{T['muted']}; font-size:9px; background:transparent;")
        self._git_remote_lbl.setWordWrap(True)
        sync_card.layout().addWidget(self._git_remote_lbl)
        self._refresh_git_status()

        sync_btn_row = QHBoxLayout(); sync_btn_row.setSpacing(4)
        SYNC_ACTIONS = [
            ("↑  Push",     "sync",    sync_git),
            ("↓  Pull",     "handoff", lambda: threading.Thread(
                target=lambda: __import__("core.server", fromlist=["run_cmd_log"])
                    .run_cmd_log("git pull origin main",
                                 load_settings().get("srv_path",
                                 __import__("core.constants", fromlist=["DEFAULT_SRV_PATH"])
                                 .DEFAULT_SRV_PATH)), daemon=True).start()),
            ("⬛  Backup",   "start",   lambda: backup_to_zip("local")),
            ("☁  GDrive",   "muted",   lambda: backup_to_zip("gdrive")),
        ]
        for label, obj, fn in SYNC_ACTIONS:
            b = QPushButton(label); b.setFixedHeight(28)
            b.setObjectName(obj if obj != "muted" else "")
            if obj == "muted":
                b.setStyleSheet(
                    f"QPushButton {{ background:transparent; color:{T['muted']};"
                    f" border:1px solid {T['border']}; border-radius:6px; font-size:10px; }}"
                    f"QPushButton:hover {{ color:{T['text']}; border-color:{T['muted']}; }}")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, f=fn: threading.Thread(target=f, daemon=True).start())
            sync_btn_row.addWidget(b)
        sync_card.layout().addLayout(sync_btn_row)

        # Auto-upload toggle row
        au_row = QHBoxLayout(); au_row.setContentsMargins(0, 2, 0, 0)
        au_lbl = QLabel("Auto-upload on stop")
        au_lbl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        au_row.addWidget(au_lbl); au_row.addStretch()
        from PyQt6.QtWidgets import QCheckBox as _QCB
        self._auto_upload_cb = _QCB()
        self._auto_upload_cb.setChecked(load_settings().get("upload_on_stop", False))
        self._auto_upload_cb.stateChanged.connect(
            lambda v: update_setting("upload_on_stop", bool(v)))
        au_row.addWidget(self._auto_upload_cb)
        sync_card.layout().addLayout(au_row)
        ll.addWidget(sync_card)
        self.btn_sync = self.btn_start  # compat alias

        # Online mode toggle card
        omc = card(); omc.layout().addWidget(lbl("SERVER MODE", header=True)); omc.layout().addWidget(hline())
        self._om_lbl = lbl("", muted=True); self._om_lbl.setWordWrap(True)
        omc.layout().addWidget(self._om_lbl)
        self._om_btn = QPushButton("")
        self._om_btn.setFixedHeight(26)
        self._om_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._om_btn.clicked.connect(self._toggle_online_mode)
        omc.layout().addWidget(self._om_btn)
        ll.addWidget(omc)
        self._refresh_online_mode()

        # Quick commands
        qc = card(); qc.layout().addWidget(lbl("QUICK COMMANDS", header=True)); qc.layout().addWidget(hline())
        grid = QGridLayout(); grid.setSpacing(4)
        QUICK = [
            ("Save World",    "save-all",            T["sync"]),
            ("Player List",   "list",                T["sync"]),
            ("Check TPS",     "tps",                 T["sync"]),
            ("Set Day",       "time set day",        T["handoff"]),
            ("Set Night",     "time set night",      T["handoff"]),
            ("Clear Weather", "weather clear",       T["handoff"]),
            ("Hard Mode",     "difficulty hard",     T["stop"]),
            ("Peaceful",      "difficulty peaceful", T["start"]),
            ("Safe Stop",     "stop",                T["stop"]),
            ("Reload",        "reload",              T["muted"]),
        ]
        for i, (label, cmd_txt, color) in enumerate(QUICK):
            b = QPushButton(label)
            b.setStyleSheet(
                f"QPushButton {{ color:{color}; border:1px solid {T['border']};"
                f" border-radius:5px; padding:5px; background:transparent; font-size:10px; }}"
                f"QPushButton:hover {{ background:{T['border']}; color:{T['text']}; }}")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, c=cmd_txt: send_server_cmd(c))
            grid.addWidget(b, i // 2, i % 2)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        qc.layout().addLayout(grid)
        ll.addWidget(qc)

        # Preset quick-launch
        pqc = card(); pqc.layout().addWidget(lbl("QUICK LAUNCH PRESET", header=True)); pqc.layout().addWidget(hline())
        pq_row = QHBoxLayout()
        self._pq_combo = QComboBox(); self._pq_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pq_row.addWidget(self._pq_combo)
        pq_launch = QPushButton("Launch"); pq_launch.setFixedWidth(80); pq_launch.setFixedHeight(28)
        pq_launch.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        pq_launch.clicked.connect(self._pq_launch)
        pq_row.addWidget(pq_launch)
        pq_refresh = QPushButton("R"); pq_refresh.setFixedWidth(28); pq_refresh.setFixedHeight(28)
        pq_refresh.clicked.connect(self._pq_refresh)
        pq_row.addWidget(pq_refresh)
        pqc.layout().addLayout(pq_row)
        ll.addWidget(pqc)
        self._pq_refresh()

        # World size + backup countdown
        wf_card = card()
        wf_lay = QHBoxLayout(); wf_lay.setContentsMargins(0, 0, 0, 0)
        self._world_lbl = lbl("Size: calculating...", muted=True)
        wf_lay.addWidget(self._world_lbl)
        self._backup_lbl = lbl("", muted=True)
        self._backup_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        wf_lay.addWidget(self._backup_lbl)
        wf_card.layout().addLayout(wf_lay)
        ll.addWidget(wf_card)
        threading.Thread(target=self._calc_world, daemon=True).start()

        self._bkup_next_ts = None
        self._backup_timer = QTimer(self)
        self._backup_timer.setInterval(5000)
        self._backup_timer.timeout.connect(self._tick_backup)
        self._backup_timer.start()

        ll.addStretch()

        # Right column
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(6)
        main.addWidget(right, 1)

        # Activity log
        lc = card(); lc.layout().setSpacing(6)
        lh = QHBoxLayout(); lh.setContentsMargins(0, 0, 0, 0)
        lh.addWidget(lbl("ACTIVITY LOG", header=True)); lh.addStretch()
        swap_b = QPushButton("Swap"); swap_b.setFixedSize(50, 24)
        swap_b.clicked.connect(self._swap_log)
        lh.addWidget(swap_b)
        copy_b = QPushButton("Copy"); copy_b.setFixedSize(50, 24)
        lh.addWidget(copy_b)
        clear_b = QPushButton("Clear"); clear_b.setFixedSize(50, 24)
        lh.addWidget(clear_b)
        lc.layout().addLayout(lh)
        self.log_box = LogWidget(); self.log_box.setMinimumHeight(220)
        lc.layout().addWidget(self.log_box)
        copy_b.clicked.connect(lambda: (
            QApplication.clipboard().setText(self.log_box.toPlainText()),
            _win() and _win().toast("Copied!", T["sync"])
        ))
        clear_b.clicked.connect(self.log_box.clear)
        rl.addWidget(lc, 3)

        # Chat & events
        cc = card(); cc.layout().setSpacing(6)
        ch = QHBoxLayout(); ch.setContentsMargins(0, 0, 0, 0)
        ch.addWidget(lbl("SERVER CHAT & EVENTS", header=True)); ch.addStretch()
        self._chat_toggle_btn = QPushButton("Hide"); self._chat_toggle_btn.setFixedSize(44, 22)
        self._chat_toggle_btn.clicked.connect(self._toggle_chat)
        ch.addWidget(self._chat_toggle_btn)
        clear_c = QPushButton("Clear"); clear_c.setFixedSize(44, 22)
        ch.addWidget(clear_c)
        cc.layout().addLayout(ch)
        self.chat_box = LogWidget(); self.chat_box.setFixedHeight(90)
        cc.layout().addWidget(self.chat_box)
        clear_c.clicked.connect(self.chat_box.clear)
        rl.addWidget(cc)

        # Command input
        ci = card(); ci.layout().setContentsMargins(10, 6, 10, 6)
        cr = QHBoxLayout(); cr.setContentsMargins(0, 0, 0, 0); cr.setSpacing(8)
        sl = QLabel("/"); sl.setStyleSheet(f"color:{T['muted']}; font-size:18px; font-weight:700; background:transparent;")
        cr.addWidget(sl)
        self.cmd_edit = QLineEdit(); self.cmd_edit.setPlaceholderText("command or chat message...")
        self.cmd_edit.returnPressed.connect(self._send)
        cr.addWidget(self.cmd_edit)
        sb2 = QPushButton("Send"); sb2.setObjectName("accent"); sb2.setFixedSize(70, 30)
        sb2.setCursor(Qt.CursorShape.PointingHandCursor); sb2.clicked.connect(self._send)
        cr.addWidget(sb2)
        ci.layout().addLayout(cr)
        rl.addWidget(ci)

        self._chat_visible = True
        self._log_left = load_settings().get("log_left", False)

    def _refresh_git_status(self):
        def _work():
            from core.constants import DEFAULT_SRV_PATH
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            try:
                import subprocess
                r = subprocess.run(["git", "remote", "get-url", "origin"],
                                   capture_output=True, text=True, cwd=path, timeout=5)
                remote = r.stdout.strip() if r.returncode == 0 else "no remote"
                r2 = subprocess.run(["git", "status", "--short"],
                                    capture_output=True, text=True, cwd=path, timeout=5)
                dirty = len(r2.stdout.strip().splitlines()) if r2.returncode == 0 else 0
                self._git_signal.emit(remote, dirty)
            except Exception:
                self._git_signal.emit("git not available", -1)
        threading.Thread(target=_work, daemon=True).start()

    def _on_git_status(self, remote: str, dirty: int):
        short = remote[:42] + ("…" if len(remote) > 42 else "")
        self._git_remote_lbl.setText(f"Remote: {short}")
        if dirty < 0:
            self._git_status_lbl.setText("● unavailable")
            self._git_status_lbl.setStyleSheet(
                f"color:{T['muted']}; font-size:10px; background:transparent;")
        elif dirty == 0:
            self._git_status_lbl.setText("● clean")
            self._git_status_lbl.setStyleSheet(
                f"color:{T['start']}; font-size:10px; background:transparent;")
        else:
            self._git_status_lbl.setText(f"● {dirty} changed")
            self._git_status_lbl.setStyleSheet(
                f"color:{T['handoff']}; font-size:10px; background:transparent;")

    def _refresh_online_mode(self):
        s = load_settings(); path = s.get("srv_path", DEFAULT_SRV_PATH)
        props = os.path.join(path, "server.properties")
        online = True
        try:
            for line in open(props, encoding="utf-8"):
                if line.strip().startswith("online-mode="):
                    online = line.strip().split("=", 1)[1].strip().lower() == "true"
                    break
        except Exception:
            online = s.get("online_mode", True)
        if online:
            self._om_lbl.setText("Online Mode ON - Players need a paid Minecraft account.")
            self._om_lbl.setStyleSheet(f"color:{T['start']}; background:transparent; font-size:11px;")
            self._om_btn.setText("Switch to Cracked/Offline")
            self._om_btn.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {T['handoff']}; color:{T['handoff']}; border-radius:5px; }}")
        else:
            self._om_lbl.setText("Online Mode OFF - Anyone can join (cracked/offline).")
            self._om_lbl.setStyleSheet(f"color:{T['handoff']}; background:transparent; font-size:11px;")
            self._om_btn.setText("Switch to Online Mode")
            self._om_btn.setStyleSheet(f"QPushButton {{ background:transparent; border:1px solid {T['start']}; color:{T['start']}; border-radius:5px; }}")
        self._om_online = online

    def _toggle_online_mode(self):
        new_val = not self._om_online
        val_str = "true" if new_val else "false"
        update_setting("online_mode", new_val)
        s = load_settings(); path = s.get("srv_path", DEFAULT_SRV_PATH)
        props = os.path.join(path, "server.properties")
        try:
            if os.path.exists(props):
                txt = open(props, encoding="utf-8").read()
                if "online-mode=" in txt:
                    txt = re.sub(r"online-mode=\S+", f"online-mode={val_str}", txt)
                else:
                    txt += f"\nonline-mode={val_str}\n"
                with open(props, "w", encoding="utf-8") as f:
                    f.write(txt)
        except Exception as ex:
            if _win(): _win().toast(f"Props write failed: {ex}", T["stop"])
            return
        self._refresh_online_mode()
        if _win(): _win().toast(f"online-mode={val_str} - restart server to apply", T["handoff"] if not new_val else T["start"])

    def _pq_refresh(self):
        self._pq_combo.clear()
        presets = list(load_presets().keys())
        if presets:
            self._pq_combo.addItems(presets)
        else:
            self._pq_combo.addItem("No presets saved")

    def _pq_launch(self):
        name = self._pq_combo.currentText()
        presets = load_presets()
        if name not in presets:
            if _win(): _win().toast("No preset selected!", T["stop"])
            return
        p = presets[name]
        update_setting("srv_path", p.get("path", ""))
        if p.get("java"): update_setting("java_path", p["java"])
        update_setting("ram_gb", p.get("ram_gb", 2))
        threading.Thread(target=start_server, daemon=True).start()

    def _calc_world(self):
        from core.server import calc_world_size
        s = load_settings(); path = s.get("srv_path", DEFAULT_SRV_PATH)
        sz = calc_world_size(path)
        self._world_size_signal.emit(sz)

    def _on_world_size(self, sz: str):
        self._world_lbl.setText(f"Size: {sz}")

    def _tick_backup(self):
        if self._bkup_next_ts:
            rem = max(0, int(self._bkup_next_ts - time.time()))
            m, s = divmod(rem, 60)
            color = T["sync"] if rem < 300 else T["muted"]
            self._backup_lbl.setText(f"Backup in {m:02d}:{s:02d}")
            self._backup_lbl.setStyleSheet(f"color:{color}; background:transparent; font-size:10px;")

    def set_backup_countdown(self, ts: float):
        self._bkup_next_ts = ts

    def _swap_log(self):
        log_left = not load_settings().get("log_left", False)
        update_setting("log_left", log_left)
        if _win(): _win().toast("Log position swapped - restart UI to apply", T["handoff"])

    def _toggle_chat(self):
        self._chat_visible = not self._chat_visible
        self.chat_box.setVisible(self._chat_visible)
        self._chat_toggle_btn.setText("Hide" if self._chat_visible else "Show")
        update_setting("show_chat", self._chat_visible)

    def _send(self):
        cmd = self.cmd_edit.text().strip()
        if not cmd: return
        self.cmd_edit.clear(); send_server_cmd(cmd)

    def log(self, text: str, cat: str):
        color = (T["start"] if ">>" in text or "joined" in text
                 else T["stop"] if "DEATH" in text or "left" in text
                 else None)
        if cat in ("chat", "event"):
            self.chat_box.append_line(text, color or T["sync"])
        else:
            self.log_box.append_line(text, color)

    def update_perf(self):
        pass  # Perf strip now lives in MainWindow bottom bar


# ── playit.gg sub-tab ─────────────────────────────────────────────────────────
_playit_proc   = None
_playit_tunnel = ""
_playit_log: list[str] = []


class _PlayitTab(QWidget):
    _log_signal    = pyqtSignal(str)
    _status_signal = pyqtSignal(str, str)
    _dl_signal     = pyqtSignal(str, str)  # text, color

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_signal.connect(self._append_on_ui)
        self._status_signal.connect(self._set_status_on_ui)
        self._dl_signal.connect(self._set_dl_status)
        scroll, _, lay = make_scroll()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(scroll)

        # About card
        ac = card()
        ac.layout().addWidget(lbl("About playit.gg", header=True)); ac.layout().addWidget(hline())
        about_lbl = lbl("playit.gg is a free tunnel that gives your server a public address without port forwarding.\nFriends connect via a .ply.gg address. Free plan supports up to 3 tunnels.", muted=True)
        about_lbl.setWordWrap(True)
        ac.layout().addWidget(about_lbl)
        lay.addWidget(ac)

        # Setup card
        sc = card(); sc.layout().addWidget(lbl("SETUP", header=True)); sc.layout().addWidget(hline())
        s = load_settings()
        pr = QHBoxLayout()
        self.path_edit = QLineEdit(s.get("playit_path", s.get("playit_exe", "")))
        self.path_edit.setPlaceholderText("path/to/playit.exe")
        pr.addWidget(self.path_edit)
        browse_b = QPushButton("Browse"); browse_b.setFixedWidth(66)
        browse_b.clicked.connect(self._browse)
        pr.addWidget(browse_b)
        dl_b = QPushButton("Auto-Download"); dl_b.setFixedWidth(120)
        dl_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        dl_b.clicked.connect(self._auto_download)
        pr.addWidget(dl_b)
        sc.layout().addLayout(pr)
        self._dl_status = lbl("", muted=True)
        sc.layout().addWidget(self._dl_status)
        lay.addWidget(sc)

        # Secret key
        kc = card(); kc.layout().addWidget(lbl("SECRET KEY", header=True)); kc.layout().addWidget(hline())
        kr = QHBoxLayout()
        self.key_edit = QLineEdit(s.get("playit_secret_key", ""))
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("paste secret key...")
        kr.addWidget(self.key_edit)
        vis = QPushButton("Show"); vis.setFixedWidth(46)
        def _toggle():
            if self.key_edit.echoMode() == QLineEdit.EchoMode.Password:
                self.key_edit.setEchoMode(QLineEdit.EchoMode.Normal); vis.setText("Hide")
            else:
                self.key_edit.setEchoMode(QLineEdit.EchoMode.Password); vis.setText("Show")
        vis.clicked.connect(_toggle); kr.addWidget(vis)
        save_k = QPushButton("Save"); save_k.setFixedWidth(46)
        save_k.clicked.connect(lambda: update_setting("playit_secret_key", self.key_edit.text().strip()))
        kr.addWidget(save_k); kc.layout().addLayout(kr)
        lay.addWidget(kc)

        # Tunnel control
        tc = card()
        th = QHBoxLayout(); th.setContentsMargins(0, 0, 0, 0)
        self.status_lbl = QLabel("Stopped")
        self.status_lbl.setStyleSheet(f"color:{T['stop']}; font-weight:700; font-size:13px; background:transparent;")
        th.addWidget(self.status_lbl); th.addStretch()
        self.addr_lbl = lbl("No tunnel address yet", muted=True)
        for txt, fn, fc, tcol in [("Start", self._start, T["start"], "#000"), ("Stop", self._stop, T["stop"], "#fff")]:
            b = QPushButton(txt); b.setFixedWidth(74)
            b.setStyleSheet(f"QPushButton {{ background:{fc}; color:{tcol}; border:none; border-radius:6px; font-weight:700; }}")
            b.clicked.connect(fn); th.addWidget(b)
        copy_b = QPushButton("Copy Address"); copy_b.setFixedWidth(110)
        copy_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        copy_b.clicked.connect(self._copy_addr); th.addWidget(copy_b)
        tc.layout().addLayout(th)
        tc.layout().addWidget(self.addr_lbl)
        lay.addWidget(tc)

        # Agent log
        lc = card()
        lh = QHBoxLayout(); lh.setContentsMargins(0, 0, 0, 0)
        lh.addWidget(lbl("AGENT LOG", header=True)); lh.addStretch()
        clr = QPushButton("Clear"); clr.setFixedSize(52, 26)
        clr.clicked.connect(lambda: (self.pt_log.clear(), _playit_log.clear()))
        lh.addWidget(clr)
        lc.layout().addLayout(lh)
        self.pt_log = LogWidget(); self.pt_log.setMinimumHeight(200)
        lc.layout().addWidget(self.pt_log)
        for line in _playit_log:
            self.pt_log.append_line(line)
        lay.addWidget(lc); lay.addStretch()

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select playit binary")
        if p:
            self.path_edit.setText(p)
            update_setting("playit_path", p)

    def _auto_download(self):
        fname = ("playit-windows.exe" if IS_WIN else
                 "playit-darwin" if IS_MAC else "playit-linux-amd64")
        dest_name = "playit.exe" if IS_WIN else "playit"
        from core.constants import _BASE_DIR
        dest = os.path.join(_BASE_DIR, dest_name)
        self._dl_signal.emit("Downloading...", T["sync"])
        def _work():
            import urllib.request
            url = f"https://github.com/playit-cloud/playit-agent/releases/latest/download/{fname}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "MC-CTRL/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    with open(dest, "wb") as f: f.write(r.read())
                if not IS_WIN: os.chmod(dest, 0o755)
                self.path_edit.setText(dest)
                update_setting("playit_path", dest)
                self._dl_signal.emit("Downloaded!", T["start"])
            except Exception as ex:
                self._dl_signal.emit(f"Failed: {ex}", T["stop"])
        threading.Thread(target=_work, daemon=True).start()

    def _set_dl_status(self, text: str, color: str):
        self._dl_status.setText(text)
        self._dl_status.setStyleSheet(f"color:{color}; background:transparent; font-size:11px;")

    def _stop(self):
        global _playit_proc
        if _playit_proc:
            try: _playit_proc.terminate()
            except Exception: pass
            _playit_proc = None
        self._status_signal.emit("Stopped", T["stop"])

    def _copy_addr(self):
        if _playit_tunnel:
            QApplication.clipboard().setText(_playit_tunnel)
            if _win(): _win().toast(f"Copied: {_playit_tunnel}", T["sync"])

    def _append(self, line: str):
        _playit_log.append(line)
        if len(_playit_log) > 300: del _playit_log[:150]
        self._log_signal.emit(line)

    def _append_on_ui(self, line: str):
        self.pt_log.append_line(line)

    def _set_status_on_ui(self, text: str, color: str):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color:{color}; font-weight:700; font-size:13px; background:transparent;")

    def set_addr(self, addr: str):
        global _playit_tunnel
        _playit_tunnel = addr
        self.addr_lbl.setText(f"  {addr}" if addr else "No tunnel address yet")
        color = T["start"] if addr else T["muted"]
        self.addr_lbl.setStyleSheet(f"color:{color}; font-weight:{'700' if addr else '400'}; background:transparent;")

    def _start(self):
        global _playit_proc
        exe = self.path_edit.text().strip()
        update_setting("playit_path", exe)
        if not exe or not os.path.isfile(exe):
            self._append("[MC CTRL] playit binary not found. Use Setup above."); return
        saved_key = self.key_edit.text().strip()
        if saved_key:
            self._write_playit_toml(exe, saved_key)
        threading.Thread(target=self._run_playit, daemon=True).start()

    def _write_playit_toml(self, exe: str, key: str):
        """Write/update secret_key in playit.toml — cross-platform."""
        import sys as _sys
        if IS_WIN:
            dirs = [os.path.join(os.environ.get("APPDATA", ""), "playit"),
                    os.path.dirname(exe)]
        elif IS_MAC:
            dirs = [os.path.join(os.path.expanduser("~"), "Library", "Application Support", "playit"),
                    os.path.dirname(exe)]
        else:  # Linux / Docker
            xdg = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
            dirs = [os.path.join(xdg, "playit"),
                    os.path.dirname(exe),
                    os.path.expanduser("~/.playit")]
        for d in dirs:
            if not d: continue
            try:
                os.makedirs(d, exist_ok=True)
                tp = os.path.join(d, "playit.toml")
                lines = open(tp, encoding="utf-8", errors="ignore").readlines() if os.path.exists(tp) else []
                new_lines, found = [], False
                for tl in lines:
                    if tl.strip().startswith("secret_key"):
                        new_lines.append(f'secret_key = "{key}"\n'); found = True
                    else:
                        new_lines.append(tl)
                if not found: new_lines.insert(0, f'secret_key = "{key}"\n')
                open(tp, "w", encoding="utf-8").writelines(new_lines)
                self._append(f"[MC CTRL] Wrote secret key to {tp}")
                return
            except Exception as ex:
                self._append(f"[MC CTRL] Could not write toml to {d}: {ex}")

    def _run_playit(self):
        global _playit_proc
        exe = self.path_edit.text().strip()
        _ansi = re.compile(r'\x1b(?:\[[0-9;]*[mABCDEFGHJKSTfhilmnprsuu]|\][^\x07]*\x07|[()][AB012]|[=>])')
        self._append("[MC CTRL] Agent starting...")
        self._status_signal.emit("Running", T["start"])

        env = os.environ.copy()
        key = self.key_edit.text().strip()
        if key:
            env["PLAYIT_SECRET"] = key  # env-var auth (works on all platforms incl. Docker)

        popen_kw = dict(
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, text=False, bufsize=0, env=env,
        )
        if IS_WIN:
            popen_kw["creationflags"] = CREATE_NO_WINDOW
        else:
            popen_kw["close_fds"]        = True
            popen_kw["start_new_session"] = True

        try:
            _playit_proc = subprocess.Popen([exe], **popen_kw)
            def _read(stream):
                for raw in iter(stream.readline, b""):
                    if not raw: break
                    clean = _ansi.sub("", raw.decode("utf-8", "replace").rstrip()).strip()
                    if not clean: continue
                    self._append(clean)
                    m = PLAYIT_ADDR_RE.search(clean)
                    if m and _win(): _win()._signals.sig_set_addr.emit(m.group(1))
                    cm = PLAYIT_CLAIM_RE.search(clean)
                    if cm and _win(): _win().toast(f"Claim URL: {cm.group(1)}", T["handoff"], 10000)
            threading.Thread(target=_read, args=(_playit_proc.stdout,), daemon=True).start()
            threading.Thread(target=_read, args=(_playit_proc.stderr,), daemon=True).start()
            code = _playit_proc.wait()
            self._append(f"[MC CTRL] Exited ({code}).")
        except Exception as ex:
            self._append(f"[MC CTRL] Failed: {ex}")
        self._stop()


# ── Remote sub-tab ────────────────────────────────────────────────────────────
class _RemoteTab(QWidget):
    _log_signal = pyqtSignal(str)
    _status_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self._log_signal.connect(self._append_on_ui)
        self._status_signal.connect(self._set_status_on_ui)
        scroll, _, lay = make_scroll()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(scroll)

        # About
        ac = card(); ac.layout().addWidget(lbl("About Remote Dashboard", header=True)); ac.layout().addWidget(hline())
        about_lbl = lbl(
            "Starts a lightweight web server so you can control Minecraft from your phone.\n"
            "Open http://<your-local-ip>:<port> in any browser - no app required.\n"
            "Features: start/stop, live log, commands, player list, TPS/RAM stats.", muted=True)
        about_lbl.setWordWrap(True)
        ac.layout().addWidget(about_lbl)
        lay.addWidget(ac)

        s = load_settings()

        # Config
        cc = card(); cc.layout().addWidget(lbl("CONFIGURATION", header=True)); cc.layout().addWidget(hline())
        for label_txt, key, default, pw in [("Port", "remote_port", "25580", False),
                                             ("Password (optional)", "remote_password", "", True)]:
            r = QHBoxLayout()
            r.addWidget(lbl(f"{label_txt}:", muted=True))
            e = QLineEdit(str(s.get(key, default)))
            if pw: e.setEchoMode(QLineEdit.EchoMode.Password)
            e.setFixedWidth(180 if pw else 80)
            e.editingFinished.connect(lambda _e=e, _k=key: update_setting(_k, _e.text().strip()))
            r.addWidget(e)
            if pw:
                show_b = QPushButton("Show"); show_b.setFixedWidth(46)
                def _toggle_pw(_e=e, _b=show_b):
                    if _e.echoMode() == QLineEdit.EchoMode.Password:
                        _e.setEchoMode(QLineEdit.EchoMode.Normal); _b.setText("Hide")
                    else:
                        _e.setEchoMode(QLineEdit.EchoMode.Password); _b.setText("Show")
                show_b.clicked.connect(_toggle_pw); r.addWidget(show_b)
            r.addStretch()
            cc.layout().addLayout(r)
        lay.addWidget(cc)

        # Control
        ctrl_c = card()
        ch = QHBoxLayout(); ch.setContentsMargins(0, 0, 0, 0)
        self.status_lbl = QLabel("Stopped")
        self.status_lbl.setStyleSheet(f"color:{T['stop']}; font-weight:700; background:transparent;")
        ch.addWidget(self.status_lbl)
        self.url_lbl = lbl("", muted=True); ch.addWidget(self.url_lbl)
        ch.addStretch()
        for txt, fn, fc, tcol in [("Start", self._start, T["start"], "#000"), ("Stop", self._stop, T["stop"], "#fff")]:
            b = QPushButton(txt); b.setFixedWidth(74)
            b.setStyleSheet(f"QPushButton {{ background:{fc}; color:{tcol}; border:none; border-radius:6px; font-weight:700; }}")
            b.clicked.connect(fn); ch.addWidget(b)
        copy_b = QPushButton("Copy URL"); copy_b.setFixedWidth(80)
        copy_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        copy_b.clicked.connect(lambda: (QApplication.clipboard().setText(self._cur_url), _win() and _win().toast(f"Copied: {self._cur_url}", T["sync"])))
        ch.addWidget(copy_b)
        ctrl_c.layout().addLayout(ch)
        lay.addWidget(ctrl_c)

        # How to use
        hc = card(); hc.layout().addWidget(lbl("How to use from your phone", header=True)); hc.layout().addWidget(hline())
        how_lbl = lbl(
            "1. Start Remote Dashboard above.\n"
            "2. Phone must be on same WiFi.\n"
            "3. Open the URL in your phone's browser.\n"
            "4. Use web UI to start/stop, send commands, watch live logs.\n\n"
            "For outside-LAN access use Tailscale or playit.gg.", muted=True)
        how_lbl.setWordWrap(True)
        hc.layout().addWidget(how_lbl)
        lay.addWidget(hc)

        self.out_log = LogWidget(); self.out_log.setMinimumHeight(120)
        lc = card(); lc.layout().addWidget(lbl("OUTPUT", header=True)); lc.layout().addWidget(self.out_log)
        lay.addWidget(lc); lay.addStretch()
        self._cur_url = ""

    def _start(self):
        import sys
        from core.constants import _BASE_DIR
        remote_script = os.path.join(_BASE_DIR, "_mc_ctrl_remote.py")
        if not os.path.exists(remote_script):
            self.out_log.append_line("[Remote] _mc_ctrl_remote.py not found.", T["stop"]); return
        port = load_settings().get("remote_port", 25580)
        import socket
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s2.connect(("8.8.8.8", 80))
            lip = s2.getsockname()[0]; s2.close()
        except Exception:
            lip = "127.0.0.1"
        self._cur_url = f"http://{lip}:{port}"
        self.status_lbl.setText("Running")
        self.status_lbl.setStyleSheet(f"color:{T['start']}; font-weight:700; background:transparent;")
        self.url_lbl.setText(f"  {self._cur_url}")
        self.out_log.append_line(f"[Remote] Starting on {self._cur_url}")
        try:
            self._proc = subprocess.Popen(
                [sys.executable, remote_script, "--port", str(port)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=CREATE_NO_WINDOW)
            threading.Thread(target=self._read_proc, daemon=True).start()
        except Exception as ex:
            self.out_log.append_line(f"[Remote] Failed: {ex}", T["stop"])
            self._stop()

    def _read_proc(self):
        if self._proc:
            for line in iter(self._proc.stdout.readline, ""):
                if line.strip(): self._log_signal.emit(line.rstrip())
        self._stop()

    def _stop(self):
        if self._proc:
            try: self._proc.terminate()
            except Exception: pass
            self._proc = None
        self._status_signal.emit("Stopped", T["stop"])

    def _append_on_ui(self, line: str):
        self.out_log.append_line(line)

    def _set_status_on_ui(self, text: str, color: str):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color:{color}; font-weight:700; background:transparent;")


# ── Multi-Server sub-tab ──────────────────────────────────────────────────────
MAX_SLOTS = 3

class _MultiTab(QWidget):
    _status_signal = pyqtSignal(int, str, str)
    _log_signal = pyqtSignal(int, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_signal.connect(self._set_status_on_ui)
        self._log_signal.connect(self._append_log_on_ui)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("topbar"); hdr.setFixedHeight(38)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(12, 0, 12, 0)
        tl = QLabel("MULTI SERVER CONTROL")
        tl.setStyleSheet(f"color:{T['handoff']}; font-weight:700; font-size:13px; background:transparent;")
        hl.addWidget(tl)
        sl = QLabel("  up to 3 servers simultaneously")
        sl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        hl.addWidget(sl); hl.addStretch()
        root.addWidget(hdr)

        cols_w = QWidget()
        cols_lay = QHBoxLayout(cols_w); cols_lay.setContentsMargins(6, 6, 6, 6); cols_lay.setSpacing(6)
        root.addWidget(cols_w, 1)

        self.slots: list[dict] = []
        for i in range(MAX_SLOTS):
            slot = {"proc": None, "stdin": None, "running": False, "status": None, "log": None, "path_edit": None}
            col = self._build_col(i, slot)
            cols_lay.addWidget(col, 1)
            self.slots.append(slot)

        cb = QFrame(); cb.setObjectName("topbar"); cb.setFixedHeight(42)
        cbl = QHBoxLayout(cb); cbl.setContentsMargins(8, 0, 8, 0); cbl.setSpacing(8)
        cbl.addWidget(lbl("Send to:", muted=True))
        self.target = QComboBox()
        self.target.addItems(["Server 1", "Server 2", "Server 3", "All Servers"])
        self.target.setFixedWidth(110); cbl.addWidget(self.target)
        self.cmd_edit = QLineEdit(); self.cmd_edit.setPlaceholderText("command...")
        self.cmd_edit.returnPressed.connect(self._send); cbl.addWidget(self.cmd_edit, 1)
        sb = QPushButton("Send"); sb.setFixedWidth(60)
        sb.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        sb.clicked.connect(self._send); cbl.addWidget(sb)
        root.addWidget(cb)

    def _build_col(self, idx, slot):
        col = QFrame(); col.setObjectName("card")
        cl = QVBoxLayout(col); cl.setContentsMargins(8, 8, 8, 8); cl.setSpacing(6)
        hdr = QFrame()
        hdrl = QHBoxLayout(hdr); hdrl.setContentsMargins(4, 3, 4, 3)
        tl = QLabel(f"Server {idx + 1}")
        tl.setStyleSheet(f"color:{T['text']}; font-weight:700; background:transparent;")
        hdrl.addWidget(tl); hdrl.addStretch()
        sl = QLabel("Stopped")
        sl.setStyleSheet(f"color:{T['stop']}; font-size:10px; font-weight:700; background:transparent;")
        hdrl.addWidget(sl); slot["status"] = sl
        cl.addWidget(hdr)

        pr = QHBoxLayout()
        pe = QLineEdit(); pe.setPlaceholderText(f"Server {idx + 1} folder..."); slot["path_edit"] = pe
        pr.addWidget(pe)
        bb = QPushButton("..."); bb.setFixedWidth(26)
        bb.clicked.connect(lambda _, s=slot: self._browse(s)); pr.addWidget(bb)
        cl.addLayout(pr)

        br = QHBoxLayout()
        stb = QPushButton("Start")
        stb.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:5px; padding:4px; font-weight:700; }}")
        stb.clicked.connect(lambda _, i=idx: threading.Thread(target=self._start, args=(i,), daemon=True).start())
        br.addWidget(stb, 1)
        spb = QPushButton("Stop")
        spb.setStyleSheet(f"QPushButton {{ background:{T['stop']}; color:#fff; border:none; border-radius:5px; padding:4px; font-weight:700; }}")
        spb.clicked.connect(lambda _, i=idx: self._stop(i)); br.addWidget(spb, 1)
        cl.addLayout(br)

        log_b = LogWidget(); slot["log"] = log_b; cl.addWidget(log_b, 1)
        return col

    def _browse(self, slot):
        p = QFileDialog.getExistingDirectory(self, "Select Server Folder")
        if p and slot["path_edit"]: slot["path_edit"].setText(p)

    def _set_status(self, idx, text, color):
        self._status_signal.emit(idx, text, color)

    def _set_status_on_ui(self, idx, text, color):
        s = self.slots[idx]["status"]
        if s: s.setText(text); s.setStyleSheet(f"color:{color}; font-size:10px; font-weight:700; background:transparent;")

    def _append_log_on_ui(self, idx, text, color):
        log_w = self.slots[idx]["log"]
        if log_w: log_w.append_line(text, color)

    def _start(self, idx):
        slot = self.slots[idx]
        path = slot["path_edit"].text().strip() if slot["path_edit"] else ""
        if not path or not os.path.isdir(path):
            self._log_signal.emit(idx, f"[{idx+1}] Invalid path.", T["stop"]); return
        if slot["running"]: return
        jar = os.path.join(path, "server.jar")
        if not os.path.exists(jar):
            self._log_signal.emit(idx, f"[{idx+1}] No server.jar.", T["stop"]); return
        s = load_settings(); java = s.get("java_path", "java"); ram = s.get("ram_gb", 2)
        try:
            proc = subprocess.Popen(
                [java, "-Xms512M", f"-Xmx{ram}G", "-XX:+UseG1GC", "-jar", jar, "--nogui"],
                cwd=path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, creationflags=CREATE_NO_WINDOW)
            slot.update({"proc": proc, "stdin": proc.stdin, "running": True})
            self._set_status(idx, "Running", T["start"])
            def _read(p=proc, i=idx, sl=slot):
                for raw in iter(p.stdout.readline, ""):
                    if raw.strip(): self._log_signal.emit(i, raw.rstrip(), None)
                sl.update({"running": False, "proc": None, "stdin": None})
                self._set_status(i, "Stopped", T["stop"])
            threading.Thread(target=_read, daemon=True).start()
        except Exception as ex:
            self._log_signal.emit(idx, f"[{idx+1}] Failed: {ex}", T["stop"])

    def _stop(self, idx):
        slot = self.slots[idx]
        if slot["stdin"]:
            try: slot["stdin"].write("stop\n"); slot["stdin"].flush()
            except Exception: pass
        if slot["proc"]:
            QTimer.singleShot(3000, lambda p=slot["proc"]: p.terminate() if p.poll() is None else None)
        slot.update({"running": False, "proc": None, "stdin": None})
        self._set_status(idx, "Stopped", T["stop"])

    def _send(self):
        cmd = self.cmd_edit.text().strip()
        if not cmd: return
        t = self.target.currentText()
        targets = list(range(MAX_SLOTS)) if t == "All Servers" else [int(t.split()[-1]) - 1]
        for i in targets:
            sl = self.slots[i]; si = sl.get("stdin")
            if si:
                try: si.write(cmd + "\n"); si.flush(); sl["log"].append_line(f">> {cmd}", T["sync"])
                except Exception as ex: sl["log"].append_line(f"[err] {ex}", T["stop"])
            else:
                sl["log"].append_line(f"[Server {i+1} not running]", T["muted"])
        self.cmd_edit.clear()


# ── Presets sub-tab ───────────────────────────────────────────────────────────
class _PresetsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll, _, lay = make_scroll()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.addWidget(scroll)

        nc = card(); nc.layout().addWidget(lbl("NEW PRESET", header=True)); nc.layout().addWidget(hline())

        self.name_e = QLineEdit(); self.name_e.setPlaceholderText("e.g. Survival SMP")
        self.path_e = QLineEdit(); self.path_e.setPlaceholderText("/path/to/server/")
        self.java_e = QLineEdit(); self.java_e.setPlaceholderText("java  (blank = default)")

        for label_txt, widget in [("Name", self.name_e), ("Path", self.path_e), ("Java", self.java_e)]:
            r = QHBoxLayout(); r.setSpacing(6)
            nl = QLabel(label_txt); nl.setFixedWidth(60)
            r.addWidget(nl); r.addWidget(widget)
            if label_txt == "Path":
                brw = QPushButton("..."); brw.setFixedWidth(26)
                def _do_brw():
                    p = QFileDialog.getExistingDirectory(self, "Select Server Folder")
                    if p: self.path_e.setText(p)
                brw.clicked.connect(_do_brw)
                r.addWidget(brw)
            nc.layout().addLayout(r)

        ram_row = QHBoxLayout()
        ram_lbl_t = QLabel("RAM (GB)"); ram_lbl_t.setFixedWidth(60)
        ram_row.addWidget(ram_lbl_t)
        self.ram_sl = QSlider(Qt.Orientation.Horizontal); self.ram_sl.setRange(1, 16); self.ram_sl.setValue(2)
        ram_row.addWidget(self.ram_sl)
        self.ram_lbl = QLabel("2 GB"); self.ram_lbl.setFixedWidth(44)
        self.ram_lbl.setStyleSheet(f"color:{T['sync']}; background:transparent;")
        self.ram_sl.valueChanged.connect(lambda v: self.ram_lbl.setText(f"{v} GB"))
        ram_row.addWidget(self.ram_lbl)
        nc.layout().addLayout(ram_row)

        add_b = QPushButton("+ Add Preset")
        add_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; padding:7px; font-weight:700; }}")
        add_b.clicked.connect(self._add); nc.layout().addWidget(add_b)
        lay.addWidget(nc)

        # Hint
        hint = QFrame(); hint.setObjectName("card")
        hl2 = QVBoxLayout(hint); hl2.setContentsMargins(14, 10, 14, 10)
        hint_title = lbl("How to use presets", header=True)
        hint_title.setStyleSheet(f"color:{T['sync']}; background:transparent; font-size:12px; font-weight:700;")
        hl2.addWidget(hint_title)
        hint_body = lbl(
            "1. Fill in the form above and click + Add Preset\n"
            "2. Your preset appears below with a Launch button\n"
            "3. Click Launch - it overrides the active server path/java/RAM and starts immediately\n"
            "4. You can keep multiple server folders (Survival, Creative, SMP...) and switch here", muted=True)
        hint_body.setWordWrap(True); hl2.addWidget(hint_body)
        lay.addWidget(hint)

        self.list_w = QWidget()
        self.list_l = QVBoxLayout(self.list_w); self.list_l.setContentsMargins(0, 0, 0, 0); self.list_l.setSpacing(6)
        lay.addWidget(self.list_w); lay.addStretch()
        self._refresh()

    def _add(self):
        n = self.name_e.text().strip(); p = self.path_e.text().strip()
        w = _win()
        if not n: w and w.toast("Enter a name!", T["stop"]); return
        if not p: w and w.toast("Enter a path!", T["stop"]); return
        j = self.java_e.text().strip() or load_settings().get("java_path", DEFAULT_JAVA_PATH)
        save_preset(n, p, j, self.ram_sl.value())
        w and w.toast(f"Preset '{n}' saved!", T["start"])
        self.name_e.clear(); self.path_e.clear(); self.java_e.clear(); self.ram_sl.setValue(2)
        self._refresh()

    def _refresh(self):
        while self.list_l.count():
            item = self.list_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        presets = load_presets()
        if not presets:
            self.list_l.addWidget(lbl("No presets yet - add one above.", muted=True)); return
        sc = card(); sc.layout().addWidget(lbl("SAVED PRESETS", header=True)); sc.layout().addWidget(hline())
        for pname, pd in presets.items():
            rw = QFrame(); rw.setObjectName("card")
            rl = QHBoxLayout(rw); rl.setContentsMargins(10, 6, 10, 6); rl.setSpacing(8)
            nl = QLabel(f"  {pname}")
            nl.setStyleSheet(f"color:{T['text']}; font-weight:700; background:transparent;")
            rl.addWidget(nl)
            pl = QLabel(pd.get("path", "?"))
            pl.setStyleSheet(f"color:{T['muted']}; font-family:Consolas; font-size:10px; background:transparent;")
            rl.addWidget(pl); rl.addStretch()
            ml = QLabel(f"Java: {pd.get('java', 'default')}  RAM: {pd.get('ram_gb', 2)}GB")
            ml.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            rl.addWidget(ml)
            db = QPushButton("Del"); db.setFixedSize(36, 24)
            db.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:4px; }}")
            db.clicked.connect(lambda _, nn=pname: (delete_preset(nn), self._refresh()))
            rl.addWidget(db)
            lb = QPushButton("Launch"); lb.setFixedWidth(80)
            lb.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; padding:4px 8px; font-weight:700; }}")
            lb.clicked.connect(lambda _, nn=pname: self._launch(nn))
            rl.addWidget(lb)
            sc.layout().addWidget(rw)
        self.list_l.addWidget(sc)

    def _launch(self, name):
        pd = load_presets().get(name)
        if not pd: return
        update_setting("srv_path", pd.get("path", ""))
        if pd.get("java"): update_setting("java_path", pd["java"])
        update_setting("ram_gb", pd.get("ram_gb", 2))
        threading.Thread(target=start_server, daemon=True).start()


# ── Dashboard outer container ─────────────────────────────────────────────────
class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        self.sub_tabs = QTabWidget(); self.sub_tabs.setObjectName("subtab")
        bar = self.sub_tabs.tabBar(); bar.setObjectName("subtabbar")

        self._ctrl    = _ControlTab()
        self._playit  = _PlayitTab()
        self._remote  = _RemoteTab()
        self._multi   = _MultiTab()
        self._presets = _PresetsTab()

        self.sub_tabs.addTab(self._ctrl,    "Control")
        self.sub_tabs.addTab(self._playit,  "playit.gg")
        self.sub_tabs.addTab(self._remote,  "Remote")
        self.sub_tabs.addTab(self._multi,   "Multi-Server")
        self.sub_tabs.addTab(self._presets, "Presets")

        root.addWidget(self.sub_tabs)

    def log(self, text: str, cat: str):
        self._ctrl.log(text, cat)

    def update_perf(self):
        self._ctrl.update_perf()

    def set_playit_addr(self, addr: str):
        self._playit.set_addr(addr)
