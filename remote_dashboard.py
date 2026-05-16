"""
MC CTRL — Remote Mobile Dashboard
Runs a Flask web server so you can control the Minecraft server
from any phone/tablet on your network.

Integrates as a tab in launcher.pyw.
Call build_remote_tab(parent, ctx) to embed it.
"""

from __future__ import annotations
import threading, time, json, os, sys, socket
from datetime import datetime

# ── shared state (injected by launcher) ──────────────────
_state = {
    "server_running":  False,
    "perf":            {},
    "online_players":  {},
    "log_lines":       [],
    "send_cmd_fn":     None,
    "start_fn":        None,
    "stop_fn":         None,
    "flask_running":   False,
    "flask_port":      5000,
    "flask_thread":    None,
}

# ── HTML served to the browser ────────────────────────────
_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>MC CTRL</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@400;600;800&display=swap');
:root{
  --bg:#07080a;--surface:#0f1014;--card:#161820;--border:#232530;
  --green:#00e87a;--red:#ff3d52;--blue:#3d9bff;--amber:#ffb020;
  --text:#dde1f0;--muted:#4a4e66;
  --r:14px; --font:'Outfit',sans-serif; --mono:'Space Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--font);overflow-x:hidden}
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 4px);
}
/* ── header ── */
header{
  position:sticky;top:0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:13px 18px;
  background:rgba(15,16,20,.92);
  border-bottom:1px solid var(--border);
  backdrop-filter:blur(14px);
}
.logo{font-size:17px;font-weight:800;letter-spacing:-.5px;color:var(--green);
  text-shadow:0 0 18px rgba(0,232,122,.35)}
.logo em{color:var(--muted);font-style:normal}
.live{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);font-family:var(--mono)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);
  box-shadow:0 0 7px var(--green);animation:blink 2s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
/* ── status strip ── */
.strip{
  display:flex;align-items:center;gap:10px;
  padding:9px 18px;
  background:var(--surface);border-bottom:1px solid var(--border);
  font-family:var(--mono);font-size:11px;
}
.pill{padding:3px 10px;border-radius:99px;font-size:10px;font-weight:700;letter-spacing:.5px}
.pill-on {background:rgba(0,232,122,.1);color:var(--green);border:1px solid rgba(0,232,122,.25)}
.pill-off{background:rgba(255,61,82,.1) ;color:var(--red)  ;border:1px solid rgba(255,61,82,.25)}
.strip-up{color:var(--muted)}
/* ── layout ── */
main{padding:14px;display:flex;flex-direction:column;gap:12px;max-width:520px;margin:0 auto}
/* ── card ── */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
.ch{padding:10px 14px;border-bottom:1px solid var(--border);
  font-size:9px;font-weight:700;letter-spacing:1.8px;color:var(--muted);text-transform:uppercase;
  display:flex;align-items:center;justify-content:space-between}
.cb{padding:13px}
/* ── stats ── */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 6px;text-align:center}
.sv{font-family:var(--mono);font-size:19px;font-weight:700;line-height:1;color:var(--green)}
.sv.w{color:var(--amber)}.sv.b{color:var(--red)}.sv.m{color:var(--muted)}
.sl{font-size:8px;font-weight:700;letter-spacing:1.2px;color:var(--muted);text-transform:uppercase;margin-top:4px}
/* ── buttons ── */
.brow{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.btn{
  display:flex;align-items:center;justify-content:center;gap:7px;
  padding:15px 10px;border:none;border-radius:var(--r);
  font-family:var(--font);font-size:14px;font-weight:700;cursor:pointer;
  transition:transform .1s,filter .1s;-webkit-user-select:none;user-select:none
}
.btn:active{transform:scale(.95);filter:brightness(.85)}
.btn-start{background:var(--green);color:#000}
.btn-stop {background:var(--red)  ;color:#fff}
.btn-sync {background:var(--blue) ;color:#fff;grid-column:1/-1}
.btn-send {background:var(--blue) ;color:#fff;padding:13px;border-radius:10px;border:none;
  font-family:var(--font);font-size:13px;font-weight:700;cursor:pointer;min-width:64px}
.btn-qc{
  background:var(--surface);border:1px solid var(--border);border-radius:9px;
  color:var(--text);font-family:var(--font);font-size:12px;font-weight:600;
  padding:10px 8px;cursor:pointer;transition:background .15s;text-align:center
}
.btn-qc:active{background:var(--border)}
/* ── command input ── */
.cmd-row{display:flex;gap:8px}
.cmd-inp{
  flex:1;background:var(--surface);border:1px solid var(--border);border-radius:10px;
  color:var(--text);font-family:var(--mono);font-size:13px;padding:12px 13px;
  outline:none;transition:border-color .2s
}
.cmd-inp:focus{border-color:var(--blue)}
.cmd-inp::placeholder{color:var(--muted)}
/* ── quick cmds grid ── */
.qcg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px}
/* ── players ── */
.player-row{
  display:flex;align-items:center;gap:10px;
  padding:9px 13px;border-bottom:1px solid var(--border)
}
.player-row:last-child{border-bottom:none}
.pdot{width:8px;height:8px;border-radius:50%;background:var(--green);flex-shrink:0}
.pname{font-weight:600;font-size:13px;flex:1}
.ptime{font-family:var(--mono);font-size:10px;color:var(--muted)}
.pkick{background:transparent;border:1px solid rgba(255,61,82,.4);border-radius:6px;
  color:var(--red);font-size:10px;font-family:var(--font);font-weight:600;
  padding:4px 9px;cursor:pointer}
.pkick:active{background:rgba(255,61,82,.15)}
.no-players{padding:14px;text-align:center;color:var(--muted);font-size:12px;font-family:var(--mono)}
/* ── log ── */
#log-box{
  background:var(--surface);border-radius:9px;
  height:220px;overflow-y:auto;padding:10px;
  font-family:var(--mono);font-size:11px;line-height:1.6;color:var(--muted);
  scroll-behavior:smooth
}
#log-box .ll{color:var(--text)}
#log-box .le{color:var(--amber)}
#log-box .lc{color:var(--blue)}
#log-box::-webkit-scrollbar{width:4px}
#log-box::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
/* ── toast ── */
#toast{
  position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(60px);
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:10px 18px;font-size:13px;font-weight:600;
  transition:transform .25s ease,opacity .25s ease;opacity:0;z-index:1000;
  white-space:nowrap;pointer-events:none
}
#toast.show{transform:translateX(-50%) translateY(0);opacity:1}
/* ── connection lost overlay ── */
#offline{
  display:none;position:fixed;inset:0;z-index:500;
  background:rgba(7,8,10,.88);
  align-items:center;justify-content:center;flex-direction:column;gap:12px;
  backdrop-filter:blur(6px)
}
#offline.show{display:flex}
#offline p{font-weight:700;font-size:16px}
#offline small{color:var(--muted);font-size:12px}
</style>
</head>
<body>

<div id="offline">
  <div class="dot" style="width:14px;height:14px"></div>
  <p>Lost connection to MC CTRL</p>
  <small>Make sure the launcher is still running</small>
</div>

<header>
  <div class="logo">MC<em>·</em>CTRL <em>remote</em></div>
  <div class="live"><div class="dot"></div><span id="ts">--:--</span></div>
</header>

<div class="strip">
  <div class="pill pill-off" id="srv-pill">STOPPED</div>
  <span class="strip-up" id="uptime-strip">uptime --:--:--</span>
</div>

<main>

  <!-- stats -->
  <div class="card">
    <div class="ch">Performance</div>
    <div class="cb">
      <div class="stats">
        <div class="stat"><div class="sv" id="s-tps">--</div><div class="sl">TPS</div></div>
        <div class="stat"><div class="sv" id="s-players">0</div><div class="sl">Players</div></div>
        <div class="stat"><div class="sv" id="s-lat">--</div><div class="sl">Latency</div></div>
        <div class="stat"><div class="sv" id="s-cpu">--</div><div class="sl">CPU Sys</div></div>
        <div class="stat"><div class="sv" id="s-ram">--</div><div class="sl">RAM %</div></div>
        <div class="stat"><div class="sv" id="s-rsrv">--</div><div class="sl">Srv RAM</div></div>
      </div>
    </div>
  </div>

  <!-- controls -->
  <div class="card">
    <div class="ch">Server Control</div>
    <div class="cb">
      <div class="brow">
        <button class="btn btn-start" onclick="action('start')">▶ Start</button>
        <button class="btn btn-stop"  onclick="action('stop')">■ Stop</button>
        <button class="btn btn-sync"  onclick="action('sync')">↑ Sync &amp; Upload</button>
      </div>
    </div>
  </div>

  <!-- console -->
  <div class="card">
    <div class="ch">Console</div>
    <div class="cb">
      <div class="cmd-row">
        <input class="cmd-inp" id="cmd" placeholder="command…" autocomplete="off"
               autocorrect="off" autocapitalize="none" spellcheck="false">
        <button class="btn-send" onclick="sendCmd()">Send</button>
      </div>
      <div class="qcg">
        <button class="btn-qc" onclick="qc('save-all')">Save</button>
        <button class="btn-qc" onclick="qc('list')">Players</button>
        <button class="btn-qc" onclick="qc('tps')">TPS</button>
        <button class="btn-qc" onclick="qc('time set day')">Day</button>
        <button class="btn-qc" onclick="qc('weather clear')">Clear Sky</button>
        <button class="btn-qc" onclick="qc('difficulty hard')">Hard</button>
      </div>
    </div>
  </div>

  <!-- players -->
  <div class="card">
    <div class="ch">Online Players <span id="player-count" style="color:var(--green)">0</span></div>
    <div id="players-list"><div class="no-players">No players online</div></div>
  </div>

  <!-- log -->
  <div class="card">
    <div class="ch">Activity Log <button onclick="clearLog()" style="background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--muted);font-size:9px;padding:2px 8px;cursor:pointer">Clear</button></div>
    <div class="cb" style="padding:10px">
      <div id="log-box"></div>
    </div>
  </div>

</main>

<div id="toast"></div>

<script>
let _logLines = [];
let _failCount = 0;

function toast(msg, color){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.borderColor = color || 'var(--border)';
  t.classList.add('show');
  setTimeout(()=> t.classList.remove('show'), 2800);
}

function pct(v){
  const n = parseFloat(v);
  if(isNaN(n)) return 'm';
  if(n < 60) return '';
  if(n < 85) return 'w';
  return 'b';
}
function tpsClass(v){
  const n = parseFloat(v);
  if(isNaN(n)) return 'm';
  if(n >= 18) return '';
  if(n >= 15) return 'w';
  return 'b';
}

function setStat(id, val, cls){
  const el = document.getElementById(id);
  if(!el) return;
  el.textContent = val ?? '--';
  el.className = 'sv ' + (cls||'');
}

async function poll(){
  try{
    const r = await fetch('/api/status', {signal: AbortSignal.timeout(3000)});
    if(!r.ok) throw new Error('bad');
    const d = await r.json();
    _failCount = 0;
    document.getElementById('offline').classList.remove('show');

    // timestamp
    const now = new Date();
    document.getElementById('ts').textContent =
      now.getHours().toString().padStart(2,'0')+':'+
      now.getMinutes().toString().padStart(2,'0')+':'+
      now.getSeconds().toString().padStart(2,'0');

    // status pill
    const pill = document.getElementById('srv-pill');
    const running = d.server_running;
    pill.textContent  = running ? 'RUNNING' : 'STOPPED';
    pill.className    = 'pill ' + (running ? 'pill-on' : 'pill-off');

    document.getElementById('uptime-strip').textContent = 'uptime ' + (d.perf.uptime || '--:--:--');

    // perf
    const p = d.perf;
    setStat('s-tps',     p.tps,      tpsClass(p.tps));
    setStat('s-players', p.players,  '');
    setStat('s-lat',     p.latency,  '');
    setStat('s-cpu',     p.cpu_sys,  pct(p.cpu_sys));
    setStat('s-ram',     p.ram_pct,  pct(p.ram_pct));
    setStat('s-rsrv',    p.ram_srv,  '');

    // players
    const pl = d.online_players || {};
    const names = Object.keys(pl);
    document.getElementById('player-count').textContent = names.length;
    const box = document.getElementById('players-list');
    if(names.length === 0){
      box.innerHTML = '<div class="no-players">No players online</div>';
    } else {
      box.innerHTML = names.map(n =>
        `<div class="player-row">
          <div class="pdot"></div>
          <div class="pname">${n}</div>
          <div class="ptime">joined ${pl[n]||'?'}</div>
          <button class="pkick" onclick="qc('kick ${n}')">Kick</button>
        </div>`
      ).join('');
    }

    // log
    const newLines = d.log_lines || [];
    if(newLines.length !== _logLines.length || newLines.slice(-1)[0] !== _logLines.slice(-1)[0]){
      _logLines = newLines;
      const lb = document.getElementById('log-box');
      lb.innerHTML = newLines.map(l => {
        const cls = l.includes('[CHAT]') ? 'lc' : l.includes('>>') || l.includes('<<') ? 'le' : 'll';
        return `<div class="${cls}">${escHtml(l)}</div>`;
      }).join('');
      lb.scrollTop = lb.scrollHeight;
    }
  } catch(e){
    _failCount++;
    if(_failCount >= 4) document.getElementById('offline').classList.add('show');
  }
}

function escHtml(s){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function action(act){
  try{
    const r = await fetch('/api/action', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({action: act})
    });
    const d = await r.json();
    toast(d.message || 'OK', act==='start'?'var(--green)':act==='stop'?'var(--red)':'var(--blue)');
  } catch(e){ toast('Request failed','var(--red)'); }
}

async function sendCmd(){
  const inp = document.getElementById('cmd');
  const cmd = inp.value.trim();
  if(!cmd) return;
  inp.value = '';
  try{
    await fetch('/api/command', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({command: cmd})
    });
    toast('Sent: '+cmd, 'var(--blue)');
  } catch(e){ toast('Failed','var(--red)'); }
}

function qc(cmd){
  fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})});
  toast(cmd,'var(--blue)');
}

function clearLog(){
  _logLines=[];
  document.getElementById('log-box').innerHTML='';
}

document.getElementById('cmd').addEventListener('keydown', e => {
  if(e.key==='Enter') sendCmd();
});

poll();
setInterval(poll, 1500);
</script>
</body>
</html>"""

# ── Flask app factory ─────────────────────────────────────
def _make_flask_app(state: dict):
    from flask import Flask, jsonify, request, Response

    flask_app = Flask("mc_ctrl_remote")
    flask_app.config["SECRET_KEY"] = os.urandom(16)

    @flask_app.route("/")
    def index():
        return Response(_HTML, mimetype="text/html")

    @flask_app.route("/api/status")
    def api_status():
        return jsonify({
            "server_running":  state["server_running"],
            "perf":            dict(state["perf"]),
            "online_players":  dict(state["online_players"]),
            "log_lines":       list(state["log_lines"])[-120:],
            "timestamp":       datetime.now().strftime("%H:%M:%S"),
        })

    @flask_app.route("/api/action", methods=["POST"])
    def api_action():
        act = (request.json or {}).get("action", "")
        if act == "start":
            fn = state.get("start_fn")
            if fn:
                threading.Thread(target=fn, daemon=True).start()
                return jsonify({"ok": True, "message": "Starting server…"})
            return jsonify({"ok": False, "message": "Start function not available"})
        elif act == "stop":
            fn = state.get("stop_fn")
            if fn:
                threading.Thread(target=fn, daemon=True).start()
                return jsonify({"ok": True, "message": "Stopping server…"})
            return jsonify({"ok": False, "message": "Stop function not available"})
        elif act == "sync":
            fn = state.get("sync_fn")
            if fn:
                threading.Thread(target=fn, daemon=True).start()
                return jsonify({"ok": True, "message": "Syncing…"})
            return jsonify({"ok": False, "message": "Sync function not available"})
        return jsonify({"ok": False, "message": f"Unknown action: {act}"})

    @flask_app.route("/api/command", methods=["POST"])
    def api_command():
        cmd = (request.json or {}).get("command", "").strip()
        if not cmd:
            return jsonify({"ok": False, "message": "No command"})
        fn = state.get("send_cmd_fn")
        if fn:
            fn(cmd)
            return jsonify({"ok": True, "message": f"Sent: {cmd}"})
        return jsonify({"ok": False, "message": "Server not running"})

    return flask_app


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_flask(state: dict, port: int = 5000) -> bool:
    """Start the Flask server in a daemon thread. Returns True on success."""
    if state.get("flask_running"):
        return True

    if not _ensure_flask():
        return False

    flask_app = _make_flask_app(state)

    import logging as _logging
    _logging.getLogger("werkzeug").setLevel(_logging.ERROR)

    def _run():
        try:
            flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        except OSError as e:
            state["flask_error"] = str(e)
            state["flask_running"] = False

    thr = threading.Thread(target=_run, daemon=True)
    thr.start()
    state["flask_thread"] = thr
    state["flask_running"] = True
    state["flask_port"]    = port
    return True


def stop_flask(state: dict):
    """Signal Flask to stop (best-effort; daemon thread dies with the process)."""
    state["flask_running"] = False


# ── Launcher tab builder ──────────────────────────────────
def build_remote_tab(parent, launcher_globals: dict):
    """
    Build the Remote Dashboard tab.
    launcher_globals should contain references from launcher.pyw:
        ctk, T, app, log, show_toast,
        perf, online_players, server_proc, server_stdin,
        start_server, stop_server, sync_git, send_server_cmd,
        log_history (str of log_box contents updated externally)
    """
    import customtkinter as ctk

    ctk   = launcher_globals["ctk"]
    T     = launcher_globals["T"]
    app   = launcher_globals["app"]
    log   = launcher_globals["log"]
    toast = launcher_globals["show_toast"]

    # Wire state
    _state["perf"]           = launcher_globals.get("perf", {})
    _state["online_players"] = launcher_globals.get("online_players", {})
    _state["send_cmd_fn"]    = launcher_globals.get("send_server_cmd")
    _state["start_fn"]       = launcher_globals.get("start_server")
    _state["stop_fn"]        = launcher_globals.get("stop_server")
    _state["sync_fn"]        = launcher_globals.get("sync_git")

    def _server_running():
        sp = launcher_globals.get("server_proc")
        if callable(sp):
            sp = sp()
        return sp is not None and (hasattr(sp, "poll") and sp.poll() is None)

    def _sync_state():
        _state["server_running"] = _server_running()
        # Pull fresh log lines from the launcher's log box widget
        try:
            lb = launcher_globals.get("log_box_ref")
            if lb:
                text = lb.get("1.0", "end").strip()
                _state["log_lines"] = text.splitlines()[-200:]
        except Exception:
            pass
        app.after(1000, _sync_state)

    app.after(1000, _sync_state)

    # ── UI ─────────────────────────────────────────────────
    import tkinter as tk

    def make_scroll(p):
        canvas = tk.Canvas(p, bg=T["bg"], highlightthickness=0, bd=0)
        vsb    = ctk.CTkScrollbar(p, orientation="vertical", command=canvas.yview,
                                   button_color=T["border"], button_hover_color=T["muted"])
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=vsb.set)
        inner = ctk.CTkFrame(canvas, fg_color="transparent")
        wid   = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",   lambda e: canvas.itemconfig(wid, width=e.width))
        inner.bind("<Configure>",    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>",  lambda e: canvas.yview_scroll(int(-e.delta/60), "units"))
        inner.bind("<MouseWheel>",   lambda e: canvas.yview_scroll(int(-e.delta/60), "units"))
        return inner

    scroll = make_scroll(parent)

    port_var    = ctk.StringVar(value="5000")
    status_var  = ctk.StringVar(value="Flask not started")
    url_var     = ctk.StringVar(value="")
    running_var = ctk.BooleanVar(value=False)

    # ── Intro card ─────────────────────────────────────────
    intro = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                          border_width=1, corner_radius=10)
    intro.pack(fill="x", padx=20, pady=(14, 0))
    ctk.CTkLabel(intro, text="REMOTE MOBILE DASHBOARD",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(intro, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    ctk.CTkLabel(intro, text=(
        "Start the web server below, then open the address on any phone or tablet\n"
        "connected to the same WiFi. You can start/stop the server, send commands,\n"
        "watch live stats and player list — all from your browser."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       justify="left", wraplength=700).pack(anchor="w", padx=14, pady=(8, 12))

    # ── Control card ───────────────────────────────────────
    ctrl = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                         border_width=1, corner_radius=10)
    ctrl.pack(fill="x", padx=20, pady=(10, 0))
    ch = ctk.CTkFrame(ctrl, fg_color="transparent"); ch.pack(fill="x", padx=14, pady=(10, 4))
    ctk.CTkLabel(ch, text="WEB SERVER",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")
    ctk.CTkFrame(ctrl, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    cb = ctk.CTkFrame(ctrl, fg_color="transparent"); cb.pack(fill="x", padx=14, pady=(10, 12))

    # Port row
    pr = ctk.CTkFrame(cb, fg_color="transparent"); pr.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(pr, text="Port", font=ctk.CTkFont(size=12), text_color=T["text"],
                 width=60, anchor="w").pack(side="left")
    ctk.CTkEntry(pr, textvariable=port_var, width=80, height=28,
                 font=ctk.CTkFont(size=12, family="Consolas"),
                 fg_color=T["bg"], border_color=T["border"], text_color=T["text"]
                 ).pack(side="left", padx=(0, 12))
    ctk.CTkLabel(pr, text="(default 5000 — change if port is in use)",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(side="left")

    # Status row
    st_row = ctk.CTkFrame(cb, fg_color=T["bg"], border_color=T["border"],
                           border_width=1, corner_radius=8)
    st_row.pack(fill="x", pady=(0, 10))
    st_inner = ctk.CTkFrame(st_row, fg_color="transparent"); st_inner.pack(fill="x", padx=12, pady=10)
    st_dot = ctk.CTkLabel(st_inner, text="●", font=ctk.CTkFont(size=13), text_color=T["stop"])
    st_dot.pack(side="left", padx=(0, 8))
    st_lbl = ctk.CTkLabel(st_inner, textvariable=status_var, font=ctk.CTkFont(size=12),
                           text_color=T["muted"]); st_lbl.pack(side="left")

    # URL row
    url_frame = ctk.CTkFrame(cb, fg_color=T["bg"], border_color=T["border"],
                              border_width=1, corner_radius=8)
    url_frame.pack(fill="x", pady=(0, 10))
    url_inner = ctk.CTkFrame(url_frame, fg_color="transparent"); url_inner.pack(fill="x", padx=12, pady=10)
    ctk.CTkLabel(url_inner, text="Open on phone →",
                 font=ctk.CTkFont(size=11), text_color=T["muted"]).pack(side="left")
    url_lbl = ctk.CTkLabel(url_inner, textvariable=url_var,
                            font=ctk.CTkFont(size=13, weight="bold", family="Consolas"),
                            text_color=T["sync"]); url_lbl.pack(side="left", padx=(8, 0))

    def _copy_url():
        u = url_var.get()
        if u:
            app.clipboard_clear(); app.clipboard_append(u)
            toast(f"Copied: {u}", T["sync"])

    ctk.CTkButton(url_inner, text="Copy", width=54, height=26,
                  font=ctk.CTkFont(size=11), fg_color="transparent",
                  border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=_copy_url).pack(side="right")

    # Buttons
    btn_row = ctk.CTkFrame(cb, fg_color="transparent"); btn_row.pack(fill="x")

    def _start_web():
        try:
            p = int(port_var.get())
        except ValueError:
            toast("Invalid port number", T["stop"]); return
        if running_var.get():
            toast("Already running", T["muted"]); return

        ok = start_flask(_state, port=p)
        if ok:
            ip  = _get_local_ip()
            url = f"http://{ip}:{p}"
            url_var.set(url)
            status_var.set(f"Running on port {p}")
            st_dot.configure(text_color=T["start"])
            st_lbl.configure(text_color=T["start"])
            running_var.set(True)
            log(f"-- Remote dashboard started: {url} --")
            toast(f"Dashboard live: {url}", T["start"])
        else:
            status_var.set("Failed — install flask: pip install flask")
            st_dot.configure(text_color=T["stop"])
            toast("Flask not installed — auto-installing, try again", T["stop"])

    def _stop_web():
        stop_flask(_state)
        running_var.set(False)
        status_var.set("Stopped")
        url_var.set("")
        st_dot.configure(text_color=T["stop"])
        st_lbl.configure(text_color=T["muted"])
        log("-- Remote dashboard stopped --")
        toast("Dashboard stopped", T["stop"])

    ctk.CTkButton(btn_row, text="▶ Start Web Server", height=34,
                  font=ctk.CTkFont(size=13, weight="bold"),
                  fg_color=T["start"], hover_color=T["start"], text_color="#000",
                  command=_start_web).pack(side="left", padx=(0, 8))
    ctk.CTkButton(btn_row, text="■ Stop", width=80, height=34,
                  font=ctk.CTkFont(size=13), fg_color=T["stop"],
                  hover_color=T["stop"], text_color="#fff",
                  command=_stop_web).pack(side="left")

    # ── QR code hint ───────────────────────────────────────
    qr_card = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                            border_width=1, corner_radius=10)
    qr_card.pack(fill="x", padx=20, pady=(10, 0))
    ctk.CTkLabel(qr_card, text="QUICK ACCESS",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(qr_card, height=1, fg_color=T["border"]).pack(fill="x", padx=14)

    def _open_browser():
        u = url_var.get()
        if u:
            import webbrowser; webbrowser.open(u)
        else:
            toast("Start the web server first", T["muted"])

    qr_body = ctk.CTkFrame(qr_card, fg_color="transparent"); qr_body.pack(fill="x", padx=14, pady=(8, 12))
    ctk.CTkLabel(qr_body, text=(
        "1. Connect your phone to the same WiFi as this PC.\n"
        "2. Start the web server above.\n"
        "3. Open the URL shown above in your phone's browser.\n"
        "4. Bookmark it for quick access anytime."
    ), font=ctk.CTkFont(size=12), text_color=T["muted"],
       justify="left", wraplength=700).pack(anchor="w", pady=(0, 8))
    ctk.CTkButton(qr_body, text="Open in Browser (this PC)", height=30,
                  font=ctk.CTkFont(size=11), fg_color="transparent",
                  border_width=1, border_color=T["sync"],
                  text_color=T["sync"], hover_color=T["border"],
                  command=_open_browser).pack(anchor="w")

    # ── Security note ──────────────────────────────────────
    sec = ctk.CTkFrame(scroll, fg_color=T["card"], border_color=T["border"],
                        border_width=1, corner_radius=10)
    sec.pack(fill="x", padx=20, pady=(10, 14))
    ctk.CTkLabel(sec, text="SECURITY NOTE",
                 font=ctk.CTkFont(size=10), text_color=T["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
    ctk.CTkFrame(sec, height=1, fg_color=T["border"]).pack(fill="x", padx=14)
    ctk.CTkLabel(sec, text=(
        "The dashboard is accessible to anyone on your local network with no password.\n"
        "Do not use on public WiFi. It is not exposed to the internet unless you\n"
        "explicitly port-forward port 5000."
    ), font=ctk.CTkFont(size=11), text_color=T["muted"],
       justify="left", wraplength=700).pack(anchor="w", padx=14, pady=(8, 12))
