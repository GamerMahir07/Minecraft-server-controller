"""ui/server_info.py — Server Info tab: Players, Properties, Whitelist, Bans, Ops, Backup, Mod/Plugin props, Server Icon"""
import json, os, re, subprocess, threading, zipfile
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QLineEdit, QComboBox, QFileDialog,
    QMessageBox, QTabWidget, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from core.themes import T
from core.settings import load_settings
from core.server import send_server_cmd, backup_to_zip, _backup_to_gdrive, online_players
from core.constants import DEFAULT_SRV_PATH, CREATE_NO_WINDOW
from .widgets import make_scroll, card, hline, lbl, btn, LogWidget

def _win():
    from .main_window import WIN
    return WIN

def _toast(msg, color=None, ms=3000):
    w = _win()
    if w: w.toast(msg, color or T["sync"], ms)

def _open_folder(path):
    import sys, subprocess
    try:
        if sys.platform == "win32": os.startfile(path)
        elif sys.platform == "darwin": subprocess.Popen(["open", path])
        else: subprocess.Popen(["xdg-open", path])
    except Exception: pass


class ServerInfoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll, inner, lay = make_scroll()
        root.addWidget(scroll)
        inner.setLayout(lay)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)

        # Row 0
        grid.addWidget(self._build_players(), 0, 0)
        grid.addWidget(self._build_properties(), 0, 1)

        # Row 1
        grid.addWidget(self._build_whitelist(), 1, 0)
        grid.addWidget(self._build_bans(), 1, 1)

        # Row 2
        grid.addWidget(self._build_ops(), 2, 0)
        grid.addWidget(self._build_backup(), 2, 1)

        # Row 3
        grid.addWidget(self._build_mod_props(), 3, 0)
        grid.addWidget(self._build_server_icon(), 3, 1)

        lay.addStretch()

        # Auto-refresh players
        self._player_timer = QTimer(self)
        self._player_timer.setInterval(3000)
        self._player_timer.timeout.connect(self._refresh_players)
        self._player_timer.start()

    # ── Players ───────────────────────────────────────────────────────────────
    def _build_players(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Online Players", header=True))
        self._p_count = lbl("0 online", muted=True)
        hdr.addStretch()
        hdr.addWidget(self._p_count)
        self._pview = "list"
        self._pview_btn = QPushButton("Grid View")
        self._pview_btn.setFixedWidth(84)
        self._pview_btn.clicked.connect(self._toggle_pview)
        hdr.addWidget(self._pview_btn)
        refresh_b = QPushButton("Refresh")
        refresh_b.setFixedWidth(68)
        refresh_b.clicked.connect(lambda: (send_server_cmd("list"), _toast("Refreshed", T["sync"])))
        hdr.addWidget(refresh_b)
        c.layout().addLayout(hdr)
        c.layout().addWidget(hline())
        self._player_scroll_w = QWidget()
        self._player_lay = QVBoxLayout(self._player_scroll_w)
        self._player_lay.setContentsMargins(0, 0, 0, 0)
        self._player_lay.setSpacing(3)
        pscroll = QScrollArea(); pscroll.setWidgetResizable(True); pscroll.setFixedHeight(180)
        pscroll.setFrameShape(QFrame.Shape.NoFrame); pscroll.setWidget(self._player_scroll_w)
        c.layout().addWidget(pscroll)
        self._refresh_players()
        return c

    def _toggle_pview(self):
        self._pview = "grid" if self._pview == "list" else "list"
        self._pview_btn.setText("List View" if self._pview == "grid" else "Grid View")
        self._refresh_players()

    def _refresh_players(self):
        while self._player_lay.count():
            item = self._player_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._p_count.setText(f"{len(online_players)} online")
        if not online_players:
            self._player_lay.addWidget(lbl("No players online", muted=True))
            return
        if self._pview == "grid":
            grid_w = QWidget(); gl = QGridLayout(grid_w); gl.setSpacing(4)
            COLS = 3
            for i, (name, joined) in enumerate(list(online_players.items())):
                row, col = i // COLS, i % COLS
                cell = QFrame(); cell.setObjectName("card")
                cl = QVBoxLayout(cell); cl.setContentsMargins(6, 6, 6, 6); cl.setSpacing(3)
                nl = QLabel(name); nl.setStyleSheet(f"color:{T['text']}; font-weight:700; background:transparent;"); cl.addWidget(nl)
                sl = QLabel(f"since {joined}"); sl.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;"); cl.addWidget(sl)
                btn_row = QHBoxLayout()
                for txt, cmd_txt, color in [("Kick","kick",T["stop"]),("Op","op",T["handoff"]),("Ban","ban",T["stop"])]:
                    b = QPushButton(txt); b.setFixedSize(44, 22)
                    b.setStyleSheet(f"QPushButton {{ background:transparent; color:{color}; border:1px solid {color}; border-radius:4px; font-size:9px; }}")
                    b.clicked.connect(lambda _, n=name, cmd=cmd_txt: send_server_cmd(f"{cmd} {n}"))
                    btn_row.addWidget(b)
                cl.addLayout(btn_row)
                gl.addWidget(cell, row, col)
            for c_i in range(COLS): gl.setColumnStretch(c_i, 1)
            self._player_lay.addWidget(grid_w)
        else:
            for name, joined in list(online_players.items()):
                row = QFrame(); row.setObjectName("card")
                rl = QHBoxLayout(row); rl.setContentsMargins(8, 5, 8, 5)
                nl = QLabel(name); nl.setStyleSheet(f"color:{T['text']}; font-weight:700; background:transparent;"); rl.addWidget(nl)
                jl = QLabel(f"joined {joined}"); jl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;"); rl.addWidget(jl)
                rl.addStretch()
                for txt, cmd_txt, color in [("Kick","kick",T["stop"]),("Ban","ban",T["stop"]),("Op","op",T["handoff"]),("Msg","msg",T["sync"])]:
                    b = QPushButton(txt); b.setFixedSize(42, 22)
                    b.setStyleSheet(f"QPushButton {{ background:transparent; color:{color}; border:1px solid {color}; border-radius:4px; font-size:9px; }}")
                    b.clicked.connect(lambda _, n=name, cmd=cmd_txt: send_server_cmd(f"{cmd} {n}"))
                    rl.addWidget(b)
                self._player_lay.addWidget(row)
        self._player_lay.addStretch()

    # ── Properties ────────────────────────────────────────────────────────────
    def _build_properties(self):
        c = card()
        hdr = QHBoxLayout()
        hdr.addWidget(lbl("server.properties", header=True)); hdr.addStretch()
        save_b = QPushButton("Save"); save_b.setFixedWidth(54)
        save_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; }}")
        save_b.clicked.connect(self._save_props)
        hdr.addWidget(save_b)
        reload_b = QPushButton("Reload"); reload_b.setFixedWidth(58)
        reload_b.clicked.connect(self._load_props)
        hdr.addWidget(reload_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        props_w = QWidget(); self._props_lay = QGridLayout(props_w)
        self._props_lay.setSpacing(3)
        self._props_lay.setColumnStretch(1, 1)
        props_scroll = QScrollArea(); props_scroll.setWidgetResizable(True); props_scroll.setFixedHeight(220)
        props_scroll.setFrameShape(QFrame.Shape.NoFrame); props_scroll.setWidget(props_w)
        c.layout().addWidget(props_scroll)

        self._prop_widgets: dict[str, QWidget] = {}
        self._load_props()
        return c

    _KEY_PROPS = [
        ("server-port","Port","25565"),("max-players","Max Players","20"),
        ("difficulty","Difficulty","normal"),("gamemode","Gamemode","survival"),
        ("motd","MOTD","A Minecraft Server"),("level-name","Level Name","world"),
        ("view-distance","View Distance","10"),("spawn-protection","Spawn Protection","16"),
        ("pvp","PvP","true"),("white-list","Whitelist","false"),
        ("enable-command-block","Command Blocks","false"),("allow-flight","Allow Flight","false"),
    ]
    _PROP_VALUES = {
        "difficulty": ["peaceful","easy","normal","hard"],
        "gamemode": ["survival","creative","adventure","spectator"],
    }

    def _load_props(self):
        if not hasattr(self, '_prop_widgets'): return
        # Clear layout
        while self._props_lay.count():
            item = self._props_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._prop_widgets.clear()

        data = {}
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            for line in open(os.path.join(path, "server.properties"), encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1); data[k.strip()] = v.strip()
        except Exception:
            pass

        for i, (key, label, default) in enumerate(self._KEY_PROPS):
            lbl_w = QLabel(label); lbl_w.setStyleSheet(f"color:{T['text']}; background:transparent; font-size:11px;")
            self._props_lay.addWidget(lbl_w, i, 0)
            val = data.get(key, default)
            if key in self._PROP_VALUES:
                w = QComboBox(); w.addItems(self._PROP_VALUES[key])
                idx = w.findText(val)
                if idx >= 0: w.setCurrentIndex(idx)
            else:
                w = QLineEdit(val)
            self._props_lay.addWidget(w, i, 1)
            self._prop_widgets[key] = w

    def _save_props(self):
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            prop_file = os.path.join(path, "server.properties")
            if not os.path.exists(prop_file):
                _toast("server.properties not found!", T["stop"]); return
            txt = open(prop_file, encoding="utf-8").read()
            for key, w in self._prop_widgets.items():
                val = w.currentText() if isinstance(w, QComboBox) else w.text()
                if re.search(rf'^{re.escape(key)}=', txt, re.M):
                    txt = re.sub(rf'^{re.escape(key)}=.*$', f"{key}={val}", txt, flags=re.M)
                else:
                    txt += f"\n{key}={val}"
            with open(prop_file, "w", encoding="utf-8") as f: f.write(txt)
            _toast("Properties saved - restart to apply", T["handoff"])
        except Exception as ex:
            _toast(f"Save failed: {ex}", T["stop"])

    # ── Whitelist ─────────────────────────────────────────────────────────────
    def _build_whitelist(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("Whitelist", header=True)); hdr.addStretch()
        add_b = QPushButton("+ Add"); add_b.setFixedWidth(52)
        add_b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; }}")
        add_b.clicked.connect(self._wl_add)
        hdr.addWidget(add_b)
        refresh_b = QPushButton("Refresh"); refresh_b.setFixedWidth(58); refresh_b.clicked.connect(self._load_wl); hdr.addWidget(refresh_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())
        self._wl_add_edit = QLineEdit(); self._wl_add_edit.setPlaceholderText("username to add...")
        self._wl_add_edit.returnPressed.connect(self._wl_add)
        c.layout().addWidget(self._wl_add_edit)
        self._wl_list_w = QWidget(); self._wl_lay = QVBoxLayout(self._wl_list_w); self._wl_lay.setContentsMargins(0,0,0,0); self._wl_lay.setSpacing(2)
        ws = QScrollArea(); ws.setWidgetResizable(True); ws.setFixedHeight(120); ws.setFrameShape(QFrame.Shape.NoFrame); ws.setWidget(self._wl_list_w)
        c.layout().addWidget(ws)
        self._load_wl()
        return c

    def _load_wl(self):
        while self._wl_lay.count():
            item = self._wl_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            data = json.loads(open(os.path.join(path, "whitelist.json"), encoding="utf-8").read())
            for entry in data:
                name = entry.get("name", "?")
                row = QFrame(); row.setObjectName("card")
                rl = QHBoxLayout(row); rl.setContentsMargins(8, 4, 8, 4)
                rl.addWidget(QLabel(name))
                rl.addStretch()
                rb = QPushButton("Remove"); rb.setFixedSize(58, 22)
                rb.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:4px; font-size:9px; }}")
                rb.clicked.connect(lambda _, n=name: (send_server_cmd(f"whitelist remove {n}"), QTimer.singleShot(600, self._load_wl)))
                rl.addWidget(rb)
                self._wl_lay.addWidget(row)
        except Exception:
            self._wl_lay.addWidget(lbl("whitelist.json not found", muted=True))

    def _wl_add(self):
        n = self._wl_add_edit.text().strip()
        if n:
            send_server_cmd(f"whitelist add {n}"); self._wl_add_edit.clear()
            QTimer.singleShot(800, self._load_wl)

    # ── Bans ──────────────────────────────────────────────────────────────────
    def _build_bans(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("Banned Players", header=True)); hdr.addStretch()
        rb2 = QPushButton("Refresh"); rb2.setFixedWidth(58); rb2.clicked.connect(self._load_bans); hdr.addWidget(rb2)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())
        self._bn_list_w = QWidget(); self._bn_lay = QVBoxLayout(self._bn_list_w); self._bn_lay.setContentsMargins(0,0,0,0); self._bn_lay.setSpacing(2)
        bs = QScrollArea(); bs.setWidgetResizable(True); bs.setFixedHeight(120); bs.setFrameShape(QFrame.Shape.NoFrame); bs.setWidget(self._bn_list_w)
        c.layout().addWidget(bs)
        self._load_bans()
        return c

    def _load_bans(self):
        while self._bn_lay.count():
            item = self._bn_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            data = json.loads(open(os.path.join(path, "banned-players.json"), encoding="utf-8").read())
            for entry in data:
                name = entry.get("name", "?"); reason = entry.get("reason", "--")
                row = QFrame(); row.setObjectName("card")
                rl = QHBoxLayout(row); rl.setContentsMargins(8, 4, 8, 4)
                nl = QLabel(name); nl.setStyleSheet(f"color:{T['stop']}; font-weight:700; background:transparent;"); rl.addWidget(nl)
                rl.addWidget(lbl(reason[:40], muted=True)); rl.addStretch()
                pb = QPushButton("Pardon"); pb.setFixedSize(54, 22)
                pb.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['start']}; border:1px solid {T['start']}; border-radius:4px; font-size:9px; }}")
                pb.clicked.connect(lambda _, n=name: (send_server_cmd(f"pardon {n}"), QTimer.singleShot(800, self._load_bans)))
                rl.addWidget(pb)
                self._bn_lay.addWidget(row)
        except Exception:
            self._bn_lay.addWidget(lbl("banned-players.json not found", muted=True))

    # ── Ops ───────────────────────────────────────────────────────────────────
    def _build_ops(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("OPs", header=True)); hdr.addStretch()
        op_add_b = QPushButton("+ Op"); op_add_b.setFixedWidth(48)
        op_add_b.setStyleSheet(f"QPushButton {{ background:{T['handoff']}; color:#000; border:none; border-radius:6px; }}")
        op_add_b.clicked.connect(self._op_add); hdr.addWidget(op_add_b)
        rb3 = QPushButton("Refresh"); rb3.setFixedWidth(58); rb3.clicked.connect(self._load_ops); hdr.addWidget(rb3)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())
        self._op_add_edit = QLineEdit(); self._op_add_edit.setPlaceholderText("username to op...")
        self._op_add_edit.returnPressed.connect(self._op_add); c.layout().addWidget(self._op_add_edit)
        self._op_list_w = QWidget(); self._op_lay = QVBoxLayout(self._op_list_w); self._op_lay.setContentsMargins(0,0,0,0); self._op_lay.setSpacing(2)
        os2 = QScrollArea(); os2.setWidgetResizable(True); os2.setFixedHeight(100); os2.setFrameShape(QFrame.Shape.NoFrame); os2.setWidget(self._op_list_w)
        c.layout().addWidget(os2)
        self._load_ops()
        return c

    def _load_ops(self):
        while self._op_lay.count():
            item = self._op_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            data = json.loads(open(os.path.join(path, "ops.json"), encoding="utf-8").read())
            for entry in data:
                name = entry.get("name", "?"); lvl = entry.get("level", 4)
                row = QFrame(); row.setObjectName("card")
                rl = QHBoxLayout(row); rl.setContentsMargins(8, 4, 8, 4)
                nl = QLabel(f"* {name}"); nl.setStyleSheet(f"color:{T['handoff']}; font-weight:700; background:transparent;"); rl.addWidget(nl)
                rl.addWidget(lbl(f"lvl {lvl}", muted=True)); rl.addStretch()
                db = QPushButton("De-op"); db.setFixedSize(50, 22)
                db.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:4px; font-size:9px; }}")
                db.clicked.connect(lambda _, n=name: (send_server_cmd(f"deop {n}"), QTimer.singleShot(800, self._load_ops)))
                rl.addWidget(db)
                self._op_lay.addWidget(row)
        except Exception:
            self._op_lay.addWidget(lbl("ops.json not found", muted=True))

    def _op_add(self):
        n = self._op_add_edit.text().strip()
        if n:
            send_server_cmd(f"op {n}"); self._op_add_edit.clear()
            QTimer.singleShot(800, self._load_ops)

    # ── Backup ────────────────────────────────────────────────────────────────
    def _build_backup(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("Backup & Restore", header=True)); hdr.addStretch()
        rb4 = QPushButton("Refresh"); rb4.setFixedWidth(58); rb4.clicked.connect(self._refresh_backups); hdr.addWidget(rb4)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        btn_row = QHBoxLayout()
        for txt, tgt, color in [("Local", "local", T["sync"]), ("Drive", "gdrive", T["start"]), ("GitHub", "github", T["handoff"])]:
            b = QPushButton(txt); b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton {{ background:{color}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
            b.clicked.connect(lambda _, t=tgt: backup_to_zip(t)); btn_row.addWidget(b)
        c.layout().addLayout(btn_row)

        self._bk_list_w = QWidget(); self._bk_lay = QVBoxLayout(self._bk_list_w); self._bk_lay.setContentsMargins(0,0,0,0); self._bk_lay.setSpacing(2)
        bs2 = QScrollArea(); bs2.setWidgetResizable(True); bs2.setFixedHeight(110); bs2.setFrameShape(QFrame.Shape.NoFrame); bs2.setWidget(self._bk_list_w)
        c.layout().addWidget(bs2)
        self._refresh_backups()
        return c

    def _refresh_backups(self):
        while self._bk_lay.count():
            item = self._bk_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        try:
            path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
            bdir = os.path.join(path, "backups")
            if not os.path.isdir(bdir):
                self._bk_lay.addWidget(lbl("No backups yet", muted=True)); return
            files = sorted([f for f in os.listdir(bdir) if f.endswith(".zip")], reverse=True)
            for fname in files[:8]:
                fpath = os.path.join(bdir, fname); mb = os.path.getsize(fpath) / 1048576
                row = QFrame(); row.setObjectName("card")
                rl = QHBoxLayout(row); rl.setContentsMargins(8, 4, 8, 4)
                rl.addWidget(lbl(fname[:42]))
                rl.addWidget(lbl(f"{mb:.1f} MB", muted=True)); rl.addStretch()
                open_b = QPushButton("Open"); open_b.setFixedSize(48, 22)
                open_b.clicked.connect(lambda _, p=os.path.dirname(fpath): _open_folder(p)); rl.addWidget(open_b)
                del_b = QPushButton("Del"); del_b.setFixedSize(36, 22)
                del_b.setStyleSheet(f"QPushButton {{ color:{T['stop']}; border:1px solid {T['stop']}; border-radius:4px; background:transparent; }}")
                del_b.clicked.connect(lambda _, p=fpath: (os.remove(p), self._refresh_backups())); rl.addWidget(del_b)
                self._bk_lay.addWidget(row)
        except Exception:
            self._bk_lay.addWidget(lbl("Error reading backups", muted=True))

    # ── Mod / Plugin Properties ───────────────────────────────────────────────
    def _build_mod_props(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("Mod / Plugin Properties", header=True)); hdr.addStretch()
        save_b = QPushButton("Save"); save_b.setFixedWidth(48)
        save_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; }}")
        save_b.clicked.connect(self._mp_save); hdr.addWidget(save_b)
        reload_b = QPushButton("Reload"); reload_b.setFixedWidth(58); reload_b.clicked.connect(self._mp_load); hdr.addWidget(reload_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())

        c.layout().addWidget(lbl("Edit any .properties file in server folder (e.g. plugins, etc.)", muted=True))

        file_row = QHBoxLayout()
        self._mp_path_edit = QLineEdit(); self._mp_path_edit.setPlaceholderText("select a .properties file...")
        file_row.addWidget(self._mp_path_edit)
        browse_b = QPushButton("Browse"); browse_b.setFixedWidth(60); browse_b.clicked.connect(self._mp_browse); file_row.addWidget(browse_b)
        scan_b = QPushButton("Scan"); scan_b.setFixedWidth(50)
        scan_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; }}")
        scan_b.clicked.connect(self._mp_scan); file_row.addWidget(scan_b)
        c.layout().addLayout(file_row)

        self._mp_inner = QWidget(); self._mp_lay = QGridLayout(self._mp_inner)
        self._mp_lay.setSpacing(3); self._mp_lay.setColumnStretch(1, 1)
        mp_scroll = QScrollArea(); mp_scroll.setWidgetResizable(True); mp_scroll.setFixedHeight(180)
        mp_scroll.setFrameShape(QFrame.Shape.NoFrame); mp_scroll.setWidget(self._mp_inner)
        c.layout().addWidget(mp_scroll)
        self._mp_entries: dict[str, QLineEdit] = {}
        return c

    def _mp_browse(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        f, _ = QFileDialog.getOpenFileName(self, "Select .properties file", path, "Properties (*.properties);;All (*.*)")
        if f:
            self._mp_path_edit.setText(f); self._mp_load()

    def _mp_scan(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        found = []
        SKIP = {"world", "world_nether", "world_the_end", "logs", "backups", "cache"}
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for fn in files:
                if fn.endswith(".properties"):
                    found.append(os.path.join(root, fn))
        if not found:
            _toast("No .properties files found!", T["muted"]); return
        from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem
        dlg = QDialog(self); dlg.setWindowTitle("Select .properties file"); dlg.resize(500, 360)
        dlg_lay = QVBoxLayout(dlg)
        dlg_lay.addWidget(lbl(f"Found {len(found)} .properties files:", header=True))
        lw = QListWidget()
        for f in found:
            lw.addItem(os.path.relpath(f, path))
        dlg_lay.addWidget(lw)
        bb = QHBoxLayout()
        ok_b = QPushButton("Select"); ok_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; padding:6px 16px; }}")
        cancel_b = QPushButton("Cancel")
        ok_b.clicked.connect(dlg.accept); cancel_b.clicked.connect(dlg.reject)
        bb.addStretch(); bb.addWidget(cancel_b); bb.addWidget(ok_b); dlg_lay.addLayout(bb)
        if dlg.exec() and lw.currentRow() >= 0:
            self._mp_path_edit.setText(found[lw.currentRow()]); self._mp_load()

    def _mp_load(self):
        while self._mp_lay.count():
            item = self._mp_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._mp_entries.clear()
        fpath = self._mp_path_edit.text().strip()
        if not fpath or not os.path.exists(fpath):
            self._mp_lay.addWidget(lbl("Select a .properties file above.", muted=True), 0, 0); return
        try:
            lines = open(fpath, encoding="utf-8", errors="ignore").readlines()
        except Exception as ex:
            self._mp_lay.addWidget(lbl(f"Error: {ex}", muted=True), 0, 0); return
        row_i = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, val = stripped.partition("=")
            key = key.strip(); val = val.strip()
            self._mp_lay.addWidget(QLabel(key), row_i, 0)
            e = QLineEdit(val); self._mp_lay.addWidget(e, row_i, 1)
            self._mp_entries[key] = e; row_i += 1
        if not self._mp_entries:
            self._mp_lay.addWidget(lbl("No key=value pairs found.", muted=True), 0, 0)

    def _mp_save(self):
        fpath = self._mp_path_edit.text().strip()
        if not fpath:
            _toast("No file selected!", T["stop"]); return
        try:
            lines = open(fpath, encoding="utf-8", errors="ignore").readlines()
            out = []; updated = set()
            for line in lines:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    key = s.partition("=")[0].strip()
                    if key in self._mp_entries:
                        out.append(f"{key}={self._mp_entries[key].text()}\n"); updated.add(key); continue
                out.append(line)
            for key, e in self._mp_entries.items():
                if key not in updated: out.append(f"{key}={e.text()}\n")
            with open(fpath, "w", encoding="utf-8") as f: f.writelines(out)
            _toast(f"Saved: {os.path.basename(fpath)}", T["start"])
        except Exception as ex:
            _toast(f"Save failed: {ex}", T["stop"])

    # ── Server Icon ───────────────────────────────────────────────────────────
    def _build_server_icon(self):
        c = card()
        hdr = QHBoxLayout(); hdr.addWidget(lbl("Server Icon", header=True)); hdr.addStretch()
        refresh_b = QPushButton("Refresh"); refresh_b.setFixedWidth(58); refresh_b.clicked.connect(self._load_icon_preview); hdr.addWidget(refresh_b)
        c.layout().addLayout(hdr); c.layout().addWidget(hline())
        c.layout().addWidget(lbl("server-icon.png must be exactly 64x64 px. Minecraft loads it on restart.", muted=True))
        self._ico_lbl = QLabel("No icon found"); self._ico_lbl.setFixedSize(80, 80)
        self._ico_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ico_lbl.setStyleSheet(f"border:1px solid {T['border']}; background:{T['bg']}; border-radius:6px; color:{T['muted']};")
        c.layout().addWidget(self._ico_lbl)
        btn_row = QHBoxLayout()
        set_b = QPushButton("Set Icon"); set_b.setFixedHeight(28)
        set_b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; }}")
        set_b.clicked.connect(self._set_icon); btn_row.addWidget(set_b)
        rm_b = QPushButton("Remove"); rm_b.setFixedHeight(28)
        rm_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:6px; }}")
        rm_b.clicked.connect(self._remove_icon); btn_row.addWidget(rm_b)
        c.layout().addLayout(btn_row)
        c.layout().addStretch()
        self._load_icon_preview()
        return c

    def _load_icon_preview(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        ico_path = os.path.join(path, "server-icon.png")
        if not os.path.exists(ico_path):
            self._ico_lbl.setText("No icon found"); self._ico_lbl.setPixmap(QPixmap()); return
        pix = QPixmap(ico_path)
        if pix.isNull():
            self._ico_lbl.setText("Cannot load icon"); return
        self._ico_lbl.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self._ico_lbl.setText("")

    def _set_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select server icon", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All (*.*)")
        if not f: return
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        dest = os.path.join(path, "server-icon.png")
        try:
            from PIL import Image as _PILImage
            img = _PILImage.open(f).resize((64, 64), _PILImage.Resampling.LANCZOS).convert("RGBA")
            img.save(dest, "PNG")
            _toast("server-icon.png saved (64x64)! Restart server to apply.", T["start"])
        except ImportError:
            if f.lower().endswith(".png"):
                import shutil; shutil.copy2(f, dest)
                _toast("Icon copied (install Pillow for auto-resize).", T["handoff"])
            else:
                _toast("Install Pillow (pip install pillow) to convert non-PNG images.", T["stop"])
                return
        self._load_icon_preview()

    def _remove_icon(self):
        path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        ico = os.path.join(path, "server-icon.png")
        try: os.remove(ico); _toast("server-icon.png removed.", T["muted"]); self._load_icon_preview()
        except: _toast("No icon to remove.", T["muted"])
