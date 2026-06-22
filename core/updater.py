"""core/updater.py — GitHub release checker"""
import json, logging, urllib.request
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)
CURRENT_VERSION = "8.0.0"
RELEASES_URL    = "https://api.github.com/repos/GamerMahir07/mc-ctrl/releases/latest"

class UpdateCheckerThread(QThread):
    update_found = pyqtSignal(str, str)
    up_to_date   = pyqtSignal()

    def run(self):
        try:
            req = urllib.request.Request(
                RELEASES_URL,
                headers={"User-Agent":"MC-CTRL/1.0",
                         "Accept":"application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            tag = data.get("tag_name","").lstrip("v")
            url = data.get("html_url","")
            if tag and tag != CURRENT_VERSION:
                self.update_found.emit(tag, url)
            else:
                self.up_to_date.emit()
        except Exception as e:
            logger.debug(f"Update check: {e}")
