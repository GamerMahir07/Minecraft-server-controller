# MC CTRL Addon API

Addons are .py files in this folder, loaded at startup.

## Minimal addon

```python
def setup(ctx):
    ctx["log"]("Hello from my addon!")
```

## Context keys
- ctx["app"]              — CTk root window
- ctx["T"]               — theme colour dict
- ctx["log"](msg)        — write to server log
- ctx["show_toast"](m,c) — show a toast notification
- ctx["send_server_cmd"] — send command to running MC server
- ctx["load_settings"]   — returns settings dict
