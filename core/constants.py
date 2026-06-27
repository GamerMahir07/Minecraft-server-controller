"""core/constants.py"""
import os, re, sys

def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_BASE_DIR    = _get_base_dir()
_ASSETS_DIR  = os.path.join(_BASE_DIR, "assets")
_THEMES_DIR  = os.path.join(_BASE_DIR, "themes")
_ADDONS_DIR  = os.path.join(_BASE_DIR, "addons")
_SCRIPTS_DIR = os.path.join(_BASE_DIR, "scripts")

def _find_file(*candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return ""

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LIN = sys.platform.startswith("linux")
IS_PI  = IS_LIN and (
    os.path.exists("/proc/device-tree/model") and
    "raspberry" in open("/proc/device-tree/model", "rb").read().decode("utf-8","ignore").lower()
    if os.path.exists("/proc/device-tree/model") else False
)
CREATE_NO_WINDOW = 0x08000000 if IS_WIN else 0

# Icon: prefer .ico on Windows (taskbar), .png elsewhere
if IS_WIN:
    ICON_PATH = _find_file(
        os.path.join(_ASSETS_DIR, "icon.ico"),
        os.path.join(_ASSETS_DIR, "icon.png"),
        os.path.join(_BASE_DIR,   "icon.ico"),
        os.path.join(_BASE_DIR,   "icon.png"),
    )
else:
    ICON_PATH = _find_file(
        os.path.join(_ASSETS_DIR, "icon.png"),
        os.path.join(_ASSETS_DIR, "icon.ico"),
        os.path.join(_BASE_DIR,   "icon.png"),
        os.path.join(_BASE_DIR,   "icon.ico"),
    )

THEMES_FILE = _find_file(
    os.path.join(_THEMES_DIR, "themes_all_128.txt"),
    os.path.join(_BASE_DIR,   "themes_all_128.txt"),
)
SETTINGS_FILE  = os.path.join(_BASE_DIR, "settings.json")
FIRST_RUN_FLAG = os.path.join(_BASE_DIR, ".mc_ctrl_initialized")

DEFAULT_SRV_PATH  = os.path.join(os.path.expanduser("~"), "minecraft-server")
DEFAULT_JAVA_PATH = "java"
REPO_URL          = ""
APP_VERSION       = "8.0.0"
UPDATE_URL        = "https://api.github.com/repos/GamerMahir07/minecraft-server/releases/latest"
MODRINTH_API      = "https://api.modrinth.com/v2"

# Font: Segoe UI is Windows-only; fall back gracefully on other platforms
if IS_WIN:
    UI_FONT = "Segoe UI"
elif IS_MAC:
    UI_FONT = "SF Pro Text"
else:
    UI_FONT = "Inter,Ubuntu,DejaVu Sans,Sans"

MONO_FONT = "Consolas" if IS_WIN else "JetBrains Mono,Fira Code,DejaVu Sans Mono,Monospace"

# Regex
STRIP_RE       = re.compile(r'^\[[\d:]+\]\s*\[?(?:Server thread/)?(?:INFO|WARN|ERROR)\]?\s*(?:\[Not Secure\])?\s*:?\s*', re.I)
DONE_RE        = re.compile(r'Done \([\d.]+s\)!', re.I)
SPARK_TPS      = re.compile(r'TPS from last 1m[^:]+:\s*([\d.]+)', re.I)
TPS_RE2        = re.compile(r'Current TPS[\s:]+([0-9.]+)', re.I)
PLAYER_RE      = re.compile(r'There are (\d+) of a max of \d+ players', re.I)
LIST_NAMES_RE  = re.compile(r'There are \d+[^:]+:\s*(.+)', re.I)
CHAT_RE        = re.compile(r'<([^>]+)>\s*(.+)')
JOIN_RE        = re.compile(r'^(\w+) joined the game', re.I)
LEAVE_RE       = re.compile(r'^(\w+) (?:lost connection|left the game)', re.I)
DEATH_RE       = re.compile(r'(\w+) (was |died|fell|drowned|burned|blew|suffocated|starved|withered)', re.I)
LATENCY_RE     = re.compile(r'(\w+)\s+has\s+(?:a\s+ping\s+of\s+)?(\d+)\s*ms', re.I)
LATENCY_RE2    = re.compile(r'(\w+)\s+(\d+)\s*ms', re.I)
LATENCY_RE3    = re.compile(r'ping:\s*(\d+)', re.I)
PLAYIT_ADDR_RE = re.compile(r'((?:[\w\-]+\.)+(?:ply\.gg|playit\.gg|joinmc\.link|mc\.gg)(?::\d+)?)', re.I)
PLAYIT_CLAIM_RE= re.compile(r'(https?://[^\s]+(?:playit|claim|tunnel)[^\s]*)', re.I)
