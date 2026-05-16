# Minecraft Server Launcher

A modern GUI launcher for managing Minecraft Java servers on Windows using Python + CustomTkinter.

This launcher gives you a clean dashboard for starting, stopping, monitoring, and managing servers without touching the terminal every 5 seconds.

---

## Features

### Core Server Control

- Start and stop Minecraft servers
- Send console commands directly from the GUI
- Live server logs and chat monitoring
- Automatic status updates
- Java process detection
- Git sync support for server files

### Performance Monitoring

- Real-time server performance tracking
- CPU and memory monitoring
- Dedicated performance panel
- Quick status indicators

### Networking Tools

- Local IP detection
- External IP lookup
- Easy copy-to-clipboard connection info
- Configurable server port

### playit.gg Integration

- Built-in support for playit.gg tunnels
- Public server access without port forwarding
- Tunnel log viewer
- Automatic tunnel detection
- Claim link parsing

### Multi Server Control

- Control up to 3 Minecraft servers at once
- Separate logs and controls for each instance
- Independent server management

### Addon System

- Dynamic addon/module loading
- Expand launcher functionality with custom Python addons

### UI & Customization

- Multiple built-in themes
- Dark and light variants
- Fullscreen mode
- Rebuildable responsive UI
- Toggleable chat and performance panels

### Extra Utilities

- Drag-and-drop support (via tkinterdnd2)
- Toast notifications
- Auto upload scheduling
- Clipboard utilities
- EULA checking
- Persistent settings system

---

## Requirements

- Windows 10/11
- Python 3.10+
- Java 21+
- Minecraft Java Server files

Python packages:

```bash
pip install customtkinter tkinterdnd2
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/GamerMahir07/minecraft-server.git
cd minecraft-server
```

Install dependencies:

```bash
pip install customtkinter tkinterdnd2
```

Edit the paths inside `launcher.pyw`:

```python
SRV_PATH  = r"C:\path\to\your\server"
JAVA_PATH = r"C:\path\to\java.exe"
```

Run the launcher:

```bash
python launcher.pyw
```

---

## Configuration

Important globals inside the script:

| Variable | Description |
| --- | --- |
| `SRV_PATH` | Minecraft server folder |
| `JAVA_PATH` | Path to Java executable |
| `REPO_URL` | Git repository used for syncing |

---

## Addons

The launcher supports loading custom addon modules dynamically.

You can create Python addons to extend functionality such as:

- Backup systems
- Discord integration
- Modpack helpers
- Custom automation
- Remote tools

---

## playit.gg Setup

1. Install the playit.gg client
2. Open the Playit tab
3. Select the executable path
4. Start a tunnel
5. Share the generated `.ply.gg` address with friends

---

## Themes

Included themes:

- Dark (Default)
- Light (Default)
- Midnight Blue
- Creeper Green
- Nether Red
- Ocean
- Sunset

Both dark and light versions are available for most themes.

---

## Planned Features

- Mod/plugin manager
- World manager
- Remote dashboard
- Docker support
- Cross-platform support
- Integrated installer

---

## Troubleshooting

### Server does not start

- Check Java path
- Verify server files exist
- Accept the Minecraft EULA
- Make sure the server jar works normally

### playit.gg not working

- Verify the executable path
- Check firewall permissions
- Restart the tunnel client

### Missing modules

Install dependencies again:

```bash
pip install -U customtkinter tkinterdnd2
```

---

## License

MIT License

---

## Credits

Built by entity["people","Md. Mahir Zawad Khan","Minecraft launcher developer"] using:

- Python
- CustomTkinter
- Minecraft Java Edition
- playit.gg
