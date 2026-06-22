# MC CTRL — First Time Setup

Welcome! This guide gets you running in under 5 minutes.

---

## Requirements

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) — check "Add to PATH" during install |
| Java | 17+ | For running the Minecraft server itself |
| OS | Windows 10/11 | Linux/macOS work but Windows is primary |

---

## Step 1 — Install Dependencies

Double-click `scripts/install_requirements.bat`  
*(or run `python scripts/install_requirements.py` in a terminal)*

This installs:
- `customtkinter` — the UI framework
- `psutil` — server performance monitoring
- `pillow` — image handling (server icon, etc.)

---

## Step 2 — Launch

Double-click `launcher.pyw`  
*(or `python launcher.pyw` in a terminal)*

---

## Step 3 — First Run Wizard

On first launch, the setup wizard will guide you through:

1. **Server path** — where your `server.jar` lives (or will live)
2. **Java executable** — usually just `java`, or full path if you have multiple JDKs
3. **RAM allocation** — how much memory to give the server
4. **Server type** — Paper, Spigot, Vanilla, Fabric, Forge, etc.

All settings are saved to `settings.json` and can be changed any time via the  gear icon.

---

## Folder Layout

```
MC-CTRL/
├── launcher.pyw          <- double-click to run
├── settings.json         <- auto-created on first launch
├── .mc_ctrl_initialized  <- auto-created; marks first-run complete
│
├── addons/               <- drop .py addon scripts here
├── assets/               <- icon.ico, icon.png
├── scripts/              <- install helpers
│   ├── install_requirements.bat
│   ├── install_requirements.sh
│   └── install_requirements.py
└── themes/
    └── themes_all_128.txt
```

---

## Common Issues

**"python is not recognized"**  
Python isn't on your PATH. Re-run the Python installer and check "Add Python to PATH".

**"customtkinter not found" after installing**  
Close and re-open the terminal/launcher after installation.

**Server won't start**  
Make sure `server.jar` exists in your server path and Java 17+ is installed.  
Run `java -version` in a terminal to check.

**Port 25565 already in use**  
Another server or app is using that port. Change the port in `server.properties` or stop the other process.

---

## Useful Links

- [Minecraft Server Download](https://www.minecraft.net/en-us/download/server)
- [PaperMC (recommended)](https://papermc.io/downloads)
- [Adoptium Java 21](https://adoptium.net/)
- [Modrinth (mods/plugins)](https://modrinth.com)
