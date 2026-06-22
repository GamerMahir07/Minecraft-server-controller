"""ui/first_run.py — FirstRunWizard"""
import os, subprocess, sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt

from core.themes import T
from core.constants import FIRST_RUN_FLAG, DEFAULT_SRV_PATH, REPO_URL, _BASE_DIR
from core.settings import load_settings, save_settings


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MC CTRL — First Run Setup")
        self.setMinimumWidth(540)
        self.setStyleSheet(
            f"QDialog {{ background:{T['bg']}; }}"
            f"QWidget {{ background:{T['bg']}; color:{T['text']}; }}"
            f"QLabel  {{ background:transparent; }}"
            f"QLineEdit {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:6px 10px; }}"
            f"QPushButton {{ background:{T['card']}; color:{T['text']}; border:1px solid {T['border']}; border-radius:6px; padding:6px 12px; }}"
            f"QPushButton:hover {{ background:{T['border']}; }}")

        root = QVBoxLayout(self); root.setContentsMargins(28, 24, 28, 24); root.setSpacing(12)

        title = QLabel("MC CTRL  —  First Run Setup")
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f)
        title.setStyleSheet(f"color:{T['start']}; background:transparent;")
        root.addWidget(title)

        sub = QLabel("Quick setup — you can change everything later in Settings.")
        sub.setStyleSheet(f"color:{T['muted']}; font-size:12px; background:transparent;")
        root.addWidget(sub)

        # Install deps notice
        deps_f = QFrame(); deps_f.setStyleSheet(
            f"QFrame {{ background:{T['card']}; border:1px solid {T['border']}; border-radius:8px; }}"
            f"QLabel {{ background:transparent; }}")
        deps_l = QVBoxLayout(deps_f); deps_l.setContentsMargins(14, 10, 14, 10)
        deps_l.addWidget(QLabel("If packages are missing, run install_requirements.bat / .sh first."))
        root.addWidget(deps_f)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{T['border']}; background:{T['border']}; max-height:1px;")
        root.addWidget(sep)

        def field(label_txt, placeholder, default=""):
            lbl_w = QLabel(label_txt)
            lbl_w.setStyleSheet(f"color:{T['muted']}; font-size:11px; font-weight:600; background:transparent;")
            root.addWidget(lbl_w)
            e = QLineEdit(default); e.setPlaceholderText(placeholder)
            root.addWidget(e)
            return e

        self.srv_edit  = field("Server folder path", f"e.g.  {DEFAULT_SRV_PATH}")
        srv_row = QHBoxLayout(); srv_row.addStretch()
        browse_b = QPushButton("Browse..."); browse_b.setFixedWidth(90)
        browse_b.clicked.connect(self._browse); srv_row.addWidget(browse_b)
        root.addLayout(srv_row)

        self.java_edit = field("Java executable", "java   (or full path to java.exe)")
        self.repo_edit = field("GitHub repo URL (optional)",
                               "https://github.com/user/repo.git",
                               load_settings().get("repo_url", REPO_URL))

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{T['border']}; background:{T['border']}; max-height:1px;")
        root.addWidget(sep2)

        finish_b = QPushButton("Finish Setup")
        finish_b.setStyleSheet(
            f"QPushButton {{ background:{T['start']}; color:#000; border:none;"
            f" border-radius:8px; padding:10px; font-size:14px; font-weight:700; }}")
        finish_b.clicked.connect(self._finish)
        root.addWidget(finish_b)

        skip_b = QPushButton("Skip — configure later in Settings")
        skip_b.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{T['muted']}; border:none; font-size:11px; }}")
        skip_b.clicked.connect(self._skip)
        root.addWidget(skip_b, alignment=Qt.AlignmentFlag.AlignCenter)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Select Server Folder")
        if p: self.srv_edit.setText(p)

    def _finish(self):
        s = load_settings()
        v = self.srv_edit.text().strip()
        if v: s["srv_path"] = v
        v = self.java_edit.text().strip()
        if v: s["java_path"] = v
        v = self.repo_edit.text().strip()
        if v: s["repo_url"] = v
        save_settings(s)
        self._mark(); self.accept()

    def _skip(self):
        self._mark(); self.reject()

    def _mark(self):
        try:
            open(FIRST_RUN_FLAG, "w").write("initialized\n")
        except Exception:
            pass
