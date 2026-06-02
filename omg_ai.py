#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║           OMG_AI  v2.0  —  Local AI Assistant        ║
║   Background Agent  •  Full Laptop Control  •  100%  ║
║   Private  •  Siri-style  •  Permission Levels       ║
╚══════════════════════════════════════════════════════╝

PERMISSION LEVELS:
  normal  → info only, no system access
  middle  → open/close apps, read files, basic shell
  full    → complete control: write files, kill tasks, send msgs, registry
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
    "username":      "User",
    "laptop_model":  "Unknown",
    "driver_issues": [],
    "permission":    "normal",   # normal | middle | full
    "hotkey":        "ctrl+space",
    "email":         "",
    "email_pass":    "",
    "theme":         "dark",
    "startup":       True,
}

LLAMA_PORT    = 8080
LLAMA_HOST    = f"http://127.0.0.1:{LLAMA_PORT}"
DEFAULT_MODEL = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_URL     = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
GITHUB_RAW    = "https://raw.githubusercontent.com/WAH-ISHAN/OMG_AI/main/omg_ai.py"
CURRENT_VER   = "2.0.0"

server_process = None
tray_icon      = None   # will hold pystray Icon

# ──────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS  (installed via requirements or wizard)
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
    _toaster = WindowsToaster("OMG_AI")
    HAS_TOAST = True
except Exception:
    HAS_TOAST = False

# ──────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

def notify(title: str, body: str):
    """Send a Windows toast notification (falls back to no-op)."""
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
# TEXT-TO-SPEECH
# ──────────────────────────────────────────────────────────────────────────────

def speak(text: str):
    if sys.platform != "win32":
        return
    def _run():
        try:
            escaped = text.replace("'", "''")[:200]
            ps = (f"Add-Type -AssemblyName System.Speech;"
                  f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{escaped}')")
            subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG  &  PERSISTENCE
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
# PERMISSION HELPERS
# ──────────────────────────────────────────────────────────────────────────────

PERMISSION_RANK = {"normal": 0, "middle": 1, "full": 2}

def has_perm(required: str) -> bool:
    cur  = PERMISSION_RANK.get(CONFIG.get("permission", "normal"), 0)
    need = PERMISSION_RANK.get(required, 0)
    return cur >= need

def perm_denied(required: str) -> str:
    return (f"⛔ This action requires '{required}' permission. "
            f"Current: '{CONFIG.get('permission','normal')}'. "
            f"Use /permission {required}  or update config.json to upgrade.")

# ──────────────────────────────────────────────────────────────────────────────
# AUTO-UPDATER
# ──────────────────────────────────────────────────────────────────────────────

def check_for_update() -> str:
    """Return '' if up-to-date, or new version string."""
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
    """Download latest omg_ai.py from GitHub and replace self, then restart."""
    try:
        req  = urllib.request.Request(GITHUB_RAW)
        code = urllib.request.urlopen(req, timeout=15).read()
        backup = __file__ + ".bak"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(__file__, backup)
        with open(__file__, "wb") as f:
            f.write(code)
        notify("OMG_AI Updated", "Restarting with the new version…")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, __file__] + sys.argv[1:])
    except Exception as e:
        return f"Update failed: {e}"

def bg_update_checker(callback):
    """Background thread: checks update every 6 hours."""
    while True:
        new_ver = check_for_update()
        if new_ver:
            notify("OMG_AI Update Available", f"v{new_ver} is ready. Use /update to install.")
            if callback:
                callback(f"[Update] Version {new_ver} is available. Type /update to install.")
        time.sleep(6 * 3600)

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM CONTROL  (gated by permission)
# ──────────────────────────────────────────────────────────────────────────────

class LaptopControl:
    """All laptop/system control actions, each guarded by permission checks."""

    # ---------- NORMAL LEVEL ----------

    @staticmethod
    def get_sysinfo() -> str:
        lines = []
        lines.append(f"Machine  : {CONFIG.get('laptop_model','Unknown')}")
        if HAS_PSUTIL:
            try:
                lines.append(f"CPU      : {psutil.cpu_percent(interval=1):.1f}%")
                ram = psutil.virtual_memory()
                lines.append(f"RAM      : {ram.percent:.1f}%  "
                             f"({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)")
                disk = psutil.disk_usage('/')
                lines.append(f"Disk     : {disk.percent:.1f}%  "
                             f"({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)")
                lines.append(f"Battery  : " + (
                    f"{psutil.sensors_battery().percent:.0f}%"
                    if psutil.sensors_battery() else "AC / N/A"))
            except Exception as e:
                lines.append(f"(psutil error: {e})")
        else:
            lines.append("(Install psutil for live stats: pip install psutil)")
        return "\n".join(lines)

    @staticmethod
    def get_time() -> str:
        return datetime.now().strftime("%A, %d %B %Y  %H:%M:%S")

    # ---------- MIDDLE LEVEL ----------

    @staticmethod
    def open_app(app_name: str) -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        try:
            subprocess.Popen(app_name, shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW
                             if sys.platform=="win32" else 0)
            return f"✅ Launched: {app_name}"
        except Exception as e:
            return f"❌ Failed to launch {app_name}: {e}"

    @staticmethod
    def close_app(app_name: str) -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill","/F","/IM", app_name],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               capture_output=True)
            else:
                subprocess.run(["pkill","-f", app_name], capture_output=True)
            return f"✅ Closed: {app_name}"
        except Exception as e:
            return f"❌ Failed to close {app_name}: {e}"

    @staticmethod
    def list_processes() -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        if HAS_PSUTIL:
            procs = [(p.info['pid'], p.info['name'])
                     for p in psutil.process_iter(['pid','name'])
                     if p.info['name']]
            lines = [f"{pid:6}  {name}" for pid, name in procs[:30]]
            return "Top 30 processes:\n" + "\n".join(lines)
        else:
            try:
                if sys.platform == "win32":
                    out = subprocess.check_output(
                        "tasklist /fo csv /nh", shell=True, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                    return "Running processes:\n" + out[:1500]
                else:
                    out = subprocess.check_output("ps aux", shell=True, text=True)
                    return "Running processes:\n" + out[:1500]
            except Exception as e:
                return f"Error listing processes: {e}"

    @staticmethod
    def read_file(path: str) -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, encoding="utf-8", errors="replace") as f:
                content = f.read(3000)
            return f"📄 {path}:\n{content}"
        except Exception as e:
            return f"❌ Cannot read '{path}': {e}"

    @staticmethod
    def list_dir(path: str = ".") -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            items = os.listdir(expanded)
            return f"📁 {expanded}:\n" + "\n".join(items[:50])
        except Exception as e:
            return f"❌ Cannot list '{path}': {e}"

    @staticmethod
    def run_command(cmd: str) -> str:
        if not has_perm("middle"):
            return perm_denied("middle")
        # Safety: block destructive commands unless full permission
        dangerous = ["format", "del /s", "rm -rf", "shutdown", "reboot",
                     "reg delete", "reg add", "netsh", "diskpart", "sfc /sc"]
        if not has_perm("full"):
            for d in dangerous:
                if d.lower() in cmd.lower():
                    return (f"⚠️ Command blocked (requires 'full' permission): {cmd}\n"
                            "Use /permission full to enable.")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = (result.stdout or "") + (result.stderr or "")
            return f"$ {cmd}\n{output[:2000]}"
        except subprocess.TimeoutExpired:
            return f"⏱ Command timed out: {cmd}"
        except Exception as e:
            return f"❌ Command error: {e}"

    # ---------- FULL LEVEL ----------

    @staticmethod
    def write_file(path: str, content: str) -> str:
        if not has_perm("full"):
            return perm_denied("full")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Written to {expanded}"
        except Exception as e:
            return f"❌ Write failed: {e}"

    @staticmethod
    def set_volume(level: int) -> str:
        if not has_perm("full"):
            return perm_denied("full")
        level = max(0, min(100, level))
        if sys.platform == "win32":
            try:
                ps = (f"$vol=[int]({level}/100*65535);"
                      "$obj=New-Object -ComObject WScript.Shell;"
                      f"(New-Object -ComObject Shell.Application).NameSpace(0).Self.InvokeVerb('Volume')")
                # simpler approach
                ps2 = (f"Add-Type -TypeDefinition '"
                       "using System.Runtime.InteropServices;"
                       "[Guid(\"5CDF2C82-841E-4546-9722-0CF74078229A\")]"
                       "[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]"
                       "interface IAudioEndpointVolume{ void _VtblGap1_6(); [PreserveSig] int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);};"
                       "' -PassThru; ")
                # Simplest Windows volume control via nircmd if available, else PowerShell
                nircmd = os.path.join(BIN_DIR, "nircmd.exe")
                if os.path.exists(nircmd):
                    subprocess.run([nircmd,"setsysvolume",str(int(level/100*65535))],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    # Use PowerShell + Windows API workaround
                    subprocess.run(
                        ["powershell","-WindowStyle","Hidden","-Command",
                         f"[audio]::Volume={level/100}"],
                        creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
                return f"🔊 Volume set to {level}%"
            except Exception as e:
                return f"⚠️ Volume set partial: {e}"
        return "Volume control only supported on Windows."

    @staticmethod
    def shutdown(mode: str = "shutdown") -> str:
        if not has_perm("full"):
            return perm_denied("full")
        if sys.platform == "win32":
            flags = {
                "shutdown": "/s",
                "restart":  "/r",
                "sleep":    "/h",
                "lock":     "/l",
            }
            flag = flags.get(mode, "/l")
            subprocess.Popen(["shutdown", flag, "/t", "5"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return f"⚡ {mode.capitalize()} in 5 seconds…"
        return f"Unsupported OS for {mode}."

    @staticmethod
    def send_email(to: str, subject: str, body: str) -> str:
        if not has_perm("full"):
            return perm_denied("full")
        email_addr = CONFIG.get("email","")
        email_pass = CONFIG.get("email_pass","")
        if not email_addr or not email_pass:
            return ("❌ No email configured. Add 'email' and 'email_pass' "
                    "to config.json first, or use /set email your@gmail.com and /set email_pass yourpassword")
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
            return f"✅ Email sent to {to}"
        except Exception as e:
            return f"❌ Email failed: {e}"

    @staticmethod
    def open_whatsapp_web(phone: str, message: str = "") -> str:
        if not has_perm("full"):
            return perm_denied("full")
        import urllib.parse, webbrowser
        encoded = urllib.parse.quote(message)
        url = f"https://wa.me/{phone}?text={encoded}"
        webbrowser.open(url)
        return f"🟢 WhatsApp Web opened for {phone}"

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
           "-c", "2048", "--threads", "4", "--no-mmap"]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags)
    for _ in range(30):
        try:
            req = urllib.request.Request(f"{LLAMA_HOST}/health")
            with urllib.request.urlopen(req, timeout=1) as r:
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

ctrl = LaptopControl()

def parse_command(text: str) -> str | None:
    """
    If text is a /command, execute it and return the output string.
    Otherwise return None (let the AI handle it).
    """
    parts = text.strip().split(None, 2)
    if not parts or not parts[0].startswith("/"):
        return None

    cmd   = parts[0].lower()
    arg1  = parts[1] if len(parts) > 1 else ""
    arg2  = parts[2] if len(parts) > 2 else ""

    # ─ Help ──────────────────────────────────────────────
    if cmd == "/help":
        return (
            "📋 COMMANDS  ([ ] = optional)\n"
            "─────────────────────────────────────────\n"
            "/help                 → this list\n"
            "/sysinfo              → CPU, RAM, disk, battery\n"
            "/time                 → current date & time\n"
            "/permission <level>   → set normal|middle|full\n"
            "/open <app>           → launch an app [middle+]\n"
            "/close <app.exe>      → kill a process [middle+]\n"
            "/ps                   → list processes [middle+]\n"
            "/ls [path]            → list directory [middle+]\n"
            "/cat <path>           → read a file [middle+]\n"
            "/run <shell command>  → run command [middle+]\n"
            "/write <path> <text>  → write to file [full]\n"
            "/volume <0-100>       → set system volume [full]\n"
            "/shutdown             → shutdown PC [full]\n"
            "/restart              → restart PC [full]\n"
            "/lock                 → lock screen [full]\n"
            "/sleep                → sleep PC [full]\n"
            "/email <to> <subject> <body>  → send email [full]\n"
            "/wa <phone> [msg]     → open WhatsApp Web [full]\n"
            "/set <key> <value>    → update config\n"
            "/remember <fact>      → save a memory\n"
            "/memories             → list memories\n"
            "/forget <n>           → delete memory #n\n"
            "/clear                → clear chat history\n"
            "/update               → check & install update\n"
        )

    # ─ System info ───────────────────────────────────────
    if cmd == "/sysinfo":
        return ctrl.get_sysinfo()

    if cmd == "/time":
        return ctrl.get_time()

    # ─ Permission ────────────────────────────────────────
    if cmd == "/permission":
        lvl = arg1.lower()
        if lvl not in ("normal","middle","full"):
            return f"Usage: /permission normal|middle|full"
        CONFIG["permission"] = lvl
        save_config()
        return f"🔐 Permission set to '{lvl}'."

    # ─ App control ───────────────────────────────────────
    if cmd == "/open":
        return ctrl.open_app(arg1 + (" " + arg2 if arg2 else ""))

    if cmd == "/close":
        return ctrl.close_app(arg1)

    if cmd == "/ps":
        return ctrl.list_processes()

    # ─ File system ───────────────────────────────────────
    if cmd == "/ls":
        return ctrl.list_dir(arg1 or ".")

    if cmd == "/cat":
        return ctrl.read_file(arg1)

    if cmd == "/write":
        # /write <path> <content...>
        p = text.split(None, 2)
        if len(p) < 3:
            return "Usage: /write <path> <content>"
        return ctrl.write_file(p[1], p[2])

    # ─ Shell ─────────────────────────────────────────────
    if cmd == "/run":
        raw_cmd = text[len("/run"):].strip()
        return ctrl.run_command(raw_cmd)

    # ─ Volume / power ────────────────────────────────────
    if cmd == "/volume":
        try:
            return ctrl.set_volume(int(arg1))
        except ValueError:
            return "Usage: /volume <0-100>"

    if cmd == "/shutdown":
        return ctrl.shutdown("shutdown")
    if cmd == "/restart":
        return ctrl.shutdown("restart")
    if cmd == "/sleep":
        return ctrl.shutdown("sleep")
    if cmd == "/lock":
        return ctrl.shutdown("lock")

    # ─ Messaging ─────────────────────────────────────────
    if cmd == "/email":
        # /email <to> <subject> <body>
        p = text.split(None, 3)
        if len(p) < 4:
            return "Usage: /email <to_address> <subject> <body>"
        return ctrl.send_email(p[1], p[2], p[3])

    if cmd == "/wa":
        p = text.split(None, 2)
        if len(p) < 2:
            return "Usage: /wa <phone_with_country_code> [message]"
        phone = p[1].replace("+","").replace(" ","")
        msg   = p[2] if len(p) > 2 else ""
        return ctrl.open_whatsapp_web(phone, msg)

    # ─ Config ────────────────────────────────────────────
    if cmd == "/set":
        p = text.split(None, 2)
        if len(p) < 3:
            return "Usage: /set <key> <value>"
        CONFIG[p[1]] = p[2]
        save_config()
        return f"✅ Config updated: {p[1]} = {p[2]}"

    # ─ Memory ────────────────────────────────────────────
    if cmd == "/remember":
        fact = text[len("/remember"):].strip()
        if not fact:
            return "Usage: /remember <fact>"
        MEMORY.append({"fact": fact, "ts": datetime.now().isoformat()})
        save_memory()
        return f"🧠 Remembered: {fact}"

    if cmd == "/memories":
        if not MEMORY:
            return "No memories saved yet."
        lines = [f"{i+1}. {m['fact']}  [{m.get('ts','?')[:10]}]"
                 for i, m in enumerate(MEMORY)]
        return "🧠 Memories:\n" + "\n".join(lines)

    if cmd == "/forget":
        try:
            idx = int(arg1) - 1
            removed = MEMORY.pop(idx)
            save_memory()
            return f"🗑 Forgot: {removed['fact']}"
        except (ValueError, IndexError):
            return f"Usage: /forget <number>  (1-{len(MEMORY)})"

    # ─ History ───────────────────────────────────────────
    if cmd == "/clear":
        global CHAT_HISTORY
        CHAT_HISTORY = []
        if os.path.exists(CHAT_HISTORY_FILE):
            os.remove(CHAT_HISTORY_FILE)
        return "🗑 Chat history cleared."

    # ─ Update ────────────────────────────────────────────
    if cmd == "/update":
        new_ver = check_for_update()
        if not new_ver:
            return f"✅ Already on the latest version ({CURRENT_VER})."
        result = do_self_update()
        return result or "Updating…"

    return f"❓ Unknown command: {cmd}. Type /help for a list."

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM TRAY  (Siri-style background presence)
# ──────────────────────────────────────────────────────────────────────────────

def make_tray_icon_image(size=64, color="#4cc9f0"):
    img  = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4,4,size-4,size-4], fill=color)
    # simple "AI" dot inside
    cx, cy = size//2, size//2
    draw.ellipse([cx-6,cy-6,cx+6,cy+6], fill="white")
    return img

def create_tray(app_ref):
    """Run pystray in its own thread so it doesn't block the GUI."""
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
        pystray.MenuItem("Show OMG_AI", on_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )

    tray_icon = pystray.Icon("OMG_AI", img, "OMG_AI — Local AI", menu)

    threading.Thread(target=tray_icon.run, daemon=True).start()

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL HOTKEY  (Ctrl+Space → toggle window)
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
# MAIN GUI
# ──────────────────────────────────────────────────────────────────────────────

DARK  = {"bg":"#0d0d0d","fg":"#e8e8e8","input_bg":"#1a1a1a",
          "user_fg":"#4cc9f0","ai_fg":"#f4a261","sys_fg":"#6b7280",
          "btn_bg":"#4cc9f0","btn_fg":"#0d0d0d","border":"#222"}
LIGHT = {"bg":"#f5f5f5","fg":"#1a1a1a","input_bg":"#ffffff",
          "user_fg":"#1565c0","ai_fg":"#b45309","sys_fg":"#555",
          "btn_bg":"#1565c0","btn_fg":"#fff","border":"#ccc"}

class AssistantApp:
    def __init__(self, root: tk.Tk):
        self.root  = root
        self.theme = DARK if CONFIG.get("theme","dark") == "dark" else LIGHT
        self._build_ui()
        load_history_and_memory()
        threading.Thread(target=self.boot_sequence, daemon=True).start()

    # ── UI BUILD ─────────────────────────────────────────

    def _build_ui(self):
        t = self.theme
        self.root.title("OMG_AI  v2.0")
        self.root.geometry("440x680")
        self.root.configure(bg=t["bg"])
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha",   0.93)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # ── Header ──
        hdr = tk.Frame(self.root, bg="#111", pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="●", font=("Segoe UI",10), fg="#4cc9f0", bg="#111").pack(side=tk.LEFT, padx=(10,2))
        self.title_lbl = tk.Label(
            hdr, text="OMG_AI  •  LOCAL  •  PRIVATE",
            font=("Consolas",9,"bold"), fg="#4cc9f0", bg="#111")
        self.title_lbl.pack(side=tk.LEFT)

        self.perm_lbl = tk.Label(
            hdr, text=f"[{CONFIG.get('permission','normal').upper()}]",
            font=("Consolas",8), fg="#f4a261", bg="#111")
        self.perm_lbl.pack(side=tk.RIGHT, padx=10)

        # ── Chat area ──
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD,
            bg=t["bg"], fg=t["fg"],
            font=("Consolas",10), bd=0, padx=12, pady=10,
            insertbackground=t["fg"])
        self.chat.pack(expand=True, fill=tk.BOTH, padx=4, pady=(4,0))
        self.chat.config(state=tk.DISABLED)
        self.chat.tag_config("user",   foreground=t["user_fg"], font=("Consolas",10,"bold"))
        self.chat.tag_config("ai",     foreground=t["ai_fg"],   font=("Consolas",10,"bold"))
        self.chat.tag_config("system", foreground=t["sys_fg"],  font=("Consolas",9,"italic"))
        self.chat.tag_config("cmd",    foreground="#a3e635",     font=("Consolas",10))

        # ── Input bar ──
        bar = tk.Frame(self.root, bg="#111", pady=8)
        bar.pack(fill=tk.X, padx=4, pady=4)

        self.entry = tk.Entry(
            bar, bg=t["input_bg"], fg=t["fg"],
            font=("Consolas",11), insertbackground=t["fg"],
            bd=0, relief="flat")
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=6, padx=(8,4))
        self.entry.bind("<Return>", self.handle_input)
        self.entry.bind("<Up>",     self._history_up)
        self.entry.bind("<Down>",   self._history_down)
        self.entry.config(state=tk.DISABLED)
        self.entry.focus()

        self.send_btn = tk.Button(
            bar, text="⏎", font=("Consolas",12,"bold"),
            bg=t["btn_bg"], fg=t["btn_fg"], bd=0, relief="flat",
            command=self.handle_input, cursor="hand2")
        self.send_btn.pack(side=tk.RIGHT, padx=(0,8), ipadx=8, ipady=4)
        self.send_btn.config(state=tk.DISABLED)

        # ── Status bar ──
        self.status_var = tk.StringVar(value="Initialising…")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Consolas",8), fg=t["sys_fg"], bg=t["bg"]
                 ).pack(fill=tk.X, padx=8, pady=(0,4))

        # input history
        self._input_hist   = []
        self._input_hist_i = -1

    # ── TRAY / WINDOW HELPERS ─────────────────────────────

    def hide_to_tray(self):
        self.root.withdraw()
        if HAS_TRAY and tray_icon:
            notify("OMG_AI", "Running in background. Tray icon or hotkey to reopen.")

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

    # ── INPUT HISTORY  (arrow keys) ──────────────────────

    def _history_up(self, _=None):
        if not self._input_hist:
            return
        self._input_hist_i = max(0, self._input_hist_i - 1)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    def _history_down(self, _=None):
        if not self._input_hist:
            return
        self._input_hist_i = min(len(self._input_hist)-1, self._input_hist_i + 1)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    # ── CHAT HELPERS ─────────────────────────────────────

    def _append(self, tag, prefix, message):
        self.chat.config(state=tk.NORMAL)
        if prefix:
            self.chat.insert(tk.END, prefix + " ", tag)
        self.chat.insert(tk.END, message + "\n\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def set_status(self, msg: str):
        self.status_var.set(msg)

    def update_perm_label(self):
        self.perm_lbl.config(text=f"[{CONFIG.get('permission','normal').upper()}]")

    # ── BOOT SEQUENCE ─────────────────────────────────────

    def boot_sequence(self):
        if not check_installation():
            self.root.after(0, self._append, "system", "[System]",
                "OMG_AI is not installed.\nRun:  python omg_ai.py install")
            self.root.after(0, self.set_status, "Not installed")
            return
        self.root.after(0, self._append, "system", "[System]",
            "🔄 Starting local AI engine…")
        self.root.after(0, self.set_status, "Starting AI engine…")

        ok = start_server()
        if not ok:
            self.root.after(0, self._append, "system", "[System]",
                "❌ Failed to start AI engine. Check bin/ directory.")
            self.root.after(0, self.set_status, "Engine failed")
            return

        self.root.after(0, self.finish_boot)

    def finish_boot(self):
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus()
        self.set_status(f"Ready  •  {CONFIG.get('permission','normal')} mode  •  v{CURRENT_VER}")

        username = CONFIG.get("username","User")
        drivers  = CONFIG.get("driver_issues",[])
        perm     = CONFIG.get("permission","normal")
        hotkey   = CONFIG.get("hotkey","ctrl+space")

        greeting = (f"Hello {username}! I'm OMG_AI running 100% locally — your data never leaves this machine.\n"
                    f"Permission level: {perm.upper()}.\n"
                    f"Press {hotkey.upper()} to toggle me, or minimise to tray. "
                    f"Type /help for all commands.")
        if drivers:
            greeting += f"\n⚠️ Driver issue detected: {', '.join(drivers)}"

        self._append("ai", "AI:", greeting)
        speak(greeting)
        CHAT_HISTORY.append({"role":"assistant","content":greeting})

        # background update check
        threading.Thread(
            target=bg_update_checker,
            args=(lambda msg: self.root.after(0, self._append, "system", "[Update]", msg),),
            daemon=True).start()

    # ── INPUT HANDLING ─────────────────────────────────────

    def handle_input(self, _=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self._input_hist.append(user_input)
        self._input_hist_i = len(self._input_hist)
        self._append("user", f"{CONFIG.get('username','You')}:", user_input)

        # Slash commands
        if user_input.startswith("/"):
            result = parse_command(user_input)
            tag = "cmd"
            if result is None:
                result = "Unknown command. Type /help"
            self._append(tag, "»", result)
            # keep permission label fresh
            self.update_perm_label()
            self.set_status(f"Ready  •  {CONFIG.get('permission','normal')} mode")
            return

        # Natural language → AI
        CHAT_HISTORY.append({"role":"user","content":user_input})
        self.entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.set_status("Thinking…")
        threading.Thread(target=self.process_chat, daemon=True).start()

    # ── AI CHAT ───────────────────────────────────────────

    def process_chat(self):
        username  = CONFIG.get("username","User")
        laptop    = CONFIG.get("laptop_model","Unknown")
        perm      = CONFIG.get("permission","normal")
        mem_lines = "\n".join([f"- {m['fact']}" for m in MEMORY])
        hotkey    = CONFIG.get("hotkey","ctrl+space")

        sys_content = (
            f"You are OMG_AI, {username}'s personal AI assistant. "
            f"You run 100% locally on {laptop}. "
            f"Current permission level: {perm}. "
            f"You can execute system commands, open apps, read files, send messages, "
            f"and control the laptop when the user gives /commands. "
            f"Be concise, helpful, and proactive. "
            f"When a user asks you to do something that needs a command, "
            f"tell them which /command to use."
        )
        if MEMORY:
            sys_content += f"\n\nFacts about {username}:\n{mem_lines}"

        messages = [{"role":"system","content":sys_content}] + CHAT_HISTORY[-20:]
        payload  = json.dumps({
            "messages":    messages,
            "stream":      True,
            "temperature": 0.7,
            "max_tokens":  512,
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
            self.root.after(0, self._stream_token, f"\n[Error: {e}]")

        self.root.after(0, self._finish_ai_message)

    def _prepare_ai_prefix(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "AI: ", "ai")
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
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus()
        self.set_status(f"Ready  •  {CONFIG.get('permission','normal')} mode")

# ──────────────────────────────────────────────────────────────────────────────
# INSTALL WIZARD  (CLI)
# ──────────────────────────────────────────────────────────────────────────────

def install_wizard():
    print("\n\033[96m" + "="*54)
    print("  OMG_AI v2.0  INSTALLATION WIZARD")
    print("="*54 + "\033[0m\n")

    # 1. Name
    name = input("1. Your name: ").strip() or "User"

    # 2. Permission level
    print("\n2. Permission level:")
    print("   normal  → AI answers only, no system access")
    print("   middle  → open apps, read files, run basic commands")
    print("   full    → complete control (power, email, file writes)")
    perm = input("   Choose [normal/middle/full]: ").strip().lower()
    if perm not in ("normal","middle","full"):
        perm = "normal"

    # 3. Email (optional, for /email command)
    print("\n3. Optional: Gmail credentials for /email command")
    email_addr = input("   Gmail address (leave blank to skip): ").strip()
    email_pass = ""
    if email_addr:
        email_pass = input("   App password (see Google Account → Security → App passwords): ").strip()

    # 4. System scan
    print("\n4. Scanning system…")
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
        "laptop_model":  laptop_model,
        "driver_issues": driver_issues,
        "permission":    perm,
        "email":         email_addr,
        "email_pass":    email_pass,
    })
    save_config()
    print(f"\033[92m✓ Config saved. Hello {name}!  (permission: {perm})\033[0m")

    # 5. Install Python deps
    print("\n5. Installing Python dependencies…")
    deps = ["pystray","pillow","keyboard","psutil","windows-toasts"]
    for dep in deps:
        try:
            subprocess.run([sys.executable,"-m","pip","install",dep,"-q"],
                           capture_output=True)
            print(f"\033[92m  ✓ {dep}\033[0m")
        except Exception as e:
            print(f"\033[93m  ⚠ {dep}: {e}\033[0m")

    # 6. Download llama-server
    print("\n6. Downloading AI Core Engine…")
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
            print("\033[92m  ✓ AI engine installed.\033[0m")
        except Exception as e:
            print(f"\033[91m  ✗ Engine download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m  ✓ Already installed.\033[0m")

    # 7. Download model
    print("\n7. Downloading Intelligence Modules…")
    model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL)
    if not os.path.exists(model_path):
        try:
            def reporthook(c, bs, tot):
                if tot > 0:
                    print(f"\r   {int(c*bs*100/tot)}%", end="", flush=True)
            urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
            print("\n\033[92m  ✓ Brain downloaded.\033[0m")
        except Exception as e:
            print(f"\n\033[91m  ✗ Brain download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m  ✓ Already downloaded.\033[0m")

    # 8. Windows startup
    print("\n8. Adding to Windows startup…")
    try:
        sp = os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\omg_ai.bat")
        with open(sp,"w") as f:
            f.write(f'@echo off\ncd /d "{BASE_DIR}"\n'
                    f'start "" pythonw "{os.path.abspath(__file__)}" start\n')
        print(f"\033[92m  ✓ Startup entry created.\033[0m")
    except Exception as e:
        print(f"\033[93m  ⚠ Startup: {e}\033[0m")

    print("\n\033[96m" + "="*54)
    print("  DONE!  Run:  python omg_ai.py")
    print(f"  Hotkey: Ctrl+Space  |  Perm: {perm}")
    print("="*54 + "\033[0m\n")

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main():
    load_config()
    args = [a.lower() for a in sys.argv[1:]]

    if "install" in args:
        install_wizard()
        return

    # Start GUI
    root = tk.Tk()
    app  = AssistantApp(root)

    # System tray (background agent)
    create_tray(app)

    # Global hotkey
    setup_hotkey(app)

    root.mainloop()

if __name__ == "__main__":
    main()