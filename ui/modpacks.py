"""ui/modpacks.py — Modrinth + Hangar browser with detail pane, install, and local scanner"""
import json, os, threading, urllib.request, urllib.parse, webbrowser
from functools import lru_cache

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QScrollArea,
    QSplitter, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from core.themes import T
from core.constants import DEFAULT_SRV_PATH, MODRINTH_API
from core.settings import load_settings, update_setting
from .widgets import make_scroll, card, hline, lbl, LogWidget

_HANGAR_API = "https://hangar.papermc.io/api/v1"
_UA = {"User-Agent": "MC-CTRL/8.0 (github.com/GamerMahir07)"}

def _win():
    from .main_window import WIN
    return WIN

def _toast(msg, color=None, ms=3000):
    w = _win()
    if w: w.toast(msg, color or T["sync"], ms)

def _get(url: str, timeout=10) -> dict | list:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ── Search thread ─────────────────────────────────────────────────────────────
class _SearchThread(QThread):
    done = pyqtSignal(dict)

    def __init__(self, q, loader, version, project_type, offset, source):
        super().__init__()
        self.q, self.loader, self.version = q, loader, version
        self.project_type, self.offset, self.source = project_type, offset, source

    def run(self):
        try:
            if self.source == "hangar":
                self.done.emit(self._search_hangar())
            else:
                self.done.emit(self._search_modrinth())
        except Exception as ex:
            self.done.emit({"hits": [], "total_hits": 0, "error": str(ex)})

    def _search_modrinth(self) -> dict:
        facets = [[f"project_type:{self.project_type}"]]
        if self.loader:  facets.append([f"categories:{self.loader}"])
        if self.version: facets.append([f"versions:{self.version}"])
        params = {"query": self.q, "limit": 20, "offset": self.offset,
                  "facets": json.dumps(facets)}
        return _get(f"{MODRINTH_API}/search?{urllib.parse.urlencode(params)}")

    def _search_hangar(self) -> dict:
        params = {"q": self.q, "limit": 20, "offset": self.offset,
                  "platform": "PAPER", "sort": "downloads"}
        data = _get(f"{_HANGAR_API}/projects?{urllib.parse.urlencode(params)}")
        # Normalise to Modrinth-like shape
        hits = []
        for p in data.get("result", []):
            slug = p.get("namespace", {}).get("slug", p.get("name",""))
            hits.append({
                "slug": slug,
                "title": p.get("name", slug),
                "description": p.get("description", ""),
                "downloads": p.get("stats", {}).get("downloads", 0),
                "project_type": "plugin",
                "categories": p.get("category", "").split(","),
                "versions": [],
                "_hangar": True,
            })
        return {"hits": hits, "total_hits": data.get("pagination", {}).get("count", len(hits))}


# ── Install thread ────────────────────────────────────────────────────────────
class _InstallThread(QThread):
    status   = pyqtSignal(str, str)   # msg, color
    progress = pyqtSignal(int)        # 0-100
    done     = pyqtSignal(str)        # filename

    def __init__(self, slug, project_type, loader, version, srv_path, is_hangar=False):
        super().__init__()
        self.slug = slug; self.project_type = project_type
        self.loader = loader; self.version = version
        self.srv_path = srv_path; self.is_hangar = is_hangar

    def run(self):
        self.status.emit("Fetching version info...", T["sync"])
        try:
            url2, fname = (self._resolve_hangar()
                           if self.is_hangar else self._resolve_modrinth())
            if not url2:
                self.status.emit("No compatible version found", T["stop"]); return

            dest_dir = self._dest_dir()
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, fname)

            self.status.emit(f"Downloading {fname}...", T["sync"])
            req = urllib.request.Request(url2, headers=_UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 65536
                with open(dest_path, "wb") as f:
                    while True:
                        buf = r.read(chunk)
                        if not buf: break
                        f.write(buf)
                        downloaded += len(buf)
                        if total:
                            self.progress.emit(int(downloaded / total * 100))
            self.progress.emit(100)
            self.status.emit(f"Installed: {fname}", T["start"])
            self.done.emit(fname)
        except Exception as ex:
            self.status.emit(f"Error: {ex}", T["stop"])

    def _dest_dir(self) -> str:
        pt = self.project_type
        dirs = {"plugin": "plugins", "datapack": os.path.join("world", "datapacks"),
                "resourcepack": "resourcepacks", "shader": "shaderpacks"}
        return os.path.join(self.srv_path, dirs.get(pt, "mods"))

    def _resolve_modrinth(self) -> tuple[str, str]:
        url = (f"{MODRINTH_API}/project/{self.slug}/version"
               f"?game_versions={json.dumps([self.version])}"
               f"&loaders={json.dumps([self.loader])}")
        vers = _get(url)
        if not vers:
            vers = _get(f"{MODRINTH_API}/project/{self.slug}/version")
        if not vers: return "", ""
        files = vers[0].get("files", [])
        f = next((x for x in files if x.get("primary")), files[0] if files else None)
        return (f["url"], f["filename"]) if f else ("", "")

    def _resolve_hangar(self) -> tuple[str, str]:
        data = _get(f"{_HANGAR_API}/projects/{self.slug}/latestrelease")
        # Hangar returns version string; fetch download URL
        ver_str = data if isinstance(data, str) else ""
        if not ver_str:
            vers = _get(f"{_HANGAR_API}/projects/{self.slug}/versions?limit=1")
            ver_str = vers.get("result", [{}])[0].get("name", "")
        if not ver_str: return "", ""
        dl_url = f"{_HANGAR_API}/projects/{self.slug}/versions/{ver_str}/PAPER/download"
        fname  = f"{self.slug}-{ver_str}.jar"
        return dl_url, fname


# ── Main tab ──────────────────────────────────────────────────────────────────
class ModpacksTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        s = load_settings()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # ── Filter bar ────────────────────────────────────────────────────────
        fb = QFrame(); fb.setObjectName("subtopbar"); fb.setFixedHeight(46)
        fl = QHBoxLayout(fb); fl.setContentsMargins(10, 0, 10, 0); fl.setSpacing(6)

        title_l = QLabel("Modrinth / Hangar Browser")
        title_l.setStyleSheet(f"color:{T['sync']}; font-weight:700; font-size:13px; background:transparent;")
        fl.addWidget(title_l)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search mods, plugins, modpacks...")
        self._search_edit.setFixedWidth(220)
        self._search_edit.returnPressed.connect(lambda: self._do_search(0))
        # Debounce: 400ms after last keypress
        self._search_timer = QTimer(singleShot=True)
        self._search_timer.setInterval(400)
        self._search_timer.timeout.connect(lambda: self._do_search(0))
        self._search_edit.textChanged.connect(lambda: self._search_timer.start())
        fl.addWidget(self._search_edit)

        self._source_cb = QComboBox(); self._source_cb.addItems(["modrinth", "hangar"])
        self._source_cb.setFixedWidth(82)
        self._source_cb.currentTextChanged.connect(self._on_source_change)
        fl.addWidget(self._source_cb)

        self._type_cb   = QComboBox()
        self._type_cb.addItems(["mod","modpack","plugin","resourcepack","shader","datapack"])
        self._type_cb.setFixedWidth(100)

        self._loader_cb = QComboBox()
        self._loader_cb.addItems(["paper","spigot","fabric","forge","quilt","neoforge",
                                   "bukkit","purpur","velocity","waterfall"])
        self._loader_cb.setFixedWidth(90)

        self._ver_cb = QComboBox()
        self._ver_cb.addItems(["1.21.4","1.21.1","1.20.6","1.20.4","1.20.1",
                                "1.19.4","1.19.2","1.18.2","1.17.1","1.16.5","1.12.2","1.8.9"])
        self._ver_cb.setFixedWidth(76)

        # Set defaults from settings
        for cb, key, default in [
            (self._loader_cb, "server_type", "paper"),
            (self._ver_cb,    "mc_version",  "1.20.1"),
        ]:
            val = s.get(key, default).lower()
            idx = cb.findText(val)
            if idx >= 0: cb.setCurrentIndex(idx)

        for label_txt, w in [("Type", self._type_cb), ("Loader", self._loader_cb), ("Ver", self._ver_cb)]:
            l = QLabel(label_txt); l.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
            fl.addWidget(l); fl.addWidget(w)

        search_b = QPushButton("Search"); search_b.setFixedHeight(28)
        search_b.setStyleSheet(f"QPushButton {{ background:{T['sync']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        search_b.clicked.connect(lambda: self._do_search(0))
        fl.addWidget(search_b)
        fl.addStretch()
        self._res_count_lbl = QLabel("")
        self._res_count_lbl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        fl.addWidget(self._res_count_lbl)
        root.addWidget(fb)

        # ── Main splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # Results panel
        results_w = QWidget()
        rl = QVBoxLayout(results_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        pg_bar = QFrame(); pg_bar.setObjectName("topbar"); pg_bar.setFixedHeight(30)
        pg_l = QHBoxLayout(pg_bar); pg_l.setContentsMargins(8, 0, 8, 0); pg_l.setSpacing(4)
        self._page_lbl = QLabel("Page 1")
        self._page_lbl.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;")
        pg_l.addWidget(self._page_lbl); pg_l.addStretch()
        for label, fn in [("< Prev", lambda: self._do_search(max(0, self._page-1))),
                           ("Next >", lambda: self._do_search(self._page+1))]:
            b = QPushButton(label); b.setFixedSize(56, 22)
            b.clicked.connect(fn); pg_l.addWidget(b)
        rl.addWidget(pg_bar)

        self._res_inner  = QWidget()
        self._res_layout = QVBoxLayout(self._res_inner)
        self._res_layout.setContentsMargins(4, 4, 4, 4); self._res_layout.setSpacing(3)
        self._res_layout.addStretch()
        res_scroll = QScrollArea(); res_scroll.setWidgetResizable(True)
        res_scroll.setFrameShape(QFrame.Shape.NoFrame); res_scroll.setWidget(self._res_inner)
        rl.addWidget(res_scroll, 1)
        splitter.addWidget(results_w)

        # Detail pane
        self._detail_w, _, self._detail_lay = make_scroll()
        splitter.addWidget(self._detail_w)
        splitter.setSizes([360, 580])

        # ── Installed bar ─────────────────────────────────────────────────────
        inst_bar = QFrame(); inst_bar.setObjectName("ip_bar"); inst_bar.setFixedHeight(72)
        inst_lay = QVBoxLayout(inst_bar); inst_lay.setContentsMargins(10, 4, 10, 4); inst_lay.setSpacing(2)
        inst_hdr = QHBoxLayout()
        inst_hdr.addWidget(lbl("Installed (.jar / .zip)", header=True)); inst_hdr.addStretch()
        scan_b = QPushButton("Scan"); scan_b.setFixedSize(52, 22)
        scan_b.clicked.connect(self._scan_installed); inst_hdr.addWidget(scan_b)
        inst_lay.addLayout(inst_hdr)
        self._inst_inner     = QWidget()
        self._inst_inner_lay = QHBoxLayout(self._inst_inner)
        self._inst_inner_lay.setContentsMargins(0, 0, 0, 0); self._inst_inner_lay.setSpacing(4)
        inst_scroll = QScrollArea(); inst_scroll.setWidgetResizable(True)
        inst_scroll.setFixedHeight(40); inst_scroll.setFrameShape(QFrame.Shape.NoFrame)
        inst_scroll.setWidget(self._inst_inner)
        inst_lay.addWidget(inst_scroll)
        root.addWidget(inst_bar)

        # ── State ─────────────────────────────────────────────────────────────
        self._page           = 0
        self._total          = 0
        self._search_gen     = 0
        self._search_thread  = None
        self._install_thread = None
        self._installed_slugs: set[str] = set(s.get("installed_mods", []))

        self._do_search(0)

    # ── Source switch ─────────────────────────────────────────────────────────
    def _on_source_change(self, source: str):
        is_hangar = source == "hangar"
        # Hangar only has plugins/Paper
        self._type_cb.setEnabled(not is_hangar)
        self._loader_cb.setEnabled(not is_hangar)
        self._do_search(0)

    # ── Search ────────────────────────────────────────────────────────────────
    def _do_search(self, page: int):
        self._page = page
        self._res_count_lbl.setText("Searching...")
        if self._search_thread and self._search_thread.isRunning():
            try: self._search_thread.done.disconnect()
            except Exception: pass
            self._search_thread.quit()
        self._search_gen += 1
        gen = self._search_gen
        self._search_thread = _SearchThread(
            self._search_edit.text().strip(),
            self._loader_cb.currentText(),
            self._ver_cb.currentText(),
            self._type_cb.currentText(),
            page * 20,
            self._source_cb.currentText(),
        )
        self._search_thread.done.connect(lambda d, g=gen: self._on_results(d, g))
        self._search_thread.start()

    def _on_results(self, data: dict, gen: int):
        if gen != self._search_gen: return
        hits  = data.get("hits", [])
        total = data.get("total_hits", 0)
        err   = data.get("error", "")
        self._total = total
        self._res_count_lbl.setText(f"{total:,} results" if not err else f"Error: {err[:60]}")
        self._page_lbl.setText(f"Page {self._page+1} / {max(1,(total+19)//20)}")

        # Clear results
        while self._res_layout.count() > 1:
            item = self._res_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not hits:
            self._res_layout.insertWidget(0, lbl("No results." if not err else err, muted=True))
            return
        for hit in hits:
            self._res_layout.insertWidget(self._res_layout.count()-1, self._make_hit_card(hit))
        self._show_detail(hits[0])

    def _make_hit_card(self, hit: dict) -> QFrame:
        slug = hit.get("slug",""); title = hit.get("title","?")
        desc = hit.get("description",""); dl = hit.get("downloads",0)
        pt   = hit.get("project_type","mod"); is_inst = slug in self._installed_slugs

        f = QFrame(); f.setObjectName("card"); f.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_inst:
            f.setStyleSheet(f"QFrame#card {{ border:2px solid {T['sync']}; }}")
        fl = QVBoxLayout(f); fl.setContentsMargins(8, 6, 8, 6); fl.setSpacing(2)

        nh = QHBoxLayout()
        tl = QLabel(title)
        tl.setStyleSheet(f"color:{T['sync'] if is_inst else T['text']}; font-weight:700; font-size:12px; background:transparent;")
        nh.addWidget(tl); nh.addStretch()
        if is_inst:
            il = QLabel("Installed"); il.setStyleSheet(f"color:{T['start']}; font-size:9px; background:transparent;")
            nh.addWidget(il)
        fl.addLayout(nh)

        dl_l = QLabel(desc[:80] + ("…" if len(desc)>80 else ""))
        dl_l.setStyleSheet(f"color:{T['muted']}; font-size:10px; background:transparent;"); dl_l.setWordWrap(True)
        fl.addWidget(dl_l)

        meta = QLabel(f"{dl:,} dl  |  {pt}")
        meta.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
        fl.addWidget(meta)
        f.mousePressEvent = lambda e, h=hit: self._show_detail(h)
        return f

    # ── Detail pane ───────────────────────────────────────────────────────────
    def _show_detail(self, hit: dict):
        while self._detail_lay.count() > 1:
            item = self._detail_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        slug     = hit.get("slug","")
        name     = hit.get("title","?")
        desc     = hit.get("description","")
        dl       = hit.get("downloads",0)
        cats     = hit.get("categories",[])
        versions = hit.get("versions",[])
        pt       = hit.get("project_type","mod")
        is_hangar= hit.get("_hangar", False)
        is_inst  = slug in self._installed_slugs

        # Header
        hc = card(); hc.layout().setSpacing(6)
        tl = QLabel(name); tl.setStyleSheet(f"color:{T['text']}; font-size:16px; font-weight:700; background:transparent;")
        hc.layout().addWidget(tl)
        dl_l = QLabel(desc); dl_l.setWordWrap(True)
        dl_l.setStyleSheet(f"color:{T['muted']}; font-size:11px; background:transparent;")
        hc.layout().addWidget(dl_l)

        meta_row = QHBoxLayout()
        ds = QLabel(f"{dl:,} downloads"); ds.setStyleSheet(f"color:{T['sync']}; font-size:11px; background:transparent;")
        meta_row.addWidget(ds)
        for cat in cats[:5]:
            cl = QLabel(cat)
            cl.setStyleSheet(f"background:{T['bg']}; color:{T['handoff']}; border:1px solid {T['border']}; border-radius:4px; padding:2px 6px; font-size:9px;")
            meta_row.addWidget(cl)
        meta_row.addStretch()
        src_lbl = "hangar" if is_hangar else "modrinth"
        ext_url = (f"https://hangar.papermc.io/{slug}" if is_hangar
                   else f"https://modrinth.com/project/{slug}")
        web_b = QPushButton(f"Open {src_lbl.title()}"); web_b.setFixedHeight(24)
        web_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['sync']}; border:1px solid {T['border']}; border-radius:4px; font-size:10px; }}")
        web_b.clicked.connect(lambda: webbrowser.open(ext_url))
        meta_row.addWidget(web_b)
        hc.layout().addLayout(meta_row)

        if versions:
            vl = QLabel("MC Versions: " + "  ".join(versions[:10]))
            vl.setStyleSheet(f"color:{T['muted']}; font-size:9px; background:transparent;")
            hc.layout().addWidget(vl)
        self._detail_lay.insertWidget(self._detail_lay.count()-1, hc)

        # Install card
        ic = card()
        ic.layout().addWidget(lbl("INSTALL", header=True)); ic.layout().addWidget(hline())

        path_row = QHBoxLayout()
        self._inst_path_edit = QLineEdit(load_settings().get("srv_path", DEFAULT_SRV_PATH))
        path_row.addWidget(self._inst_path_edit)
        browse_b = QPushButton("…"); browse_b.setFixedWidth(28)
        browse_b.clicked.connect(self._browse_install_path)
        path_row.addWidget(browse_b)
        ic.layout().addLayout(path_row)

        self._inst_progress = QProgressBar(); self._inst_progress.setFixedHeight(6)
        self._inst_progress.setTextVisible(False); self._inst_progress.setValue(0)
        self._inst_progress.setStyleSheet(f"QProgressBar {{ background:{T['border']}; border-radius:3px; }} QProgressBar::chunk {{ background:{T['sync']}; border-radius:3px; }}")
        ic.layout().addWidget(self._inst_progress)

        self._inst_status = QLabel("Already installed" if is_inst else "")
        self._inst_status.setStyleSheet(f"color:{T['start'] if is_inst else T['muted']}; background:transparent; font-size:11px;")
        ic.layout().addWidget(self._inst_status)

        btn_row = QHBoxLayout()
        inst_b = QPushButton("Download & Install"); inst_b.setFixedHeight(30)
        inst_b.setStyleSheet(f"QPushButton {{ background:{T['start']}; color:#000; border:none; border-radius:6px; font-weight:700; }}")
        inst_b.clicked.connect(lambda: self._install(slug, pt, is_hangar))
        btn_row.addWidget(inst_b)
        if is_inst:
            rm_b = QPushButton("Remove from tracking"); rm_b.setFixedHeight(30)
            rm_b.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['stop']}; border:1px solid {T['stop']}; border-radius:6px; }}")
            rm_b.clicked.connect(lambda: self._untrack(slug))
            btn_row.addWidget(rm_b)
        btn_row.addStretch()
        ic.layout().addLayout(btn_row)
        self._detail_lay.insertWidget(self._detail_lay.count()-1, ic)

    def _browse_install_path(self):
        p = QFileDialog.getExistingDirectory(self, "Server folder")
        if p: self._inst_path_edit.setText(p)

    def _untrack(self, slug: str):
        self._installed_slugs.discard(slug)
        update_setting("installed_mods", list(self._installed_slugs))
        self._inst_status.setText("")

    def _install(self, slug: str, pt: str, is_hangar: bool):
        if self._install_thread and self._install_thread.isRunning():
            _toast("Already installing...", T["muted"]); return
        srv_path = self._inst_path_edit.text().strip()
        self._install_thread = _InstallThread(
            slug, pt,
            self._loader_cb.currentText(), self._ver_cb.currentText(),
            srv_path, is_hangar)
        self._install_thread.status.connect(
            lambda msg, col: (self._inst_status.setText(msg),
                              self._inst_status.setStyleSheet(f"color:{col}; background:transparent; font-size:11px;")))
        self._install_thread.progress.connect(self._inst_progress.setValue)
        self._install_thread.done.connect(
            lambda fname: (self._installed_slugs.add(slug),
                           update_setting("installed_mods", list(self._installed_slugs)),
                           _toast(f"Installed: {fname}", T["start"])))
        self._install_thread.start()

    # ── Installed scanner ─────────────────────────────────────────────────────
    def _scan_installed(self):
        while self._inst_inner_lay.count():
            item = self._inst_inner_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        srv_path = load_settings().get("srv_path", DEFAULT_SRV_PATH)
        found = []
        for sub in ("plugins", "mods", "datapacks", "resourcepacks", "shaderpacks"):
            d = os.path.join(srv_path, sub)
            if os.path.isdir(d):
                for fn in sorted(os.listdir(d)):
                    if fn.endswith((".jar", ".zip")):
                        found.append((sub, fn))
        if not found:
            self._inst_inner_lay.addWidget(lbl("No files found in plugins/ mods/ datapacks/", muted=True))
            return
        for sub, fn in found:
            f = QFrame(); f.setObjectName("card")
            fl = QVBoxLayout(f); fl.setContentsMargins(6, 3, 6, 3); fl.setSpacing(1)
            nl = QLabel(fn[:26] + ("…" if len(fn) > 26 else ""))
            nl.setStyleSheet(f"color:{T['text']}; font-size:9px; font-family:Consolas; background:transparent;")
            sl = QLabel(sub)
            sl.setStyleSheet(f"color:{T['muted']}; font-size:8px; background:transparent;")
            fl.addWidget(nl); fl.addWidget(sl)
            self._inst_inner_lay.addWidget(f)
        self._inst_inner_lay.addStretch()
