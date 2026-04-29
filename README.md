# ⛏ MC Server Controller

A sleek, Python-based GUI for managing a Minecraft server with integrated Git synchronization. Automates pulling world updates, launching the server with optimized Aikar JVM flags, and pushing changes back to GitHub — making hosting hand-offs seamless.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Automated Git Sync** | Pulls the latest world data on startup and pushes updates when the server stops |
| **Optimized JVM Flags** | Launches using Aikar's flags for high performance and stable garbage collection |
| **Dual-Log Interface** | Separate Activity Log for system events and a Chat/Events box for player activity |
| **Performance Monitor** | Live stats for TPS, RAM, CPU, latency, uptime, player count, and thread count — updated every 2 seconds |
| **Server IP Panel** | Displays local, external, localhost, and custom domain IPs with one-click copy buttons |
| **Server Info Panel** | Collapsible panels for plugins, online players, resource packs, and server.properties |
| **Auto Upload** | Scheduled automatic Git push at a configurable interval (default: every 10 minutes) |
| **25+ Themes** | Visual presets including Obsidian, Midnight Blue, Creeper Green, Dracula, Nord, Matrix, and more |
| **Headless Operation** | Runs the Java process without an external console window, routing all output into the app |
| **Live Console** | Type server commands directly into the app and send them to the running server in real time |

---

## 📋 Requirements

Before running the launcher, make sure you have the following installed:

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.x | Must be added to system PATH |
| **Git** | Any | Must be configured in system PATH |
| **Java (JDK)** | 21 | Default path points to Eclipse Adoptium JDK 21 |
| **OS** | Windows | Uses `ctypes` and `taskkill` — not compatible with macOS/Linux |

---

## 🚀 Quick Start

### 1. Clone or download this repository

```
git clone https://github.com/GamerMahir07/minecraft-server.git
```

### 2. Install dependencies

Run the included batch file — it handles everything automatically:

```
install_requirements.bat
```

Or install manually:

```bash
pip install customtkinter psutil matplotlib
```

### 3. Configure your paths

Open `launcher.pyw` and update these three variables near the top of the file:

```python
SRV_PATH  = r"C:\path\to\your\server"          # Folder containing server.jar
JAVA_PATH = r"C:\path\to\your\java.exe"         # Your Java 21 executable
REPO_URL  = "https://github.com/you/your-repo"  # GitHub repo for world storage
```

> These can also be changed at any time from the **Settings → Server** panel inside the app without editing the script.

### 4. Run the launcher

Double-click `launcher.pyw`, or run it from a terminal:

```bash
pythonw launcher.pyw
```

---

## 🖥️ Usage

### Buttons

| Button | What it does |
|---|---|
| **▶ Start Server** | Pulls latest files from GitHub, then launches the server with Aikar JVM flags |
| **■ Stop Server** | Sends `/stop` to the server, kills the Java process, and pushes world data to GitHub |
| **↑ Sync & Upload** | Manually runs `git add .` → commit → push (useful for config file changes) |

### Console

Type any server command into the bottom input field (without the leading `/`) and press **Enter** or click **Send** to execute it on the live server.

**Examples:**
```
say Hello everyone!
op PlayerName
time set day
difficulty hard
```

---

## ⚙️ Settings

All settings are saved automatically to `settings.json` in the same directory as the launcher.

| Setting | Description |
|---|---|
| **Theme** | Choose from 25+ visual presets |
| **Fullscreen** | Toggle fullscreen mode |
| **Show RAM as x/y GB** | Switch between percentage and fraction display for RAM |
| **Log panel on left** | Swap the layout so the activity log appears on the left |
| **Show performance panel** | Show or hide the live stats grid |
| **Show chat & events panel** | Show or hide the player chat and event feed |
| **Server path** | Path to the folder containing `server.jar` |
| **GitHub repo URL** | Remote URL for Git sync operations |
| **Java path** | Full path to your `java.exe` |
| **Enable auto upload** | Automatically push to GitHub on a timer |
| **Upload interval** | How often auto upload runs (in minutes) |
| **Upload world on stop** | Push world folders to GitHub when the server is stopped |

---

## 📁 File Structure

```
mc-launcher/
├── launcher.pyw         # Main application
├── icon.ico             # Taskbar and window icon
├── settings.json        # Saved user preferences (auto-generated)
├── install_requirements.bat  # One-click dependency installer
└── README.md            # This file
```

---

## 🔧 Troubleshooting

**The window opens but immediately closes**
→ Make sure you're running with `pythonw launcher.pyw`, not `python launcher.pyw`. If you need to see errors, run with `python launcher.pyw` in a terminal.

**`ModuleNotFoundError: No module named 'customtkinter'`**
→ Run `install_requirements.bat` or manually run `pip install customtkinter psutil matplotlib`.

**Git pull/push fails on start or stop**
→ Make sure Git is installed and in your PATH. Run `git --version` in a terminal to verify. Also confirm your `REPO_URL` is correct and you have push access to the repository.

**Server doesn't start / Java not found**
→ Check that `JAVA_PATH` in the script (or in Settings) points to the correct `java.exe`. The default path is for Eclipse Adoptium JDK 21.

**Performance stats all show `—`**
→ Stats populate once the server is fully started. Wait for the `Done (Xs)! For help, type "help"` message in the activity log.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern themed UI widgets |
| `psutil` | System and process performance metrics |
| `matplotlib` | Graphing support (TkAgg backend) |

---

*Built for Windows · Designed for personal Minecraft server hosting with friends*
