# ⛏ MC CTRL — Minecraft Server Controller

> A powerful, fully-featured Python GUI for managing Minecraft servers. Handles everything from server launch and world management to GitHub backups, live performance monitoring, network tunneling, and multi-server control — all in one sleek, animated interface.

---

## ✨ What MC CTRL Can Do

### Server Control
- **One-click Start / Stop / Sync** with animated feedback and status indicators
- **Aikar JVM Flags** applied automatically for optimal GC performance and low-latency gameplay
- **Git Pull on Start** — always loads the latest world before launching
- **Git Push on Stop** — world is committed and pushed to GitHub automatically when you shut down
- **EULA auto-handling** — prompts you to accept the Minecraft EULA on first run; never blocks silently
- **Live server console** — type any command directly into the app and send it to the running server in real time
- **Quick Commands panel** — one-click buttons for Save World, Check TPS, Set Day/Night, Change Difficulty, Reload, and more

### Performance Monitoring
- **Live stats grid** refreshed every 2 seconds: TPS, Players, Latency, Uptime, RAM (system + server process), CPU (system + server process), Thread count
- **Color-coded values** — green for healthy, amber for warning, red for critical, with smooth transitions
- **Per-PID process tracking** — monitors only the exact Java process it launched, no full system scan overhead
- **TPS polling** via `tps` and `spark ping` commands sent automatically while the server is running
- **Uptime timer** displayed in HH:MM:SS format from the moment the server started

### World & Server Management
- **Active Server Switcher** — select which server subfolder loads by updating `level-name` in `server.properties` live
- **World Creation wizard** — pick server software (Paper, Purpur, Vanilla, Fabric), Minecraft version, world name, seed, level type, game mode, difficulty, hardcore toggle, and structure generation — then download the JAR and configure everything automatically
- **server.properties editor** — edit 23+ properties directly in the UI without touching any config file manually; save with one click
- **Plugin manager** — install, view, and remove plugin JARs without leaving the app
- **Resource pack manager** — install packs via file browser or drag-and-drop (requires `tkinterdnd2`); remove with one click
- **Subfolder-based multi-world support** — each subfolder with its own `server.properties` is auto-detected as a separate server instance

### GitHub Backup & Sync
- **Auto-upload timer** — configurable interval (default 10 minutes) pushes world changes to GitHub in the background while the server runs
- **Upload on Stop** — world folders are committed and pushed every time you stop the server
- **Manual Sync button** — `git add . → commit → push` on demand for config or plugin changes
- **Backup upload toggle** — master switch to disable all GitHub uploads without touching other settings
- **Timestamped world backups** — before any world creation or replacement, existing folders are copied with a timestamp suffix so nothing is ever lost

### Network & Connection Info
- **IP panel** showing Local (LAN), External (internet), Localhost, and Custom Domain addresses all at once
- **One-click copy** for any IP address
- **External IP auto-detection** via `api.ipify.org`
- **Editable port** — change the port in the UI and all displayed addresses update live
- **Custom domain / proxy support** — set your own domain and it replaces the external IP in the display

### playit.gg Tunnel Integration
- **Full playit.gg agent control** — start and stop the tunnel from inside MC CTRL
- **Auto-download** of `playit-windows.exe` directly from GitHub releases
- **Secret key injection** — paste your agent key once and it's written to `playit.toml` automatically on every start
- **Tunnel address detection** — the address appears automatically as soon as playit establishes the tunnel, with a toast notification
- **Agent log viewer** — all playit output is captured and displayed in a scrollable log with copy and clear buttons
- **First-run claim URL detection** — the browser claim link is highlighted in the log and shown as a long-lasting toast
- **TOML config patching** for both `%APPDATA%\playit\` and the folder next to the executable
- **Step-by-step setup guide** and troubleshooting FAQ built into the tab

### Multi-Server Control (MULTI CTRL)
- **Run up to 3 independent Minecraft servers simultaneously** in side-by-side columns
- **Per-server path selector** with folder browser
- **Per-server Start / Stop buttons** and individual log boxes
- **Shared command bar** — target Server 1, Server 2, Server 3, or All Servers with a single command
- **Independent process management** — each server runs its own Java process

### Theming & Appearance
- **64 built-in themes** across dark and light variants: Dark/Light Default, Midnight Blue, Creeper Green, Nether Red, Ocean, Sunset, Obsidian, Ender Night, Arctic, Forest, Rose Gold, Dracula, Lava, Sand, Void, Carbon, Lavender, Mocha, Sakura, Matrix, Nord, Solarized, Gruvbox, Cyberpunk, Slate, Amber, Copper, and colorblind-safe CB series (Blue & Orange, Green & Purple, High Contrast, Tol Muted, Monochrome)
- **Theme Search window** — filter by name, dark/light mode, and up to 6 color roles (bg, card, text, start, stop, sync) with hue-bucket buttons; live preview with color swatches
- **Custom Theme Creator** — build your own theme by picking every color role with a visual color picker; preview live and save with a custom name; saved themes persist across sessions
- **Glow effects** on active/selected elements, animated button press feedback, and smooth status transitions
- **Animated splash screen** on startup with a progress bar
- **Toast notifications** for every major action — positioned bottom-right, color-coded, auto-dismiss

### Layout & UI Customization
- **Swap layout** — move the log panel to the left or right side
- **Fullscreen mode** toggle
- **Show/hide performance panel** without restarting
- **Show/hide chat & events panel**
- **RAM display mode** — switch between percentage and x/y GB fraction
- **Lazy tab rendering** — only the Dashboard is built at startup; other tabs build on first visit for fast load

### Addon System
- **Python addon API** — drop any `.py` file into the `addons/` folder and it loads at startup
- **`setup(ctx)` entry point** — addons receive the app window, theme dict, log function, toast function, server command sender, and settings loader
- **Live addon management** in Settings — install, reload, and remove addons without restarting the app
- **Auto-generated README** in the addons folder explains the API

### Onboarding
- **First-launch setup dialog** — choose your theme and configure GitHub backup preferences before anything else happens; shown only once, re-openable from Settings

---

## 📋 Requirements

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.8+ | Must be in system PATH |
| **Git** | Any | Must be in system PATH and configured |
| **Java (JDK)** | 21 | Eclipse Adoptium recommended |
| **OS** | Windows | Uses `ctypes`, `taskkill`, `CREATE_NO_WINDOW` |
| **customtkinter** | Latest | Main UI framework |
| **psutil** | Latest | System and process metrics |

Optional:
- **tkinterdnd2** — enables drag-and-drop for resource packs

---

## 🚀 Quick Start

### 1. Clone or download
```
git clone https://github.com/GamerMahir07/minecraft-server.git
```

### 2. Install dependencies
```
install_requirements.bat
```
Or manually:
```bash
pip install customtkinter psutil
```

### 3. Configure paths (first launch or Settings panel)

Either edit `launcher.pyw` directly:
```python
SRV_PATH  = r"C:\path\to\your\server"
JAVA_PATH = r"C:\path\to\your\java.exe"
REPO_URL  = "https://github.com/you/your-repo"
```
Or launch the app and set them in **Settings → Server** — no file editing needed.

### 4. Run
```bash
pythonw launcher.pyw
```

---

## 🖥️ Interface Overview

### Dashboard
The main hub. Left column has Start / Stop / Sync buttons and Quick Commands. Right column has the Activity Log, Chat & Events feed, and the command input. The performance stats grid sits below.

### playit.gg Tab
Set up and control a free public tunnel so friends can connect without port forwarding. Auto-downloads the agent, manages the secret key, detects the tunnel address, and shows the full agent log.

### Server Info Tab
Online player list (live, auto-refreshing every 2s with kick buttons), active server switcher, plugin list, resource pack manager, and the full `server.properties` editor.

### Network & IPs Tab
All connection addresses in one place, plus the active server switcher and port editor.

### ⊞ MULTI CTRL Tab
Side-by-side control of up to 3 independent servers with shared command bar.

### Settings Window (⚙ button, top bar)
Theme picker, layout toggles, server paths, GitHub config, auto-upload settings, plugin manager, addon manager, and first-launch setup re-opener.

### 🎨 Theme Button (top bar)
Opens the searchable theme picker. Also contains the **+ Create Theme** button to build a custom theme with a visual color picker.

---

## ⌨️ Quick Commands Reference

| Button | Command sent |
|---|---|
| Save World | `save-all` |
| Player List | `list` |
| Check TPS | `tps` |
| Set Day | `time set day` |
| Set Night | `time set night` |
| Clear Weather | `weather clear` |
| Hard Mode | `difficulty hard` |
| Peaceful | `difficulty peaceful` |
| Safe Stop | `stop` |
| Reload | `reload` |

---

## 📁 File Structure

```
mc-launcher/
├── launcher.pyw              # Main application
├── icon.ico                  # Taskbar icon
├── settings.json             # Auto-generated user preferences
├── install_requirements.bat  # One-click dependency installer
├── addons/                   # Drop .py addon files here
│   └── README.md             # Addon API reference (auto-generated)
└── README.md                 # This file
```

---

## 🔧 Troubleshooting

**Window opens then immediately closes**
→ Run `python launcher.pyw` in a terminal to see the error output. Likely a missing dependency.

**`ModuleNotFoundError: No module named 'customtkinter'`**
→ Run `install_requirements.bat` or `pip install customtkinter psutil`.

**Git pull/push fails**
→ Confirm Git is installed (`git --version` in terminal). Check that `REPO_URL` is correct and you have push access. Make sure your Git credentials are configured.

**Server doesn't start / Java not found**
→ Verify `JAVA_PATH` in Settings points to the correct `java.exe`. Default assumes Eclipse Adoptium JDK 21.

**Performance stats all show `—`**
→ Stats populate after the server finishes loading. Wait for the `Done (Xs)!` message in the Activity Log.

**playit tunnel address never appears**
→ Check the Agent Log for a claim URL on first run. After claiming, stop and restart the agent. Make sure `playit.exe` path is correct.

**EULA popup blocks server start**
→ Read and accept the Minecraft EULA at `https://aka.ms/MinecraftEULA`, then click "I Agree" in the popup. This only happens once.

**Custom theme not saving**
→ Make sure `settings.json` is not read-only. The file is created automatically next to `launcher.pyw`.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern themed UI widgets built on tkinter |
| `psutil` | System and Java process performance metrics |
| `tkinterdnd2` | Optional — drag-and-drop for resource pack installation |

---

## 🎨 Addon API

Drop a `.py` file in the `addons/` folder. It will be loaded at startup.

```python
def setup(ctx):
    ctx["log"]("Hello from my addon!")
    ctx["show_toast"]("Addon loaded!", ctx["T"]["start"])

    # Available context keys:
    # ctx["app"]              — CTk root window
    # ctx["T"]               — theme colour dict (bg, card, border, text, muted, start, stop, sync, handoff)
    # ctx["log"](msg)        — write to Activity Log
    # ctx["show_toast"](m,c) — show bottom-right toast notification
    # ctx["send_server_cmd"] — send a command to the running MC server
    # ctx["load_settings"]   — returns current settings dict
```

Addons can be managed (reload, remove) from **Settings → MC CTRL App Addons** without restarting.

---

*Built for Windows · Personal Minecraft server hosting with friends · GamerMahir07*