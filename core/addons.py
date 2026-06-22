"""core/addons.py"""
import importlib.util, logging, os
from .constants import _ADDONS_DIR

logger = logging.getLogger(__name__)
_loaded_addons: dict = {}

def _load_addon(path: str) -> bool:
    try:
        name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(name, path)
        if not spec: return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _loaded_addons[name] = mod
        logger.info(f"Addon loaded: {name}")
        return True
    except Exception as e:
        logger.warning(f"Addon failed {path}: {e}")
        return False

def _load_all_addons():
    if not os.path.isdir(_ADDONS_DIR): return
    for fn in sorted(os.listdir(_ADDONS_DIR)):
        if fn.endswith(".py") and not fn.startswith("_"):
            _load_addon(os.path.join(_ADDONS_DIR, fn))
