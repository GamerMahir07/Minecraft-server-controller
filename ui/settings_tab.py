"""ui/settings_tab.py — Settings tab with image-style pill rows"""
import os, re, shutil, threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QCheckBox, QFileDialog, QSlider, QComboBox,
    QColorDialog, QDialog, QScrollArea, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer

from core.themes import T, THEMES
from core.constants import DEFAULT_SRV_PATH, DEFAULT_JAVA_PATH, REPO_URL, APP_VERSION, SETTINGS_FILE, _ADDONS_DIR
from core.settings import load_settings, save_settings, update_setting
from core.server import run_repair, schedule_auto_upload
from .widgets import make_scroll, card, hline, lbl

def _win():
    from .main_window import WIN
    return WIN

def _toast(msg, color=None, ms=3000):
    w = _win()
    if w: w.toast(msg, color or T["sync"], ms)


def _row(label: str, sublabel: str = "") -> tuple[QFrame, QHBoxLayout]:
    """Create a pill-style settings row card. Returns (frame, right_layout)."""
    f = QFrame(); f.setObjectName("settings_row")
    outer = QHBoxLayout(f); outer.setContentsMargins(14, 8, 14, 8); outer.setSpacing(10)
    text_col = QVBoxLayout(); text_col.setSpacing(1)
    tl = QLabel(label)
    tl.setStyleSheet(f"color:{T['text']}; font-size:12px; font-weight:500; background:transparent;")
    text_col.addWidget(tl)
    if sublabel:
        sl = QLabel(sublabel)
        sl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        text_col.addWidget(sl)
    outer.addLayout(text_col, 1)
    right = QHBoxLayout(); right.setSpacing(6); right.setContentsMargins(0,0,0,0)
    outer.addLayout(right)
    return f, right


def _section_label(text: str) -> QLabel:
    l = QLabel(text.upper())
    l.setObjectName("section_hdr")
    l.setStyleSheet(
        f"color:{T['muted']}; font-size:10px; font-weight:600; letter-spacing:1.2px;"
        " background:transparent; padding:10px 2px 4px 2px;")
    return l


class SettingsTab(QWidget):
    def __init__(self, parent_win=None):
        super().__init__()
        self._parent_win = parent_win
        self._dirty: dict = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        scroll, _, lay = make_scroll()
        root.addWidget(scroll, 1)

        s = load_settings()

        # ── Row helpers ───────────────────────────────────────────────────────
        def _entry_row(label, sublabel, key, default="", password=False, ph=""):
            f, right = _row(label, sublabel)
            e = QLineEdit(str(s.get(key, default))); e.setFixedWidth(240)
            if password: e.setEchoMode(QLineEdit.EchoMode.Password)
            if ph: e.setPlaceholderText(ph)
            e.editingFinished.connect(lambda k=key, le=e: self._dirty.__setitem__(k, le.text().strip()))
            right.addWidget(e)
            if password:
                sb = QPushButton("Show"); sb.setFixedWidth(46); sb.setFixedHeight(26)
                def _tog(_e=e, _b=sb):
                    vis = _e.echoMode() == QLineEdit.EchoMode.Normal
                    _e.setEchoMode(QLineEdit.EchoMode.Password if vis else QLineEdit.EchoMode.Normal)
                    _b.setText("Show" if vis else "Hide")
                sb.clicked.connect(_tog); right.addWidget(sb)
            lay.addWidget(f); return e

        def _browse_row(label, sublabel, key, default="", is_file=False):
            f, right = _row(label, sublabel)
            e = QLineEdit(str(s.get(key, default))); e.setFixedWidth(200)
            e.editingFinished.connect(lambda k=key, le=e: self._dirty.__setitem__(k, le.text().strip()))
            right.addWidget(e)
            def _br(_e=e, _k=key):
                p = (QFileDialog.getOpenFileName(self, label)[0] if is_file
                     else QFileDialog.getExistingDirectory(self, label))
                if p: _e.setText(p); self._dirty[_k] = p
            b = QPushButton("Browse"); b.setFixedWidth(64); b.clicked.connect(_br)
            right.addWidget(b); lay.addWidget(f); return e

        def _toggle_row(label, sublabel, key, default=False, on_change=None):
            f, right = _row(label, sublabel)
            cb = QCheckBox(); cb.setChecked(bool(s.get(key, default)))
            def _changed(v, k=key):
                self._dirty[k] = bool(v)
                if on_change: on_change(bool(v))
            cb.stateChanged.connect(_changed)
            right.addWidget(cb); lay.addWidget(f); return cb

        def _slider_row(label, sublabel, key, lo, hi, default, fmt="{:.0f}"):
            f, right = _row(label, sublabel)
            sl = QSlider(Qt.Orientation.Horizontal); sl.setRange(lo, hi)
            sl.setValue(int(s.get(key, default))); sl.setFixedWidth(160)
            val_l = QLabel(fmt.format(s.get(key, default)))
            val_l.setFixedWidth(54)
            val_l.setStyleSheet(f"color:{T['sync']}; font-weight:600; background:transparent;")
            sl.valueChanged.connect(lambda v, vl=val_l, k=key, ff=fmt: (
                vl.setText(ff.format(v)), self._dirty.__setitem__(k, v)))
            right.addWidget(sl); right.addWidget(val_l)
            lay.addWidget(f); return sl

        def _combo_row(label, sublabel, key, items, default=""):
            f, right = _row(label, sublabel)
            cb = QComboBox(); cb.addItems(items); cb.setFixedWidth(140)
            cur = s.get(key, default)
            idx = cb.findText(str(cur))
            if idx >= 0: cb.setCurrentIndex(idx)
            cb.currentTextChanged.connect(lambda v, k=key: self._dirty.__setitem__(k, v))
            right.addWidget(cb); lay.addWidget(f); return cb


        # ── SERVER ───────────────────────────────────────────────────────────
        lay.addWidget(_section_label("Server"))
        _browse_row("Server Folder",   "Path to your server .jar directory", "srv_path",  DEFAULT_SRV_PATH)
        _browse_row("Java Executable", "Full path or just 'java'",           "java_path", DEFAULT_JAVA_PATH, is_file=True)
        _slider_row("RAM (GB)",        "Heap memory for the server JVM",     "ram_gb",    1, 32, 2, "{:.0f} GB")
        _entry_row( "Server Port",     "Default: 25565",                     "server_port", "25565")
        _combo_row( "Server Type",     "Used for modpack search defaults",   "server_type",
                    ["paper","spigot","fabric","forge","quilt","neoforge","purpur","vanilla"], "paper")
        _entry_row( "MC Version",      "e.g. 1.21.4",                        "mc_version",  "1.21.4")
        _toggle_row("Online Mode",     "Require paid Minecraft account",     "online_mode", True)

        # ── GITHUB BACKUP ─────────────────────────────────────────────────────
        lay.addWidget(_section_label("GitHub Backup"))
        _entry_row( "Repo URL",              "https://github.com/user/repo.git", "repo_url", "")
        _toggle_row("Upload on stop",        "Push world to GitHub when server stops", "upload_on_stop", True)
        _toggle_row("Auto-upload",           "Periodic background git push",           "auto_upload",    False)
        _slider_row("Auto-upload interval",  "Minutes between auto uploads",           "auto_upload_mins", 5, 120, 10, "{:.0f} min")

        # ── GOOGLE DRIVE ──────────────────────────────────────────────────────
        lay.addWidget(_section_label("Google Drive (rclone)"))
        _entry_row("rclone remote",     "Name configured in rclone config", "gdrive_remote", "gdrive")
        _entry_row("Destination folder","Remote folder for backups",        "gdrive_folder", "MC_Backups")
        # Test button row
        tr, tright = _row("Test rclone", "Verify rclone can list remotes")
        tb2 = QPushButton("Test"); tb2.setFixedWidth(72); tb2.setFixedHeight(28)
        tb2.clicked.connect(self._test_rclone); tright.addWidget(tb2); lay.addWidget(tr)

        # ── APPEARANCE ────────────────────────────────────────────────────────
        lay.addWidget(_section_label("Appearance"))
        _toggle_row("Log panel on left",       "", "log_left",  False)
        _toggle_row("Show chat & events",      "", "show_chat", True)
        _toggle_row("Show performance stats",  "", "show_perf", True)
        _toggle_row("Fullscreen on launch",    "", "fullscreen", False)

        # ── REMOTE DASHBOARD ──────────────────────────────────────────────────
        lay.addWidget(_section_label("Remote Dashboard"))
        _entry_row("Web UI Port",     "Port for the remote control web UI", "remote_port",     "25580")
        _entry_row("Password",        "Blank = no auth (not recommended)",  "remote_password", "", password=True)

        # ── PLAYIT.GG ────────────────────────────────────────────────────────
        lay.addWidget(_section_label("playit.gg"))
        _browse_row("playit binary", "Path to the playit agent executable", "playit_path", "", is_file=True)

        # ── UPDATES ──────────────────────────────────────────────────────────
        lay.addWidget(_section_label("Updates"))
        ur, uright = _row(f"MC CTRL  v{APP_VERSION}", "Check for new releases on GitHub")
        chk_b = QPushButton("Check Now"); chk_b.setFixedWidth(100); chk_b.setFixedHeight(28)
        chk_b.clicked.connect(self._check_update); uright.addWidget(chk_b); lay.addWidget(ur)

        # ── ADDONS ───────────────────────────────────────────────────────────
        lay.addWidget(_section_label("Addons"))
        ar, aright = _row("Addons folder", "Drop .py addon scripts into addons/")
        open_b = QPushButton("Open Folder"); open_b.setFixedWidth(100); open_b.setFixedHeight(28)
        open_b.clicked.connect(lambda: self._open_folder(_ADDONS_DIR)); aright.addWidget(open_b)
        lay.addWidget(ar)

        # ── REPAIR ───────────────────────────────────────────────────────────
        lay.addWidget(_section_label("Repair & Maintenance"))
        rr, rright = _row("Repair", "Check Java, EULA, server.jar, git pull")
        repair_b = QPushButton("Run Repair"); repair_b.setFixedWidth(100); repair_b.setFixedHeight(28)
        repair_b.setObjectName("sync")
        repair_b.clicked.connect(lambda: threading.Thread(target=run_repair, daemon=True).start())
        rright.addWidget(repair_b)
        uninst_b = QPushButton("Uninstall…"); uninst_b.setFixedWidth(100); uninst_b.setFixedHeight(28)
        uninst_b.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{T['stop']};"
            f" border:1px solid {T['stop']}; border-radius:7px; }}")
        uninst_b.clicked.connect(self._uninstall_wizard); rright.addWidget(uninst_b)
        lay.addWidget(rr)

        # ── THEME CREATOR ────────────────────────────────────────────────────
        lay.addWidget(_section_label("Theme Creator"))
        tc_card = card()
        tc_card.layout().addWidget(lbl("Build a custom theme. Swatches update live.", muted=True))

        nm_row = QHBoxLayout()
        nm_row.addWidget(lbl("Name:", muted=True))
        self._tc_name = QLineEdit(); self._tc_name.setPlaceholderText("My Theme"); self._tc_name.setFixedWidth(200)
        nm_row.addWidget(self._tc_name); nm_row.addSpacing(16)
        nm_row.addWidget(lbl("Mode:", muted=True))
        self._tc_mode = QComboBox(); self._tc_mode.addItems(["dark","light"]); self._tc_mode.setFixedWidth(90)
        nm_row.addWidget(self._tc_mode); nm_row.addStretch()
        tc_card.layout().addLayout(nm_row)

        TC_FIELDS = [
            ("bg","#1a1a2e","Background"), ("card","#16213e","Card"),
            ("border","#0f3460","Border"), ("text","#e0e0e0","Text"),
            ("muted","#555555","Muted"),   ("start","#22c55e","Success"),
            ("stop","#ef4444","Danger"),   ("sync","#60a5fa","Accent"),
            ("handoff","#f59e0b","Warning"),
        ]
        self._tc_entries: dict[str, QLineEdit] = {}
        self._tc_swatches: dict[str, QLabel] = {}

        for key, default, desc in TC_FIELDS:
            fr = QHBoxLayout(); fr.setSpacing(8)
            dl = QLabel(desc); dl.setFixedWidth(110)
            dl.setStyleSheet(f"color:{T['text']}; font-size:11px; background:transparent;")
            fr.addWidget(dl)
            sw = QLabel(); sw.setFixedSize(28, 26)
            sw.setStyleSheet(f"background:{default}; border:1px solid {T['border']}; border-radius:5px;")
            fr.addWidget(sw); self._tc_swatches[key] = sw
            e = QLineEdit(default); e.setFixedWidth(110)
            e.textChanged.connect(lambda txt, k=key, s2=sw: self._tc_swatch_update(k, txt, s2))
            fr.addWidget(e); self._tc_entries[key] = e
            pb = QPushButton("Pick"); pb.setFixedWidth(46); pb.setFixedHeight(24)
            pb.clicked.connect(lambda _, k=key: self._tc_pick_color(k))
            fr.addWidget(pb); fr.addStretch()
            tc_card.layout().addLayout(fr)

        tc_btns = QHBoxLayout()
        stb = QPushButton("Save Theme"); stb.setFixedHeight(30)
        stb.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:7px; font-weight:700; }}")
        stb.clicked.connect(self._tc_save)
        atb = QPushButton("Apply Now"); atb.setFixedHeight(30)
        atb.clicked.connect(self._tc_apply)
        tc_btns.addWidget(stb); tc_btns.addWidget(atb); tc_btns.addStretch()
        tc_card.layout().addLayout(tc_btns)
        lay.addWidget(tc_card)
        lay.addStretch()

        # ── Save bar ─────────────────────────────────────────────────────────
        save_bar = QFrame(); save_bar.setObjectName("ip_bar"); save_bar.setFixedHeight(48)
        sbl = QHBoxLayout(save_bar); sbl.setContentsMargins(14, 0, 14, 0); sbl.setSpacing(8)
        self._saved_lbl = QLabel(""); self._saved_lbl.setStyleSheet(f"color:{T['start']}; background:transparent;")
        sbl.addWidget(self._saved_lbl); sbl.addStretch()
        apply_b = QPushButton("Save Settings"); apply_b.setFixedHeight(34)
        apply_b.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{T['muted']};"
            f" border:1px solid {T['border']}; border-radius:7px; padding:0 14px; }}"
            f"QPushButton:hover {{ color:{T['text']}; border-color:{T['sync']}; }}")
        apply_b.clicked.connect(lambda: (self._save_all(), _toast("Restart the app to apply all changes", T["handoff"])))
        sbl.addWidget(apply_b)
        save_b2 = QPushButton("Save Settings"); save_b2.setFixedHeight(34)
        save_b2.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; padding:0 18px; font-weight:700; }}")
        save_b2.clicked.connect(self._save_all)
        sbl.addWidget(save_b2)
        root.addWidget(save_bar)

    # ── Save ─────────────────────────────────────────────────────────────────
    def _save_all(self):
        snap = load_settings(); snap.update(self._dirty)
        save_settings(snap); self._dirty.clear()
        self._saved_lbl.setText("Saved")
        # Apply auto-upload if changed
        if snap.get("auto_upload"): schedule_auto_upload()
        QTimer.singleShot(1800, lambda: self._saved_lbl.setText(""))
        _toast("Settings saved!", T["start"])

    # ── Actions ──────────────────────────────────────────────────────────────
    def _test_rclone(self):
        import subprocess
        from core.constants import CREATE_NO_WINDOW
        def _work():
            try:
                r = subprocess.run("rclone listremotes", shell=True, capture_output=True,
                                   text=True, timeout=8, creationflags=CREATE_NO_WINDOW)
                result = r.stdout.strip() or "rclone returned no remotes"
                _toast(result[:80], T["sync"])
            except FileNotFoundError:
                _toast("rclone not found - install from rclone.org", T["stop"])
        threading.Thread(target=_work, daemon=True).start()

    def _check_update(self):
        from core.updater import UpdateCheckerThread
        t = UpdateCheckerThread()
        t.update_found.connect(lambda v, u: _toast(f"Update v{v} available: {u}", T["handoff"], 6000))
        t.up_to_date.connect(lambda: _toast(f"MC CTRL is up to date (v{APP_VERSION})", T["start"]))
        t.start()

    def _open_folder(self, path: str):
        import sys, subprocess
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception: pass

    def _uninstall_wizard(self):
        dlg = QDialog(self); dlg.setWindowTitle("Uninstall / Cleanup Wizard"); dlg.resize(440, 300)
        dlg.setStyleSheet(f"QDialog {{ background:{T['bg']}; }} QWidget {{ background:{T['bg']}; color:{T['text']}; }} QLabel {{ background:transparent; }} QPushButton {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:5px 14px; }}")
        dl = QVBoxLayout(dlg); dl.setContentsMargins(24, 20, 24, 20); dl.setSpacing(10)
        tl = QLabel("Uninstall / Cleanup"); f = tl.font(); f.setPointSize(14); f.setBold(True); tl.setFont(f)
        tl.setStyleSheet(f"color:{T['stop']}; background:transparent;")
        dl.addWidget(tl)
        dl.addWidget(lbl("Choose what to remove:", muted=True))
        v_settings = QCheckBox("Launcher settings (settings.json)"); v_settings.setChecked(True)
        v_addons   = QCheckBox("Addons folder")
        v_server   = QCheckBox("Server data folder (DESTRUCTIVE - deletes world!)")
        for cb in (v_settings, v_addons, v_server): dl.addWidget(cb)
        br = QHBoxLayout(); br.addStretch()
        cancel_b = QPushButton("Cancel"); cancel_b.clicked.connect(dlg.reject); br.addWidget(cancel_b)
        confirm_b = QPushButton("Confirm Removal")
        confirm_b.setStyleSheet(f"QPushButton {{ background:{T['stop']}; color:#fff; border:none; font-weight:700; }}")
        def _do():
            removed = []
            if v_settings.isChecked():
                try: os.remove(SETTINGS_FILE); removed.append("settings.json")
                except Exception: pass
            if v_addons.isChecked():
                try: shutil.rmtree(_ADDONS_DIR); removed.append("addons/")
                except Exception: pass
            if v_server.isChecked():
                spath = load_settings().get("srv_path", DEFAULT_SRV_PATH)
                if os.path.isdir(spath):
                    try: shutil.rmtree(spath); removed.append(spath)
                    except Exception as ex: _toast(f"Could not remove: {ex}", T["stop"])
            dlg.accept()
            _toast(f"Removed: {', '.join(removed) if removed else 'nothing'}", T["stop"])
        confirm_b.clicked.connect(_do); br.addWidget(confirm_b)
        dl.addLayout(br); dlg.exec()

    # ── Theme Creator helpers ─────────────────────────────────────────────────
    def _tc_swatch_update(self, key: str, txt: str, swatch: QLabel):
        txt = txt.strip()
        if re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', txt):
            try: swatch.setStyleSheet(f"background:{txt}; border:1px solid {T['border']}; border-radius:4px;")
            except Exception: pass

    def _tc_pick_color(self, key: str):
        current = self._tc_entries[key].text().strip() or "#ffffff"
        from PyQt6.QtGui import QColor
        dlg = QColorDialog(QColor(current), self)
        if dlg.exec() == QColorDialog.DialogCode.Accepted:
            hex_c = dlg.selectedColor().name()
            self._tc_entries[key].setText(hex_c)

    def _tc_save(self):
        name = self._tc_name.text().strip()
        if not name: _toast("Enter a theme name!", T["stop"]); return
        for key, e in self._tc_entries.items():
            if not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', e.text().strip()):
                _toast(f"Invalid hex for {key}: {e.text()}", T["stop"]); return
        td = {"appearance": self._tc_mode.currentText(),
              **{k: e.text().strip() for k, e in self._tc_entries.items()}}
        THEMES[name] = td
        # Persist to settings
        s = load_settings(); s.setdefault("custom_themes", {})[name] = td; save_settings(s)
        _toast(f'Theme "{name}" saved!', T["start"])

    def _tc_apply(self):
        name = self._tc_name.text().strip() or "_preview"
        for key, e in self._tc_entries.items():
            if not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', e.text().strip()):
                _toast(f"Fix {key} first", T["stop"]); return
        td = {"appearance": self._tc_mode.currentText(),
              **{k: e.text().strip() for k, e in self._tc_entries.items()}}
        THEMES[name] = td
        w = _win()
        if w: w.apply_theme(name)
