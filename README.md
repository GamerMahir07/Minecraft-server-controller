# MC CTRL — Tauri + Vanilla HTML UI

The lightest possible native window frontend for MC CTRL.
**No Node.js. No npm. No node_modules. No bundler.**
Just one HTML file and a Rust backend.

## File sizes

| What | Size |
|---|---|
| `ui/index.html` | ~20 KB |
| `mc-ctrl-ui.exe` (release build) | ~3 MB |
| `node_modules/` | **0 bytes — doesn't exist** |

Compare to the React version: ~150 MB of node_modules, 8 MB exe.

---

## Prerequisites (one-time installs)

### 1. Rust + Cargo
https://rustup.rs — download and run `rustup-init.exe`
```
rustc --version   # should print 1.70+
```

### 2. Visual Studio C++ Build Tools
https://visualstudio.microsoft.com/visual-cpp-build-tools/
Select **Desktop development with C++** during install.

### 3. WebView2 Runtime
Already on every Windows 10 (post-2021) and Windows 11 machine.
If missing: https://developer.microsoft.com/microsoft-edge/webview2/

That's it. No Node, no npm, no Python packages.

---

## Build

Open a terminal in this `webui/` folder:

```bat
cargo tauri build
```

First build: **4–7 minutes** (Rust compiles from scratch).
Subsequent builds: **20–40 seconds**.

Output:
```
webui\src-tauri\target\release\mc-ctrl-ui.exe
```

Copy it next to `launcher.pyw`:
```bat
copy src-tauri\target\release\mc-ctrl-ui.exe ..\mc-ctrl-ui.exe
```

---

## Dev mode (live reload)

```bat
cargo tauri dev
```

Edit `ui/index.html` and save — the window reloads instantly.
No build step needed during development.

---

## How it works

```
ui/index.html          ← the entire frontend (HTML + CSS + JS, one file)
src-tauri/
  Cargo.toml           ← Rust dependencies
  tauri.conf.json      ← points the window at ui/index.html
  src/main.rs          ← backend: settings IO, server process, log streaming
```

The Tauri window is just a WebView2 frame pointed at the local HTML file.
The JS calls `invoke("command_name", {args})` to talk to the Rust backend.
The Rust backend emits events (`"log"`, `"server-started"`, `"server-stopped"`)
that the JS listens to with `listen("event-name", handler)`.

Settings are read/written from the **same `settings.json`** as the Python
launcher, so switching between UIs requires no reconfiguration.

---

## Project structure

```
webui/
├── README.md              this file
├── src-tauri/
│   ├── Cargo.toml         Rust deps (tauri, tokio, serde_json only)
│   ├── tauri.conf.json    window config + permissions
│   ├── icons/             app icon (copy icon.ico + icon.png here)
│   └── src/
│       └── main.rs        Rust backend
└── ui/
    └── index.html         complete frontend
```

---

## Troubleshooting

**`error: linker 'link.exe' not found`**
→ Install Visual Studio C++ Build Tools (step 2 above).

**White/blank window**
→ WebView2 is starting up. Wait 2–3 seconds.
  Run from terminal to see errors: `mc-ctrl-ui.exe`

**Settings not loading**
→ `settings.json` must be in the same folder as `mc-ctrl-ui.exe`,
  OR set the environment variable `MCCTRL_SETTINGS=C:\path\to\settings.json`.

**`invoke is not defined`**
→ You're opening `index.html` directly in a browser instead of through Tauri.
  The `invoke` bridge only works inside the Tauri window. Use `cargo tauri dev`.
