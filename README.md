# MC CTRL

A modern Minecraft server launcher and control panel built with Python + CustomTkinter.

MC CTRL is designed to make hosting and managing Minecraft servers easier with a clean dashboard, remote controls, backups, Docker integration, modpack tools, performance monitoring, and network sharing support.

---

## Features

### Dashboard System
- Clean multi-tab interface
- Real-time server logs
- Performance monitoring
- Quick server controls
- Multiple layout modes
- Built-in status tracking

### Server Management
- Start / stop / restart Minecraft servers
- Java process management
- Auto-detect server files
- Server directory controls
- Console command support
- Backup system

### Remote & Network Features
- Remote dashboard access
- LAN sharing support
- playit.gg integration support
- Network control tools
- Multi-CTRL support

### Modding & Packs
- Modpack management
- Addon system
- Custom server setups
- Easy file organization

### Docker Support
- Docker tab included
- Container-based server support
- Easier deployment workflows

### Customization
- Huge built-in theme collection
- Light and dark themes
- UI customization settings
- Layout customization

### Performance Tools
- RAM monitoring
- CPU usage tracking
- Live stats panel
- Optional performance widgets

---

## Screens Included

Main tabs:
- Dashboard
- Server Info
- Docker
- Modpacks
- Multi-CTRL

Dashboard modes:
- Dashboard
- MC Ctrl
- Network
- playit.gg
- Remote

---

## Requirements

### Python
Recommended:
- Python 3.11+

### Java
Recommended:
- Java 21

### Operating Systems
Supported:
- Windows
- Linux
- macOS

---

## Python Dependencies

Install requirements manually:

```bash
pip install customtkinter psutil
```

Or use your installer script if included.

---

## Project Structure

```text
project/
│
├── launcher.pyw
├── settings.json
├── server.jar
├── mods/
├── backups/
├── logs/
└── README.md
```

---

## Running MC CTRL

### Windows

```bash
python launcher.pyw
```

or simply double-click:

```text
launcher.pyw
```

### Linux / macOS

```bash
python3 launcher.pyw
```

---

## First Launch

On first startup, MC CTRL will:

- Generate settings automatically
- Create required configuration files
- Apply the default theme
- Detect server paths
- Prepare the dashboard environment

---

## Remote Dashboard Hosting

MC CTRL is designed so devices on the same network can access the dashboard remotely.

Possible use cases:
- Monitor the server from your phone
- Manage the server from another PC
- Local network administration
- Remote control utilities

Future versions may expand:
- Web dashboard support
- Authentication systems
- Public remote access
- Mobile-optimized interface

---

## Docker Support

Docker integration helps isolate Minecraft servers in containers.

Benefits:
- Easier deployment
- Cleaner environments
- Portable server setups
- Better dependency management

Future improvements may include:
- Auto container creation
- Docker Compose templates
- One-click deployment

---

## Theme System

MC CTRL includes an absolutely massive theme collection.

Examples:
- Tokyonight
- Dracula
- Creeper Green
- Ocean
- Midnight Purple
- Forest
- Nether Red
- Frostbite
- Bubblegum
- Deep Space
- Ultra Black

Both light and dark variants are available for many themes.

---

## Backup System

Included backup tools allow:
- Manual backups
- Organized save storage
- Easier world recovery
- Safer experimentation

---

## Planned Features

- Web-based dashboard
- Mobile dashboard UI
- Plugin marketplace
- Multi-server cluster management
- Remote authentication
- Cloud backup syncing
- Better Docker tooling
- One-click server installers
- Modpack downloader
- Performance graphs

---

## Troubleshooting

### Java not found
Install Java 21 and update the configured Java path.

### App does not start
Make sure required Python packages are installed:

```bash
pip install customtkinter psutil
```

### Server does not launch
Check:
- `server.jar` exists
- Java path is correct
- Enough RAM is available
- Firewall permissions

---

## License

MIT License

You are free to:
- Use
- Modify
- Distribute
- Fork

with proper attribution.

---

## Credits

Created by Md. Mahir Zawad Khan.

GitHub repository:

```text
https://github.com/GamerMahir07/minecraft-server
```

---

## Notes

This project is still evolving and may receive major updates over time.

Some systems shown in the UI may still be experimental or under development.

---

## Minecraft Server Hosting But Epic

fr this launcher got enough themes to summon a GPU 💀

