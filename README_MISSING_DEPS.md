# MC CTRL — Missing Dependencies

One or more required packages are not installed.  
This page explains how to fix it.

---

## Quick Fix (Windows)

Double-click:
```
scripts\install_requirements.bat
```
Then re-launch `launcher.pyw`.

---

## Quick Fix (Any OS — Terminal)

```bash
python -m pip install customtkinter psutil pillow --upgrade
```

Or use the installer script:
```bash
python scripts/install_requirements.py
```

---

## What's Missing?

| Package | Used For | Install Command |
|---|---|---|
| `customtkinter` | The entire UI | `pip install customtkinter` |
| `psutil` | CPU / RAM monitoring | `pip install psutil` |
| `pillow` (PIL) | Server icon, image handling | `pip install pillow` |

---

## Troubleshooting

### "pip is not recognized"
Your Python installation is incomplete or not on PATH.

Option A — Use the Python Launcher:
```bash
py -m pip install customtkinter psutil pillow
```

Option B — Reinstall Python from [python.org](https://python.org),  
making sure to check **"Add Python to PATH"**.

---

### "Permission denied" during install

Run the terminal as Administrator, or add `--user`:
```bash
pip install customtkinter psutil pillow --user
```

---

### Multiple Python versions installed

Make sure you're installing to the same Python that runs `launcher.pyw`.  
Check which Python is being used:
```bash
python -c "import sys; print(sys.executable)"
```
Then install to that exact interpreter:
```bash
C:\path\to\python.exe -m pip install customtkinter psutil pillow
```

---

### Still broken after installing

Try a clean install:
```bash
pip uninstall customtkinter psutil pillow -y
pip install customtkinter psutil pillow
```

If `psutil` fails to build on Linux:
```bash
sudo apt install python3-dev gcc   # Debian/Ubuntu
pip install psutil
```

---

## Getting Help

Open an issue on the project GitHub page and include the output of:
```bash
python -m pip list
python --version
```
