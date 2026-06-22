"""
launcher.pyw - MC CTRL entry point
Dep-check (plain tkinter) -> first-run flag -> launch
"""
import sys, os

# Ensure project root is on path so `import core` and `import ui` resolve
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _check_deps():
    missing = []
    for pkg in ("PyQt6", "psutil"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(
            "MC CTRL - Missing Dependencies",
            "The following packages are not installed:\n\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nRun  install_requirements.bat  (Windows)\n"
              "or   install_requirements.sh   (Mac/Linux)\n"
              "then restart MC CTRL.")
        root.destroy()
    except Exception:
        print("MISSING:", missing)
    sys.exit(1)


_check_deps()

from ui.main_window import main
main()
