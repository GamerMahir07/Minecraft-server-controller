"""ui/settings_tab.py — full Settings tab matching reference launcher"""
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

        # ── helpers ──────────────────────────────────────────────────────────
        def _entry(parent_c, label_txt, key, default="", width=320, password=False, ph=""):
            r = QHBoxLayout(); r.setSpacing(8)
            l = QLabel(label_txt); l.setFixedWidth(200)
            l.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
            r.addWidget(l)
            e = QLineEdit(str(s.get(key, default)))
            if password: e.setEchoMode(QLineEdit.EchoMode.Password)
            if ph: e.setPlaceholderText(ph)
            e.setFixedWidth(width)
            e.editingFinished.connect(lambda k=key, le=e: self._dirty.__setitem__(k, le.text().strip()))
            r.addWidget(e)
            if password:
                show_b = QPushButton("Show"); show_b.setFixedWidth(46); show_b.setFixedHeight(24)
                def _tog(_e=e, _b=show_b):
                    if _e.echoMode() == QLineEdit.EchoMode.Password:
                        _e.setEchoMode(QLineEdit.EchoMode.Normal); _b.setText("Hide")
                    else:
                        _e.setEchoMode(QLineEdit.EchoMode.Password); _b.setText("Show")
                show_b.clicked.connect(_tog); r.addWidget(show_b)
            r.addStretch()
            parent_c.layout().addLayout(r)
            return e

        def _browse(parent_c, label_txt, key, default="", is_file=False):
            r = QHBoxLayout(); r.setSpacing(8)
            l = QLabel(label_txt); l.setFixedWidth(200)
            l.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
            r.addWidget(l)
            e = QLineEdit(str(s.get(key, default))); e.setFixedWidth(280)
            e.editingFinished.connect(lambda k=key, le=e: self._dirty.__setitem__(k, le.text().strip()))
            r.addWidget(e)
            def _br(_e=e, _k=key, _f=is_file):
                p = (QFileDialog.getOpenFileName(self, label_txt)[0] if _f
                     else QFileDialog.getExistingDirectory(self, label_txt))
                if p: _e.setText(p); self._dirty[_k] = p
            b = QPushButton("Browse"); b.setFixedWidth(70); b.clicked.connect(_br); r.addWidget(b)
            r.addStretch(); parent_c.layout().addLayout(r)
            return e

        def _toggle(parent_c, label_txt, key, default=False):
            r = QHBoxLayout()
            l = QLabel(label_txt); l.setFixedWidth(300)
            l.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
            r.addWidget(l); r.addStretch()
            cb = QCheckBox(); cb.setChecked(bool(s.get(key, default)))
            cb.stateChanged.connect(lambda v, k=key: self._dirty.__setitem__(k, bool(v)))
            r.addWidget(cb); parent_c.layout().addLayout(r); return cb

        def _slider(parent_c, label_txt, key, lo, hi, default, fmt="{:.0f}"):
            r = QHBoxLayout(); r.setSpacing(8)
            l = QLabel(label_txt); l.setFixedWidth(200)
            l.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
            r.addWidget(l)
            sl = QSlider(Qt.Orientation.Horizontal); sl.setRange(lo, hi)
            sl.setValue(int(s.get(key, default))); sl.setFixedWidth(200)
            val_l = QLabel(fmt.format(s.get(key, default)))
            val_l.setFixedWidth(60); val_l.setStyleSheet(f"color:{T['sync']}; background:transparent;")
            sl.valueChanged.connect(lambda v, vl=val_l, k=key, f=fmt: (
                vl.setText(f.format(v)), self._dirty.__setitem__(k, v)))
            r.addWidget(sl); r.addWidget(val_l); r.addStretch()
            parent_c.layout().addLayout(r); return sl

        def _section(title):
            c = card(); c.layout().addWidget(lbl(title, header=True)); c.layout().addWidget(hline())
            return c

        # ── Server ──────────────────────────────────────────────────────────
        sc = _section("SERVER")
        _browse(sc, "Server Folder",    "srv_path",   DEFAULT_SRV_PATH)
        _browse(sc, "Java Executable",  "java_path",  DEFAULT_JAVA_PATH, is_file=True)
        _slider(sc, "RAM (GB)",         "server_ram_gb", 1, 32, 2, "{:.0f} GB")
        _entry( sc, "Server Port",      "server_port",   "25565", width=100)
        _entry( sc, "Server Type",      "server_type",   "paper",  width=140)
        _entry( sc, "MC Version",       "mc_version",    "1.20.1", width=120)
        _toggle(sc, "Online Mode (require paid account)", "online_mode", True)
        lay.addWidget(sc)

        # ── GitHub Backup ────────────────────────────────────────────────────
        gc = _section("GITHUB BACKUP")
        _entry( gc, "GitHub Repo URL",       "repo_url",        "",    width=360, ph="https://github.com/user/repo.git")
        _toggle(gc, "Upload world on server stop", "upload_on_stop",  True)
        _toggle(gc, "Enable auto-upload",          "auto_upload",     False)
        _slider(gc, "Auto-upload interval (mins)", "auto_upload_mins", 5, 120, 10, "{:.0f} min")
        lay.addWidget(gc)

        # ── Google Drive ─────────────────────────────────────────────────────
        gdc = _section("GOOGLE DRIVE BACKUP (via rclone)")
        _entry(gdc, "rclone remote name",    "gdrive_remote", "gdrive",     width=160)
        _entry(gdc, "Destination folder",    "gdrive_folder", "MC_Backups", width=200)
        note = lbl("Run:  rclone config  — to set up your Google Drive remote.", muted=True)
        gdc.layout().addWidget(note)
        test_b = QPushButton("Test rclone"); test_b.setFixedWidth(110); test_b.setFixedHeight(26)
        test_b.clicked.connect(self._test_rclone); gdc.layout().addWidget(test_b)
        lay.addWidget(gdc)

        # ── Appearance ───────────────────────────────────────────────────────
        apc = _section("APPEARANCE")
        _toggle(apc, "Log panel on left",          "log_left",   False)
        _toggle(apc, "Show chat & events panel",   "show_chat",  True)
        _toggle(apc, "Show performance stats",     "show_perf",  True)
        _toggle(apc, "Mini / compact mode",        "mini_mode",  False)
        _toggle(apc, "Fullscreen on launch",       "fullscreen", False)

        # Glossy UI toggle — applies immediately
        glossy_row = QHBoxLayout(); glossy_row.setContentsMargins(0, 2, 0, 2)
        glossy_lbl = QLabel("Glossy UI"); glossy_lbl.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
        glossy_row.addWidget(glossy_lbl); glossy_row.addStretch()
        glossy_cb = QCheckBox()
        glossy_cb.setChecked(load_settings().get("glossy_ui", False))
        def _on_glossy(state):
            w = _win()
            if w: w.apply_glossy(bool(state))
        glossy_cb.stateChanged.connect(_on_glossy)
        glossy_row.addWidget(glossy_cb)
        apc.layout().addLayout(glossy_row)

        # Side tabs toggle — applies immediately
        sidetab_row = QHBoxLayout(); sidetab_row.setContentsMargins(0, 2, 0, 2)
        sidetab_lbl = QLabel("Tabs on left side"); sidetab_lbl.setStyleSheet(f"color:{T['text']}; font-size:12px; background:transparent;")
        sidetab_row.addWidget(sidetab_lbl); sidetab_row.addStretch()
        sidetab_cb = QCheckBox()
        sidetab_cb.setChecked(load_settings().get("side_tabs", False))
        def _on_sidetabs(state):
            w = _win()
            if w: w.apply_side_tabs(bool(state))
        sidetab_cb.stateChanged.connect(_on_sidetabs)
        sidetab_row.addWidget(sidetab_cb)
        apc.layout().addLayout(sidetab_row)

        lay.addWidget(apc)

        # ── Remote Dashboard ─────────────────────────────────────────────────
        rdc = _section("REMOTE DASHBOARD")
        _entry(rdc, "Web UI Port",           "remote_port",     "25580", width=100)
        _entry(rdc, "Password (blank=none)", "remote_password", "",      width=200, password=True)
        lay.addWidget(rdc)

        # ── playit.gg ────────────────────────────────────────────────────────
        ptc = _section("PLAYIT.GG")
        _browse(ptc, "playit binary path", "playit_path", "", is_file=True)
        lay.addWidget(ptc)

        # ── Updates ──────────────────────────────────────────────────────────
        upc = _section("UPDATES")
        ur = QHBoxLayout()
        ur.addWidget(lbl(f"MC CTRL  v{APP_VERSION}", muted=True))
        chk_b = QPushButton("Check for Updates"); chk_b.setFixedHeight(28)
        chk_b.clicked.connect(self._check_update); ur.addWidget(chk_b)
        ur.addStretch(); upc.layout().addLayout(ur)
        lay.addWidget(upc)

        # ── Addons ───────────────────────────────────────────────────────────
        adc = _section("ADDONS")
        adc.layout().addWidget(lbl("Drop .py addon scripts into the 'addons/' folder next to the launcher.", muted=True))
        open_addons_b = QPushButton("Open addons/"); open_addons_b.setFixedWidth(120); open_addons_b.setFixedHeight(28)
        open_addons_b.clicked.connect(lambda: self._open_folder(_ADDONS_DIR))
        adc.layout().addWidget(open_addons_b)
        lay.addWidget(adc)

        # ── Repair & Maintenance ─────────────────────────────────────────────
        rpc = _section("REPAIR & MAINTENANCE")
        mb = QHBoxLayout()
        repair_b = QPushButton("Run Repair"); repair_b.setFixedHeight(30)
        repair_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['sync']}; border:1px solid {T['sync']}; border-radius:6px; }}")
        repair_b.clicked.connect(lambda: threading.Thread(target=run_repair, daemon=True).start())
        mb.addWidget(repair_b)
        uninst_b = QPushButton("Uninstall Wizard"); uninst_b.setFixedHeight(30)
        uninst_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:6px; }}")
        uninst_b.clicked.connect(self._uninstall_wizard)
        mb.addWidget(uninst_b); mb.addStretch(); rpc.layout().addLayout(mb)
        lay.addWidget(rpc)

        # ── Theme Creator ────────────────────────────────────────────────────
        tcc = _section("THEME CREATOR")
        tcc.layout().addWidget(lbl("Build a custom theme. Color swatches update live as you type.", muted=True))

        name_mode_row = QHBoxLayout()
        name_mode_row.addWidget(lbl("Name:", muted=True))
        self._tc_name = QLineEdit(); self._tc_name.setPlaceholderText("My Theme"); self._tc_name.setFixedWidth(200)
        name_mode_row.addWidget(self._tc_name)
        name_mode_row.addSpacing(16)
        name_mode_row.addWidget(lbl("Mode:", muted=True))
        self._tc_mode = QComboBox(); self._tc_mode.addItems(["dark", "light"]); self._tc_mode.setFixedWidth(90)
        name_mode_row.addWidget(self._tc_mode); name_mode_row.addStretch()
        tcc.layout().addLayout(name_mode_row)

        TC_FIELDS = [
            ("bg",      "#1a1a2e", "Background"),
            ("card",    "#16213e", "Card / panel"),
            ("border",  "#0f3460", "Border"),
            ("text",    "#e0e0e0", "Text"),
            ("muted",   "#555555", "Muted text"),
            ("start",   "#22c55e", "Start / success"),
            ("stop",    "#ef4444", "Stop / danger"),
            ("sync",    "#60a5fa", "Sync / accent"),
            ("handoff", "#f59e0b", "Warning / handoff"),
        ]
        self._tc_entries: dict[str, QLineEdit] = {}
        self._tc_swatches: dict[str, QLabel] = {}

        for key, default, desc in TC_FIELDS:
            fr = QHBoxLayout(); fr.setSpacing(8)
            desc_l = QLabel(desc); desc_l.setFixedWidth(150)
            desc_l.setStyleSheet(f"color:{T['text']}; font-size:11px; background:transparent;")
            fr.addWidget(desc_l)
            swatch = QLabel(); swatch.setFixedSize(28, 26)
            swatch.setStyleSheet(f"background:{default}; border:1px solid {T['border']}; border-radius:4px;")
            fr.addWidget(swatch)
            self._tc_swatches[key] = swatch
            e = QLineEdit(default); e.setFixedWidth(110)
            e.textChanged.connect(lambda txt, k=key, sw=swatch: self._tc_swatch_update(k, txt, sw))
            fr.addWidget(e)
            self._tc_entries[key] = e
            pick_b = QPushButton("Pick"); pick_b.setFixedWidth(46); pick_b.setFixedHeight(24)
            pick_b.clicked.connect(lambda _, k=key: self._tc_pick_color(k))
            fr.addWidget(pick_b); fr.addStretch()
            tcc.layout().addLayout(fr)

        tc_btns = QHBoxLayout()
        save_theme_b = QPushButton("Save to themes.py"); save_theme_b.setFixedHeight(30)
        save_theme_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        save_theme_b.clicked.connect(self._tc_save)
        apply_theme_b = QPushButton("Apply Now"); apply_theme_b.setFixedHeight(30)
        apply_theme_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['muted']}; border:1px solid {T['border']}; border-radius:6px; }}")
        apply_theme_b.clicked.connect(self._tc_apply)
        tc_btns.addWidget(save_theme_b); tc_btns.addWidget(apply_theme_b); tc_btns.addStretch()
        tcc.layout().addLayout(tc_btns)
        lay.addWidget(tcc)
        lay.addStretch()

        # ── Save bar ─────────────────────────────────────────────────────────
        save_bar = QFrame(); save_bar.setObjectName("ip_bar"); save_bar.setFixedHeight(48)
        sbl = QHBoxLayout(save_bar); sbl.setContentsMargins(14, 0, 14, 0); sbl.setSpacing(8)
        self._saved_lbl = QLabel(""); self._saved_lbl.setStyleSheet(f"color:{T['start']}; background:transparent;")
        sbl.addWidget(self._saved_lbl); sbl.addStretch()
        apply_b = QPushButton("Apply & Restart UI"); apply_b.setFixedHeight(34)
        apply_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['muted']}; border:1px solid {T['border']}; border-radius:6px; padding:0 14px; }}")
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
