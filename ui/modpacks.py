"""ui/modpacks.py — Modrinth browser with detail pane + installed mod scanner"""
import json, os, threading, urllib.request, urllib.parse, webbrowser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QScrollArea,
    QSplitter, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.themes import T
from core.constants import DEFAULT_SRV_PATH, MODRINTH_API
from core.settings import load_settings, update_setting
from .widgets import make_scroll, card, hline, lbl, LogWidget

def _win():
    from .main_window import WIN
    return WIN

def _toast(msg, color=None, ms=3000):
    w = _win()
    if w: w.toast(msg, color or T["sync"], ms)


class _SearchThread(QThread):
    done = pyqtSignal(dict)
    def __init__(self, q, loader, version, project_type, offset=0):
        super().__init__()
        self.q, self.loader, self.version = q, loader, version
        self.project_type, self.offset = project_type, offset

    def run(self):
        params = {"query": self.q, "limit": 20, "offset": self.offset}
        facets = [[f"project_type:{self.project_type}"]]
        if self.loader: facets.append([f"categories:{self.loader}"])
        if self.version: facets.append([f"versions:{self.version}"])
        params["facets"] = json.dumps(facets)
        qs = urllib.parse.urlencode(params)
        url = f"{MODRINTH_API}/search?{qs}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MC-CTRL/8.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                self.done.emit(json.loads(r.read().decode()))
        except Exception as ex:
            self.done.emit({"hits": [], "total_hits": 0, "error": str(ex)})


class _InstallThread(QThread):
    status = pyqtSignal(str, str)  # msg, color
    done   = pyqtSignal(str)       # filename

    def __init__(self, slug, project_type, loader, version, srv_path):
        super().__init__()
        self.slug, self.project_type = slug, project_type
        self.loader, self.version, self.srv_path = loader, version, srv_path

    def run(self):
        self.status.emit("Fetching versions...", T["sync"])
        try:
            url = (f"{MODRINTH_API}/project/{self.slug}/version"
                   f"?game_versions={json.dumps([self.version])}"
                   f"&loaders={json.dumps([self.loader])}&featured=true")
            req = urllib.request.Request(url, headers={"User-Agent": "MC-CTRL/8.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ver_data = json.loads(r.read().decode())
            if not ver_data:
                req2 = urllib.request.Request(
                    f"{MODRINTH_API}/project/{self.slug}/version",
                    headers={"User-Agent": "MC-CTRL/8.0"})
                with urllib.request.urlopen(req2, timeout=8) as r2:
                    ver_data = json.loads(r2.read().decode())
            if not ver_data:
                self.status.emit("No compatible version found", T["stop"]); return
            files = ver_data[0].get("files", [])
            primary = [f for f in files if f.get("primary")]
            file_obj = primary[0] if primary else files[0]
            url2 = file_obj["url"]; fname = file_obj["filename"]
            pt = self.project_type
            if pt == "plugin":      dest_dir = os.path.join(self.srv_path, "plugins")
            elif pt == "datapack":  dest_dir = os.path.join(self.srv_path, "world", "datapacks")
            elif pt in ("resourcepack", "shader"): dest_dir = os.path.join(self.srv_path, f"{pt}s")
            else:                   dest_dir = os.path.join(self.srv_path, "mods")
            os.makedirs(dest_dir, exist_ok=True)
            self.status.emit(f"Downloading {fname}...", T["sync"])
            req3 = urllib.request.Request(url2, headers={"User-Agent": "MC-CTRL/8.0"})
            with urllib.request.urlopen(req3, timeout=120) as rd:
                with open(os.path.join(dest_dir, fname), "wb") as f: f.write(rd.read())
            self.status.emit(f"Installed: {fname}", T["start"])
            self.done.emit(fname)
        except Exception as ex:
            self.status.emit(f"Error: {ex}", T["stop"])


class ModpacksTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        s = load_settings()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Filter bar
        fb = QFrame(); fb.setObjectName("subtopbar"); fb.setFixedHeight(46)
        fl = QHBoxLayout(fb); fl.setContentsMargins(10, 0, 10, 0); fl.setSpacing(6)
        title_l = QLabel("Modrinth Browser")
        title_l.setStyleSheet(f"color:{T['sync']}; font-weight:700; font-size:13px; background:transparent;")
        fl.addWidget(title_l)
        self._search_edit = QLineEdit(); self._search_edit.setPlaceholderText("Search mods, plugins, modpacks...")
        self._search_edit.setFixedWidth(240); self._search_edit.returnPressed.connect(lambda: self._do_search(0))
        fl.addWidget(self._search_edit)

        self._type_cb   = QComboBox(); self._type_cb.addItems(["mod","modpack","plugin","resourcepack","shader","datapack"]); self._type_cb.setFixedWidth(100)
        self._loader_cb = QComboBox(); self._loader_cb.addItems(["paper","spigot","fabric","forge","quilt","neoforge","bukkit","purpur","velocity","waterfall"]); self._loader_cb.setFixedWidth(100)
        self._ver_cb    = QComboBox(); self._ver_cb.addItems(["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1","1.19.4","1.19.2","1.18.2","1.17.1","1.16.5","1.12.2","1.8.9"]); self._ver_cb.setFixedWidth(80)

        loader_default = s.get("server_type", "paper").lower()
        ver_default = s.get("mc_version", "1.20.1")
        for idx in range(self._loader_cb.count()):
            if self._loader_cb.itemText(idx) == loader_default:
                self._loader_cb.setCurrentIndex(idx); break
        for idx in range(self._ver_cb.count()):
            if self._ver_cb.itemText(idx) == ver_default:
                self._ver_cb.setCurrentIndex(idx); break

        for widget, label_txt in [(self._type_cb,"Type"),(self._loader_cb,"Loader"),(self._ver_cb,"Version")]:
            l = QLabel(label_txt); l.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
            fl.addWidget(l); fl.addWidget(widget)

        search_b = QPushButton("Search"); search_b.setFixedHeight(28)
        search_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        search_b.clicked.connect(lambda: self._do_search(0)); fl.addWidget(search_b)
        fl.addStretch()
        self._res_count_lbl = QLabel(""); self._res_count_lbl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        fl.addWidget(self._res_count_lbl)
        root.addWidget(fb)

        # Main splitter: results list | detail pane
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # Results panel
        results_w = QWidget()
        rl = QVBoxLayout(results_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        # Pagination
        pg_bar = QFrame(); pg_bar.setObjectName("topbar"); pg_bar.setFixedHeight(30)
        pg_l = QHBoxLayout(pg_bar); pg_l.setContentsMargins(8, 0, 8, 0); pg_l.setSpacing(4)
        self._page_lbl = QLabel("Page 1"); self._page_lbl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        pg_l.addWidget(self._page_lbl)
        pg_l.addStretch()
        prev_b = QPushButton("< Prev"); prev_b.setFixedSize(56, 22)
        prev_b.clicked.connect(lambda: self._do_search(max(0, self._page - 1))); pg_l.addWidget(prev_b)
        next_b = QPushButton("Next >"); next_b.setFixedSize(56, 22)
        next_b.clicked.connect(lambda: self._do_search(self._page + 1)); pg_l.addWidget(next_b)
        rl.addWidget(pg_bar)

        self._res_scroll_area = QScrollArea(); self._res_scroll_area.setWidgetResizable(True)
        self._res_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._res_scroll_inner = QWidget(); self._res_scroll_layout = QVBoxLayout(self._res_scroll_inner)
        self._res_scroll_layout.setContentsMargins(4, 4, 4, 4); self._res_scroll_layout.setSpacing(3)
        self._res_scroll_layout.addStretch()
        self._res_scroll_area.setWidget(self._res_scroll_inner)
        rl.addWidget(self._res_scroll_area, 1)
        splitter.addWidget(results_w)

        # Detail pane
        self._detail_w, _, self._detail_lay = make_scroll()
        splitter.addWidget(self._detail_w)
        splitter.setSizes([360, 560])

        # Installed mods scanner bar
        inst_bar = QFrame(); inst_bar.setObjectName("ip_bar"); inst_bar.setFixedHeight(70)
        inst_lay = QVBoxLayout(inst_bar); inst_lay.setContentsMargins(10, 4, 10, 4); inst_lay.setSpacing(2)
        inst_hdr = QHBoxLayout()
        inst_hdr.addWidget(lbl("Installed (.jar/.zip)", header=True))
        inst_hdr.addStretch()
        scan_b = QPushButton("Scan"); scan_b.setFixedSize(52, 22)
        scan_b.clicked.connect(self._scan_installed); inst_hdr.addWidget(scan_b)
        inst_lay.addLayout(inst_hdr)
        self._inst_scroll = QScrollArea(); self._inst_scroll.setWidgetResizable(True)
        self._inst_scroll.setFixedHeight(38); self._inst_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._inst_inner = QWidget(); self._inst_inner_lay = QHBoxLayout(self._inst_inner)
        self._inst_inner_lay.setContentsMargins(0, 0, 0, 0); self._inst_inner_lay.setSpacing(4)
        self._inst_scroll.setWidget(self._inst_inner); inst_lay.addWidget(self._inst_scroll)
        root.addWidget(inst_bar)

        self._page = 0; self._total = 0; self._installed_slugs: set[str] = set(s.get("installed_mods", []))
        self._search_thread = None; self._install_thread = None
        self._search_gen = 0
        self._do_search(0)

    def _do_search(self, page: int):
        self._page = page
        q = self._search_edit.text().strip()
        loader = self._loader_cb.currentText(); version = self._ver_cb.currentText()
        pt = self._type_cb.currentText()
        self._res_count_lbl.setText("Searching...")
        if self._search_thread and self._search_thread.isRunning():
            try: self._search_thread.done.disconnect()
            except Exception: pass
            self._search_thread.quit()
        self._search_gen += 1
        gen = self._search_gen
        self._search_thread = _SearchThread(q, loader, version, pt, page * 20)
        self._search_thread.done.connect(lambda data, g=gen: self._on_results(data, g))
        self._search_thread.start()

    def _on_results(self, data: dict, gen: int = None):
        if gen is not None and gen != self._search_gen:
            return  # stale result from a superseded search
        hits = data.get("hits", []); total = data.get("total_hits", 0)
        err = data.get("error", ""); self._total = total
        self._res_count_lbl.setText(f"{total:,} results" if not err else f"Error: {err}")
        self._page_lbl.setText(f"Page {self._page + 1} / {max(1, (total + 19) // 20)}")
        # Clear
        while self._res_scroll_layout.count() > 1:
            item = self._res_scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not hits:
            self._res_scroll_layout.insertWidget(0, lbl("No results found.", muted=True)); return
        for hit in hits:
            self._res_scroll_layout.insertWidget(
                self._res_scroll_layout.count() - 1,
                self._make_hit_card(hit))
        if hits: self._show_detail(hits[0])

    def _make_hit_card(self, hit: dict) -> QFrame:
        slug = hit.get("slug", ""); title = hit.get("title", "?")
        desc = hit.get("description", ""); dl = hit.get("downloads", 0)
        pt = hit.get("project_type", "mod"); is_inst = slug in self._installed_slugs
        border = T["sync"] if is_inst else T["border"]
        f = QFrame(); f.setObjectName("card"); f.setCursor(Qt.CursorShape.PointingHandCursor)
        f.setStyleSheet(f"QFrame#card {{ border: {'2' if is_inst else '1'}px solid {border}; background:{T['card']}; border-radius:8px; }}")
        fl = QVBoxLayout(f); fl.setContentsMargins(8, 6, 8, 6); fl.setSpacing(3)
        nh = QHBoxLayout()
        tl = QLabel(title); tl.setStyleSheet(f"color:{T['start'] if is_inst else T['text']}; font-weight:700; font-size:12px; background:transparent;")
        nh.addWidget(tl); nh.addStretch()
        if is_inst:
            il = QLabel("Installed"); il.setStyleSheet(f"color:{T['start']}; font-size:9px; background:transparent;")
            nh.addWidget(il)
        fl.addLayout(nh)
        dl_text = desc[:80] + ("..." if len(desc) > 80 else "")
        dl_l = QLabel(dl_text); dl_l.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;"); dl_l.setWordWrap(True)
        fl.addWidget(dl_l)
        meta_l = QLabel(f"{dl:,} downloads  |  {pt}")
        meta_l.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
        fl.addWidget(meta_l)
        f.mousePressEvent = lambda e, h=hit: self._show_detail(h)
        return f

    def _show_detail(self, hit: dict):
        while self._detail_lay.count() > 1:
            item = self._detail_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        slug = hit.get("slug", ""); name = hit.get("title", "?")
        desc = hit.get("description", ""); dl = hit.get("downloads", 0)
        categories = hit.get("categories", []); versions = hit.get("versions", [])
        pt = hit.get("project_type", "mod")

        # Header card
        hc = card(); hc.layout().setSpacing(6)
        tl = QLabel(name); tl.setStyleSheet(f"color:{T['text']}; font-size:16px; font-weight:700; background:transparent;")
        hc.layout().addWidget(tl)
        dl_l = QLabel(desc); dl_l.setWordWrap(True); dl_l.setStyleSheet(f"color:{T['muted']}; font-size:11px; background:transparent;")
        hc.layout().addWidget(dl_l)

        meta_row = QHBoxLayout()
        dl_stat = QLabel(f"{dl:,} downloads")
        dl_stat.setStyleSheet(f"color:{T['sync']}; font-size:11px; background:transparent;")
        meta_row.addWidget(dl_stat)
        for cat in categories[:6]:
            cl = QLabel(cat); cl.setStyleSheet(
                f"background:{T['bg']}; color:{T['handoff']}; border:1px solid {T['border']};"
                f" border-radius:4px; padding:2px 6px; font-size:9px;")
            meta_row.addWidget(cl)
        meta_row.addStretch()
        mrinth_b = QPushButton("Modrinth Page"); mrinth_b.setFixedHeight(24)
        mrinth_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['sync']}; border:1px solid {T['border']}; border-radius:4px; font-size:10px; }}")
        mrinth_b.clicked.connect(lambda: webbrowser.open(f"https://modrinth.com/mod/{slug}"))
        meta_row.addWidget(mrinth_b)
        hc.layout().addLayout(meta_row)
        hc.layout().addWidget(hline())

        # MC versions
        if versions:
            vl = QLabel("MC Versions: " + "  ".join(versions[:10]))
            vl.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            hc.layout().addWidget(vl)

        self._detail_lay.insertWidget(self._detail_lay.count() - 1, hc)

        # Install card
        ic = card(); ic.layout().addWidget(lbl("INSTALL", header=True)); ic.layout().addWidget(hline())
        srv_path_label = lbl("Server path:", muted=True); ic.layout().addWidget(srv_path_label)
        path_row = QHBoxLayout()
        self._inst_path_edit = QLineEdit(load_settings().get("srv_path", DEFAULT_SRV_PATH))
        path_row.addWidget(self._inst_path_edit)
        browse_b = QPushButton("..."); browse_b.setFixedWidth(26)
        browse_b.clicked.connect(lambda: self._browse_install_path())
        path_row.addWidget(browse_b); ic.layout().addLayout(path_row)

        self._inst_status = QLabel("Already installed" if slug in self._installed_slugs else "")
        self._inst_status.setStyleSheet(f"color:{T['start']}; background:transparent; font-size:11px;")
        ic.layout().addWidget(self._inst_status)

        btn_row = QHBoxLayout()
        inst_b = QPushButton("Download & Install"); inst_b.setFixedHeight(30)
        inst_b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        inst_b.clicked.connect(lambda: self._install(slug, pt, hit))
        btn_row.addWidget(inst_b)
        if slug in self._installed_slugs:
            rm_b = QPushButton("Remove from tracking"); rm_b.setFixedHeight(30)
            rm_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:6px; }}")
            rm_b.clicked.connect(lambda: (self._installed_slugs.discard(slug), update_setting("installed_mods", list(self._installed_slugs)), self._inst_status.setText("")))
            btn_row.addWidget(rm_b)
        btn_row.addStretch(); ic.layout().addLayout(btn_row)
        self._detail_lay.insertWidget(self._detail_lay.count() - 1, ic)

    def _browse_install_path(self):
        p = QFileDialog.getExistingDirectory(self, "Server folder")
        if p:
            self._inst_path_edit.setText(p)

    def _install(self, slug, pt, hit):
        if self._install_thread and self._install_thread.isRunning():
            _toast("Already installing...", T["muted"]); return
        srv_path = self._inst_path_edit.text().strip()
        self._install_thread = _InstallThread(slug, pt, self._loader_cb.currentText(),
                                              self._ver_cb.currentText(), srv_path)
        self._install_thread.status.connect(lambda msg, col: self._inst_status.setText(msg) or self._inst_status.setStyleSheet(f"color:{col}; background:transparent; font-size:11px;"))
        self._install_thread.done.connect(lambda fname: (self._installed_slugs.add(slug), update_setting("installed_mods", list(self._installed_slugs)), _toast(f"Installed: {fname}", T["start"])))
        self._install_thread.start()

    def _scan_installed(self):
        while self._inst_inner_lay.count():
            item = self._inst_inner_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        srv_path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        found = []
        for sub in ("plugins", "mods", "datapacks"):
            d = os.path.join(srv_path, sub)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.endswith((".jar", ".zip")):
                        found.append((sub, fn))
        if not found:
            self._inst_inner_lay.addWidget(lbl("No .jar/.zip files found in plugins/ mods/ datapacks/", muted=True)); return
        for sub, fn in found:
            f = QFrame(); f.setObjectName("card")
            fl = QVBoxLayout(f); fl.setContentsMargins(6, 4, 6, 4); fl.setSpacing(2)
            nl = QLabel(fn[:28] + ("..." if len(fn) > 28 else "")); nl.setStyleSheet(f"color:{T['text']}; font-size:9px; font-family:Consolas; background:transparent;")
            sl = QLabel(sub); sl.setStyleSheet(f"color:{T['muted']}; font-size:8px; background:transparent;")
            fl.addWidget(nl); fl.addWidget(sl)
            self._inst_inner_lay.addWidget(f)
        self._inst_inner_lay.addStretch()
