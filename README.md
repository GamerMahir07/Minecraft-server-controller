# ⛏ MC Server Controller

A Python-based GUI for managing a Minecraft server with integrated Git synchronization. Automates pulling world updates, launching the server with optimized Aikar JVM flags, and pushing changes back to GitHub.

**Runs on Windows, Linux, and macOS.**

---

## ✨ Features

| Feature | Description |
|---|---|
| **Cross-platform** | Works on Windows, Linux, and macOS — platform-specific calls (taskkill, os.startfile, etc.) are handled automatically |
| **Automated Git Sync** | Pulls the latest world data on startup and pushes updates when the server stops |
| **Optimized JVM Flags** | Launches using Aikar's flags for high performance and stable garbage collection |
| **Dual-Log Interface** | Separate Activity Log for system events and a Chat/Events box for player activity |
| **Performance Monitor** | Live stats for TPS, RAM, CPU, latency, uptime, player count, and thread count — updated every 2 seconds |
| **Network & IPs Panel** | Displays local, external, and localhost IPs with one-click copy buttons |
| **Server Info Panel** | Panels for online players, plugins, and server.properties editor |
| **playit.gg Integration** | Built-in tunnel control — start/stop the agent, auto-detect tunnel address, claim URL detection |
| **🧩 Addons Tab** | Split-pane addon manager: list on the left, full description + settings + source preview on the right |
| **Auto Upload** | Scheduled automatic Git push at a configurable interval |
| **30+ Themes** | Visual presets including Obsidian, Midnight Blue, Dracula, Nord, Matrix, Cyberpunk, and more |
| **Multi CTRL** | Control up to 3 independent server instances simultaneously from one window |
| **Live Console** | Type server commands directly into the app and send them to the running server |

---

## 📋 Requirements

| Requirement | Notes |
|---|---|
| **Python 3.x** | Must be on PATH |
| **Git** | Must be on PATH |
| **Java 21** | See platform notes below |
| **customtkinter** | `pip install customtkinter` |
| **psutil** | `pip install psutil` |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/GamerMahir07/minecraft-server.git
```

### 2. Install Python dependencies

**Windows** — run the included batch file:
```
install_requirements.bat
```

**Linux / macOS** — run directly:
```bash
pip install customtkinter psutil
```

### 3. Configure your paths

Open the app and go to **⚙ Settings → Server** to set:

- **Server path** — folder containing `server.jar`
- **Java path** — path to your `java` executable
- **GitHub repo URL** — remote repo for world backup

Or edit these defaults at the top of `launcher.pyw`:

```python
SRV_PATH  = "/path/to/your/server"
JAVA_PATH = "java"          # or full path if not on PATH
REPO_URL  = "https://github.com/you/your-repo"
```

### 4. Run the launcher

**Windows:**
```bash
pythonw launcher.pyw
```

**Linux / macOS:**
```bash
python3 launcher.pyw
```

---

## 🖥️ Platform Notes

### Windows
- Java 21 from [Eclipse Adoptium](https://adoptium.net/temurin/releases/?version=21) — default path is pre-filled
- Server processes killed via `taskkill /F /IM java.exe`
- Folders opened via `os.startfile`
- playit downloads `playit-windows.exe`

### Linux
- Install Java 21: `sudo apt install openjdk-21-jdk` (Ubuntu/Debian) or equivalent
- `java` must be on PATH — the default Java path is just `"java"`
- Server processes killed via `pkill -f 'server.jar'`
- Folders opened via `xdg-open`
- playit downloads `playit-linux-amd64` and `chmod +x`s it automatically
- Window icon uses `.png` fallback (`.ico` not supported on Linux)
- The `.pyw` extension is Windows-specific; on Linux just run `python3 launcher.pyw`

### macOS
- Install Java 21 from [Adoptium](https://adoptium.net) or via Homebrew: `brew install --cask temurin@21`
- Folders opened via `open`
- playit downloads `playit-darwin`

---

## 🖥️ Usage

### Buttons

| Button | What it does |
|---|---|
| **▶ Start Server** | Pulls latest files from GitHub, then launches the server with Aikar JVM flags |
| **■ Stop Server** | Sends `/stop` to the server, kills the Java process, and pushes world data to GitHub |
| **↑ Sync & Upload** | Manually runs `git add .` → commit → push |

### Console

Type any server command into the bottom input field (without `/`) and press **Enter** or **Send**.

```
say Hello everyone!
op PlayerName
time set day
difficulty hard
```

### Quick Commands

Pre-built buttons for common commands: Save World, Set Day/Night, Clear Weather, Check TPS, Hard/Peaceful mode, and more.

---

## 🧩 Addons

Addons are `.py` files placed in the `addons/` folder next to `launcher.pyw`. They are loaded at startup.

### Minimal addon

```python
def setup(ctx):
    ctx["log"]("Hello from my addon!")
```

### Addon with metadata and settings

```python
__meta__ = {
    "title":       "My Addon",
    "version":     "1.0",
    "author":      "You",
    "description": "What this addon does.",
    "preview_colors": ["#ff0000", "#00ff00"],
    "settings": [
        ("My setting", "my_addon_key",    "default", "entry"),
        ("Toggle",     "my_addon_enabled", True,     "switch"),
    ]
}

def setup(ctx):
    ctx["log"]("My addon loaded!")
```

Addons with `__meta__` get a full detail panel in the **🧩 Addons** tab — description, colour swatches, settings form, and a source preview.

### Context object

| Key | Type | Description |
|---|---|---|
| `ctx["app"]` | CTk window | Root application window |
| `ctx["T"]` | dict | Current theme colour dict |
| `ctx["log"](msg)` | function | Write a line to the activity log |
| `ctx["show_toast"](msg, color)` | function | Show a toast notification |
| `ctx["send_server_cmd"](cmd)` | function | Send a command to the running server |
| `ctx["load_settings"]()` | function | Returns the current settings dict |

To install an addon: drop the `.py` file into the `addons/` folder, or use **🧩 Addons → + Install** in the app.

---

## ⚙️ Settings

All settings are saved automatically to `settings.json`.

| Setting | Description |
|---|---|
| **Theme** | Choose from 30+ visual presets |
| **Fullscreen** | Toggle fullscreen mode |
| **Log panel on left** | Swap the layout |
| **Show performance panel** | Show/hide the live stats grid |
| **Show chat & events panel** | Show/hide the player chat feed |
| **Server path** | Path to the folder containing `server.jar` |
| **GitHub repo URL** | Remote URL for Git sync |
| **Java path** | Full path to `java` (or just `java` if on PATH) |
| **Enable auto upload** | Push to GitHub on a timer |
| **Upload interval** | How often auto upload runs (minutes) |
| **Upload world on stop** | Push world folders to GitHub when server stops |

---

## 📁 File Structure

```
mc-launcher/
├── launcher.pyw              # Main application
├── icon.ico                  # Window icon (Windows)
├── icon.png                  # Window icon (Linux/macOS)
├── settings.json             # Saved preferences (auto-generated)
├── install_requirements.bat  # Windows dependency installer
├── addons/                   # Drop addon .py files here
│   └── README.md             # Addon API reference (auto-generated)
└── README.md                 # This file
```

---

## 🔧 Troubleshooting

**Window opens but immediately closes (Windows)**
→ Run with `python launcher.pyw` in a terminal to see the error output.

**`ModuleNotFoundError: No module named 'customtkinter'`**
→ Run `pip install customtkinter psutil` (or `install_requirements.bat` on Windows).

**Git pull/push fails**
→ Make sure Git is installed and on PATH. Verify `REPO_URL` in Settings and that you have push access.

**Server doesn't start / Java not found**
→ Check that the Java path in Settings points to a valid `java` binary. On Linux run `which java` to find it.

**Performance stats all show `—`**
→ Stats populate once the server finishes starting. Wait for `Done (Xs)!` in the activity log.

**playit.gg address never appears**
→ Check the Agent Log in the playit.gg tab for a claim URL or error. Stop and restart the agent if needed.

**Linux: permission denied on playit binary**
→ The app runs `chmod +x` automatically on download. If you placed it manually: `chmod +x ./playit`

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern themed UI widgets |
| `psutil` | System and process performance metrics |
| `tkinterdnd2` | Drag-and-drop support (optional) |

---

*Designed for personal Minecraft server hosting · Windows, Linux, macOS*
