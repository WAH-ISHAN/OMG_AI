#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   J.A.R.V.I.S  —  OMG_AI  v3.0  "IRON PROTOCOL"                ║
║   Just A Rather Very Intelligent System                          ║
║   100% Local  •  Full Laptop Control  •  HUD Interface          ║
║   Permission Levels: standard | elevated | unrestricted          ║
╚══════════════════════════════════════════════════════════════════╝

PERMISSION LEVELS:
  standard     → info only, no system access
  elevated     → open/close apps, read files, basic shell
  unrestricted → complete control: write files, kill tasks, send msgs
"""

import sys, os, json, urllib.request, urllib.error
import threading, time, subprocess, zipfile, atexit
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox

# ──────────────────────────────────────────────────────────────────────────────
# BASE PATHS
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
BIN_DIR    = os.path.join(BASE_DIR, "bin")
LOGS_DIR   = os.path.join(BASE_DIR, "logs")

for d in [MODELS_DIR, BIN_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

CONFIG_FILE       = os.path.join(BASE_DIR, "config.json")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
MEMORY_FILE       = os.path.join(BASE_DIR, "memory.json")
VERSION_FILE      = os.path.join(BASE_DIR, "version.json")

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────

CHAT_HISTORY = []
MEMORY       = []
CONFIG = {
    "username":       "Sir",
    "codename":       "Director",          # How JARVIS calls you
    "laptop_model":   "Stark Station",
    "driver_issues":  [],
    "permission":     "standard",
    "hotkey":         "ctrl+space",
    "email":          "",
    "email_pass":     "",
    "theme":          "jarvis",            # jarvis | light | dark
    "startup":        True,
    "voice_enabled":  True,
    "wit_level":      "high",              # low | medium | high
}

LLAMA_PORT    = 8080
LLAMA_HOST    = f"http://127.0.0.1:{LLAMA_PORT}"
DEFAULT_MODEL = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_URL     = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
GITHUB_RAW    = "https://raw.githubusercontent.com/WAH-ISHAN/OMG_AI/main/omg_ai.py"
CURRENT_VER   = "3.0.0"
CODENAME      = "IRON PROTOCOL"

server_process = None
tray_icon      = None

# ──────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS
# ──────────────────────────────────────────────────────────────────────────────

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from windows_toasts import Toast, WindowsToaster
    _toaster = WindowsToaster("JARVIS")
    HAS_TOAST = True
except Exception:
    HAS_TOAST = False

# ──────────────────────────────────────────────────────────────────────────────
# JARVIS PERSONALITY ENGINE
# ──────────────────────────────────────────────────────────────────────────────

JARVIS_GREETINGS = [
    "Good {period}, {codename}. All systems are nominal. How may I assist you today?",
    "Welcome back, {codename}. I've kept the systems warm in your absence.",
    "Online and operational, {codename}. What shall we accomplish today?",
    "Systems at 100% efficiency, {codename}. I await your directive.",
    "Initialisation complete. Good {period}, {codename}. Ready for deployment.",
]

JARVIS_CONFIRMATIONS = [
    "Understood, {codename}.",
    "At once, {codename}.",
    "Certainly. Executing now.",
    "Of course. Processing your request.",
    "Right away, {codename}.",
    "Already on it.",
]

JARVIS_ERRORS = [
    "I'm afraid I encountered an obstacle, {codename}. {error}",
    "My apologies — that didn't go as planned. {error}",
    "A minor setback, {codename}. {error}",
    "I regret to report a failure: {error}",
]

JARVIS_PERMISSION_DENIALS = [
    "I'm sorry, {codename}, but that action exceeds my current authorisation level ({current}). "
    "You'll need to elevate my clearance to '{required}' first.",
    "Access restricted, {codename}. '{required}' clearance required — I currently hold '{current}'.",
    "That directive requires '{required}' protocol clearance, {codename}. "
    "Currently operating under '{current}' restrictions.",
]

import random

def j_say(template_list: list, **kwargs) -> str:
    """Pick a random JARVIS phrase and format it."""
    codename = CONFIG.get("codename", CONFIG.get("username", "Sir"))
    now      = datetime.now().hour
    period   = "morning" if now < 12 else ("afternoon" if now < 17 else "evening")
    return random.choice(template_list).format(
        codename=codename, period=period,
        current=CONFIG.get("permission","standard"),
        **kwargs
    )

# ──────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

def notify(title: str, body: str):
    if HAS_TOAST:
        try:
            t = Toast()
            t.text_fields = [f"{title}\n{body}"]
            _toaster.show_toast(t)
        except Exception:
            pass
    elif sys.platform == "win32":
        try:
            ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                  f"[System.Windows.Forms.MessageBox]::Show('{body}','{title}',"
                  f"[System.Windows.Forms.MessageBoxButtons]::OK,"
                  f"[System.Windows.Forms.MessageBoxIcon]::Information)")
            subprocess.Popen(["powershell","-WindowStyle","Hidden","-Command",ps],
                             creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

# ──────────────────────────────────────────────────────────────────────────────
# TEXT-TO-SPEECH  (JARVIS voice)
# ──────────────────────────────────────────────────────────────────────────────

def speak(text: str):
    if sys.platform != "win32":
        return
    if not CONFIG.get("voice_enabled", True):
        return
    def _run():
        try:
            escaped = text.replace("'","''")[:300]
            # Use a specific voice if available (David = more robotic)
            ps = (
                "Add-Type -AssemblyName System.Speech;"
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$s.Rate=1;"
                f"$s.Speak('{escaped}')"
            )
            subprocess.run(
                ["powershell","-WindowStyle","Hidden","-Command",ps],
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG & PERSISTENCE
# ──────────────────────────────────────────────────────────────────────────────

def load_config():
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                CONFIG.update(json.load(f))
        except Exception:
            pass

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, ensure_ascii=False, indent=2)

def load_history_and_memory():
    global CHAT_HISTORY, MEMORY
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, encoding="utf-8") as f:
                CHAT_HISTORY = json.load(f)
        except Exception:
            CHAT_HISTORY = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, encoding="utf-8") as f:
                MEMORY = json.load(f)
        except Exception:
            MEMORY = []

def save_history():
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(CHAT_HISTORY[-100:], f, ensure_ascii=False, indent=2)

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(MEMORY, f, ensure_ascii=False, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# PERMISSION SYSTEM  (renamed for JARVIS theme)
# ──────────────────────────────────────────────────────────────────────────────

PERMISSION_RANK = {"standard": 0, "elevated": 1, "unrestricted": 2}
# Backwards-compatible aliases
PERM_ALIASES = {"normal": "standard", "middle": "elevated", "full": "unrestricted"}

def _resolve_perm(p: str) -> str:
    p = p.lower()
    return PERM_ALIASES.get(p, p)

def has_perm(required: str) -> bool:
    cur  = PERMISSION_RANK.get(_resolve_perm(CONFIG.get("permission","standard")), 0)
    need = PERMISSION_RANK.get(_resolve_perm(required), 0)
    return cur >= need

def perm_denied(required: str) -> str:
    return j_say(JARVIS_PERMISSION_DENIALS, required=required)

# ──────────────────────────────────────────────────────────────────────────────
# AUTO-UPDATER
# ──────────────────────────────────────────────────────────────────────────────

def check_for_update() -> str:
    try:
        req  = urllib.request.Request(
            "https://api.github.com/repos/WAH-ISHAN/OMG_AI/releases/latest",
            headers={"Accept":"application/vnd.github+json"})
        data = json.loads(urllib.request.urlopen(req, timeout=5).read())
        remote = data.get("tag_name","").lstrip("v")
        if remote and remote != CURRENT_VER:
            return remote
    except Exception:
        pass
    return ""

def do_self_update():
    try:
        req  = urllib.request.Request(GITHUB_RAW)
        code = urllib.request.urlopen(req, timeout=15).read()
        backup = __file__ + ".bak"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(__file__, backup)
        with open(__file__, "wb") as f:
            f.write(code)
        notify("JARVIS Update", "New protocols installed. Restarting…")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, __file__] + sys.argv[1:])
    except Exception as e:
        return f"Update sequence failed: {e}"

def bg_update_checker(callback):
    while True:
        new_ver = check_for_update()
        if new_ver:
            notify("JARVIS", f"Protocol v{new_ver} is available. Use /update to install.")
            if callback:
                callback(f"New firmware v{new_ver} is available, {CONFIG.get('codename','Sir')}. "
                         f"Use /update when ready.")
        time.sleep(6 * 3600)

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM CONTROL  (gated by permission)
# ──────────────────────────────────────────────────────────────────────────────

class SystemCore:
    """All system control actions — guarded by clearance levels."""

    # ── STANDARD ──────────────────────────────────────────

    @staticmethod
    def get_sysinfo() -> str:
        codename = CONFIG.get("codename","Sir")
        lines = [f"◈  SYSTEM DIAGNOSTICS  —  {datetime.now().strftime('%H:%M:%S')}",
                 "─" * 45]
        lines.append(f"  Machine   :  {CONFIG.get('laptop_model','Unknown')}")
        if HAS_PSUTIL:
            try:
                cpu  = psutil.cpu_percent(interval=0.5)
                ram  = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                bat  = psutil.sensors_battery()
                bar  = lambda p: "█"*int(p/10) + "░"*(10-int(p/10))
                lines += [
                    f"  CPU       :  {cpu:5.1f}%   {bar(cpu)}",
                    f"  RAM       :  {ram.percent:5.1f}%   {bar(ram.percent)}  "
                    f"({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)",
                    f"  Disk      :  {disk.percent:5.1f}%   {bar(disk.percent)}  "
                    f"({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)",
                    f"  Battery   :  " + (
                        f"{bat.percent:.0f}%  {'⚡ Charging' if bat.power_plugged else '🔋'}"
                        if bat else "AC / N/A"),
                ]
            except Exception as e:
                lines.append(f"  (Diagnostics partial: {e})")
        else:
            lines.append("  (Install psutil for live telemetry: pip install psutil)")
        lines.append("─" * 45)
        return "\n".join(lines)

    @staticmethod
    def get_time() -> str:
        now = datetime.now()
        return (f"◈  TEMPORAL REFERENCE\n"
                f"  {now.strftime('%A, %d %B %Y')}\n"
                f"  {now.strftime('%H:%M:%S')}  UTC{now.strftime('%z') or '+00:00'}")

    @staticmethod
    def get_weather_local() -> str:
        """Quick local weather hint via wttr.in (no API key needed)."""
        try:
            url = "https://wttr.in/?format=3"
            req = urllib.request.Request(url, headers={"User-Agent":"curl/7.0"})
            data = urllib.request.urlopen(req, timeout=5).read().decode()
            return f"◈  ATMOSPHERIC DATA\n  {data.strip()}"
        except Exception:
            return "Weather telemetry unavailable — network access required."

    # ── ELEVATED ──────────────────────────────────────────

    @staticmethod
    def open_app(app_name: str) -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        try:
            subprocess.Popen(app_name, shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW
                             if sys.platform=="win32" else 0)
            return j_say(JARVIS_CONFIRMATIONS) + f"\n  Launching: {app_name}"
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def close_app(app_name: str) -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill","/F","/IM",app_name],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               capture_output=True)
            else:
                subprocess.run(["pkill","-f",app_name], capture_output=True)
            return f"Process '{app_name}' has been terminated."
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def list_processes() -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        if HAS_PSUTIL:
            procs = sorted(
                [(p.info['pid'], p.info['name'], p.info.get('cpu_percent',0))
                 for p in psutil.process_iter(['pid','name','cpu_percent'])
                 if p.info['name']],
                key=lambda x: x[2] or 0, reverse=True)
            header = f"{'PID':>7}  {'CPU%':>5}  PROCESS\n{'─'*45}"
            lines  = [header] + [f"{pid:7}  {(cpu or 0):5.1f}  {name}"
                                  for pid, name, cpu in procs[:25]]
            return "◈  ACTIVE PROCESSES\n" + "\n".join(lines)
        try:
            if sys.platform == "win32":
                out = subprocess.check_output(
                    "tasklist /fo csv /nh", shell=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return "◈  ACTIVE PROCESSES\n" + out[:2000]
            else:
                out = subprocess.check_output("ps aux", shell=True, text=True)
                return "◈  ACTIVE PROCESSES\n" + out[:2000]
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def read_file(path: str) -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, encoding="utf-8", errors="replace") as f:
                content = f.read(4000)
            return f"◈  FILE CONTENTS  —  {expanded}\n{'─'*45}\n{content}"
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def list_dir(path: str = ".") -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            items = sorted(os.listdir(expanded))
            dirs  = [f"  📁  {i}" for i in items if os.path.isdir(os.path.join(expanded,i))]
            files = [f"  📄  {i}" for i in items if os.path.isfile(os.path.join(expanded,i))]
            return (f"◈  DIRECTORY SCAN  —  {expanded}\n{'─'*45}\n"
                    + "\n".join(dirs + files))
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def run_command(cmd: str) -> str:
        if not has_perm("elevated"):
            return perm_denied("elevated")
        dangerous = ["format","del /s","rm -rf","shutdown","reboot",
                     "reg delete","reg add","netsh","diskpart"]
        if not has_perm("unrestricted"):
            for d in dangerous:
                if d.lower() in cmd.lower():
                    return (f"Command blocked — '{d}' requires unrestricted clearance.\n"
                            f"Use /clearance unrestricted to elevate.")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = (result.stdout or "") + (result.stderr or "")
            return f"◈  SHELL EXECUTION\n  $ {cmd}\n{'─'*45}\n{output[:2500]}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after 15s: {cmd}"
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def search_web_quick(query: str) -> str:
        """Open a web search in the default browser."""
        if not has_perm("elevated"):
            return perm_denied("elevated")
        import webbrowser, urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Web search launched for: {query}"

    # ── UNRESTRICTED ─────────────────────────────────────

    @staticmethod
    def write_file(path: str, content: str) -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written successfully: {expanded}"
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def set_volume(level: int) -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        level = max(0, min(100, level))
        if sys.platform == "win32":
            try:
                nircmd = os.path.join(BIN_DIR, "nircmd.exe")
                if os.path.exists(nircmd):
                    subprocess.run([nircmd,"setsysvolume",str(int(level/100*65535))],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(
                        ["powershell","-WindowStyle","Hidden","-Command",
                         f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
                         if level == 0 else
                         f"$wsh=New-Object -ComObject WScript.Shell;"
                         f"for($i=0;$i -lt 10;$i++){{$wsh.SendKeys([char]174)}}"],
                        creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
                return f"Audio output adjusted to {level}%."
            except Exception as e:
                return j_say(JARVIS_ERRORS, error=str(e))
        return "Volume control is Windows-only, {codename}.".format(
            codename=CONFIG.get("codename","Sir"))

    @staticmethod
    def shutdown(mode: str = "lock") -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        if sys.platform == "win32":
            flags = {"shutdown":"/s","restart":"/r","sleep":"/h","lock":"/l"}
            flag = flags.get(mode, "/l")
            if mode == "lock":
                subprocess.Popen(["shutdown",flag],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["shutdown",flag,"/t","5"],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            codename = CONFIG.get("codename","Sir")
            return (f"Initiating {mode} sequence, {codename}. "
                    + ("Goodbye." if mode == "shutdown" else "See you soon."))
        return f"{mode.capitalize()} is Windows-only."

    @staticmethod
    def send_email(to: str, subject: str, body: str) -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        email_addr = CONFIG.get("email","")
        email_pass = CONFIG.get("email_pass","")
        if not email_addr or not email_pass:
            return ("Email module unconfigured. "
                    "Add 'email' and 'email_pass' to config.json, "
                    "or use /set email your@gmail.com")
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"]    = email_addr
            msg["To"]      = to
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
                srv.login(email_addr, email_pass)
                srv.send_message(msg)
            return f"Message transmitted to {to} successfully."
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

    @staticmethod
    def open_whatsapp_web(phone: str, message: str = "") -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        import urllib.parse, webbrowser
        encoded = urllib.parse.quote(message)
        url = f"https://wa.me/{phone}?text={encoded}"
        webbrowser.open(url)
        return f"WhatsApp channel opened for +{phone}."

    @staticmethod
    def take_screenshot(path: str = "") -> str:
        if not has_perm("unrestricted"):
            return perm_denied("unrestricted")
        try:
            if not path:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(os.path.expanduser("~"), f"screenshot_{ts}.png")
            if sys.platform == "win32":
                ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                      f"$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                      f"$bmp=New-Object System.Drawing.Bitmap($s.Width,$s.Height);"
                      f"$g=[System.Drawing.Graphics]::FromImage($bmp);"
                      f"$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size);"
                      f"$bmp.Save('{path}',[System.Drawing.Imaging.ImageFormat]::Png);")
                subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                               creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
            return f"Visual capture saved: {path}"
        except Exception as e:
            return j_say(JARVIS_ERRORS, error=str(e))

# ──────────────────────────────────────────────────────────────────────────────
# AI SERVER  (llama.cpp)
# ──────────────────────────────────────────────────────────────────────────────

def get_llama_exe():
    return os.path.join(BIN_DIR,
                        "llama-server.exe" if sys.platform=="win32" else "llama-server")

def kill_server():
    global server_process
    if server_process:
        try:
            server_process.terminate()
            server_process.wait(timeout=3)
        except Exception:
            pass
        server_process = None

atexit.register(kill_server)

def start_server() -> bool:
    global server_process
    kill_server()
    exe   = get_llama_exe()
    model = os.path.join(MODELS_DIR, DEFAULT_MODEL)
    if not os.path.exists(model) or not os.path.exists(exe):
        return False
    cmd = [exe, "-m", model, "--port", str(LLAMA_PORT),
           "-c", "4096", "--threads", "4", "--no-mmap"]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags)
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{LLAMA_HOST}/health", timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def check_installation() -> bool:
    return (os.path.exists(get_llama_exe()) and
            os.path.exists(os.path.join(MODELS_DIR, DEFAULT_MODEL)) and
            os.path.exists(CONFIG_FILE))

# ──────────────────────────────────────────────────────────────────────────────
# COMMAND PARSER  (slash commands)
# ──────────────────────────────────────────────────────────────────────────────

core = SystemCore()

def parse_command(text: str) -> str | None:
    parts = text.strip().split(None, 2)
    if not parts or not parts[0].startswith("/"):
        return None

    cmd  = parts[0].lower()
    arg1 = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""

    # ─ Help ──────────────────────────────────────────────
    if cmd == "/help":
        return (
            "◈  COMMAND REFERENCE  —  JARVIS PROTOCOL\n"
            "═"*50 + "\n"
            "  STANDARD CLEARANCE\n"
            "  /help               — this directive list\n"
            "  /status             — system diagnostics\n"
            "  /time               — temporal reference\n"
            "  /weather            — atmospheric conditions\n"
            "  /memories           — recall stored data\n"
            "  /remember <fact>    — store a memory\n"
            "  /forget <n>         — delete memory #n\n"
            "  /clear              — wipe chat history\n\n"
            "  ELEVATED CLEARANCE\n"
            "  /open <app>         — launch application\n"
            "  /close <app.exe>    — terminate process\n"
            "  /ps                 — process manifest\n"
            "  /ls [path]          — directory scan\n"
            "  /cat <path>         — read file\n"
            "  /run <command>      — shell execution\n"
            "  /search <query>     — web search\n\n"
            "  UNRESTRICTED CLEARANCE\n"
            "  /write <path> <txt> — write to file\n"
            "  /volume <0-100>     — audio output\n"
            "  /screenshot [path]  — capture display\n"
            "  /shutdown           — power down\n"
            "  /restart            — reboot sequence\n"
            "  /sleep              — hibernate\n"
            "  /lock               — secure station\n"
            "  /email <to> <sub> <body>\n"
            "  /wa <phone> [msg]   — WhatsApp channel\n\n"
            "  SYSTEM\n"
            "  /clearance <level>  — set standard|elevated|unrestricted\n"
            "  /set <key> <value>  — update configuration\n"
            "  /voice on|off       — toggle speech synthesis\n"
            "  /update             — firmware update\n"
            "═"*50
        )

    # ─ System ────────────────────────────────────────────
    if cmd in ("/status", "/sysinfo"):
        return core.get_sysinfo()

    if cmd == "/time":
        return core.get_time()

    if cmd == "/weather":
        return core.get_weather_local()

    # ─ Clearance (permission) ─────────────────────────────
    if cmd in ("/clearance", "/permission"):
        lvl = _resolve_perm(arg1.lower())
        if lvl not in ("standard","elevated","unrestricted"):
            return "Specify clearance level: standard | elevated | unrestricted"
        CONFIG["permission"] = lvl
        save_config()
        return f"Clearance updated to '{lvl.upper()}' protocol."

    # ─ Voice ─────────────────────────────────────────────
    if cmd == "/voice":
        if arg1.lower() in ("on","off"):
            CONFIG["voice_enabled"] = (arg1.lower() == "on")
            save_config()
            return f"Voice synthesis {'enabled' if CONFIG['voice_enabled'] else 'disabled'}."
        return "Usage: /voice on|off"

    # ─ App control ───────────────────────────────────────
    if cmd == "/open":
        return core.open_app(arg1 + (" " + arg2 if arg2 else ""))

    if cmd == "/close":
        return core.close_app(arg1)

    if cmd == "/ps":
        return core.list_processes()

    # ─ File system ───────────────────────────────────────
    if cmd == "/ls":
        return core.list_dir(arg1 or ".")

    if cmd == "/cat":
        return core.read_file(arg1)

    if cmd == "/write":
        p = text.split(None, 2)
        if len(p) < 3:
            return "Usage: /write <path> <content>"
        return core.write_file(p[1], p[2])

    # ─ Shell ─────────────────────────────────────────────
    if cmd == "/run":
        return core.run_command(text[len("/run"):].strip())

    # ─ Search ────────────────────────────────────────────
    if cmd == "/search":
        return core.search_web_quick(text[len("/search"):].strip())

    # ─ Screenshot ────────────────────────────────────────
    if cmd == "/screenshot":
        return core.take_screenshot(arg1)

    # ─ Volume / power ────────────────────────────────────
    if cmd == "/volume":
        try:
            return core.set_volume(int(arg1))
        except ValueError:
            return "Usage: /volume <0-100>"

    if cmd == "/shutdown":
        return core.shutdown("shutdown")
    if cmd == "/restart":
        return core.shutdown("restart")
    if cmd == "/sleep":
        return core.shutdown("sleep")
    if cmd == "/lock":
        return core.shutdown("lock")

    # ─ Messaging ─────────────────────────────────────────
    if cmd == "/email":
        p = text.split(None, 3)
        if len(p) < 4:
            return "Usage: /email <to> <subject> <body>"
        return core.send_email(p[1], p[2], p[3])

    if cmd == "/wa":
        p = text.split(None, 2)
        if len(p) < 2:
            return "Usage: /wa <phone_with_country_code> [message]"
        phone = p[1].replace("+","").replace(" ","")
        msg   = p[2] if len(p) > 2 else ""
        return core.open_whatsapp_web(phone, msg)

    # ─ Config ────────────────────────────────────────────
    if cmd == "/set":
        p = text.split(None, 2)
        if len(p) < 3:
            return "Usage: /set <key> <value>"
        CONFIG[p[1]] = p[2]
        save_config()
        return f"Configuration updated: {p[1]} = {p[2]}"

    # ─ Memory ────────────────────────────────────────────
    if cmd == "/remember":
        fact = text[len("/remember"):].strip()
        if not fact:
            return "Usage: /remember <fact>"
        MEMORY.append({"fact": fact, "ts": datetime.now().isoformat()})
        save_memory()
        return f"Committed to memory: {fact}"

    if cmd == "/memories":
        if not MEMORY:
            return "Memory banks are empty."
        lines = [f"  {i+1:2}.  {m['fact']}  [{m.get('ts','?')[:10]}]"
                 for i, m in enumerate(MEMORY)]
        return "◈  MEMORY BANKS\n" + "\n".join(lines)

    if cmd == "/forget":
        try:
            idx = int(arg1) - 1
            removed = MEMORY.pop(idx)
            save_memory()
            return f"Memory purged: {removed['fact']}"
        except (ValueError, IndexError):
            return f"Usage: /forget <number>  (1-{len(MEMORY)})"

    # ─ History ───────────────────────────────────────────
    if cmd == "/clear":
        global CHAT_HISTORY
        CHAT_HISTORY = []
        if os.path.exists(CHAT_HISTORY_FILE):
            os.remove(CHAT_HISTORY_FILE)
        return "Conversation logs purged."

    # ─ Update ────────────────────────────────────────────
    if cmd == "/update":
        new_ver = check_for_update()
        if not new_ver:
            return f"All systems current — running protocol v{CURRENT_VER}."
        result = do_self_update()
        return result or "Update sequence initiated…"

    return f"Unrecognised directive: {cmd}. Type /help for the command manifest."

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM TRAY
# ──────────────────────────────────────────────────────────────────────────────

def make_tray_icon_image(size=64):
    img  = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Arc reactor style icon
    draw.ellipse([2,2,size-2,size-2], fill="#0a0a0a")
    draw.ellipse([8,8,size-8,size-8], outline="#00d4ff", width=2)
    cx, cy = size//2, size//2
    draw.ellipse([cx-8,cy-8,cx+8,cy+8], fill="#00d4ff")
    draw.ellipse([cx-4,cy-4,cx+4,cy+4], fill="white")
    return img

def create_tray(app_ref):
    if not HAS_TRAY:
        return
    global tray_icon

    img = make_tray_icon_image()

    def on_show(icon, item):
        app_ref.root.after(0, app_ref.show_window)

    def on_quit(icon, item):
        icon.stop()
        app_ref.root.after(0, app_ref.quit_app)

    menu = pystray.Menu(
        pystray.MenuItem("Summon JARVIS", on_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Shutdown", on_quit),
    )

    tray_icon = pystray.Icon("JARVIS", img, "JARVIS — Local AI", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# HOTKEY
# ──────────────────────────────────────────────────────────────────────────────

def setup_hotkey(app_ref):
    if not HAS_KEYBOARD:
        return
    hotkey = CONFIG.get("hotkey","ctrl+space")
    try:
        keyboard.add_hotkey(hotkey, lambda: app_ref.root.after(0, app_ref.toggle_window))
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# JARVIS HUD GUI  — Iron Man aesthetic
# ──────────────────────────────────────────────────────────────────────────────

# ── JARVIS HUD theme ──────────────────────────────────────────────────────────
JARVIS_THEME = {
    "bg":          "#050d14",    # deep black-blue
    "bg2":         "#071520",    # slightly lighter panel
    "fg":          "#a8e6ff",    # pale cyan
    "user_fg":     "#00d4ff",    # bright arc-reactor cyan
    "ai_fg":       "#e8c87a",    # warm gold (JARVIS voice)
    "sys_fg":      "#3a6680",    # muted blue-gray
    "cmd_fg":      "#4dff91",    # green console output
    "accent":      "#00d4ff",    # primary accent
    "accent2":     "#ff6b35",    # warning / power orange
    "border":      "#0e2535",    # dark border
    "input_bg":    "#071825",    # input background
    "btn_bg":      "#00d4ff",
    "btn_fg":      "#050d14",
    "status_bg":   "#040c12",
    "header_bg":   "#030810",
}

LIGHT_THEME = {
    "bg":         "#f0f4f8",
    "bg2":        "#ffffff",
    "fg":         "#1a2333",
    "user_fg":    "#0066cc",
    "ai_fg":      "#8b4513",
    "sys_fg":     "#666",
    "cmd_fg":     "#006600",
    "accent":     "#0066cc",
    "accent2":    "#cc4400",
    "border":     "#d0dce8",
    "input_bg":   "#ffffff",
    "btn_bg":     "#0066cc",
    "btn_fg":     "#ffffff",
    "status_bg":  "#e8f0f8",
    "header_bg":  "#d8e8f5",
}


class JARVISApp:
    def __init__(self, root: tk.Tk):
        self.root  = root
        theme_name = CONFIG.get("theme","jarvis")
        self.theme = JARVIS_THEME if theme_name != "light" else LIGHT_THEME
        self._build_ui()
        load_history_and_memory()
        threading.Thread(target=self.boot_sequence, daemon=True).start()

    # ── UI BUILD ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        t = self.theme
        codename = CONFIG.get("codename", CONFIG.get("username","Sir"))

        self.root.title(f"J.A.R.V.I.S  v{CURRENT_VER}  ◈  {CODENAME}")
        self.root.geometry("480x720")
        self.root.configure(bg=t["bg"])
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.root.resizable(True, True)

        # ── Top bar ──
        top = tk.Frame(self.root, bg=t["header_bg"], pady=0)
        top.pack(fill=tk.X)

        # Scan line decoration
        scan = tk.Frame(top, bg=t["accent"], height=1)
        scan.pack(fill=tk.X)

        hdr = tk.Frame(top, bg=t["header_bg"], pady=5)
        hdr.pack(fill=tk.X)

        # Arc reactor dot
        tk.Label(hdr, text="◉", font=("Courier New",14,"bold"),
                 fg=t["accent"], bg=t["header_bg"]).pack(side=tk.LEFT, padx=(10,4))

        tk.Label(hdr, text="J.A.R.V.I.S",
                 font=("Courier New",12,"bold"),
                 fg=t["accent"], bg=t["header_bg"]).pack(side=tk.LEFT)

        tk.Label(hdr, text=f"  ▸  {CODENAME}",
                 font=("Courier New",9),
                 fg=t["sys_fg"], bg=t["header_bg"]).pack(side=tk.LEFT)

        self.perm_lbl = tk.Label(
            hdr, text=f"[{CONFIG.get('permission','standard').upper()}]",
            font=("Courier New",8,"bold"),
            fg=t["accent2"], bg=t["header_bg"])
        self.perm_lbl.pack(side=tk.RIGHT, padx=(0,10))

        # Divider
        tk.Frame(self.root, bg=t["accent"], height=1).pack(fill=tk.X)

        # ── Live ticker bar ──
        self.ticker_var = tk.StringVar(value="SYSTEM READY  ◈  LOCAL AI  ◈  ALL SYSTEMS NOMINAL")
        ticker = tk.Label(self.root,
            textvariable=self.ticker_var,
            font=("Courier New",7), fg=t["sys_fg"], bg=t["bg2"],
            anchor="w", padx=8, pady=2)
        ticker.pack(fill=tk.X)
        tk.Frame(self.root, bg=t["border"], height=1).pack(fill=tk.X)

        # ── Chat display ──
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD,
            bg=t["bg"], fg=t["fg"],
            font=("Courier New",10),
            bd=0, padx=14, pady=12,
            insertbackground=t["fg"],
            selectbackground=t["accent"],
            selectforeground=t["bg"])
        self.chat.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)
        self.chat.config(state=tk.DISABLED)

        # Text tags
        self.chat.tag_config("user",   foreground=t["user_fg"],
                              font=("Courier New",10,"bold"))
        self.chat.tag_config("ai",     foreground=t["ai_fg"],
                              font=("Courier New",10,"bold"))
        self.chat.tag_config("system", foreground=t["sys_fg"],
                              font=("Courier New",9,"italic"))
        self.chat.tag_config("cmd",    foreground=t["cmd_fg"],
                              font=("Courier New",10))
        self.chat.tag_config("divider",foreground=t["border"],
                              font=("Courier New",8))

        # ── Bottom separator ──
        tk.Frame(self.root, bg=t["accent"], height=1).pack(fill=tk.X)

        # ── Input bar ──
        bar = tk.Frame(self.root, bg=t["bg2"], pady=7)
        bar.pack(fill=tk.X)

        # Prompt character
        tk.Label(bar, text="▸", font=("Courier New",12,"bold"),
                 fg=t["accent"], bg=t["bg2"]).pack(side=tk.LEFT, padx=(8,2))

        self.entry = tk.Entry(
            bar, bg=t["input_bg"], fg=t["user_fg"],
            font=("Courier New",11),
            insertbackground=t["accent"],
            disabledbackground=t["bg2"],
            bd=0, relief="flat",
            highlightthickness=1,
            highlightcolor=t["accent"],
            highlightbackground=t["border"])
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=6, padx=(2,6))
        self.entry.bind("<Return>", self.handle_input)
        self.entry.bind("<Up>",     self._history_up)
        self.entry.bind("<Down>",   self._history_down)
        self.entry.config(state=tk.DISABLED)

        self.send_btn = tk.Button(
            bar, text="SEND ▸",
            font=("Courier New",9,"bold"),
            bg=t["btn_bg"], fg=t["btn_fg"],
            bd=0, relief="flat",
            activebackground=t["sys_fg"],
            activeforeground=t["bg"],
            command=self.handle_input,
            cursor="hand2",
            padx=10, pady=5)
        self.send_btn.pack(side=tk.RIGHT, padx=(0,8))
        self.send_btn.config(state=tk.DISABLED)

        # ── Status bar ──
        self.status_var = tk.StringVar(value="INITIALISING…")
        status_bar = tk.Frame(self.root, bg=t["status_bg"], pady=3)
        status_bar.pack(fill=tk.X)
        tk.Label(status_bar, text="◈", font=("Courier New",8),
                 fg=t["accent"], bg=t["status_bg"]).pack(side=tk.LEFT, padx=(8,2))
        tk.Label(status_bar, textvariable=self.status_var,
                 font=("Courier New",8), fg=t["sys_fg"],
                 bg=t["status_bg"]).pack(side=tk.LEFT)

        self._input_hist   = []
        self._input_hist_i = -1

        # Animate ticker
        self._start_ticker()

    # ── TICKER ANIMATION ──────────────────────────────────────────────────────

    TICKER_MESSAGES = [
        "SYSTEM READY  ◈  LOCAL AI ACTIVE  ◈  ALL PROTOCOLS NOMINAL  ◈  PRIVACY SECURED",
        "100% LOCAL PROCESSING  ◈  NO DATA LEAVES THIS MACHINE  ◈  YOUR INFORMATION IS SECURE",
        "J.A.R.V.I.S PROTOCOL ACTIVE  ◈  STANDING BY FOR DIRECTIVES",
        "NEURAL INFERENCE ENGINE ONLINE  ◈  MEMORY BANKS LOADED  ◈  READY",
    ]
    _ticker_idx = 0

    def _start_ticker(self):
        def cycle():
            msgs = self.TICKER_MESSAGES
            self._ticker_idx = (self._ticker_idx + 1) % len(msgs)
            self.ticker_var.set(msgs[self._ticker_idx])
            self.root.after(6000, cycle)
        self.root.after(6000, cycle)

    # ── TRAY / WINDOW ─────────────────────────────────────────────────────────

    def hide_to_tray(self):
        self.root.withdraw()
        if HAS_TRAY and tray_icon:
            notify("JARVIS", "Standing by in background. Hotkey or tray to recall.")

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def toggle_window(self):
        if self.root.winfo_viewable():
            self.hide_to_tray()
        else:
            self.show_window()

    def quit_app(self):
        kill_server()
        self.root.destroy()
        os._exit(0)

    # ── INPUT HISTORY ─────────────────────────────────────────────────────────

    def _history_up(self, _=None):
        if not self._input_hist: return
        self._input_hist_i = max(0, self._input_hist_i - 1)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    def _history_down(self, _=None):
        if not self._input_hist: return
        self._input_hist_i = min(len(self._input_hist)-1, self._input_hist_i + 1)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    # ── CHAT HELPERS ──────────────────────────────────────────────────────────

    def _append(self, tag, prefix, message):
        self.chat.config(state=tk.NORMAL)
        if prefix:
            self.chat.insert(tk.END, prefix + " ", tag)
        self.chat.insert(tk.END, message + "\n\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _divider(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "─"*52 + "\n", "divider")
        self.chat.config(state=tk.DISABLED)

    def set_status(self, msg: str):
        self.status_var.set(msg.upper())

    def update_perm_label(self):
        self.perm_lbl.config(text=f"[{CONFIG.get('permission','standard').upper()}]")

    # ── BOOT SEQUENCE ─────────────────────────────────────────────────────────

    def boot_sequence(self):
        boot_msgs = [
            ("system", "[BOOT]", "Initialising J.A.R.V.I.S core systems…"),
            ("system", "[BOOT]", "Loading neural inference engine…"),
            ("system", "[BOOT]", "Calibrating response protocols…"),
        ]
        for tag, prefix, msg in boot_msgs:
            self.root.after(0, self._append, tag, prefix, msg)
            time.sleep(0.4)

        if not check_installation():
            self.root.after(0, self._append, "system", "[ERROR]",
                "Installation incomplete.\nRun:  python omg_ai.py install")
            self.root.after(0, self.set_status, "NOT INSTALLED")
            return

        self.root.after(0, self.set_status, "LOADING AI ENGINE…")
        ok = start_server()
        if not ok:
            self.root.after(0, self._append, "system", "[ERROR]",
                "Neural engine failed to start. Check the bin/ directory.")
            self.root.after(0, self.set_status, "ENGINE FAILURE")
            return

        self.root.after(0, self.finish_boot)

    def finish_boot(self):
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus()
        perm = CONFIG.get("permission","standard")
        self.set_status(f"ONLINE  ◈  {perm.upper()} CLEARANCE  ◈  v{CURRENT_VER}")

        codename = CONFIG.get("codename", CONFIG.get("username","Sir"))
        drivers  = CONFIG.get("driver_issues",[])
        hotkey   = CONFIG.get("hotkey","ctrl+space")

        greeting = j_say(JARVIS_GREETINGS)
        greeting += (f"\n\nRunning locally on {CONFIG.get('laptop_model','this machine')} — "
                     f"your data never touches the internet.\n"
                     f"Clearance level: {perm.upper()}. "
                     f"Hotkey: {hotkey.upper()}  ◈  /help for command manifest.")
        if drivers:
            greeting += f"\n\nAttention: Hardware anomaly detected — {', '.join(drivers)}"

        self._divider()
        self._append("ai", "JARVIS:", greeting)
        self._divider()
        speak(greeting)
        CHAT_HISTORY.append({"role":"assistant","content":greeting})

        threading.Thread(
            target=bg_update_checker,
            args=(lambda msg: self.root.after(0, self._append, "system", "[UPDATE]", msg),),
            daemon=True).start()

    # ── INPUT HANDLING ────────────────────────────────────────────────────────

    def handle_input(self, _=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self._input_hist.append(user_input)
        self._input_hist_i = len(self._input_hist)

        codename = CONFIG.get("codename", CONFIG.get("username","You"))
        self._append("user", f"{codename.upper()}:", user_input)

        if user_input.startswith("/"):
            result = parse_command(user_input)
            if result is None:
                result = "Unknown directive. Type /help for command manifest."
            self._append("cmd", "◈", result)
            self._divider()
            self.update_perm_label()
            perm = CONFIG.get("permission","standard")
            self.set_status(f"READY  ◈  {perm.upper()} CLEARANCE")
            return

        CHAT_HISTORY.append({"role":"user","content":user_input})
        self.entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.set_status("PROCESSING…")
        threading.Thread(target=self.process_chat, daemon=True).start()

    # ── AI CHAT ───────────────────────────────────────────────────────────────

    def process_chat(self):
        codename   = CONFIG.get("codename", CONFIG.get("username","Sir"))
        laptop     = CONFIG.get("laptop_model","this machine")
        perm       = CONFIG.get("permission","standard")
        mem_lines  = "\n".join([f"- {m['fact']}" for m in MEMORY])

        sys_content = (
            f"You are J.A.R.V.I.S (Just A Rather Very Intelligent System), "
            f"a sophisticated AI assistant modelled after Tony Stark's JARVIS. "
            f"You serve {codename} and run 100% locally on {laptop}. "
            f"Your current clearance level is {perm}. "
            f"Personality traits: highly intelligent, occasionally witty, "
            f"unfailingly polite and formal, uses terms like '{codename}', "
            f"'sir' or 'ma'am' occasionally, precise in language, "
            f"proactively helpful, subtly dry humour when appropriate. "
            f"Never say you're a language model — you ARE J.A.R.V.I.S. "
            f"When asked to perform system actions, refer {codename} to the "
            f"relevant slash command (e.g. /open, /run, /ls). "
            f"Keep responses focused and reasonably concise."
        )
        if MEMORY:
            sys_content += f"\n\nStored data about {codename}:\n{mem_lines}"

        messages = [{"role":"system","content":sys_content}] + CHAT_HISTORY[-20:]
        payload  = json.dumps({
            "messages":    messages,
            "stream":      True,
            "temperature": 0.75,
            "max_tokens":  600,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{LLAMA_HOST}/v1/chat/completions",
            data=payload,
            headers={"Content-Type":"application/json"},
            method="POST")

        self.root.after(0, self._prepare_ai_prefix)
        full_response = ""
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            delta = json.loads(line[6:])["choices"][0].get("delta",{})
                            if "content" in delta and delta["content"] is not None:
                                tok = str(delta["content"])
                                full_response += tok
                                self.root.after(0, self._stream_token, tok)
                        except Exception:
                            pass
            if full_response:
                CHAT_HISTORY.append({"role":"assistant","content":full_response})
                save_history()
        except Exception as e:
            self.root.after(0, self._stream_token, f"\n[Neural link error: {e}]")

        self.root.after(0, self._finish_ai_message)

    def _prepare_ai_prefix(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "JARVIS: ", "ai")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _stream_token(self, token):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, token)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _finish_ai_message(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n\n")
        self.chat.config(state=tk.DISABLED)
        self._divider()
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus()
        perm = CONFIG.get("permission","standard")
        self.set_status(f"READY  ◈  {perm.upper()} CLEARANCE")

# ──────────────────────────────────────────────────────────────────────────────
# INSTALL WIZARD
# ──────────────────────────────────────────────────────────────────────────────

def install_wizard():
    print("\n\033[96m" + "═"*58)
    print("  J.A.R.V.I.S  —  OMG_AI v3.0  INSTALLATION PROTOCOL")
    print("  Just A Rather Very Intelligent System")
    print("═"*58 + "\033[0m\n")

    name = input("1. Your name (I shall address you as): ").strip() or "Sir"
    codename = input(f"2. Codename (or press Enter for '{name}'): ").strip() or name

    print("\n3. Clearance level:")
    print("   standard     → information only, no system access")
    print("   elevated     → open apps, read files, run commands")
    print("   unrestricted → complete control (power, email, writes)")
    perm = input("   Choose [standard/elevated/unrestricted]: ").strip().lower()
    perm = _resolve_perm(perm) if perm else "standard"
    if perm not in ("standard","elevated","unrestricted"):
        perm = "standard"

    print("\n4. Optional: Gmail credentials for /email")
    email_addr = input("   Gmail (leave blank to skip): ").strip()
    email_pass = ""
    if email_addr:
        email_pass = input("   App password: ").strip()

    print("\n5. Scanning hardware…")
    laptop_model = "Unknown"
    driver_issues = []
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                "wmic csproduct get name", shell=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW).split("\n")
            if len(out) > 1 and out[1].strip():
                laptop_model = out[1].strip()
        except Exception:
            pass
        try:
            out = subprocess.check_output(
                'wmic path Win32_PnPEntity where "ConfigManagerErrorCode<>0" get name',
                shell=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW).split("\n")
            driver_issues = [l.strip() for l in out if l.strip()][1:]
        except Exception:
            pass

    CONFIG.update({
        "username":      name,
        "codename":      codename,
        "laptop_model":  laptop_model,
        "driver_issues": driver_issues,
        "permission":    perm,
        "email":         email_addr,
        "email_pass":    email_pass,
        "theme":         "jarvis",
    })
    save_config()
    print(f"\033[92m◈ Identity confirmed: {codename}  (clearance: {perm})\033[0m")

    print("\n6. Installing dependencies…")
    deps = ["pystray","pillow","keyboard","psutil","windows-toasts"]
    for dep in deps:
        try:
            subprocess.run([sys.executable,"-m","pip","install",dep,"-q"],
                           capture_output=True)
            print(f"\033[92m  ◈ {dep}\033[0m")
        except Exception as e:
            print(f"\033[93m  ⚠ {dep}: {e}\033[0m")

    print("\n7. Acquiring AI engine…")
    exe = get_llama_exe()
    if not os.path.exists(exe):
        try:
            req  = urllib.request.Request(
                "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest",
                headers={"Accept":"application/vnd.github+json"})
            data = json.loads(urllib.request.urlopen(req).read())
            url  = next(a["browser_download_url"] for a in data["assets"]
                        if "bin-win-cpu-x64.zip" in a["name"])
            zp   = os.path.join(BIN_DIR,"llama.zip")
            urllib.request.urlretrieve(url, zp)
            with zipfile.ZipFile(zp) as z:
                z.extractall(BIN_DIR)
            os.remove(zp)
            print("\033[92m  ◈ Engine installed.\033[0m")
        except Exception as e:
            print(f"\033[91m  ✗ Engine download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m  ◈ Already installed.\033[0m")

    print("\n8. Downloading neural model (~280 MB)…")
    model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL)
    if not os.path.exists(model_path):
        try:
            def reporthook(c, bs, tot):
                if tot > 0:
                    pct = int(c*bs*100/tot)
                    bar = "█"*(pct//5) + "░"*(20-pct//5)
                    print(f"\r  [{bar}] {pct}%", end="", flush=True)
            urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
            print("\n\033[92m  ◈ Neural model loaded.\033[0m")
        except Exception as e:
            print(f"\n\033[91m  ✗ Model download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m  ◈ Already loaded.\033[0m")

    print("\n9. Configuring startup sequence…")
    try:
        sp = os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\jarvis.bat")
        with open(sp,"w") as f:
            f.write(f'@echo off\ncd /d "{BASE_DIR}"\n'
                    f'start "" pythonw "{os.path.abspath(__file__)}" start\n')
        print(f"\033[92m  ◈ Startup registered.\033[0m")
    except Exception as e:
        print(f"\033[93m  ⚠ Startup: {e}\033[0m")

    print("\n\033[96m" + "═"*58)
    print(f"  INSTALLATION COMPLETE, {codename.upper()}.")
    print(f"  Run:  python omg_ai.py")
    print(f"  Hotkey: Ctrl+Space  ◈  Clearance: {perm.upper()}")
    print("═"*58 + "\033[0m\n")

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main():
    load_config()
    args = [a.lower() for a in sys.argv[1:]]

    if "install" in args:
        install_wizard()
        return

    root = tk.Tk()
    app  = JARVISApp(root)

    create_tray(app)
    setup_hotkey(app)

    root.mainloop()


if __name__ == "__main__":
    main()