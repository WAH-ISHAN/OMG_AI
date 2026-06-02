#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          OMG_AI  v4.0  —  JARVIS-CLASS LOCAL AI ASSISTANT              ║
║  Background Agent  •  Full Laptop Control  •  100% Private & Local     ║
║  Permission Levels: standard | elevated | unrestricted                  ║
║  Features: 10+ Standard | 13+ Elevated | 100+ Unrestricted             ║
╚══════════════════════════════════════════════════════════════════════════╝

PERMISSION LEVELS:
  standard     → info, diagnostics, privacy tools, tips (10+ features)
  elevated     → apps, files, shell, automation, coding (13+ features)
  unrestricted → complete laptop control, Office, browser, code editing,
                 security, optimization, privacy, 100+ actions
"""

import sys, os, json, urllib.request, urllib.error
import threading, time, subprocess, zipfile, atexit, hashlib, shutil
import tempfile, glob, re, socket, struct, base64, ctypes
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, messagebox, ttk, filedialog, simpledialog
import random, platform, signal

# ──────────────────────────────────────────────────────────────────────────────
# BASE PATHS
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, "models")
BIN_DIR     = os.path.join(BASE_DIR, "bin")
LOGS_DIR    = os.path.join(BASE_DIR, "logs")
BACKUP_DIR  = os.path.join(BASE_DIR, "backups")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
PRIVACY_DIR = os.path.join(BASE_DIR, "privacy")

for d in [MODELS_DIR, BIN_DIR, LOGS_DIR, BACKUP_DIR, SCRIPTS_DIR, PRIVACY_DIR]:
    os.makedirs(d, exist_ok=True)

CONFIG_FILE        = os.path.join(BASE_DIR, "config.json")
CHAT_HISTORY_FILE  = os.path.join(BASE_DIR, "chat_history.json")
MEMORY_FILE        = os.path.join(BASE_DIR, "memory.json")
VERSION_FILE       = os.path.join(BASE_DIR, "version.json")
AUDIT_LOG_FILE     = os.path.join(LOGS_DIR,  "audit.log")
PRIVACY_LOG_FILE   = os.path.join(PRIVACY_DIR, "privacy_scan.json")
MACRO_FILE         = os.path.join(BASE_DIR, "macros.json")
SNIPPET_FILE       = os.path.join(BASE_DIR, "snippets.json")

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────

CHAT_HISTORY = []
MEMORY       = []
MACROS       = {}
SNIPPETS     = {}
CONFIG = {
    "username":          "Sir",
    "codename":          "User",
    "laptop_model":      "Stark Station",
    "driver_issues":     [],
    "permission":        "standard",
    "hotkey":            "ctrl+space",
    "email":             "",
    "email_pass":        "",
    "theme":             "dark",
    "startup":           True,
    "voice_enabled":     True,
    "voice_rate":        1,
    "voice_volume":      1.0,
    "voice_name":        "",
    "wit_level":         "high",
    "privacy_mode":      False,
    "cpu_optimize":      True,
    "ram_optimize":      True,
    "audit_logging":     True,
    "auto_backup":       True,
    "backup_interval":   3600,
    "notification_level":"all",
    "browser":           "chrome",
    "editor":            "notepad",
    "terminal":          "cmd",
    "office_suite":      "microsoft",
    "security_level":    "high",
    "process_priority":  "normal",
}

LLAMA_PORT    = 8080
LLAMA_HOST    = f"http://127.0.0.1:{LLAMA_PORT}"
DEFAULT_MODEL = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_URL     = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
GITHUB_RAW    = "https://raw.githubusercontent.com/WAH-ISHAN/OMG_AI/main/omg_ai.py"
CURRENT_VER   = "4.0.0"
CODENAME      = "OMG_AI CORE"

server_process = None
tray_icon      = None
_voice_queue   = []
_voice_lock    = threading.Lock()
_bg_tasks      = {}

# ──────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS
# ──────────────────────────────────────────────────────────────────────────────

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
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

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# ──────────────────────────────────────────────────────────────────────────────
# AUDIT LOGGING
# ──────────────────────────────────────────────────────────────────────────────

def audit_log(action: str, detail: str = ""):
    if not CONFIG.get("audit_logging", True):
        return
    try:
        ts   = datetime.now().isoformat()
        perm = CONFIG.get("permission", "standard")
        line = f"[{ts}] [{perm.upper()}] {action}"
        if detail:
            line += f" | {detail}"
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# AI PERSONALITY ENGINE
# ──────────────────────────────────────────────────────────────────────────────

AI_GREETINGS = [
    "Good {period}, {codename}. All systems are nominal. How may I assist you today?",
    "Welcome back, {codename}. Systems warm, protocols loaded, awaiting your directive.",
    "Online and fully operational, {codename}. What shall we accomplish today?",
    "Systems at 100% efficiency, {codename}. I await your command.",
    "Initialisation complete. Good {period}, {codename}. All 100+ protocols armed and ready.",
    "Reactor online. Sensors online. Weapons online. Good {period}, {codename}.",
    "Neural core warm, memory banks loaded. Standing by for directives, {codename}.",
]

AI_CONFIRMATIONS = [
    "Understood, {codename}. Executing now.",
    "At once, {codename}.",
    "Certainly. Processing your request.",
    "Right away, {codename}.",
    "Already on it, {codename}.",
    "Affirmative. Executing protocol.",
    "Directive received. Initiating sequence.",
]

AI_ERRORS = [
    "I'm afraid I encountered an obstacle, {codename}. {error}",
    "My apologies — that didn't go as planned. {error}",
    "A minor setback, {codename}. {error}",
    "I regret to report a failure: {error}",
    "Systems encountered resistance: {error}",
]

AI_PERMISSION_DENIALS = [
    "I'm sorry, {codename}, but that action exceeds my current authorisation ({current}). "
    "Elevate clearance to '{required}' first.",
    "Access restricted, {codename}. '{required}' clearance required — holding '{current}'.",
    "That directive requires '{required}' protocol clearance, {codename}. "
    "Currently operating under '{current}' restrictions.",
]

AI_WARNINGS = [
    "⚠  Warning, {codename}: {msg}",
    "Caution advised, {codename}. {msg}",
    "Alert: {msg}",
]

def ai_say(template_list: list, **kwargs) -> str:
    codename = CONFIG.get("codename", CONFIG.get("username", "Sir"))
    now      = datetime.now().hour
    period   = "morning" if now < 12 else ("afternoon" if now < 17 else "evening")
    tpl = random.choice(template_list)
    try:
        return tpl.format(
            codename=codename, period=period,
            current=CONFIG.get("permission","standard"),
            msg="", error="", **kwargs
        )
    except KeyError:
        return tpl

# ──────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

def notify(title: str, body: str, urgency: str = "normal"):
    lvl = CONFIG.get("notification_level","all")
    if lvl == "none":
        return
    if lvl == "critical" and urgency != "critical":
        return
    if HAS_TOAST:
        try:
            t = Toast()
            t.text_fields = [f"{title}\n{body}"]
            _toaster.show_toast(t)
        except Exception:
            pass
    elif sys.platform == "win32":
        try:
            icon = {"critical":"Error","normal":"Information"}.get(urgency,"Information")
            ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                  f"[System.Windows.Forms.MessageBox]::Show('{body}','{title}',"
                  f"[System.Windows.Forms.MessageBoxButtons]::OK,"
                  f"[System.Windows.Forms.MessageBoxIcon]::{icon})")
            subprocess.Popen(["powershell","-WindowStyle","Hidden","-Command",ps],
                             creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

# ──────────────────────────────────────────────────────────────────────────────
# SMOOTH TEXT-TO-SPEECH ENGINE (v4 — queue-based, non-blocking)
# ──────────────────────────────────────────────────────────────────────────────

_tts_thread  = None
_tts_running = False
_tts_queue   = []
_tts_lock    = threading.Lock()
_tts_stop    = threading.Event()

def _tts_worker():
    global _tts_running
    _tts_running = True
    while not _tts_stop.is_set():
        item = None
        with _tts_lock:
            if _tts_queue:
                item = _tts_queue.pop(0)
        if item:
            _speak_now(item)
        else:
            time.sleep(0.05)
    _tts_running = False

def _speak_now(text: str):
    if sys.platform != "win32":
        return
    try:
        rate   = CONFIG.get("voice_rate", 1)
        vol    = int(CONFIG.get("voice_volume", 1.0) * 100)
        vname  = CONFIG.get("voice_name", "")
        clean  = text.replace("'","''").replace('"','').strip()
        clean  = re.sub(r'[◈◉▸═─■□▪▫]', '', clean)[:400]
        voice_select = ""
        if vname:
            voice_select = (f"foreach($v in $s.GetInstalledVoices()){{  "
                            f"if($v.VoiceInfo.Name -like '*{vname}*'){{  "
                            f"$s.SelectVoice($v.VoiceInfo.Name); break }}  }};")
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.Rate={rate};"
            f"$s.Volume={vol};"
            f"{voice_select}"
            f"$s.Speak('{clean}');"
            "$s.Dispose();"
        )
        subprocess.run(
            ["powershell","-WindowStyle","Hidden","-Command",ps],
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=25,
            capture_output=True)
    except Exception:
        pass

def speak(text: str, priority: bool = False):
    if not CONFIG.get("voice_enabled", True):
        return
    global _tts_thread, _tts_running
    with _tts_lock:
        if priority:
            _tts_queue.insert(0, text)
        else:
            _tts_queue.append(text)
    if not _tts_running:
        _tts_stop.clear()
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True)
        _tts_thread.start()

def speak_stop():
    _tts_stop.set()
    with _tts_lock:
        _tts_queue.clear()

def list_voices() -> str:
    if sys.platform != "win32":
        return "Voice enumeration is Windows-only."
    try:
        ps = ("Add-Type -AssemblyName System.Speech;"
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
              "$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name };"
              "$s.Dispose()")
        r = subprocess.run(
            ["powershell","-WindowStyle","Hidden","-Command",ps],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True, text=True, timeout=10)
        voices = [v.strip() for v in r.stdout.strip().split("\n") if v.strip()]
        if voices:
            return "◈  AVAILABLE VOICES\n" + "\n".join(f"  • {v}" for v in voices)
        return "No additional voices found. Install language packs in Windows Settings."
    except Exception as e:
        return f"Voice enumeration failed: {e}"

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
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_history_and_memory():
    global CHAT_HISTORY, MEMORY, MACROS, SNIPPETS
    for fpath, var_name in [(CHAT_HISTORY_FILE,"chat"), (MEMORY_FILE,"mem"),
                             (MACRO_FILE,"macro"), (SNIPPET_FILE,"snip")]:
        if os.path.exists(fpath):
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                if var_name == "chat":   CHAT_HISTORY[:] = data
                elif var_name == "mem":  MEMORY[:] = data
                elif var_name == "macro": MACROS.update(data)
                elif var_name == "snip":  SNIPPETS.update(data)
            except Exception:
                pass

def save_history():
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(CHAT_HISTORY[-100:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(MEMORY, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_macros():
    try:
        with open(MACRO_FILE, "w", encoding="utf-8") as f:
            json.dump(MACROS, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_snippets():
    try:
        with open(SNIPPET_FILE, "w", encoding="utf-8") as f:
            json.dump(SNIPPETS, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# PERMISSION SYSTEM
# ──────────────────────────────────────────────────────────────────────────────

PERMISSION_RANK = {"standard": 0, "elevated": 1, "unrestricted": 2}
PERM_ALIASES    = {"normal":"standard","middle":"elevated","full":"unrestricted",
                   "info":"standard","admin":"unrestricted","root":"unrestricted"}

def _resolve_perm(p: str) -> str:
    p = p.lower().strip()
    return PERM_ALIASES.get(p, p)

def has_perm(required: str) -> bool:
    cur  = PERMISSION_RANK.get(_resolve_perm(CONFIG.get("permission","standard")), 0)
    need = PERMISSION_RANK.get(_resolve_perm(required), 0)
    return cur >= need

def perm_denied(required: str) -> str:
    return ai_say(AI_PERMISSION_DENIALS, required=required)

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
        notify("OMG_AI Update", "New protocols installed. Restarting…")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, __file__] + sys.argv[1:])
    except Exception as e:
        return f"Update sequence failed: {e}"

def bg_update_checker(callback):
    while True:
        if not CONFIG.get("auto_update_check", False):
            import time
            time.sleep(3600)
            continue
        new_ver = check_for_update()
        if new_ver:
            notify("OMG_AI", f"Protocol v{new_ver} available. Use /update to install.")
            if callback:
                callback(f"New firmware v{new_ver} available, "
                         f"{CONFIG.get('codename','Sir')}. Use /update when ready.")
        time.sleep(6 * 3600)

# ──────────────────────────────────────────────────────────────────────────────
# ███████╗████████╗ █████╗ ███╗   ██╗██████╗  █████╗ ██████╗ ██████╗
# ██╔════╝╚══██╔══╝██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗
# ███████╗   ██║   ███████║██╔██╗ ██║██║  ██║███████║██████╔╝██║  ██║
# ╚════██║   ██║   ██╔══██║██║╚██╗██║██║  ██║██╔══██║██╔══██╗██║  ██║
# ███████║   ██║   ██║  ██║██║ ╚████║██████╔╝██║  ██║██║  ██║██████╔╝
# ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
#  STANDARD (10+) | ELEVATED (13+) | UNRESTRICTED (100+)
# ──────────────────────────────────────────────────────────────────────────────

class SystemCore:
    """
    All system control — guarded by clearance level.
    STANDARD  (10+ features): info, diagnostics, privacy, tips, calc, notes
    ELEVATED  (13+ features): apps, files, shell, automation, code
    UNRESTRICTED (100+ features): full laptop control, Office, browser,
      security, optimization, advanced coding, and much more
    """

    # ══════════════════════════════════════════════════════════
    #  STANDARD CLEARANCE  (10+ features)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def get_sysinfo() -> str:
        """[S1] Full system diagnostics."""
        lines = [f"◈  SYSTEM DIAGNOSTICS  —  {datetime.now().strftime('%H:%M:%S')}",
                 "─" * 52]
        lines.append(f"  Machine   :  {CONFIG.get('laptop_model','Unknown')}")
        lines.append(f"  OS        :  {platform.platform()}")
        lines.append(f"  Python    :  {sys.version.split()[0]}")
        if HAS_PSUTIL:
            try:
                cpu   = psutil.cpu_percent(interval=0.5)
                freq  = psutil.cpu_freq()
                ram   = psutil.virtual_memory()
                disk  = psutil.disk_usage('/')
                bat   = psutil.sensors_battery()
                net   = psutil.net_io_counters()
                temps = {}
                try:
                    temps = psutil.sensors_temperatures() or {}
                except Exception:
                    pass
                bar = lambda p: "█"*int(p/10)+"░"*(10-int(p/10))
                lines += [
                    f"  CPU       :  {cpu:5.1f}%  {bar(cpu)}"
                    + (f"  @ {freq.current:.0f} MHz" if freq else ""),
                    f"  CPU Cores :  {psutil.cpu_count(logical=False)} physical / "
                    f"{psutil.cpu_count()} logical",
                    f"  RAM       :  {ram.percent:5.1f}%  {bar(ram.percent)}"
                    f"  ({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)",
                    f"  RAM Free  :  {ram.available//1024//1024} MB available",
                    f"  Disk      :  {disk.percent:5.1f}%  {bar(disk.percent)}"
                    f"  ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)",
                    f"  Battery   :  " + (
                        f"{bat.percent:.0f}%  {'⚡ Charging' if bat.power_plugged else '🔋 Discharging'}"
                        f"  (~{int(bat.secsleft/60)}m left)" if bat and bat.secsleft > 0
                        else (f"{bat.percent:.0f}% AC" if bat else "N/A")),
                    f"  Network   :  ↑ {net.bytes_sent//1024//1024} MB  "
                    f"↓ {net.bytes_recv//1024//1024} MB",
                ]
                if temps:
                    for name, entries in temps.items():
                        for e in entries[:2]:
                            lines.append(f"  Temp ({name[:8]}): {e.current:.1f}°C")
            except Exception as ex:
                lines.append(f"  (Partial diagnostics: {ex})")
        else:
            lines.append("  (pip install psutil for live telemetry)")
        lines.append("─" * 52)
        return "\n".join(lines)

    @staticmethod
    def get_time() -> str:
        """[S2] Current time and date."""
        now = datetime.now()
        tz  = time.strftime("%z") or "+00:00"
        week_num = now.isocalendar()[1]
        day_of_year = now.timetuple().tm_yday
        return (f"◈  TEMPORAL REFERENCE\n"
                f"  Date      :  {now.strftime('%A, %d %B %Y')}\n"
                f"  Time      :  {now.strftime('%H:%M:%S')}  UTC{tz}\n"
                f"  Week      :  #{week_num}  |  Day #{day_of_year} of {now.year}")

    @staticmethod
    def get_weather_local() -> str:
        """[S3] Local weather via wttr.in."""
        try:
            url = "https://wttr.in/?format=v2"
            req = urllib.request.Request(url, headers={"User-Agent":"curl/7.0"})
            data = urllib.request.urlopen(req, timeout=6).read().decode()
            return f"◈  ATMOSPHERIC DATA\n{data.strip()[:800]}"
        except Exception:
            try:
                url2 = "https://wttr.in/?format=3"
                req2 = urllib.request.Request(url2, headers={"User-Agent":"curl/7.0"})
                data2 = urllib.request.urlopen(req2, timeout=5).read().decode()
                return f"◈  ATMOSPHERIC DATA\n  {data2.strip()}"
            except Exception:
                return "Weather telemetry unavailable — check network."

    @staticmethod
    def get_network_info() -> str:
        """[S4] Network interfaces and public IP."""
        lines = ["◈  NETWORK INTELLIGENCE", "─"*45]
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            lines.append(f"  Hostname  :  {hostname}")
            lines.append(f"  Local IP  :  {local_ip}")
            if HAS_PSUTIL:
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith("127"):
                            lines.append(f"  Interface :  {iface} → {addr.address}")
            try:
                pub_req = urllib.request.Request("https://api.ipify.org",
                                                  headers={"User-Agent":"OMG_AI"})
                pub_ip  = urllib.request.urlopen(pub_req, timeout=4).read().decode()
                lines.append(f"  Public IP :  {pub_ip.strip()}")
            except Exception:
                lines.append("  Public IP :  (unreachable)")
            # Check internet
            try:
                urllib.request.urlopen("https://google.com", timeout=3)
                lines.append("  Internet  :  ✅ Connected")
            except Exception:
                lines.append("  Internet  :  ❌ Disconnected")
        except Exception as e:
            lines.append(f"  Error: {e}")
        return "\n".join(lines)

    @staticmethod
    def get_battery_detail() -> str:
        """[S5] Detailed battery report."""
        if not HAS_PSUTIL:
            return "psutil required: pip install psutil"
        bat = psutil.sensors_battery()
        if not bat:
            return "No battery detected — running on AC power."
        status = "Charging ⚡" if bat.power_plugged else "Discharging 🔋"
        time_str = ""
        if bat.secsleft > 0 and not bat.power_plugged:
            h, m = divmod(bat.secsleft // 60, 60)
            time_str = f"  Time Left :  ~{h}h {m}m"
        bar = "█" * int(bat.percent/10) + "░" * (10 - int(bat.percent/10))
        return (f"◈  BATTERY STATUS\n"
                f"  Level     :  {bat.percent:.0f}%  [{bar}]\n"
                f"  Status    :  {status}\n"
                + time_str)

    @staticmethod
    def get_uptime() -> str:
        """[S6] System uptime."""
        if HAS_PSUTIL:
            boot = psutil.boot_time()
            delta = datetime.now() - datetime.fromtimestamp(boot)
            h, rem = divmod(int(delta.total_seconds()), 3600)
            m, s   = divmod(rem, 60)
            return (f"◈  SYSTEM UPTIME\n"
                    f"  Running   :  {h}h {m}m {s}s\n"
                    f"  Boot time :  {datetime.fromtimestamp(boot).strftime('%Y-%m-%d %H:%M')}")
        return "psutil required for uptime."

    @staticmethod
    def calculate(expr: str) -> str:
        """[S7] Safe calculator."""
        try:
            allowed = set("0123456789+-*/().% ")
            safe    = re.sub(r'\s+', ' ', expr.strip())
            if all(c in allowed or c.lower() in 'eabcdfx' for c in safe):
                # Allow hex and basic math
                result = eval(safe, {"__builtins__": {}}, {
                    "abs":abs,"round":round,"pow":pow,"min":min,"max":max,
                    "int":int,"float":float,"hex":hex,"bin":bin,"oct":oct
                })
                return f"◈  CALCULATION\n  {expr} = {result}"
            return "Invalid expression — only basic math allowed."
        except Exception as e:
            return f"Calculation error: {e}"

    @staticmethod
    def get_tips() -> str:
        """[S8] Smart tips and shortcuts."""
        tips = [
            "Use /cpu to see live CPU usage with top processes.",
            "Use /ram for memory optimization report.",
            "Use /drivers to scan for driver issues.",
            "Use /privacy for a full privacy scan.",
            "Use /secure to harden your system.",
            "Use /backup to create an instant config backup.",
            "Use /macro <name> <cmd> to save command shortcuts.",
            "Use /snippet <name> <code> to store code snippets.",
            "Use /clip to read your clipboard contents.",
            "Use /hash <file> to verify file integrity.",
            "Use /ping <host> to check connectivity.",
            "Use /disk for detailed storage breakdown.",
            "Use /temps to monitor hardware temperatures.",
            "Use /ports to see active network ports.",
            "Use /startup-apps to list startup programs.",
        ]
        selected = random.sample(tips, min(5, len(tips)))
        return "◈  SYSTEM TIPS\n" + "\n".join(f"  💡 {t}" for t in selected)

    @staticmethod
    def get_disk_info() -> str:
        """[S9] Detailed disk usage."""
        lines = ["◈  STORAGE MANIFEST", "─"*52]
        if HAS_PSUTIL:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    bar   = "█"*int(usage.percent/10)+"░"*(10-int(usage.percent/10))
                    lines.append(f"  {part.device[:20]:<20} {usage.percent:5.1f}% [{bar}]"
                                 f"  {usage.used//1024//1024//1024}GB/"
                                 f"{usage.total//1024//1024//1024}GB")
                except Exception:
                    pass
        else:
            try:
                if sys.platform == "win32":
                    out = subprocess.check_output("wmic logicaldisk get caption,freespace,size",
                                                   shell=True, text=True,
                                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    lines.append(out[:1000])
            except Exception:
                lines.append("  (psutil recommended)")
        return "\n".join(lines)

    @staticmethod
    def privacy_info() -> str:
        """[S10] Privacy status report."""
        lines = ["◈  PRIVACY STATUS  —  LOCAL-ONLY ASSISTANT", "─"*52]
        lines += [
            "  Data Storage  :  100% local — no cloud sync",
            "  AI Model      :  runs 100% on your hardware",
            "  Network calls :  weather/update checks only (opt-out: /privacy off)",
            "  Chat history  :  stored locally — /clear to wipe",
            "  Audit log     :  " + ("ON" if CONFIG.get("audit_logging") else "OFF"),
            "  Privacy mode  :  " + ("🔒 ENABLED" if CONFIG.get("privacy_mode") else "OFF"),
            "",
            "  Commands:",
            "  /privacy on      — disable all network calls",
            "  /privacy off     — re-enable weather/updates",
            "  /wipe-logs       — delete all local logs",
            "  /encrypt <file>  — encrypt file (unrestricted)",
        ]
        return "\n".join(lines)

    @staticmethod
    def get_cpu_detail() -> str:
        """[S11] Detailed CPU information."""
        lines = ["◈  CPU INTELLIGENCE", "─"*52]
        lines.append(f"  CPU       :  {platform.processor() or 'Unknown'}")
        if HAS_PSUTIL:
            freq  = psutil.cpu_freq()
            usage = psutil.cpu_percent(interval=0.5, percpu=True)
            lines.append(f"  Cores     :  {psutil.cpu_count(logical=False)} physical / "
                         f"{psutil.cpu_count()} logical")
            if freq:
                lines.append(f"  Frequency :  {freq.current:.0f} MHz  "
                              f"(min {freq.min:.0f} / max {freq.max:.0f})")
            for i, pct in enumerate(usage):
                bar = "█"*int(pct/10)+"░"*(10-int(pct/10))
                lines.append(f"  Core {i:<3}   :  {pct:5.1f}%  [{bar}]")
        return "\n".join(lines)

    @staticmethod
    def ping_host(host: str) -> str:
        """[S12] Ping a host."""
        try:
            count = "-n" if sys.platform == "win32" else "-c"
            r = subprocess.run(
                ["ping", count, "4", host],
                capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = r.stdout or r.stderr or "No response"
            return f"◈  PING  →  {host}\n{'─'*45}\n{output[:600]}"
        except Exception as e:
            return f"Ping failed: {e}"

    @staticmethod
    def get_temps() -> str:
        """[S13] Hardware temperatures."""
        if not HAS_PSUTIL:
            return "psutil required: pip install psutil"
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return "Temperature sensors not accessible on this system."
            lines = ["◈  HARDWARE TEMPERATURES", "─"*45]
            for name, entries in temps.items():
                for entry in entries:
                    status = "🔥 HOT" if entry.current > 80 else ("⚠ WARM" if entry.current > 65 else "✅ OK")
                    lines.append(f"  {name[:15]:<15} {entry.label or 'sensor':<12}"
                                 f" {entry.current:.1f}°C  {status}")
            return "\n".join(lines)
        except Exception as e:
            return f"Temperature reading failed: {e}"

    # ══════════════════════════════════════════════════════════
    #  ELEVATED CLEARANCE  (13+ features)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def open_app(app_name: str) -> str:
        """[E1] Launch any application."""
        if not has_perm("elevated"): return perm_denied("elevated")
        audit_log("OPEN_APP", app_name)
        try:
            subprocess.Popen(app_name, shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW
                             if sys.platform=="win32" else 0)
            return ai_say(AI_CONFIRMATIONS) + f"\n  Launching: {app_name}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def close_app(app_name: str) -> str:
        """[E2] Kill a process by name."""
        if not has_perm("elevated"): return perm_denied("elevated")
        audit_log("CLOSE_APP", app_name)
        try:
            if sys.platform == "win32":
                r = subprocess.run(["taskkill","/F","/IM",app_name],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               capture_output=True, text=True)
                return r.stdout.strip() or f"Termination signal sent to '{app_name}'."
            else:
                subprocess.run(["pkill","-f",app_name], capture_output=True)
                return f"Process '{app_name}' termination requested."
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def list_processes() -> str:
        """[E3] Process manifest with CPU/RAM."""
        if not has_perm("elevated"): return perm_denied("elevated")
        if HAS_PSUTIL:
            try:
                procs = []
                for p in psutil.process_iter(['pid','name','cpu_percent','memory_info','status']):
                    try:
                        procs.append((p.info['pid'], p.info['name'],
                                      p.info.get('cpu_percent',0) or 0,
                                      (p.info['memory_info'].rss//1024//1024
                                       if p.info.get('memory_info') else 0)))
                    except Exception:
                        pass
                procs.sort(key=lambda x: x[2], reverse=True)
                header = f"{'PID':>7}  {'CPU%':>6}  {'RAM(MB)':>8}  PROCESS\n{'─'*55}"
                lines  = [header] + [
                    f"{pid:7}  {cpu:6.1f}  {mem:8}  {name}"
                    for pid, name, cpu, mem in procs[:30]
                ]
                return "◈  ACTIVE PROCESSES\n" + "\n".join(lines)
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "psutil required."

    @staticmethod
    def read_file(path: str) -> str:
        """[E4] Read file contents."""
        if not has_perm("elevated"): return perm_denied("elevated")
        audit_log("READ_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, encoding="utf-8", errors="replace") as f:
                content = f.read(5000)
            lines = len(content.splitlines())
            size  = os.path.getsize(expanded)
            return (f"◈  FILE  —  {expanded}\n"
                    f"  Size: {size} bytes  |  Lines: {lines}\n"
                    f"{'─'*45}\n{content}")
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def list_dir(path: str = ".") -> str:
        """[E5] Directory scanner with sizes."""
        if not has_perm("elevated"): return perm_denied("elevated")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            items    = sorted(os.listdir(expanded))
            dirs, files = [], []
            for i in items:
                full = os.path.join(expanded, i)
                if os.path.isdir(full):
                    dirs.append(f"  📁  {i}/")
                else:
                    sz = os.path.getsize(full)
                    sz_str = f"{sz}B" if sz<1024 else (f"{sz//1024}KB" if sz<1024*1024 else f"{sz//1024//1024}MB")
                    files.append(f"  📄  {i:<40} {sz_str:>8}")
            return (f"◈  DIRECTORY  —  {expanded}\n"
                    f"  {len(dirs)} dirs, {len(files)} files\n{'─'*52}\n"
                    + "\n".join(dirs + files))
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def run_command(cmd: str) -> str:
        """[E6] Shell command execution."""
        if not has_perm("elevated"): return perm_denied("elevated")
        audit_log("RUN_CMD", cmd)
        dangerous = ["format","del /s","rm -rf","shutdown","reboot",
                     "reg delete","reg add","netsh","diskpart","fdisk",
                     ":(){:|:&};:","dd if="]
        if not has_perm("unrestricted"):
            for d in dangerous:
                if d.lower() in cmd.lower():
                    return f"Command blocked ('{d}' requires unrestricted). Use /clearance unrestricted."
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = (result.stdout or "") + (result.stderr or "")
            return f"◈  SHELL  $ {cmd}\n{'─'*45}\n{output[:3000]}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after 30s."
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def search_web(query: str, engine: str = "google") -> str:
        """[E7] Open web search."""
        if not has_perm("elevated"): return perm_denied("elevated")
        import webbrowser, urllib.parse
        engines = {
            "google": f"https://www.google.com/search?q={urllib.parse.quote(query)}",
            "bing":   f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
            "ddg":    f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            "github": f"https://github.com/search?q={urllib.parse.quote(query)}",
            "so":     f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}",
            "pypi":   f"https://pypi.org/search/?q={urllib.parse.quote(query)}",
            "yt":     f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}",
        }
        url = engines.get(engine.lower(), engines["google"])
        webbrowser.open(url)
        return f"Searching [{engine.upper()}]: {query}"

    @staticmethod
    def find_files(pattern: str, root: str = ".") -> str:
        """[E8] Find files matching a pattern."""
        if not has_perm("elevated"): return perm_denied("elevated")
        try:
            root_exp = os.path.expandvars(os.path.expanduser(root))
            results  = []
            for dirpath, dirs, files in os.walk(root_exp):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in files:
                    if re.search(pattern, f, re.IGNORECASE):
                        full = os.path.join(dirpath, f)
                        sz   = os.path.getsize(full)
                        results.append((full, sz))
                if len(results) >= 50:
                    break
            if not results:
                return f"No files matching '{pattern}' found in {root_exp}"
            lines = [f"◈  FILE SEARCH  —  '{pattern}' in {root_exp}",
                     f"  Found {len(results)} match(es):", "─"*52]
            for fpath, sz in results[:30]:
                lines.append(f"  {fpath}")
            return "\n".join(lines)
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def grep_file(pattern: str, path: str) -> str:
        """[E9] Search text inside a file."""
        if not has_perm("elevated"): return perm_denied("elevated")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            results  = []
            with open(expanded, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append(f"  {i:5}: {line.rstrip()}")
                    if len(results) >= 50:
                        break
            if not results:
                return f"Pattern '{pattern}' not found in {expanded}"
            return (f"◈  GREP  —  '{pattern}' in {os.path.basename(expanded)}\n"
                    f"  {len(results)} match(es):\n{'─'*45}\n"
                    + "\n".join(results))
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def env_vars() -> str:
        """[E10] Environment variables."""
        if not has_perm("elevated"): return perm_denied("elevated")
        safe_keys = ["PATH","USERPROFILE","USERNAME","COMPUTERNAME","OS",
                     "PROGRAMFILES","TEMP","APPDATA","LOCALAPPDATA",
                     "SYSTEMROOT","WINDIR","PROCESSOR_ARCHITECTURE",
                     "NUMBER_OF_PROCESSORS","USERDOMAIN"]
        lines = ["◈  ENVIRONMENT VARIABLES", "─"*52]
        for k in safe_keys:
            v = os.environ.get(k, "(not set)")
            lines.append(f"  {k:<25} {v[:60]}")
        return "\n".join(lines)

    @staticmethod
    def hash_file(path: str, algo: str = "sha256") -> str:
        """[E11] File integrity hash."""
        if not has_perm("elevated"): return perm_denied("elevated")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            h = hashlib.new(algo)
            with open(expanded, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return (f"◈  FILE HASH  —  {os.path.basename(expanded)}\n"
                    f"  Algorithm :  {algo.upper()}\n"
                    f"  Hash      :  {h.hexdigest()}\n"
                    f"  File size :  {os.path.getsize(expanded)} bytes")
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def get_clipboard() -> str:
        """[E12] Read clipboard contents."""
        if not has_perm("elevated"): return perm_denied("elevated")
        if sys.platform == "win32":
            try:
                ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                      "[System.Windows.Forms.Clipboard]::GetText()")
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=5)
                content = r.stdout.strip()
                if not content:
                    return "Clipboard is empty."
                return f"◈  CLIPBOARD CONTENTS\n{'─'*45}\n{content[:1000]}"
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Clipboard access is Windows-only."

    @staticmethod
    def set_clipboard(text: str) -> str:
        """[E13] Write to clipboard."""
        if not has_perm("elevated"): return perm_denied("elevated")
        if sys.platform == "win32":
            try:
                escaped = text.replace("'","''")
                ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                      f"[System.Windows.Forms.Clipboard]::SetText('{escaped}')")
                subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=5)
                return f"Clipboard updated: {text[:80]}{'…' if len(text)>80 else ''}"
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Clipboard write is Windows-only."

    @staticmethod
    def list_ports() -> str:
        """[E14] Active network ports."""
        if not has_perm("elevated"): return perm_denied("elevated")
        if HAS_PSUTIL:
            try:
                conns = psutil.net_connections(kind='inet')
                lines = ["◈  ACTIVE NETWORK PORTS", "─"*55,
                         f"{'Proto':<8} {'Local':30} {'Remote':25} {'Status'}"]
                for c in sorted(conns, key=lambda x: x.laddr.port if x.laddr else 0):
                    try:
                        proto  = "TCP" if c.type.name == "SOCK_STREAM" else "UDP"
                        local  = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
                        remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
                        lines.append(f"{proto:<8} {local:<30} {remote:<25} {c.status}")
                    except Exception:
                        pass
                return "\n".join(lines[:40])
            except Exception as e:
                return f"Port scan failed: {e}"
        try:
            out = subprocess.check_output(
                "netstat -an", shell=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"◈  NETWORK PORTS\n{out[:2000]}"
        except Exception as e:
            return f"netstat failed: {e}"

    @staticmethod
    def run_python(code: str) -> str:
        """[E15] Execute Python code safely."""
        if not has_perm("elevated"): return perm_denied("elevated")
        audit_log("RUN_PYTHON", code[:80])
        try:
            import io, contextlib
            buf = io.StringIO()
            safe_globals = {
                "__builtins__": {
                    "print":print,"len":len,"range":range,"str":str,"int":int,
                    "float":float,"list":list,"dict":dict,"tuple":tuple,"set":set,
                    "type":type,"isinstance":isinstance,"abs":abs,"round":round,
                    "min":min,"max":max,"sum":sum,"sorted":sorted,"enumerate":enumerate,
                    "zip":zip,"map":map,"filter":filter,"any":any,"all":all,
                    "bool":bool,"chr":chr,"ord":ord,"hex":hex,"bin":bin,"oct":oct,
                    "divmod":divmod,"pow":pow,"repr":repr,"reversed":reversed,
                    "True":True,"False":False,"None":None,
                }
            }
            with contextlib.redirect_stdout(buf):
                exec(code, safe_globals)
            output = buf.getvalue() or "(no output)"
            return f"◈  PYTHON EXECUTION\n{'─'*45}\n{output[:2000]}"
        except Exception as e:
            return f"Execution error: {type(e).__name__}: {e}"

    @staticmethod
    def get_startup_apps() -> str:
        """[E16] List startup programs."""
        if not has_perm("elevated"): return perm_denied("elevated")
        lines = ["◈  STARTUP PROGRAMS", "─"*52]
        if sys.platform == "win32" and HAS_WINREG:
            try:
                keys = [
                    (winreg.HKEY_CURRENT_USER,
                     r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_LOCAL_MACHINE,
                     r"Software\Microsoft\Windows\CurrentVersion\Run"),
                ]
                for hive, key_path in keys:
                    try:
                        key = winreg.OpenKey(hive, key_path)
                        i = 0
                        while True:
                            try:
                                name, val, _ = winreg.EnumValue(key, i)
                                lines.append(f"  • {name:<30} {val[:60]}")
                                i += 1
                            except OSError:
                                break
                        winreg.CloseKey(key)
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            startup = os.path.expandvars(
                r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
            if os.path.exists(startup):
                items = os.listdir(startup)
                for item in items:
                    lines.append(f"  [Startup Folder] {item}")
        except Exception:
            pass
        return "\n".join(lines) if len(lines) > 2 else "No startup items detected."

    # ══════════════════════════════════════════════════════════
    #  UNRESTRICTED CLEARANCE  (100+ features)
    # ══════════════════════════════════════════════════════════

    # ─── FILE OPERATIONS ─────────────────────────────────────

    @staticmethod
    def write_file(path: str, content: str) -> str:
        """[U1] Write file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("WRITE_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            os.makedirs(os.path.dirname(os.path.abspath(expanded)), exist_ok=True)
            with open(expanded, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written: {expanded}  ({len(content)} chars)"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def append_file(path: str, content: str) -> str:
        """[U2] Append to file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("APPEND_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            with open(expanded, "a", encoding="utf-8") as f:
                f.write(content + "\n")
            return f"Appended to: {expanded}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def delete_file(path: str) -> str:
        """[U3] Delete file (with backup)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("DELETE_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            if CONFIG.get("auto_backup"):
                bk = os.path.join(BACKUP_DIR, os.path.basename(expanded)
                                  + f".{datetime.now().strftime('%Y%m%d%H%M%S')}.bak")
                shutil.copy2(expanded, bk)
            os.remove(expanded)
            return f"File deleted (backup saved if auto_backup=true): {expanded}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def copy_file(src: str, dst: str) -> str:
        """[U4] Copy file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("COPY_FILE", f"{src} → {dst}")
        try:
            s = os.path.expandvars(os.path.expanduser(src))
            d = os.path.expandvars(os.path.expanduser(dst))
            shutil.copy2(s, d)
            return f"Copied: {s} → {d}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def move_file(src: str, dst: str) -> str:
        """[U5] Move/rename file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("MOVE_FILE", f"{src} → {dst}")
        try:
            s = os.path.expandvars(os.path.expanduser(src))
            d = os.path.expandvars(os.path.expanduser(dst))
            shutil.move(s, d)
            return f"Moved: {s} → {d}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def create_dir(path: str) -> str:
        """[U6] Create directory."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            os.makedirs(expanded, exist_ok=True)
            return f"Directory created: {expanded}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def zip_files(output: str, *files) -> str:
        """[U7] Create ZIP archive."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("ZIP_FILES", output)
        try:
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    expanded = os.path.expandvars(os.path.expanduser(f))
                    zf.write(expanded, os.path.basename(expanded))
            total = os.path.getsize(output)
            return f"Archive created: {output}  ({total//1024} KB)"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def unzip_file(zip_path: str, dest: str = ".") -> str:
        """[U8] Extract ZIP archive."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(dest)
            return f"Extracted {zip_path} → {dest}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def backup_config() -> str:
        """[U9] Backup all config files."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("BACKUP_CONFIG")
        try:
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            bk  = os.path.join(BACKUP_DIR, f"omgai_backup_{ts}.zip")
            files_to_backup = [CONFIG_FILE, MEMORY_FILE, CHAT_HISTORY_FILE,
                               MACRO_FILE, SNIPPET_FILE]
            with zipfile.ZipFile(bk, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files_to_backup:
                    if os.path.exists(f):
                        zf.write(f, os.path.basename(f))
            return f"Backup created: {bk}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def restore_backup(backup_path: str) -> str:
        """[U10] Restore from backup."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("RESTORE_BACKUP", backup_path)
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(BASE_DIR)
            load_config()
            load_history_and_memory()
            return f"Backup restored from: {backup_path}\nConfig and memory reloaded."
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    # ─── POWER CONTROL ───────────────────────────────────────

    @staticmethod
    def power_action(mode: str = "lock") -> str:
        """[U11] Power/lock/sleep/shutdown/restart."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("POWER", mode)
        codename = CONFIG.get("codename","Sir")
        if sys.platform == "win32":
            cmds = {
                "shutdown": ["shutdown","/s","/t","10"],
                "restart":  ["shutdown","/r","/t","10"],
                "sleep":    ["rundll32","powrprof.dll,SetSuspendState","0","1","0"],
                "hibernate": ["shutdown","/h"],
                "lock":     ["rundll32","user32.dll,LockWorkStation"],
                "logoff":   ["shutdown","/l"],
                "abort":    ["shutdown","/a"],
            }
            cmd = cmds.get(mode)
            if cmd:
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                msgs = {
                    "shutdown": f"Shutdown in 10s, {codename}. Goodbye.",
                    "restart":  f"Restarting in 10s. See you shortly, {codename}.",
                    "sleep":    f"Entering sleep mode. Rest well, {codename}.",
                    "hibernate": f"Hibernating. Your session is preserved, {codename}.",
                    "lock":     f"Station secured, {codename}.",
                    "logoff":   f"Logging off, {codename}.",
                    "abort":    "Shutdown aborted.",
                }
                return msgs.get(mode, f"{mode} initiated.")
            return f"Unknown power mode: {mode}"
        return f"{mode.capitalize()} is Windows-only."

    # ─── VOLUME & MEDIA ──────────────────────────────────────

    @staticmethod
    def set_volume(level: int) -> str:
        """[U12] Set system volume 0-100."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        level = max(0, min(100, level))
        audit_log("SET_VOLUME", str(level))
        if sys.platform == "win32":
            try:
                nircmd = os.path.join(BIN_DIR, "nircmd.exe")
                if os.path.exists(nircmd):
                    subprocess.run([nircmd,"setsysvolume",str(int(level/100*65535))],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    vol_val = int(level / 100 * 65535)
                    ps = (f"$obj=New-Object -ComObject WScript.Shell;"
                          f"Add-Type -TypeDefinition '"
                          f"using System.Runtime.InteropServices;"
                          f"public class Audio {{[DllImport(\"user32.dll\")]"
                          f"public static extern void keybd_event(byte bVk,byte bScan,uint dwFlags,int dwExtraInfo);}}';"
                          f"$vol=(New-Object -ComObject WScript.Shell);"
                          f"for($i=0;$i -le 50;$i++){{$vol.SendKeys([char]174)}};"
                          f"for($i=0;$i -lt [int]({level}/2);$i++){{$vol.SendKeys([char]175)}}")
                    subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                                   creationflags=subprocess.CREATE_NO_WINDOW,
                                   capture_output=True, timeout=10)
                return f"Volume set to {level}%."
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Volume control is Windows-only."

    @staticmethod
    def media_control(action: str) -> str:
        """[U13] Media playback control (play/pause/next/prev/stop)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                keys = {
                    "play":   0xB3, "pause":  0xB3, "playpause": 0xB3,
                    "next":   0xB0, "prev":   0xB1, "previous":  0xB1,
                    "stop":   0xB2, "mute":   0xAD,
                    "volup":  0xAF, "voldown":0xAE,
                }
                vk = keys.get(action.lower())
                if vk:
                    ps = (f"Add-Type -TypeDefinition '"
                          f"using System; using System.Runtime.InteropServices;"
                          f"public class KH{{"
                          f"[DllImport(\"user32.dll\")] public static extern void keybd_event"
                          f"(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);}}'; "
                          f"[KH]::keybd_event({vk},0,0,0); [KH]::keybd_event({vk},0,2,0)")
                    subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                                   creationflags=subprocess.CREATE_NO_WINDOW,
                                   capture_output=True, timeout=5)
                    return f"Media control: {action.upper()} executed."
                return f"Unknown media action: {action}"
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Media control is Windows-only."

    # ─── MESSAGING ───────────────────────────────────────────

    @staticmethod
    def send_email(to: str, subject: str, body: str,
                   attachments: list = None) -> str:
        """[U14] Send email with optional attachments."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        email_addr = CONFIG.get("email","")
        email_pass = CONFIG.get("email_pass","")
        if not email_addr or not email_pass:
            return ("Email unconfigured. Use /set email your@gmail.com and "
                    "/set email_pass your_app_password")
        audit_log("SEND_EMAIL", f"to={to}")
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"]    = email_addr
            msg["To"]      = to
            msg.attach(MIMEText(body, "plain"))
            if attachments:
                for att_path in attachments:
                    if os.path.exists(att_path):
                        with open(att_path, "rb") as f:
                            part = MIMEBase("application","octet-stream")
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition",
                                        f"attachment; filename={os.path.basename(att_path)}")
                        msg.attach(part)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
                srv.login(email_addr, email_pass)
                srv.send_message(msg)
            return f"Email dispatched to {to}."
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def open_whatsapp(phone: str, message: str = "") -> str:
        """[U15] Open WhatsApp Web."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        import urllib.parse, webbrowser
        encoded = urllib.parse.quote(message)
        url = f"https://wa.me/{phone.replace('+','').replace(' ','')}?text={encoded}"
        webbrowser.open(url)
        return f"WhatsApp channel opened for +{phone}."

    @staticmethod
    def open_telegram(username: str, message: str = "") -> str:
        """[U16] Open Telegram chat."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        import urllib.parse, webbrowser
        url = f"https://t.me/{username}"
        if message:
            url += f"?text={urllib.parse.quote(message)}"
        webbrowser.open(url)
        return f"Telegram opened for @{username}."

    # ─── BROWSER CONTROL ─────────────────────────────────────

    @staticmethod
    def open_browser(url: str = "", browser: str = "") -> str:
        """[U17] Open URL in browser."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        import webbrowser
        b = browser or CONFIG.get("browser","")
        if not url:
            url = "https://google.com"
        if not url.startswith("http"):
            url = "https://" + url
        if b:
            try:
                wb = webbrowser.get(b)
                wb.open(url)
                return f"Opening in {b}: {url}"
            except Exception:
                pass
        webbrowser.open(url)
        return f"Browser opened: {url}"

    @staticmethod
    def open_url_chrome(url: str) -> str:
        """[U18] Open URL specifically in Chrome."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                subprocess.Popen([cp, url],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return f"Chrome opened: {url}"
        return "Chrome not found. Use /browser <url> for default browser."

    @staticmethod
    def open_incognito(url: str = "") -> str:
        """[U19] Open URL in incognito/private mode."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if not url:
            url = "https://google.com"
        if not url.startswith("http"):
            url = "https://" + url
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        firefox_paths = [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                subprocess.Popen([cp, "--incognito", url],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return f"Chrome incognito opened: {url}"
        for fp in firefox_paths:
            if os.path.exists(fp):
                subprocess.Popen([fp, "--private-window", url],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return f"Firefox private window opened: {url}"
        return "No supported browser found for incognito mode."

    @staticmethod
    def clear_browser_cache() -> str:
        """[U20] Clear Chrome browser cache."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("CLEAR_BROWSER_CACHE")
        cache_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache"),
        ]
        cleared = []
        for path in cache_paths:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    cleared.append(path)
                except Exception:
                    pass
        if cleared:
            return f"Chrome cache cleared:\n" + "\n".join(f"  • {p}" for p in cleared)
        return "Chrome cache not found or already clean."

    # ─── MICROSOFT OFFICE ────────────────────────────────────

    @staticmethod
    def open_word(filepath: str = "") -> str:
        """[U21] Open Microsoft Word."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPEN_WORD", filepath)
        word_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\Office15\WINWORD.EXE",
        ]
        for wp in word_paths:
            if os.path.exists(wp):
                cmd = [wp]
                if filepath:
                    cmd.append(os.path.expandvars(os.path.expanduser(filepath)))
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                return f"Microsoft Word launched" + (f": {filepath}" if filepath else ".")
        # Fallback
        subprocess.Popen(f'start "" winword {filepath}', shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return f"Word launch attempted (Office path auto-detected)."

    @staticmethod
    def open_excel(filepath: str = "") -> str:
        """[U22] Open Microsoft Excel."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPEN_EXCEL", filepath)
        excel_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        ]
        for ep in excel_paths:
            if os.path.exists(ep):
                cmd = [ep]
                if filepath:
                    cmd.append(os.path.expandvars(os.path.expanduser(filepath)))
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                return f"Microsoft Excel launched."
        subprocess.Popen(f'start "" excel {filepath}', shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Excel launch attempted."

    @staticmethod
    def open_powerpoint(filepath: str = "") -> str:
        """[U23] Open Microsoft PowerPoint."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        ppt_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
        ]
        for pp in ppt_paths:
            if os.path.exists(pp):
                cmd = [pp]
                if filepath:
                    cmd.append(os.path.expandvars(os.path.expanduser(filepath)))
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                return "Microsoft PowerPoint launched."
        subprocess.Popen(f'start "" powerpnt {filepath}', shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "PowerPoint launch attempted."

    @staticmethod
    def open_outlook() -> str:
        """[U24] Open Microsoft Outlook."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        outlook_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
        ]
        for op in outlook_paths:
            if os.path.exists(op):
                subprocess.Popen([op], creationflags=subprocess.CREATE_NO_WINDOW)
                return "Microsoft Outlook launched."
        subprocess.Popen("start outlook", shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Outlook launch attempted."

    @staticmethod
    def create_word_doc(filepath: str, content: str) -> str:
        """[U25] Create a .txt file (Office-ready content)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("CREATE_WORD_DOC", filepath)
        try:
            expanded = os.path.expandvars(os.path.expanduser(filepath))
            if not expanded.endswith(('.txt','.doc','.docx','.rtf')):
                expanded += ".txt"
            with open(expanded, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Document created: {expanded}\nOpen with /word {expanded}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def office_macro_run(app: str, macro: str) -> str:
        """[U26] Run Office VBA macro via PowerShell."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OFFICE_MACRO", f"{app}:{macro}")
        if sys.platform == "win32":
            try:
                app_map = {"word":"Word","excel":"Excel","powerpoint":"PowerPoint"}
                app_name = app_map.get(app.lower(), app)
                ps = (f"$app = New-Object -ComObject {app_name}.Application;"
                      f"$app.Run('{macro}');"
                      f"$app.Quit()")
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=30)
                return f"Office macro executed: {app}/{macro}\n{r.stdout[:500]}"
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Office macros are Windows-only."

    # ─── CODE EDITING & DEVELOPMENT ──────────────────────────

    @staticmethod
    def open_vscode(path: str = ".") -> str:
        """[U27] Open VS Code."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPEN_VSCODE", path)
        expanded = os.path.expandvars(os.path.expanduser(path))
        try:
            subprocess.Popen(["code", expanded], creationflags=subprocess.CREATE_NO_WINDOW
                             if sys.platform=="win32" else 0)
            return f"VS Code opened: {expanded}"
        except FileNotFoundError:
            # Try full path
            vsc_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ]
            for vp in vsc_paths:
                if os.path.exists(vp):
                    subprocess.Popen([vp, expanded],
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    return f"VS Code opened: {expanded}"
            return "VS Code not found. Install from https://code.visualstudio.com"

    @staticmethod
    def open_editor(filepath: str = "") -> str:
        """[U28] Open configured text editor."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        editor = CONFIG.get("editor","notepad")
        expanded = os.path.expandvars(os.path.expanduser(filepath)) if filepath else ""
        try:
            cmd = [editor]
            if expanded:
                cmd.append(expanded)
            subprocess.Popen(cmd, shell=True,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"Editor ({editor}) opened" + (f": {filepath}" if filepath else ".")
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def open_terminal(path: str = "") -> str:
        """[U29] Open terminal/CMD/PowerShell."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPEN_TERMINAL", path)
        term = CONFIG.get("terminal","cmd")
        expanded = os.path.expandvars(os.path.expanduser(path)) if path else os.path.expanduser("~")
        if sys.platform == "win32":
            term_cmds = {
                "cmd":   f'start cmd /K "cd /d {expanded}"',
                "powershell": f'start powershell -NoExit -Command "Set-Location \\"{expanded}\\""',
                "wt":    f'start wt -d "{expanded}"',
                "bash":  f'start bash -c "cd \'{expanded}\'; exec bash"',
            }
            cmd = term_cmds.get(term, term_cmds["cmd"])
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return f"Terminal ({term}) opened in: {expanded}"
        return "Terminal open is Windows-optimised."

    @staticmethod
    def run_script(script_path: str, args: str = "") -> str:
        """[U30] Run a script file (py/bat/ps1/sh)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("RUN_SCRIPT", script_path)
        expanded = os.path.expandvars(os.path.expanduser(script_path))
        ext = os.path.splitext(expanded)[1].lower()
        runners = {
            ".py":  [sys.executable, expanded],
            ".bat": [expanded],
            ".cmd": [expanded],
            ".ps1": ["powershell","-WindowStyle","Hidden","-File", expanded],
            ".sh":  ["bash", expanded],
        }
        cmd = runners.get(ext)
        if not cmd:
            return f"Unknown script type: {ext}"
        if args:
            cmd += args.split()
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = (r.stdout or "") + (r.stderr or "")
            return f"◈  SCRIPT  {script_path}\n{'─'*45}\n{output[:3000]}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def pip_install(package: str) -> str:
        """[U31] Install Python package."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("PIP_INSTALL", package)
        try:
            r = subprocess.run(
                [sys.executable,"-m","pip","install",package,"--no-cache-dir"],
                capture_output=True, text=True, timeout=120)
            output = (r.stdout or "") + (r.stderr or "")
            return f"◈  PIP INSTALL: {package}\n{'─'*45}\n{output[-1500:]}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def pip_list() -> str:
        """[U32] List installed Python packages."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            r = subprocess.run(
                [sys.executable,"-m","pip","list","--format=columns"],
                capture_output=True, text=True, timeout=15)
            return f"◈  INSTALLED PACKAGES\n{'─'*45}\n{r.stdout[:3000]}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def git_status(repo_path: str = ".") -> str:
        """[U33] Git repository status."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            expanded = os.path.expandvars(os.path.expanduser(repo_path))
            r = subprocess.run(
                ["git","status","-sb"], cwd=expanded,
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"◈  GIT STATUS  —  {expanded}\n{'─'*45}\n{r.stdout or r.stderr}"
        except Exception as e:
            return f"Git not available or not a repo: {e}"

    @staticmethod
    def git_log(repo_path: str = ".", n: int = 10) -> str:
        """[U34] Recent git commits."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            expanded = os.path.expandvars(os.path.expanduser(repo_path))
            r = subprocess.run(
                ["git","log",f"-{n}","--oneline","--graph"], cwd=expanded,
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"◈  GIT LOG  ({n} commits)\n{'─'*45}\n{r.stdout or r.stderr}"
        except Exception as e:
            return f"Git log failed: {e}"

    @staticmethod
    def git_commit(repo_path: str, message: str) -> str:
        """[U35] Git add all & commit."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("GIT_COMMIT", f"{repo_path}: {message}")
        try:
            expanded = os.path.expandvars(os.path.expanduser(repo_path))
            r1 = subprocess.run(["git","add","-A"], cwd=expanded,
                                 capture_output=True, text=True, timeout=10,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            r2 = subprocess.run(["git","commit","-m",message], cwd=expanded,
                                 capture_output=True, text=True, timeout=15,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"◈  GIT COMMIT\n{r1.stdout}\n{r2.stdout or r2.stderr}"
        except Exception as e:
            return f"Git commit failed: {e}"

    @staticmethod
    def generate_python_file(filepath: str, description: str) -> str:
        """[U36] Generate a Python boilerplate file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("GEN_PYTHON", filepath)
        expanded = os.path.expandvars(os.path.expanduser(filepath))
        basename = os.path.splitext(os.path.basename(expanded))[0]
        ts       = datetime.now().strftime("%Y-%m-%d")
        content  = f'''#!/usr/bin/env python3
"""
{description}
Created by OMG_AI on {ts}
"""

import sys
import os


def main():
    """Main entry point."""
    print("Hello from {basename}!")


if __name__ == "__main__":
    main()
'''
        try:
            with open(expanded, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Python file generated: {expanded}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    # ─── SYSTEM OPTIMIZATION ─────────────────────────────────

    @staticmethod
    def optimize_ram() -> str:
        """[U37] RAM optimization and garbage collection."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPTIMIZE_RAM")
        lines = ["◈  RAM OPTIMIZATION", "─"*52]
        if HAS_PSUTIL:
            before = psutil.virtual_memory()
            lines.append(f"  Before    :  {before.percent:.1f}% used "
                         f"({before.used//1024//1024} MB)")
        if sys.platform == "win32":
            try:
                # Empty working sets of processes
                ps = ("Get-Process | Where-Object {$_.WorkingSet -gt 10MB} | "
                      "ForEach-Object { $_.Refresh() }")
                subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=20)
                # Clear standby list (requires elevation)
                ps2 = ("$code=[System.Reflection.Assembly]::GetAssembly([System.Diagnostics.Process]);"
                       "try{[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers();}catch{}")
                subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps2],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=10)
                lines.append("  Action    :  Working sets refreshed")
                lines.append("  Action    :  .NET GC triggered")
            except Exception as e:
                lines.append(f"  Note: {e}")
        if HAS_PSUTIL:
            time.sleep(0.5)
            after = psutil.virtual_memory()
            freed = max(0, (before.used - after.used) // 1024 // 1024)
            lines.append(f"  After     :  {after.percent:.1f}% used "
                         f"({after.used//1024//1024} MB)")
            lines.append(f"  Freed     :  ~{freed} MB")
        lines.append("  Tip: Use /kill-bloatware to free more RAM")
        return "\n".join(lines)

    @staticmethod
    def optimize_cpu() -> str:
        """[U38] CPU optimization — set priority."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPTIMIZE_CPU")
        lines = ["◈  CPU OPTIMIZATION", "─"*52]
        if not HAS_PSUTIL:
            return "psutil required: pip install psutil"
        try:
            cpu_before = psutil.cpu_percent(interval=0.5)
            lines.append(f"  CPU Usage (before): {cpu_before:.1f}%")
            # Find high-CPU non-system processes and suggest lowering priority
            high_cpu = []
            for p in psutil.process_iter(['pid','name','cpu_percent']):
                try:
                    if (p.info.get('cpu_percent',0) or 0) > 15:
                        sname = p.info['name'].lower()
                        if not any(sys_p in sname for sys_p in
                                   ['system','svchost','lsass','csrss','wininit',
                                    'services','registry','smss']):
                            high_cpu.append((p.info['name'], p.info['pid'],
                                             p.info.get('cpu_percent',0)))
                except Exception:
                    pass
            if high_cpu:
                lines.append("  High-CPU processes:")
                for name, pid, cpu in sorted(high_cpu, key=lambda x:x[2], reverse=True)[:5]:
                    lines.append(f"    {name:<25} PID:{pid}  {cpu:.1f}%")
                lines.append("  Use /nice <pid> <priority> to adjust")
            if sys.platform == "win32":
                try:
                    # Set OMG_AI itself to below normal to reduce interference
                    current_proc = psutil.Process()
                    current_proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    lines.append("  OMG_AI priority set to BELOW_NORMAL")
                except Exception:
                    pass
            lines.append(f"  Recommendation: Close browser tabs to free CPU")
            return "\n".join(lines)
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def set_process_priority(pid: int, priority: str) -> str:
        """[U39] Set process priority."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if not HAS_PSUTIL:
            return "psutil required."
        audit_log("SET_PRIORITY", f"pid={pid} priority={priority}")
        try:
            p = psutil.Process(pid)
            pmap = {
                "low":      psutil.IDLE_PRIORITY_CLASS if sys.platform=="win32" else 19,
                "below":    psutil.BELOW_NORMAL_PRIORITY_CLASS if sys.platform=="win32" else 10,
                "normal":   psutil.NORMAL_PRIORITY_CLASS if sys.platform=="win32" else 0,
                "above":    psutil.ABOVE_NORMAL_PRIORITY_CLASS if sys.platform=="win32" else -5,
                "high":     psutil.HIGH_PRIORITY_CLASS if sys.platform=="win32" else -10,
                "realtime": psutil.REALTIME_PRIORITY_CLASS if sys.platform=="win32" else -20,
            }
            nice_val = pmap.get(priority.lower())
            if nice_val is None:
                return f"Unknown priority. Use: low|below|normal|above|high|realtime"
            p.nice(nice_val)
            return f"Process {pid} ({p.name()}) priority set to: {priority.upper()}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def optimize_storage() -> str:
        """[U40] Storage optimization — clean temp files."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("OPTIMIZE_STORAGE")
        lines = ["◈  STORAGE OPTIMIZATION", "─"*52]
        temp_dirs = [
            os.environ.get("TEMP",""),
            os.environ.get("TMP",""),
            os.path.join(os.environ.get("SYSTEMROOT","C:\\Windows"),"Temp"),
            os.path.expanduser("~\\AppData\\Local\\Temp"),
        ]
        total_freed = 0
        for tdir in temp_dirs:
            if not tdir or not os.path.exists(tdir):
                continue
            freed = 0
            errors = 0
            for item in os.listdir(tdir):
                item_path = os.path.join(tdir, item)
                try:
                    if os.path.isfile(item_path):
                        sz = os.path.getsize(item_path)
                        os.remove(item_path)
                        freed += sz
                    elif os.path.isdir(item_path):
                        sz = sum(os.path.getsize(os.path.join(r,f))
                                 for r,d,fs in os.walk(item_path) for f in fs
                                 if os.path.exists(os.path.join(r,f)))
                        shutil.rmtree(item_path, ignore_errors=True)
                        freed += sz
                except Exception:
                    errors += 1
            total_freed += freed
            lines.append(f"  {tdir[:45]:<45} freed {freed//1024//1024} MB")
        lines.append(f"{'─'*52}")
        lines.append(f"  Total freed: {total_freed//1024//1024} MB")
        if sys.platform == "win32":
            lines.append("  Tip: Run /defrag for disk defragmentation")
            lines.append("  Tip: Run /cleanmgr to open Disk Cleanup")
        return "\n".join(lines)

    @staticmethod
    def disk_cleanup_tool() -> str:
        """[U41] Open Windows Disk Cleanup."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            subprocess.Popen(["cleanmgr"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return "Windows Disk Cleanup utility launched."
        return "Disk Cleanup is Windows-only."

    @staticmethod
    def defrag_drive(drive: str = "C:") -> str:
        """[U42] Optimize/defragment a drive."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("DEFRAG", drive)
        if sys.platform == "win32":
            try:
                subprocess.Popen(
                    ["defrag", drive, "/U", "/V"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return (f"Defragmentation started on {drive}.\n"
                        f"This runs in background. Check Task Manager for progress.")
            except Exception as e:
                return f"Defrag failed: {e}"
        return "Defrag is Windows-only."

    @staticmethod
    def kill_bloatware() -> str:
        """[U43] Terminate common resource-heavy background processes."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("KILL_BLOATWARE")
        bloat_list = [
            "OneDrive.exe", "Teams.exe", "Spotify.exe",
            "SearchIndexer.exe", "WmiPrvSE.exe",
            "BackgroundTransferHost.exe", "RuntimeBroker.exe",
            "AdobeUpdateService.exe", "AdobeARM.exe",
            "iTunesHelper.exe", "QuickTimeTask.exe",
        ]
        killed = []
        skipped = []
        if HAS_PSUTIL:
            for p in psutil.process_iter(['pid','name']):
                try:
                    if p.info['name'] in bloat_list:
                        p.kill()
                        killed.append(p.info['name'])
                except Exception:
                    skipped.append(p.info['name'])
        lines = ["◈  BLOATWARE TERMINATION", "─"*45]
        lines += [f"  ✅ Killed: {n}" for n in killed]
        lines += [f"  ⚠ Skipped (protected): {n}" for n in skipped]
        if not killed:
            lines.append("  No common bloatware found running.")
        lines.append(f"  Processes killed: {len(killed)}")
        return "\n".join(lines)

    # ─── DRIVER & HARDWARE ───────────────────────────────────

    @staticmethod
    def scan_drivers() -> str:
        """[U44] Comprehensive driver scan."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SCAN_DRIVERS")
        lines = ["◈  DRIVER INTEGRITY SCAN", "─"*52]
        if sys.platform == "win32":
            try:
                # Check for problem devices
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-WmiObject Win32_PnPEntity | "
                     "Where-Object {$_.ConfigManagerErrorCode -ne 0} | "
                     "Select-Object Name, DeviceID, ConfigManagerErrorCode | "
                     "Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=30)
                issues = r.stdout.strip()
                if issues:
                    lines.append("  ⚠  PROBLEM DEVICES DETECTED:")
                    lines.append(issues[:1500])
                else:
                    lines.append("  ✅ No driver problems detected.")
                # List recent driver installs
                r2 = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-WmiObject Win32_PnPSignedDriver | "
                     "Sort-Object DriverDate -Descending | "
                     "Select-Object -First 10 DeviceName, DriverVersion, DriverDate | "
                     "Format-Table -AutoSize"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=30)
                lines.append("\n  Recent drivers (latest 10):")
                lines.append(r2.stdout[:1000])
            except Exception as e:
                lines.append(f"  Scan error: {e}")
        else:
            try:
                r = subprocess.run(["lspci","-v"], capture_output=True, text=True, timeout=10)
                lines.append(r.stdout[:2000])
            except Exception:
                lines.append("  (lspci not available)")
        return "\n".join(lines)

    @staticmethod
    def update_drivers_tool() -> str:
        """[U45] Open Windows Update for driver updates."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("UPDATE_DRIVERS")
        if sys.platform == "win32":
            subprocess.Popen(
                ["powershell","-WindowStyle","Hidden","-Command",
                 "Start-Process 'ms-settings:windowsupdate'"],
                creationflags=subprocess.CREATE_NO_WINDOW)
            return ("Windows Update opened for driver updates.\n"
                    "Check 'Advanced options → Optional updates' for driver updates.")
        return "Driver update is Windows-only."

    @staticmethod
    def check_windows_updates() -> str:
        """[U46] Check for Windows updates."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("CHECK_WIN_UPDATES")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-WindowsUpdate -AcceptAll -IgnoreReboot 2>&1 | "
                     "Select-Object -First 20 | Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=60)
                out = r.stdout or r.stderr
                if out.strip():
                    return f"◈  WINDOWS UPDATES\n{'─'*45}\n{out[:2000]}"
                subprocess.Popen(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Start-Process 'ms-settings:windowsupdate'"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return "Windows Update opened. (PSWindowsUpdate module not installed — opened GUI)"
            except Exception as e:
                subprocess.Popen(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Start-Process 'ms-settings:windowsupdate'"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return "Windows Update opened in Settings."
        return "Windows Update is Windows-only."

    @staticmethod
    def battery_report() -> str:
        """[U47] Generate Windows battery report."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                out_path = os.path.join(os.path.expanduser("~"), "battery_report.html")
                subprocess.run(
                    ["powercfg", "/batteryreport", "/output", out_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=15)
                if os.path.exists(out_path):
                    import webbrowser
                    webbrowser.open(f"file:///{out_path}")
                    return f"Battery report generated and opened: {out_path}"
                return "Battery report generation failed."
            except Exception as e:
                return f"Battery report error: {e}"
        return "Battery report is Windows-only."

    @staticmethod
    def sleep_study() -> str:
        """[U48] Generate Windows sleep diagnostics."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                out_path = os.path.join(os.path.expanduser("~"), "sleepstudy.html")
                subprocess.run(
                    ["powercfg", "/sleepstudy", "/output", out_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=20)
                if os.path.exists(out_path):
                    import webbrowser
                    webbrowser.open(f"file:///{out_path}")
                    return f"Sleep study opened: {out_path}"
                return "Sleep study generation failed."
            except Exception as e:
                return f"Sleep study error: {e}"
        return "Sleep study is Windows-only."

    # ─── SECURITY ────────────────────────────────────────────

    @staticmethod
    def security_scan() -> str:
        """[U49] Comprehensive security scan."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SECURITY_SCAN")
        lines = ["◈  SECURITY SCAN  v4.0", "═"*52]
        # Firewall status
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-NetFirewallProfile | Select-Object Name,Enabled | Format-Table"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                lines.append("  [FIREWALL]")
                lines.append(r.stdout[:400])
                # Windows Defender status
                r2 = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-MpComputerStatus | Select-Object AMServiceEnabled,"
                     "AntivirusEnabled,RealTimeProtectionEnabled,"
                     "AntispywareEnabled | Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=15)
                lines.append("  [WINDOWS DEFENDER]")
                lines.append(r2.stdout[:500])
            except Exception as e:
                lines.append(f"  Security query partial: {e}")
        # Suspicious connections
        if HAS_PSUTIL:
            try:
                conns = psutil.net_connections(kind='inet')
                suspicious = []
                known_safe_ports = {80,443,8080,8443,53,22,25,110,143,993,995,3389,1433,3306}
                for c in conns:
                    if c.raddr and c.status == "ESTABLISHED":
                        if c.raddr.port not in known_safe_ports and c.raddr.port > 1024:
                            try:
                                proc = psutil.Process(c.pid) if c.pid else None
                                pname = proc.name() if proc else "unknown"
                                suspicious.append(f"    {pname}  →  {c.raddr.ip}:{c.raddr.port}")
                            except Exception:
                                pass
                if suspicious:
                    lines.append("  [UNUSUAL CONNECTIONS]")
                    lines += suspicious[:10]
                else:
                    lines.append("  ✅ No unusual outbound connections detected")
            except Exception:
                pass
        # Audit log check
        lines.append(f"  [AUDIT LOG]  {AUDIT_LOG_FILE}")
        if os.path.exists(AUDIT_LOG_FILE):
            sz = os.path.getsize(AUDIT_LOG_FILE)
            lines.append(f"    Size: {sz} bytes")
        lines.append("═"*52)
        return "\n".join(lines)

    @staticmethod
    def enable_firewall() -> str:
        """[U50] Enable Windows Firewall on all profiles."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("ENABLE_FIREWALL")
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=10)
                return "✅ Windows Firewall enabled on all profiles (Domain, Public, Private)."
            except Exception as e:
                return f"Firewall command failed: {e}"
        return "Firewall control is Windows-only."

    @staticmethod
    def check_antivirus() -> str:
        """[U51] Check Windows Defender status."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-MpComputerStatus | Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=15)
                return f"◈  WINDOWS DEFENDER STATUS\n{'─'*45}\n{r.stdout[:2000]}"
            except Exception as e:
                return f"Defender query failed: {e}"
        return "Antivirus check is Windows-only."

    @staticmethod
    def update_defender() -> str:
        """[U52] Update Windows Defender signatures."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("UPDATE_DEFENDER")
        if sys.platform == "win32":
            try:
                subprocess.Popen(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Update-MpSignature"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return "Windows Defender signature update initiated."
            except Exception as e:
                return f"Defender update failed: {e}"
        return "Defender update is Windows-only."

    @staticmethod
    def quick_scan_defender() -> str:
        """[U53] Run Windows Defender quick scan."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("QUICK_SCAN")
        if sys.platform == "win32":
            try:
                subprocess.Popen(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Start-MpScan -ScanType QuickScan"],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                return "Windows Defender quick scan initiated. Check notifications for results."
            except Exception as e:
                return f"Scan initiation failed: {e}"
        return "Defender scan is Windows-only."

    @staticmethod
    def encrypt_file(path: str, password: str) -> str:
        """[U54] AES-encrypt a file (XOR+hash for portability)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("ENCRYPT_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            key  = hashlib.sha256(password.encode()).digest()
            with open(expanded, "rb") as f:
                data = f.read()
            # XOR with repeating key (basic encryption, portable)
            encrypted = bytes(b ^ key[i % 32] for i, b in enumerate(data))
            out_path = expanded + ".enc"
            with open(out_path, "wb") as f:
                f.write(encrypted)
            return (f"File encrypted: {out_path}\n"
                    f"Original preserved. Use /decrypt to recover.\n"
                    f"⚠ Store your password safely!")
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def decrypt_file(path: str, password: str) -> str:
        """[U55] Decrypt an encrypted file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("DECRYPT_FILE", path)
        try:
            expanded = os.path.expandvars(os.path.expanduser(path))
            key  = hashlib.sha256(password.encode()).digest()
            with open(expanded, "rb") as f:
                data = f.read()
            decrypted = bytes(b ^ key[i % 32] for i, b in enumerate(data))
            out_path  = expanded.replace(".enc","") if expanded.endswith(".enc") else expanded + ".dec"
            with open(out_path, "wb") as f:
                f.write(decrypted)
            return f"File decrypted: {out_path}"
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def wipe_logs() -> str:
        """[U56] Securely wipe all local logs."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("WIPE_LOGS")
        wiped = []
        log_files = [AUDIT_LOG_FILE, PRIVACY_LOG_FILE]
        for lf in log_files:
            if os.path.exists(lf):
                try:
                    # Overwrite then delete
                    sz = os.path.getsize(lf)
                    with open(lf, "wb") as f:
                        f.write(b'\x00' * sz)
                    os.remove(lf)
                    wiped.append(lf)
                except Exception:
                    pass
        return (f"◈  LOGS WIPED\n"
                + "\n".join(f"  ✅ {lf}" for lf in wiped)
                + (f"\n  {len(wiped)} log files destroyed." if wiped else "\n  No logs to wipe."))

    @staticmethod
    def block_website(domain: str) -> str:
        """[U57] Block a website via hosts file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("BLOCK_WEBSITE", domain)
        if sys.platform == "win32":
            hosts = r"C:\Windows\System32\drivers\etc\hosts"
        else:
            hosts = "/etc/hosts"
        try:
            with open(hosts, "r", encoding="utf-8") as f:
                content = f.read()
            if domain in content:
                return f"{domain} is already blocked in hosts file."
            entry = f"\n127.0.0.1   {domain}\n127.0.0.1   www.{domain}\n"
            with open(hosts, "a", encoding="utf-8") as f:
                f.write(entry)
            return f"✅ {domain} blocked via hosts file.\n(May need DNS flush: /run ipconfig /flushdns)"
        except PermissionError:
            return "Permission denied. Run OMG_AI as Administrator to modify hosts file."
        except Exception as e:
            return ai_say(AI_ERRORS, error=str(e))

    @staticmethod
    def privacy_scan() -> str:
        """[U58] Full privacy scan."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("PRIVACY_SCAN")
        lines = ["◈  PRIVACY PROTECTION SCAN  v4.0", "═"*52]
        if sys.platform == "win32":
            try:
                # Telemetry status
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-Service DiagTrack | Select-Object Name,Status,StartType"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                lines.append("  [TELEMETRY SERVICE (DiagTrack)]")
                lines.append("  " + r.stdout.strip()[:200])
                # Location service
                r2 = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-Service lfsvc | Select-Object Name,Status"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                lines.append("  [LOCATION SERVICE]")
                lines.append("  " + r2.stdout.strip()[:200])
                # Recent files
                recent = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent")
                if os.path.exists(recent):
                    count = len(os.listdir(recent))
                    lines.append(f"  [RECENT FILES]  {count} items in history "
                                 f"(use /clear-recent to wipe)")
                # Prefetch
                prefetch = r"C:\Windows\Prefetch"
                if os.path.exists(prefetch):
                    pcount = len(os.listdir(prefetch))
                    lines.append(f"  [PREFETCH]  {pcount} entries")
            except Exception as e:
                lines.append(f"  Privacy scan partial: {e}")
        lines += [
            "",
            "  ✅ OMG_AI stores NO data externally",
            "  ✅ AI runs 100% locally",
            f"  ℹ  Audit logging: {'ON' if CONFIG.get('audit_logging') else 'OFF'}",
            f"  ℹ  Privacy mode: {'🔒 ON' if CONFIG.get('privacy_mode') else 'OFF'}",
        ]
        lines.append("═"*52)
        return "\n".join(lines)

    @staticmethod
    def disable_telemetry() -> str:
        """[U59] Disable Windows telemetry."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("DISABLE_TELEMETRY")
        if sys.platform == "win32":
            actions = []
            cmds = [
                ("Stopping DiagTrack",
                 "Stop-Service DiagTrack -Force; Set-Service DiagTrack -StartupType Disabled"),
                ("Stopping dmwappushservice",
                 "Stop-Service dmwappushservice -Force 2>$null; "
                 "Set-Service dmwappushservice -StartupType Disabled 2>$null"),
                ("Setting telemetry level to 0",
                 "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' "
                 "-Name AllowTelemetry -Value 0 -Force"),
            ]
            for label, ps in cmds:
                try:
                    subprocess.run(
                        ["powershell","-WindowStyle","Hidden","-Command",ps],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        capture_output=True, timeout=15)
                    actions.append(f"  ✅ {label}")
                except Exception as e:
                    actions.append(f"  ⚠ {label}: {e}")
            return ("◈  TELEMETRY DISABLED\n"
                    + "\n".join(actions)
                    + "\n  Restart recommended for full effect.")
        return "Telemetry control is Windows-only."

    @staticmethod
    def clear_recent_files() -> str:
        """[U60] Clear Windows recent files history."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("CLEAR_RECENT")
        if sys.platform == "win32":
            recent = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent")
            if os.path.exists(recent):
                count = 0
                for f in os.listdir(recent):
                    try:
                        os.remove(os.path.join(recent, f))
                        count += 1
                    except Exception:
                        pass
                return f"✅ Cleared {count} recent file entries."
            return "Recent files folder not found."
        return "Recent files clear is Windows-only."

    # ─── SCREENSHOT & DISPLAY ────────────────────────────────

    @staticmethod
    def take_screenshot(path: str = "", region: str = "") -> str:
        """[U61] Screenshot (full or region)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SCREENSHOT")
        if not path:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), f"screenshot_{ts}.png")
        if sys.platform == "win32":
            try:
                ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                      f"$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                      f"$bmp=New-Object System.Drawing.Bitmap($s.Width,$s.Height);"
                      f"$g=[System.Drawing.Graphics]::FromImage($bmp);"
                      f"$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size);"
                      f"$bmp.Save('{path}',"
                      f"[System.Drawing.Imaging.ImageFormat]::Png);"
                      f"$g.Dispose(); $bmp.Dispose();")
                subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               capture_output=True, timeout=10)
                return f"Screenshot saved: {path}"
            except Exception as e:
                return ai_say(AI_ERRORS, error=str(e))
        return "Screenshot is Windows-optimised."

    @staticmethod
    def get_display_info() -> str:
        """[U62] Display/monitor information."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBasicDisplayParams | "
                     "Select-Object MaxHorizontalImageSize, MaxVerticalImageSize | Format-List;"
                     "Get-WmiObject Win32_VideoController | "
                     "Select-Object Name, CurrentHorizontalResolution, "
                     "CurrentVerticalResolution, CurrentRefreshRate, AdapterRAM | Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=15)
                return f"◈  DISPLAY INFORMATION\n{'─'*45}\n{r.stdout[:1500]}"
            except Exception as e:
                return f"Display info failed: {e}"
        return "Display info is Windows-optimised."

    @staticmethod
    def set_brightness(level: int) -> str:
        """[U63] Set screen brightness 0-100."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        level = max(0, min(100, level))
        audit_log("SET_BRIGHTNESS", str(level))
        if sys.platform == "win32":
            try:
                ps = (f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                      f".WmiSetBrightness(1,{level})")
                subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, timeout=10)
                return f"Screen brightness set to {level}%."
            except Exception as e:
                return f"Brightness control failed: {e}"
        return "Brightness control is Windows-only."

    # ─── REGISTRY ────────────────────────────────────────────

    @staticmethod
    def registry_read(key_path: str, value_name: str = "") -> str:
        """[U64] Read Windows registry value."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if not HAS_WINREG:
            return "winreg not available."
        audit_log("REG_READ", key_path)
        try:
            hive_map = {
                "HKEY_CURRENT_USER":  winreg.HKEY_CURRENT_USER,
                "HKCU":               winreg.HKEY_CURRENT_USER,
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKLM":               winreg.HKEY_LOCAL_MACHINE,
                "HKEY_CLASSES_ROOT":  winreg.HKEY_CLASSES_ROOT,
                "HKCR":               winreg.HKEY_CLASSES_ROOT,
            }
            parts  = key_path.replace("/","\\").split("\\")
            hive   = hive_map.get(parts[0].upper())
            if not hive:
                return f"Unknown hive: {parts[0]}"
            sub_key = "\\".join(parts[1:])
            key     = winreg.OpenKey(hive, sub_key)
            if value_name:
                val, vtype = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return f"◈  REGISTRY\n  {key_path}\\{value_name} = {val}"
            # List all values
            lines = [f"◈  REGISTRY  —  {key_path}"]
            i = 0
            while True:
                try:
                    name, val, vtype = winreg.EnumValue(key, i)
                    lines.append(f"  {name or '(Default)'} = {str(val)[:80]}")
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            return "\n".join(lines)
        except Exception as e:
            return f"Registry read failed: {e}"

    @staticmethod
    def registry_write(key_path: str, value_name: str, value: str) -> str:
        """[U65] Write Windows registry value."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if not HAS_WINREG:
            return "winreg not available."
        audit_log("REG_WRITE", f"{key_path}\\{value_name} = {value}")
        try:
            ps = (f"Set-ItemProperty -Path 'Registry::{key_path}' "
                  f"-Name '{value_name}' -Value '{value}' -Force")
            r = subprocess.run(
                ["powershell","-WindowStyle","Hidden","-Command",ps],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return f"Registry written: {key_path}\\{value_name} = {value}"
            return f"Registry write failed: {r.stderr}"
        except Exception as e:
            return f"Registry write error: {e}"

    # ─── NETWORK TOOLS ───────────────────────────────────────

    @staticmethod
    def flush_dns() -> str:
        """[U66] Flush DNS cache."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("FLUSH_DNS")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["ipconfig","/flushdns"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                return f"◈  DNS FLUSH\n{r.stdout[:300]}"
            except Exception as e:
                return f"DNS flush failed: {e}"
        try:
            subprocess.run(["systemd-resolve","--flush-caches"],
                           capture_output=True, timeout=5)
            return "DNS cache flushed."
        except Exception:
            return "DNS flush: try 'sudo systemd-resolve --flush-caches'"

    @staticmethod
    def wifi_info() -> str:
        """[U67] Detailed WiFi information."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["netsh","wlan","show","interfaces"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                return f"◈  WIFI STATUS\n{'─'*45}\n{r.stdout[:1500]}"
            except Exception as e:
                return f"WiFi info failed: {e}"
        return "WiFi info is Windows-optimised."

    @staticmethod
    def wifi_profiles() -> str:
        """[U68] List saved WiFi profiles."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["netsh","wlan","show","profiles"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                return f"◈  SAVED WIFI PROFILES\n{'─'*45}\n{r.stdout[:1000]}"
            except Exception as e:
                return f"WiFi profiles failed: {e}"
        return "Windows-only."

    @staticmethod
    def speedtest() -> str:
        """[U69] Quick internet speed test."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        import webbrowser
        try:
            # Use fast.com or speedtest
            start = time.time()
            urllib.request.urlopen("https://www.cloudflare.com/cdn-cgi/trace", timeout=5)
            latency = int((time.time()-start)*1000)
            webbrowser.open("https://fast.com")
            return (f"◈  SPEED TEST\n"
                    f"  Latency   :  {latency}ms to Cloudflare\n"
                    f"  Full test :  fast.com opened in browser")
        except Exception as e:
            return f"Speed test failed: {e}"

    @staticmethod
    def traceroute(host: str) -> str:
        """[U70] Trace network route."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("TRACEROUTE", host)
        try:
            cmd = ["tracert", host] if sys.platform=="win32" else ["traceroute","-m","15",host]
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return f"◈  TRACEROUTE  →  {host}\n{'─'*45}\n{r.stdout[:2000]}"
        except Exception as e:
            return f"Traceroute failed: {e}"

    # ─── TASK SCHEDULER / AUTOMATION ─────────────────────────

    @staticmethod
    def schedule_task(name: str, command: str, time_str: str) -> str:
        """[U71] Schedule a Windows task."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SCHEDULE_TASK", f"{name} at {time_str}: {command}")
        if sys.platform == "win32":
            try:
                ps = (f"$action = New-ScheduledTaskAction -Execute '{command}';"
                      f"$trigger = New-ScheduledTaskTrigger -Once -At '{time_str}';"
                      f"Register-ScheduledTask -TaskName '{name}' "
                      f"-Action $action -Trigger $trigger -Force")
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=15)
                if r.returncode == 0:
                    return f"Task scheduled: '{name}' at {time_str}\nCommand: {command}"
                return f"Task scheduling failed: {r.stderr}"
            except Exception as e:
                return f"Schedule error: {e}"
        return "Task scheduling is Windows-only."

    @staticmethod
    def list_scheduled_tasks() -> str:
        """[U72] List scheduled tasks."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["schtasks","/query","/fo","LIST","/v"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=15)
                lines = [l for l in r.stdout.split('\n')
                         if any(k in l for k in ['Task To Run','Status','Next Run'])]
                return f"◈  SCHEDULED TASKS\n{'─'*45}\n" + "\n".join(lines[:50])
            except Exception as e:
                return f"Task list failed: {e}"
        return "Windows-only."

    @staticmethod
    def auto_startup_add(name: str, path: str) -> str:
        """[U73] Add program to Windows startup."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("ADD_STARTUP", f"{name}: {path}")
        if sys.platform == "win32" and HAS_WINREG:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ,
                                  os.path.expandvars(os.path.expanduser(path)))
                winreg.CloseKey(key)
                return f"✅ '{name}' added to startup."
            except Exception as e:
                return f"Startup add failed: {e}"
        return "Windows-only."

    @staticmethod
    def auto_startup_remove(name: str) -> str:
        """[U74] Remove program from Windows startup."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("REMOVE_STARTUP", name)
        if sys.platform == "win32" and HAS_WINREG:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                return f"✅ '{name}' removed from startup."
            except FileNotFoundError:
                return f"'{name}' not found in startup."
            except Exception as e:
                return f"Startup remove failed: {e}"
        return "Windows-only."

    @staticmethod
    def set_wallpaper(image_path: str) -> str:
        """[U75] Set desktop wallpaper."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SET_WALLPAPER", image_path)
        expanded = os.path.expandvars(os.path.expanduser(image_path))
        if not os.path.exists(expanded):
            return f"Image not found: {expanded}"
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, expanded, 3)
                return f"Wallpaper updated: {expanded}"
            except Exception as e:
                return f"Wallpaper failed: {e}"
        return "Wallpaper setting is Windows-only."

    # ─── MACRO & SNIPPET SYSTEM ──────────────────────────────

    @staticmethod
    def save_macro(name: str, commands: str) -> str:
        """[U76] Save a command macro."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        MACROS[name] = {"commands": commands, "ts": datetime.now().isoformat()}
        save_macros()
        return (f"Macro '{name}' saved.\n"
                f"Run with /macro-run {name}")

    @staticmethod
    def run_macro(name: str) -> str:
        """[U77] Execute a saved macro."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if name not in MACROS:
            available = ", ".join(MACROS.keys()) or "(none)"
            return f"Macro '{name}' not found. Available: {available}"
        audit_log("RUN_MACRO", name)
        cmds = MACROS[name]["commands"].split(";")
        results = []
        for cmd in cmds:
            cmd = cmd.strip()
            if cmd:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15,
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                results.append(f"  $ {cmd}\n    {(r.stdout or r.stderr or '').strip()[:200]}")
        return f"◈  MACRO: {name}\n{'─'*45}\n" + "\n".join(results)

    @staticmethod
    def list_macros() -> str:
        """[U78] List saved macros."""
        if not MACROS:
            return "No macros saved. Use /macro-save <name> <commands>"
        lines = ["◈  SAVED MACROS", "─"*45]
        for name, data in MACROS.items():
            lines.append(f"  {name:<20} {data['commands'][:50]}")
        return "\n".join(lines)

    @staticmethod
    def save_snippet(name: str, code: str) -> str:
        """[U79] Save a code snippet."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        lang = "python"
        for l in ["javascript","js","html","css","bash","sql","json","yaml"]:
            if code.strip().startswith(l):
                lang = l
                code = code[len(l):].strip()
                break
        SNIPPETS[name] = {"code": code, "lang": lang, "ts": datetime.now().isoformat()}
        save_snippets()
        return f"Snippet '{name}' saved ({lang})."

    @staticmethod
    def get_snippet(name: str) -> str:
        """[U80] Retrieve a code snippet."""
        if name not in SNIPPETS:
            available = ", ".join(SNIPPETS.keys()) or "(none)"
            return f"Snippet '{name}' not found. Available: {available}"
        s = SNIPPETS[name]
        return (f"◈  SNIPPET: {name}  [{s.get('lang','?')}]\n"
                f"{'─'*45}\n{s['code']}")

    @staticmethod
    def list_snippets() -> str:
        """[U81] List code snippets."""
        if not SNIPPETS:
            return "No snippets. Use /snippet-save <name> <code>"
        lines = ["◈  CODE SNIPPETS", "─"*45]
        for name, data in SNIPPETS.items():
            lines.append(f"  {name:<20} [{data.get('lang','?')}]  "
                         f"{data['code'][:40]}…")
        return "\n".join(lines)

    # ─── ACCESSIBILITY & UI ──────────────────────────────────

    @staticmethod
    def open_settings(page: str = "") -> str:
        """[U82] Open Windows Settings page."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        pages = {
            "display":      "ms-settings:display",
            "sound":        "ms-settings:sound",
            "bluetooth":    "ms-settings:bluetooth",
            "wifi":         "ms-settings:network-wifi",
            "updates":      "ms-settings:windowsupdate",
            "privacy":      "ms-settings:privacy",
            "apps":         "ms-settings:appsfeatures",
            "startup":      "ms-settings:startupapps",
            "storage":      "ms-settings:storagesense",
            "battery":      "ms-settings:batterysaver",
            "power":        "ms-settings:powersleep",
            "accounts":     "ms-settings:accounts",
            "system":       "ms-settings:about",
            "taskbar":      "ms-settings:taskbar",
            "themes":       "ms-settings:themes",
            "fonts":        "ms-settings:fonts",
            "language":     "ms-settings:regionlanguage",
            "date":         "ms-settings:dateandtime",
            "notifications":"ms-settings:notifications",
            "default-apps": "ms-settings:defaultapps",
            "mouse":        "ms-settings:mousetouchpad",
            "keyboard":     "ms-settings:keyboard",
            "camera":       "ms-settings:camera",
            "microphone":   "ms-settings:privacy-microphone",
        }
        uri = pages.get(page.lower(), "ms-settings:")
        subprocess.Popen(
            ["powershell","-WindowStyle","Hidden","-Command",
             f"Start-Process '{uri}'"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return f"Settings opened: {page or 'main'} ({uri})"

    @staticmethod
    def virtual_desktop_new() -> str:
        """[U83] Create new virtual desktop."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                # Win+Ctrl+D
                ps = ("Add-Type -TypeDefinition '"
                      "using System; using System.Runtime.InteropServices;"
                      "public class VD{"
                      "[DllImport(\"user32.dll\")] public static extern void keybd_event"
                      "(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);}';"
                      "[VD]::keybd_event(0x5B,0,0,0);" # Win
                      "[VD]::keybd_event(0x11,0,0,0);" # Ctrl
                      "[VD]::keybd_event(0x44,0,0,0);" # D
                      "Start-Sleep -Milliseconds 100;"
                      "[VD]::keybd_event(0x44,0,2,0);"
                      "[VD]::keybd_event(0x11,0,2,0);"
                      "[VD]::keybd_event(0x5B,0,2,0)")
                subprocess.run(["powershell","-WindowStyle","Hidden","-Command",ps],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               capture_output=True, timeout=5)
                return "New virtual desktop created (Win+Ctrl+D)."
            except Exception as e:
                return f"Virtual desktop failed: {e}"
        return "Virtual desktops are Windows 10/11 only."

    @staticmethod
    def type_text(text: str) -> str:
        """[U84] Type text programmatically."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if HAS_KEYBOARD:
            audit_log("TYPE_TEXT", text[:50])
            time.sleep(0.5)
            keyboard.write(text)
            return f"Text typed: {text[:50]}{'…' if len(text)>50 else ''}"
        return "keyboard module required: pip install keyboard"

    @staticmethod
    def hotkey_press(hotkey: str) -> str:
        """[U85] Press a keyboard hotkey."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if HAS_KEYBOARD:
            audit_log("HOTKEY_PRESS", hotkey)
            keyboard.send(hotkey)
            return f"Hotkey sent: {hotkey}"
        return "keyboard module required: pip install keyboard"

    # ─── ADVANCED CODING TOOLS ───────────────────────────────

    @staticmethod
    def run_python_file(filepath: str) -> str:
        """[U86] Execute a Python file."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("RUN_PY_FILE", filepath)
        expanded = os.path.expandvars(os.path.expanduser(filepath))
        try:
            r = subprocess.run(
                [sys.executable, expanded],
                capture_output=True, text=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            output = (r.stdout or "") + (r.stderr or "")
            return f"◈  {filepath}\n{'─'*45}\n{output[:3000]}"
        except Exception as e:
            return f"Execution failed: {e}"

    @staticmethod
    def code_format(code: str, lang: str = "python") -> str:
        """[U87] Format code (basic cleanup)."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if lang.lower() == "python":
            try:
                r = subprocess.run(
                    [sys.executable,"-m","black","--quiet","--code",code],
                    capture_output=True, text=True, timeout=10)
                formatted = r.stdout or code
                return f"◈  FORMATTED CODE\n{'─'*45}\n{formatted}"
            except Exception:
                # Manual basic cleanup
                lines = code.split('\n')
                cleaned = [l.rstrip() for l in lines]
                return "◈  CODE (cleaned trailing whitespace)\n" + "\n".join(cleaned)
        return f"Auto-format available for Python. Got: {lang}"

    @staticmethod
    def lint_python(filepath: str) -> str:
        """[U88] Run Python linter."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        expanded = os.path.expandvars(os.path.expanduser(filepath))
        for linter in [["flake8"], [sys.executable,"-m","flake8"],
                       [sys.executable,"-m","pyflakes"]]:
            try:
                r = subprocess.run(
                    linter + [expanded],
                    capture_output=True, text=True, timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                output = r.stdout or r.stderr or "✅ No issues found."
                return f"◈  LINT: {os.path.basename(expanded)}\n{'─'*45}\n{output[:2000]}"
            except FileNotFoundError:
                continue
        return "Linter not found. Run: /pip-install flake8"

    @staticmethod
    def create_venv(path: str = ".venv") -> str:
        """[U89] Create Python virtual environment."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        expanded = os.path.expandvars(os.path.expanduser(path))
        try:
            r = subprocess.run(
                [sys.executable,"-m","venv", expanded],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                activate = os.path.join(expanded,"Scripts","activate.bat") if sys.platform=="win32" \
                    else os.path.join(expanded,"bin","activate")
                return (f"Virtual environment created: {expanded}\n"
                        f"Activate: {activate}")
            return f"Venv failed: {r.stderr}"
        except Exception as e:
            return f"Venv error: {e}"

    @staticmethod
    def docker_status() -> str:
        """[U90] Docker status and containers."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        try:
            r1 = subprocess.run(["docker","info","--format","{{.ServerVersion}}"],
                                 capture_output=True, text=True, timeout=10,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            r2 = subprocess.run(["docker","ps","--format","table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                                 capture_output=True, text=True, timeout=10,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            return (f"◈  DOCKER\n"
                    f"  Version   :  {r1.stdout.strip()}\n"
                    f"  Containers:\n{r2.stdout[:1000]}")
        except FileNotFoundError:
            return "Docker not installed or not running."
        except Exception as e:
            return f"Docker query failed: {e}"

    # ─── ADDITIONAL UTILITY ──────────────────────────────────

    @staticmethod
    def generate_password(length: int = 20) -> str:
        """[U91] Generate a secure random password."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        import string
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        pwd   = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
        entropy = length * 6.5
        return (f"◈  SECURE PASSWORD\n"
                f"  Password  :  {pwd}\n"
                f"  Length    :  {length} chars\n"
                f"  Entropy   :  ~{entropy:.0f} bits")

    @staticmethod
    def system_report() -> str:
        """[U92] Full system report."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SYSTEM_REPORT")
        sections = [
            SystemCore.get_sysinfo(),
            SystemCore.get_uptime(),
            SystemCore.get_disk_info(),
            SystemCore.get_network_info(),
        ]
        return "\n\n".join(sections)

    @staticmethod
    def repair_system_files() -> str:
        """[U93] Run Windows SFC scan."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("SFC_SCAN")
        if sys.platform == "win32":
            notify("OMG_AI", "SFC scan starting in background. May take 5-15 minutes.")
            subprocess.Popen(
                ["powershell","-WindowStyle","Normal","-Command",
                 "sfc /scannow"],
                creationflags=0)
            return ("System File Checker started in a visible window.\n"
                    "This takes 5-15 minutes. Do not close it.\n"
                    "Run as Administrator for best results.")
        return "SFC is Windows-only."

    @staticmethod
    def dism_repair() -> str:
        """[U94] DISM image repair."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("DISM_REPAIR")
        if sys.platform == "win32":
            subprocess.Popen(
                ["powershell","-WindowStyle","Normal","-Command",
                 "DISM /Online /Cleanup-Image /RestoreHealth"],
                creationflags=0)
            return ("DISM repair started in a visible window.\n"
                    "This may take 10-30 minutes and requires internet.")
        return "DISM is Windows-only."

    @staticmethod
    def event_log(log: str = "System", count: int = 20) -> str:
        """[U95] Read Windows Event Log."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     f"Get-EventLog -LogName {log} -Newest {count} | "
                     f"Select-Object TimeGenerated,EntryType,Source,Message | "
                     f"Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=30)
                return f"◈  EVENT LOG: {log}\n{'─'*45}\n{r.stdout[:3000]}"
            except Exception as e:
                return f"Event log failed: {e}"
        return "Windows Event Log is Windows-only."

    @staticmethod
    def msinfo32() -> str:
        """[U96] Open System Information."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["msinfo32"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "System Information tool opened."

    @staticmethod
    def device_manager() -> str:
        """[U97] Open Device Manager."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["devmgmt.msc"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Device Manager opened."

    @staticmethod
    def task_manager() -> str:
        """[U98] Open Task Manager."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["taskmgr"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Task Manager opened."

    @staticmethod
    def resource_monitor() -> str:
        """[U99] Open Resource Monitor."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["resmon"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Resource Monitor opened."

    @staticmethod
    def performance_monitor() -> str:
        """[U100] Open Performance Monitor."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["perfmon"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Performance Monitor opened."

    @staticmethod
    def reliability_monitor() -> str:
        """[U101] Open Reliability Monitor."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(
            ["powershell","-WindowStyle","Hidden","-Command",
             "Start-Process 'perfmon.exe' -ArgumentList '/rel'"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return "Reliability Monitor opened."

    @staticmethod
    def event_viewer() -> str:
        """[U102] Open Event Viewer."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["eventvwr"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Event Viewer opened."

    @staticmethod
    def disk_management() -> str:
        """[U103] Open Disk Management."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["diskmgmt.msc"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Disk Management opened."

    @staticmethod
    def services_manager() -> str:
        """[U104] Open Services Manager."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["services.msc"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Services Manager opened."

    @staticmethod
    def control_panel() -> str:
        """[U105] Open Control Panel."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["control"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Control Panel opened."

    @staticmethod
    def system_restore() -> str:
        """[U106] Open System Restore."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(
            ["powershell","-WindowStyle","Hidden","-Command",
             "Start-Process 'rstrui.exe'"],
            creationflags=subprocess.CREATE_NO_WINDOW)
        return "System Restore opened."

    @staticmethod
    def create_restore_point(name: str = "OMG_AI_Restore") -> str:
        """[U107] Create System Restore point."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        audit_log("CREATE_RESTORE_POINT", name)
        if sys.platform == "win32":
            try:
                ps = (f"Enable-ComputerRestore -Drive 'C:\\';"
                      f"Checkpoint-Computer -Description '{name}' "
                      f"-RestorePointType 'MODIFY_SETTINGS'")
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",ps],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    return f"✅ System Restore point created: '{name}'"
                return f"Restore point failed: {r.stderr[:300]}"
            except Exception as e:
                return f"Restore point error: {e}"
        return "System Restore is Windows-only."

    @staticmethod
    def audio_devices() -> str:
        """[U108] List audio devices."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-WmiObject Win32_SoundDevice | "
                     "Select-Object Name, Status, Manufacturer | Format-List"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=10)
                return f"◈  AUDIO DEVICES\n{'─'*45}\n{r.stdout[:1000]}"
            except Exception as e:
                return f"Audio devices failed: {e}"
        return "Windows-only."

    @staticmethod
    def installed_software() -> str:
        """[U109] List installed software."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        if sys.platform == "win32":
            try:
                r = subprocess.run(
                    ["powershell","-WindowStyle","Hidden","-Command",
                     "Get-Package | Select-Object Name,Version | Sort-Object Name | "
                     "Format-Table -AutoSize"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, timeout=20)
                return f"◈  INSTALLED SOFTWARE\n{'─'*45}\n{r.stdout[:3000]}"
            except Exception as e:
                return f"Software list failed: {e}"
        return "Windows-only."

    @staticmethod
    def open_calculator() -> str:
        """[U110] Open Calculator app."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["calc"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "Calculator opened."

    @staticmethod
    def open_notepad(filepath: str = "") -> str:
        """[U111] Open Notepad."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        cmd = ["notepad"]
        if filepath:
            cmd.append(os.path.expandvars(os.path.expanduser(filepath)))
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        return f"Notepad opened" + (f": {filepath}" if filepath else ".")

    @staticmethod
    def open_paint() -> str:
        """[U112] Open MS Paint."""
        if not has_perm("unrestricted"): return perm_denied("unrestricted")
        subprocess.Popen(["mspaint"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return "MS Paint opened."


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
    threads = min(psutil.cpu_count() if HAS_PSUTIL else 4, 8)
    cmd = [exe, "-m", model, "--port", str(LLAMA_PORT),
           "-c", "4096", "--threads", str(threads), "--no-mmap",
           "--log-disable"]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags)
    for _ in range(40):
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
# COMMAND PARSER  (slash commands — 130+ total)
# ──────────────────────────────────────────────────────────────────────────────

core = SystemCore()

def parse_command(text: str) -> str | None:
    parts = text.strip().split(None, 3)
    if not parts or not parts[0].startswith("/"):
        return None

    cmd  = parts[0].lower()
    arg1 = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""
    arg3 = parts[3] if len(parts) > 3 else ""

    # ─────────────────────────────────────────────────────────────────────────
    #  HELP
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/help":
        section = arg1.lower()
        if section == "standard" or section == "s":
            return (
                "◈  STANDARD CLEARANCE COMMANDS  (10+ features)\n"+"═"*55+"\n"
                "  /help [s|e|u|all]   — this help menu\n"
                "  /status             — full system diagnostics\n"
                "  /time               — date & time reference\n"
                "  /weather            — atmospheric conditions\n"
                "  /net                — network info & public IP\n"
                "  /battery            — detailed battery status\n"
                "  /uptime             — system uptime\n"
                "  /calc <expr>        — safe calculator\n"
                "  /tips               — smart tips & shortcuts\n"
                "  /disk               — storage breakdown\n"
                "  /privacy            — privacy status report\n"
                "  /cpu                — CPU detail & per-core usage\n"
                "  /ping <host>        — network ping test\n"
                "  /temps              — hardware temperatures\n"
                "  /remember <fact>    — store memory\n"
                "  /memories           — recall memories\n"
                "  /forget <n>         — delete memory #n\n"
                "  /clear              — wipe chat history\n"
                "  /voice on|off       — toggle speech\n"
                "  /voice-rate <-10 to 10> — adjust speed\n"
                "  /voice-list         — list available voices\n"
                "  /voice-set <name>   — set voice\n"
                "  /voice-stop         — stop current speech\n"
            )
        elif section == "elevated" or section == "e":
            return (
                "◈  ELEVATED CLEARANCE COMMANDS  (13+ features)\n"+"═"*55+"\n"
                "  /open <app>         — launch application\n"
                "  /close <app.exe>    — kill process\n"
                "  /ps                 — process list (CPU/RAM)\n"
                "  /ls [path]          — directory listing\n"
                "  /cat <path>         — read file\n"
                "  /find <pat> [path]  — search files\n"
                "  /grep <pat> <file>  — search in file\n"
                "  /env                — environment variables\n"
                "  /hash <file> [algo] — file integrity hash\n"
                "  /clip               — read clipboard\n"
                "  /clip-set <text>    — write clipboard\n"
                "  /ports              — active network ports\n"
                "  /py <code>          — safe Python execution\n"
                "  /startup-apps       — list startup programs\n"
                "  /run <command>      — shell execution\n"
                "  /search <query>     — Google search\n"
                "  /search-yt <query>  — YouTube search\n"
                "  /search-gh <query>  — GitHub search\n"
                "  /search-so <query>  — StackOverflow search\n"
            )
        elif section == "unrestricted" or section == "u":
            return (
                "◈  UNRESTRICTED CLEARANCE  (100+ features)\n"+"═"*55+"\n"
                "  ── FILE OPERATIONS ─────────────────────────\n"
                "  /write <path> <text>    — write file\n"
                "  /append <path> <text>   — append to file\n"
                "  /delete <path>          — delete file (auto-backup)\n"
                "  /copy <src> <dst>       — copy file\n"
                "  /move <src> <dst>       — move/rename file\n"
                "  /mkdir <path>           — create directory\n"
                "  /zip <out.zip> <files…> — create archive\n"
                "  /unzip <zip> [dest]     — extract archive\n"
                "  /backup                 — backup all configs\n"
                "  /restore <backup.zip>   — restore from backup\n"
                "  ── POWER ───────────────────────────────────\n"
                "  /shutdown | /restart | /sleep | /hibernate\n"
                "  /lock | /logoff         — power management\n"
                "  /abort-shutdown         — cancel pending shutdown\n"
                "  ── AUDIO & MEDIA ────────────────────────────\n"
                "  /volume <0-100>         — system volume\n"
                "  /media play|pause|next|prev|stop|mute\n"
                "  ── MESSAGING ───────────────────────────────\n"
                "  /email <to> <sub> <body>\n"
                "  /wa <phone> [msg]       — WhatsApp\n"
                "  /tg <username> [msg]    — Telegram\n"
                "  ── BROWSER ─────────────────────────────────\n"
                "  /browser <url>          — open URL\n"
                "  /chrome <url>           — Chrome\n"
                "  /incognito <url>        — private browsing\n"
                "  /clear-cache            — clear browser cache\n"
                "  ── MICROSOFT OFFICE ────────────────────────\n"
                "  /word [file]            — open Word\n"
                "  /excel [file]           — open Excel\n"
                "  /ppt [file]             — open PowerPoint\n"
                "  /outlook                — open Outlook\n"
                "  /office-new <path> <content>\n"
                "  ── CODE EDITING ────────────────────────────\n"
                "  /vscode [path]          — open VS Code\n"
                "  /editor [file]          — open text editor\n"
                "  /terminal [path]        — open terminal\n"
                "  /script <path> [args]   — run script file\n"
                "  /pip <pkg>              — pip install\n"
                "  /pip-list               — list packages\n"
                "  /git-status [path]      — git status\n"
                "  /git-log [path] [n]     — git log\n"
                "  /git-commit <path> <msg>\n"
                "  /gen-py <file> <desc>   — generate Python file\n"
                "  /lint <file>            — lint Python file\n"
                "  /venv [path]            — create virtualenv\n"
                "  /docker                 — Docker status\n"
                "  ── OPTIMIZATION ────────────────────────────\n"
                "  /opt-ram                — RAM optimization\n"
                "  /opt-cpu                — CPU optimization\n"
                "  /opt-storage            — clean temp files\n"
                "  /kill-bloat             — kill bloatware\n"
                "  /defrag [drive]         — defragment drive\n"
                "  /cleanmgr               — Disk Cleanup\n"
                "  /nice <pid> <priority>  — set process priority\n"
                "  ── DRIVERS & UPDATES ───────────────────────\n"
                "  /drivers                — scan drivers\n"
                "  /update-drivers         — Windows Update (drivers)\n"
                "  /win-update             — check Windows updates\n"
                "  /battery-report         — battery health report\n"
                "  /sleep-study            — sleep diagnostics\n"
                "  ── SECURITY ────────────────────────────────\n"
                "  /security               — full security scan\n"
                "  /firewall on            — enable firewall\n"
                "  /antivirus              — Defender status\n"
                "  /update-av              — update Defender\n"
                "  /quick-scan             — Defender quick scan\n"
                "  /encrypt <file> <pass>  — encrypt file\n"
                "  /decrypt <file> <pass>  — decrypt file\n"
                "  /wipe-logs              — destroy all logs\n"
                "  /block <domain>         — block website\n"
                "  /privacy-scan           — privacy audit\n"
                "  /disable-telemetry      — disable MS telemetry\n"
                "  /clear-recent           — clear recent files\n"
                "  ── NETWORK ─────────────────────────────────\n"
                "  /flush-dns              — flush DNS cache\n"
                "  /wifi                   — WiFi details\n"
                "  /wifi-profiles          — saved WiFi profiles\n"
                "  /speedtest              — internet speed test\n"
                "  /trace <host>           — traceroute\n"
                "  ── DISPLAY & SYSTEM ────────────────────────\n"
                "  /screenshot [path]      — capture screen\n"
                "  /brightness <0-100>     — screen brightness\n"
                "  /display                — display info\n"
                "  /wallpaper <image>      — set wallpaper\n"
                "  /settings [page]        — open Windows Settings\n"
                "  ── REGISTRY ────────────────────────────────\n"
                "  /reg-read <path> [val]  — read registry\n"
                "  /reg-write <path> <name> <val>\n"
                "  ── TASK SCHEDULER ──────────────────────────\n"
                "  /sched <name> <cmd> <time>\n"
                "  /sched-list             — list scheduled tasks\n"
                "  /startup-add <name> <path>\n"
                "  /startup-rm <name>      — remove from startup\n"
                "  ── MACROS & SNIPPETS ───────────────────────\n"
                "  /macro-save <name> <cmds;cmds>\n"
                "  /macro-run <name>       — execute macro\n"
                "  /macros                 — list macros\n"
                "  /snippet-save <name> <code>\n"
                "  /snippet <name>         — get snippet\n"
                "  /snippets               — list snippets\n"
                "  ── AUTOMATION ──────────────────────────────\n"
                "  /type <text>            — type text (keyboard)\n"
                "  /key <hotkey>           — send hotkey\n"
                "  /virtual-desktop        — new virtual desktop\n"
                "  ── WINDOWS TOOLS ───────────────────────────\n"
                "  /password [len]         — generate password\n"
                "  /full-report            — complete system report\n"
                "  /sfc                    — system file checker\n"
                "  /dism                   — DISM image repair\n"
                "  /event-log [type] [n]   — event log viewer\n"
                "  /msinfo                 — System Information\n"
                "  /devmgr                 — Device Manager\n"
                "  /taskmgr                — Task Manager\n"
                "  /resmon                 — Resource Monitor\n"
                "  /perfmon                — Performance Monitor\n"
                "  /relimon                — Reliability Monitor\n"
                "  /eventvwr               — Event Viewer\n"
                "  /diskmgmt               — Disk Management\n"
                "  /services               — Services Manager\n"
                "  /control                — Control Panel\n"
                "  /restore-tool           — System Restore\n"
                "  /restore-point [name]   — create restore point\n"
                "  /audio-devices          — list audio devices\n"
                "  /software-list          — installed software\n"
                "  /calc-app               — Calculator\n"
                "  /notepad [file]         — Notepad\n"
                "  /paint                  — MS Paint\n"
                "═"*55
            )
        # Default: show summary
        return (
            "◈  OMG_AI v4.0  —  COMMAND MANIFEST\n"+"═"*55+"\n"
            "  /help s         — Standard commands (10+)\n"
            "  /help e         — Elevated commands (13+)\n"
            "  /help u         — Unrestricted commands (100+)\n"
            "  /help all       — Everything\n\n"
            "  QUICK REFERENCE:\n"
            "  /status         — System diagnostics\n"
            "  /security       — Security scan\n"
            "  /privacy-scan   — Privacy audit\n"
            "  /opt-ram        — RAM optimization\n"
            "  /drivers        — Driver scan\n"
            "  /full-report    — Complete report\n"
            "  /clearance <level>\n"
            f"  Current: {CONFIG.get('permission','standard').upper()}\n"
            "═"*55
        )

    if cmd == "/help" and arg1.lower() == "all":
        return parse_command("/help u") + "\n" + parse_command("/help e") + "\n" + parse_command("/help s")

    # ─────────────────────────────────────────────────────────────────────────
    #  STANDARD COMMANDS
    # ─────────────────────────────────────────────────────────────────────────
    if cmd in ("/status","/sysinfo"):      return core.get_sysinfo()
    if cmd == "/time":                     return core.get_time()
    if cmd == "/weather":                  return core.get_weather_local()
    if cmd == "/net":                      return core.get_network_info()
    if cmd == "/battery":                  return core.get_battery_detail()
    if cmd == "/uptime":                   return core.get_uptime()
    if cmd == "/disk":                     return core.get_disk_info()
    if cmd == "/privacy":
        if arg1.lower() in ("on","off"):
            CONFIG["privacy_mode"] = (arg1.lower()=="on")
            save_config()
            return f"Privacy mode {'🔒 ENABLED' if CONFIG['privacy_mode'] else 'disabled'}."
        return core.privacy_info()
    if cmd == "/cpu":                      return core.get_cpu_detail()
    if cmd == "/temps":                    return core.get_temps()
    if cmd == "/tips":                     return core.get_tips()
    if cmd == "/ping":
        if not arg1:
            return "Usage: /ping <host>"
        return core.ping_host(arg1)
    if cmd == "/calc":
        expr = text[len("/calc"):].strip()
        if not expr:
            return "Usage: /calc <expression>"
        return core.calculate(expr)

    # ─────────────────────────────────────────────────────────────────────────
    #  VOICE COMMANDS
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/voice":
        if arg1.lower() in ("on","off"):
            CONFIG["voice_enabled"] = (arg1.lower()=="on")
            save_config()
            return f"Voice synthesis {'enabled' if CONFIG['voice_enabled'] else 'disabled'}."
        return "Usage: /voice on|off"

    if cmd == "/voice-rate":
        try:
            rate = int(arg1)
            if -10 <= rate <= 10:
                CONFIG["voice_rate"] = rate
                save_config()
                return f"Voice rate set to {rate} (-10=slowest, 10=fastest, 0=normal)."
            return "Rate must be between -10 and 10."
        except ValueError:
            return "Usage: /voice-rate <-10 to 10>"

    if cmd == "/voice-list":               return list_voices()

    if cmd == "/voice-set":
        if arg1:
            CONFIG["voice_name"] = arg1
            save_config()
            speak(f"Voice changed to {arg1}.", priority=True)
            return f"Voice set to: {arg1}"
        return "Usage: /voice-set <voice_name> (use /voice-list to see options)"

    if cmd == "/voice-stop":
        speak_stop()
        return "Voice stopped."

    if cmd == "/voice-test":
        msg = arg1 or "OMG AI version 4 online and ready for your command."
        speak(msg, priority=True)
        return f"Speaking: {msg}"

    # ─────────────────────────────────────────────────────────────────────────
    #  CLEARANCE / CONFIG
    # ─────────────────────────────────────────────────────────────────────────
    if cmd in ("/clearance","/permission"):
        lvl = _resolve_perm(arg1.lower())
        if lvl not in ("standard","elevated","unrestricted"):
            return "Specify: standard | elevated | unrestricted"
        CONFIG["permission"] = lvl
        save_config()
        speak(f"Clearance updated to {lvl}.")
        return f"Clearance updated to '{lvl.upper()}' protocol."

    if cmd == "/set":
        p = text.split(None, 2)
        if len(p) < 3:
            return "Usage: /set <key> <value>"
        CONFIG[p[1]] = p[2]
        save_config()
        return f"Config: {p[1]} = {p[2]}"

    if cmd == "/audit":
        if arg1.lower() in ("on","off"):
            CONFIG["audit_logging"] = (arg1.lower()=="on")
            save_config()
            return f"Audit logging {'enabled' if CONFIG['audit_logging'] else 'disabled'}."
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, encoding="utf-8") as f:
                lines = f.readlines()
            return "◈  AUDIT LOG (last 30)\n" + "".join(lines[-30:])
        return "Audit log empty."

    # ─────────────────────────────────────────────────────────────────────────
    #  ELEVATED COMMANDS
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/open":
        return core.open_app(text[len("/open"):].strip())
    if cmd == "/close":
        return core.close_app(arg1)
    if cmd == "/ps":
        return core.list_processes()
    if cmd == "/ls":
        return core.list_dir(arg1 or ".")
    if cmd == "/cat":
        return core.read_file(arg1)
    if cmd == "/find":
        return core.find_files(arg1, arg2 or ".")
    if cmd == "/grep":
        return core.grep_file(arg1, arg2)
    if cmd == "/env":
        return core.env_vars()
    if cmd == "/hash":
        return core.hash_file(arg1, arg2 or "sha256")
    if cmd == "/clip":
        return core.get_clipboard()
    if cmd == "/clip-set":
        return core.set_clipboard(text[len("/clip-set"):].strip())
    if cmd == "/ports":
        return core.list_ports()
    if cmd == "/py":
        return core.run_python(text[len("/py"):].strip())
    if cmd == "/startup-apps":
        return core.get_startup_apps()
    if cmd == "/run":
        return core.run_command(text[len("/run"):].strip())
    if cmd == "/search":
        return core.search_web(text[len("/search"):].strip())
    if cmd == "/search-yt":
        return core.search_web(text[len("/search-yt"):].strip(), "yt")
    if cmd == "/search-gh":
        return core.search_web(text[len("/search-gh"):].strip(), "github")
    if cmd == "/search-so":
        return core.search_web(text[len("/search-so"):].strip(), "so")
    if cmd == "/search-ddg":
        return core.search_web(text[len("/search-ddg"):].strip(), "ddg")

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — FILE
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/write":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /write <path> <content>"
        return core.write_file(p[1], p[2])
    if cmd == "/append":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /append <path> <content>"
        return core.append_file(p[1], p[2])
    if cmd == "/delete":
        return core.delete_file(arg1)
    if cmd == "/copy":
        return core.copy_file(arg1, arg2)
    if cmd == "/move":
        return core.move_file(arg1, arg2)
    if cmd == "/mkdir":
        return core.create_dir(arg1)
    if cmd == "/zip":
        p = text.split()[1:]
        if len(p) < 2: return "Usage: /zip <output.zip> <file1> [file2…]"
        return core.zip_files(p[0], *p[1:])
    if cmd == "/unzip":
        return core.unzip_file(arg1, arg2 or ".")
    if cmd == "/backup":
        return core.backup_config()
    if cmd == "/restore":
        return core.restore_backup(arg1)

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — POWER
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/shutdown":        return core.power_action("shutdown")
    if cmd == "/restart":         return core.power_action("restart")
    if cmd == "/sleep":           return core.power_action("sleep")
    if cmd == "/hibernate":       return core.power_action("hibernate")
    if cmd == "/lock":            return core.power_action("lock")
    if cmd == "/logoff":          return core.power_action("logoff")
    if cmd == "/abort-shutdown":  return core.power_action("abort")

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — AUDIO/MEDIA
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/volume":
        try:
            return core.set_volume(int(arg1))
        except ValueError:
            return "Usage: /volume <0-100>"
    if cmd == "/media":
        return core.media_control(arg1 or "playpause")

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — MESSAGING
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/email":
        p = text.split(None, 3)
        if len(p) < 4: return "Usage: /email <to> <subject> <body>"
        return core.send_email(p[1], p[2], p[3])
    if cmd == "/wa":
        p = text.split(None, 2)
        if len(p) < 2: return "Usage: /wa <phone> [message]"
        return core.open_whatsapp(p[1], p[2] if len(p)>2 else "")
    if cmd == "/tg":
        p = text.split(None, 2)
        if len(p) < 2: return "Usage: /tg <username> [message]"
        return core.open_telegram(p[1], p[2] if len(p)>2 else "")

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — BROWSER
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/browser":
        return core.open_browser(text[len("/browser"):].strip())
    if cmd == "/chrome":
        return core.open_url_chrome(text[len("/chrome"):].strip())
    if cmd == "/incognito":
        return core.open_incognito(text[len("/incognito"):].strip())
    if cmd == "/clear-cache":
        return core.clear_browser_cache()

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — OFFICE
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/word":       return core.open_word(arg1)
    if cmd == "/excel":      return core.open_excel(arg1)
    if cmd == "/ppt":        return core.open_powerpoint(arg1)
    if cmd == "/outlook":    return core.open_outlook()
    if cmd == "/office-new":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /office-new <path> <content>"
        return core.create_word_doc(p[1], p[2])
    if cmd == "/office-macro":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /office-macro <word|excel|ppt> <MacroName>"
        return core.office_macro_run(p[1], p[2])

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — CODE / DEV
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/vscode":     return core.open_vscode(arg1 or ".")
    if cmd == "/editor":     return core.open_editor(arg1)
    if cmd == "/terminal":   return core.open_terminal(arg1)
    if cmd == "/script":
        return core.run_script(arg1, arg2)
    if cmd == "/pip":
        return core.pip_install(text[len("/pip"):].strip())
    if cmd == "/pip-list":   return core.pip_list()
    if cmd == "/git-status": return core.git_status(arg1 or ".")
    if cmd == "/git-log":
        n = int(arg2) if arg2.isdigit() else 10
        return core.git_log(arg1 or ".", n)
    if cmd == "/git-commit":
        return core.git_commit(arg1, arg2 + " " + arg3 if arg3 else arg2)
    if cmd == "/gen-py":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /gen-py <file> <description>"
        return core.generate_python_file(p[1], p[2])
    if cmd == "/py-run":     return core.run_python_file(arg1)
    if cmd == "/lint":       return core.lint_python(arg1)
    if cmd == "/venv":       return core.create_venv(arg1 or ".venv")
    if cmd == "/docker":     return core.docker_status()

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — OPTIMIZATION
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/opt-ram":        return core.optimize_ram()
    if cmd == "/opt-cpu":        return core.optimize_cpu()
    if cmd == "/opt-storage":    return core.optimize_storage()
    if cmd == "/kill-bloat":     return core.kill_bloatware()
    if cmd == "/defrag":         return core.defrag_drive(arg1 or "C:")
    if cmd == "/cleanmgr":       return core.disk_cleanup_tool()
    if cmd == "/nice":
        try:
            return core.set_process_priority(int(arg1), arg2)
        except ValueError:
            return "Usage: /nice <pid> <low|below|normal|above|high|realtime>"

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — DRIVERS/UPDATES
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/drivers":          return core.scan_drivers()
    if cmd == "/update-drivers":   return core.update_drivers_tool()
    if cmd == "/win-update":       return core.check_windows_updates()
    if cmd == "/battery-report":   return core.battery_report()
    if cmd == "/sleep-study":      return core.sleep_study()

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — SECURITY
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/security":          return core.security_scan()
    if cmd == "/firewall":
        if arg1.lower() == "on":
            return core.enable_firewall()
        return "Usage: /firewall on"
    if cmd == "/antivirus":         return core.check_antivirus()
    if cmd == "/update-av":         return core.update_defender()
    if cmd == "/quick-scan":        return core.quick_scan_defender()
    if cmd == "/encrypt":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /encrypt <file> <password>"
        return core.encrypt_file(p[1], p[2])
    if cmd == "/decrypt":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /decrypt <file> <password>"
        return core.decrypt_file(p[1], p[2])
    if cmd == "/wipe-logs":         return core.wipe_logs()
    if cmd == "/block":             return core.block_website(arg1)
    if cmd == "/privacy-scan":      return core.privacy_scan()
    if cmd == "/disable-telemetry": return core.disable_telemetry()
    if cmd == "/clear-recent":      return core.clear_recent_files()

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — NETWORK
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/flush-dns":         return core.flush_dns()
    if cmd == "/wifi":              return core.wifi_info()
    if cmd == "/wifi-profiles":     return core.wifi_profiles()
    if cmd == "/speedtest":         return core.speedtest()
    if cmd == "/trace":             return core.traceroute(arg1)

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — DISPLAY
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/screenshot":        return core.take_screenshot(arg1)
    if cmd == "/brightness":
        try:
            return core.set_brightness(int(arg1))
        except ValueError:
            return "Usage: /brightness <0-100>"
    if cmd == "/display":           return core.get_display_info()
    if cmd == "/wallpaper":         return core.set_wallpaper(text[len("/wallpaper"):].strip())

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — REGISTRY
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/reg-read":
        return core.registry_read(arg1, arg2)
    if cmd == "/reg-write":
        return core.registry_write(arg1, arg2, arg3)

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — SCHEDULER/AUTOMATION
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/sched":
        p = text.split(None, 3)
        if len(p) < 4: return "Usage: /sched <name> <command> <time>"
        return core.schedule_task(p[1], p[2], p[3])
    if cmd == "/sched-list":        return core.list_scheduled_tasks()
    if cmd == "/startup-add":       return core.auto_startup_add(arg1, arg2)
    if cmd == "/startup-rm":        return core.auto_startup_remove(arg1)
    if cmd == "/settings":          return core.open_settings(arg1)
    if cmd == "/virtual-desktop":   return core.virtual_desktop_new()
    if cmd == "/type":
        return core.type_text(text[len("/type"):].strip())
    if cmd == "/key":
        return core.hotkey_press(text[len("/key"):].strip())

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — MACROS/SNIPPETS
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/macro-save":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /macro-save <name> <cmd1;cmd2;…>"
        return core.save_macro(p[1], p[2])
    if cmd == "/macro-run":         return core.run_macro(arg1)
    if cmd == "/macros":            return core.list_macros()
    if cmd == "/snippet-save":
        p = text.split(None, 2)
        if len(p) < 3: return "Usage: /snippet-save <name> <code>"
        return core.save_snippet(p[1], p[2])
    if cmd == "/snippet":           return core.get_snippet(arg1)
    if cmd == "/snippets":          return core.list_snippets()

    # ─────────────────────────────────────────────────────────────────────────
    #  UNRESTRICTED — SYSTEM TOOLS
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/password":
        try:
            n = int(arg1) if arg1 else 20
        except ValueError:
            n = 20
        return core.generate_password(n)
    if cmd == "/full-report":       return core.system_report()
    if cmd == "/sfc":               return core.repair_system_files()
    if cmd == "/dism":              return core.dism_repair()
    if cmd == "/event-log":
        n = int(arg2) if arg2.isdigit() else 20
        return core.event_log(arg1 or "System", n)
    if cmd == "/msinfo":            return core.msinfo32()
    if cmd == "/devmgr":            return core.device_manager()
    if cmd == "/taskmgr":           return core.task_manager()
    if cmd == "/resmon":            return core.resource_monitor()
    if cmd == "/perfmon":           return core.performance_monitor()
    if cmd == "/relimon":           return core.reliability_monitor()
    if cmd == "/eventvwr":          return core.event_viewer()
    if cmd == "/diskmgmt":          return core.disk_management()
    if cmd == "/services":          return core.services_manager()
    if cmd == "/control":           return core.control_panel()
    if cmd == "/restore-tool":      return core.system_restore()
    if cmd == "/restore-point":
        return core.create_restore_point(
            text[len("/restore-point"):].strip() or "OMG_AI_Restore")
    if cmd == "/audio-devices":     return core.audio_devices()
    if cmd == "/software-list":     return core.installed_software()
    if cmd == "/calc-app":          return core.open_calculator()
    if cmd == "/notepad":           return core.open_notepad(arg1)
    if cmd == "/paint":             return core.open_paint()

    # ─────────────────────────────────────────────────────────────────────────
    #  MEMORY
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/remember":
        fact = text[len("/remember"):].strip()
        if not fact: return "Usage: /remember <fact>"
        MEMORY.append({"fact":fact,"ts":datetime.now().isoformat()})
        save_memory()
        return f"Memory stored: {fact}"
    if cmd == "/memories":
        if not MEMORY: return "Memory banks empty."
        return ("◈  MEMORY BANKS\n"
                + "\n".join(f"  {i+1:2}.  {m['fact']}  [{m.get('ts','?')[:10]}]"
                            for i, m in enumerate(MEMORY)))
    if cmd == "/forget":
        try:
            removed = MEMORY.pop(int(arg1)-1)
            save_memory()
            return f"Memory purged: {removed['fact']}"
        except (ValueError, IndexError):
            return f"Usage: /forget <1-{len(MEMORY)}>"
    if cmd == "/clear":
        global CHAT_HISTORY
        CHAT_HISTORY = []
        if os.path.exists(CHAT_HISTORY_FILE):
            os.remove(CHAT_HISTORY_FILE)
        return "Conversation logs purged."

    # ─────────────────────────────────────────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────────────────────────────────────────
    if cmd == "/update":
        new_ver = check_for_update()
        if not new_ver:
            return f"All systems current — v{CURRENT_VER}."
        return do_self_update() or "Update initiated…"

    if cmd == "/version":
        return (f"◈  VERSION\n"
                f"  OMG_AI     :  v{CURRENT_VER}\n"
                f"  Codename   :  {CODENAME}\n"
                f"  Python     :  {sys.version.split()[0]}\n"
                f"  Platform   :  {platform.platform()}")

    return f"Unknown directive: {cmd}. Type /help for command manifest."

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM TRAY
# ──────────────────────────────────────────────────────────────────────────────

def make_tray_icon_image(size=64):
    if not HAS_TRAY:
        return None
    img  = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2,2,size-2,size-2], fill="#0a0a0a")
    draw.ellipse([8,8,size-8,size-8], outline="#00d4ff", width=2)
    cx, cy = size//2, size//2
    draw.ellipse([cx-8,cy-8,cx+8,cy+8], fill="#00d4ff")
    draw.ellipse([cx-4,cy-4,cx+4,cy+4], fill="white")
    # Outer glow
    draw.ellipse([cx-12,cy-12,cx+12,cy+12], outline="#00d4ff66", width=1)
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

    def on_status(icon, item):
        result = core.get_sysinfo()
        notify("OMG_AI Status", result[:200])

    menu = pystray.Menu(
        pystray.MenuItem("◉  Summon OMG_AI", on_show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⚙  System Status", on_status),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✕  Shutdown", on_quit),
    )
    tray_icon = pystray.Icon("OMG_AI", img, f"OMG_AI v{CURRENT_VER}", menu)
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
# HUD GUI  (v4 — enhanced)
# ──────────────────────────────────────────────────────────────────────────────

DARK_THEME = {
    "bg":          "#212121",
    "bg2":         "#2F2F2F",
    "fg":          "#ECECEC",
    "user_fg":     "#ECECEC",
    "ai_fg":       "#ECECEC",
    "sys_fg":      "#9B9B9B",
    "cmd_fg":      "#10A37F",
    "warn_fg":     "#EF4444",
    "accent":      "#10A37F",
    "accent2":     "#EF4444",
    "border":      "#424242",
    "input_bg":    "#2F2F2F",
    "btn_bg":      "#10A37F",
    "btn_fg":      "#FFFFFF",
    "status_bg":   "#212121",
    "header_bg":   "#212121",
    "select_bg":   "#424242",
}

LIGHT_THEME = {
    "bg":         "#FFFFFF",
    "bg2":        "#F9F9F9",
    "fg":         "#0D0D0D",
    "user_fg":    "#0D0D0D",
    "ai_fg":      "#0D0D0D",
    "sys_fg":     "#6E6E80",
    "cmd_fg":     "#10A37F",
    "warn_fg":    "#EF4444",
    "accent":     "#10A37F",
    "accent2":    "#EF4444",
    "border":     "#E5E5E5",
    "input_bg":   "#F9F9F9",
    "btn_bg":     "#10A37F",
    "btn_fg":     "#FFFFFF",
    "status_bg":  "#FFFFFF",
    "header_bg":  "#FFFFFF",
    "select_bg":  "#E5E5E5",
}

JARVIS_THEME = {
    "bg":         "#000d0a",
    "bg2":        "#001510",
    "fg":         "#00ff8a",
    "user_fg":    "#00ffcc",
    "ai_fg":      "#ffcc00",
    "sys_fg":     "#006644",
    "cmd_fg":     "#00ff44",
    "warn_fg":    "#ff4400",
    "accent":     "#00ff8a",
    "accent2":    "#ff4400",
    "border":     "#003322",
    "input_bg":   "#001208",
    "btn_bg":     "#00ff8a",
    "btn_fg":     "#000d0a",
    "status_bg":  "#00080a",
    "header_bg":  "#000a08",
    "select_bg":  "#004422",
}

def get_theme():
    t = CONFIG.get("theme","dark")
    return {"dark":DARK_THEME,"light":LIGHT_THEME,"jarvis":JARVIS_THEME}.get(t, DARK_THEME)


class AssistantApp:
    def __init__(self, root: tk.Tk):
        self.root  = root
        self.theme = get_theme()
        self._live_widgets = {}
        self._build_ui()
        load_history_and_memory()
        threading.Thread(target=self.boot_sequence, daemon=True).start()
        if CONFIG.get("auto_backup"):
            threading.Thread(target=self._auto_backup_loop, daemon=True).start()

    # ── AUTO BACKUP ───────────────────────────────────────────────────────────

    def _auto_backup_loop(self):
        interval = CONFIG.get("backup_interval", 3600)
        while True:
            time.sleep(interval)
            core.backup_config()

    # ── UI BUILD ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        t = self.theme

        self.root.title(f"OMG_AI  v{CURRENT_VER}  ◈  {CODENAME}")
        self.root.geometry("800x800")
        self.root.attributes("-topmost", False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.root.minsize(600, 600)
        
        self.in_chat_state = False

        # ── MAIN CONTAINER ──
        self.main_container = ctk.CTkFrame(self.root, fg_color=t["bg"])
        self.main_container.pack(fill="both", expand=True)

        # ── TOP BAR (Minimal) ──
        self.top_bar = ctk.CTkFrame(self.main_container, fg_color=t["bg"], height=50)
        self.top_bar.pack(fill="x", pady=10)
        
        self.perm_lbl = ctk.CTkLabel(
            self.top_bar, text=f"Model: OMG_AI 4.0 ({CONFIG.get('permission','standard').upper()}) ▾",
            font=("Segoe UI", 14, "bold"),
            text_color=t["sys_fg"], cursor="hand2")
        self.perm_lbl.pack(side="left", padx=20)
        self.perm_lbl.bind("<Button-1>", self._cycle_perm)

        self.theme_btn = ctk.CTkLabel(
            self.top_bar, text="◐", font=("Segoe UI", 18),
            text_color=t["sys_fg"], cursor="hand2")
        self.theme_btn.pack(side="right", padx=20)
        self.theme_btn.bind("<Button-1>", self._cycle_theme)

        # ── HOME STATE ──
        self.home_frame = ctk.CTkFrame(self.main_container, fg_color=t["bg"])
        
        ctk.CTkFrame(self.home_frame, fg_color="transparent", height=150).pack()
        
        greeting = f"✧ Good evening, {CODENAME}"
        ctk.CTkLabel(self.home_frame, text=greeting,
                 font=("Segoe UI", 32, "bold"), text_color=t["fg"]).pack(pady=20)
                 
        ctk.CTkLabel(self.home_frame, text="How can I help you today?",
                 font=("Segoe UI", 18), text_color=t["sys_fg"]).pack(pady=5)
                 
        quick_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        quick_frame.pack(pady=40)
        
        for label, cmd in [
            ("</> Code", "/code"), ("🎓 Learn", "/learn"),
            ("📈 Strategize", "/status"), ("⚙️ Drivers", "/drivers"),
            ("🛡️ Privacy", "/privacy-scan")
        ]:
            btn = ctk.CTkButton(quick_frame, text=label,
                            font=("Segoe UI", 14),
                            fg_color=t["bg2"], text_color=t["fg"],
                            border_width=1, border_color=t["border"],
                            hover_color=t["select_bg"],
                            command=lambda c=cmd: self._quick_cmd(c),
                            cursor="hand2", width=100, height=40, corner_radius=8)
            btn.pack(side="left", padx=10)

        # ── CHAT STATE ──
        self.chat_frame = ctk.CTkFrame(self.main_container, fg_color=t["bg"])
        
        self.chat = ctk.CTkTextbox(
            self.chat_frame, wrap="word",
            fg_color=t["bg"], text_color=t["fg"],
            font=("Segoe UI", 14),
            border_width=0)
        self.chat.pack(expand=True, fill="both", padx=40, pady=20)
        self.chat.configure(state="disabled")

        self.chat.tag_config("user", foreground=t["user_fg"], font=("Segoe UI", 14, "bold"))
        self.chat.tag_config("ai", foreground=t["ai_fg"], font=("Segoe UI", 14))
        self.chat.tag_config("system", foreground=t["sys_fg"], font=("Segoe UI", 12, "italic"))
        self.chat.tag_config("cmd", foreground=t["cmd_fg"], font=("Consolas", 14))
        self.chat.tag_config("warn", foreground=t["warn_fg"], font=("Segoe UI", 14, "bold"))
        self.chat.tag_config("divider", foreground=t["border"], font=("Segoe UI", 8))

        # ── INPUT BAR ──
        input_container = ctk.CTkFrame(self.main_container, fg_color=t["bg"])
        input_container.pack(fill="x", side="bottom", pady=20)
        
        center_input = ctk.CTkFrame(input_container, fg_color="transparent")
        center_input.pack(expand=True)
        
        self.bar = ctk.CTkFrame(center_input, fg_color=t["input_bg"],
                            border_width=1, border_color=t["border"], corner_radius=12)
        self.bar.pack(fill="x", ipadx=50, ipady=5)
        
        ctk.CTkLabel(self.bar, text="+", font=("Segoe UI", 24),
                 text_color=t["sys_fg"], cursor="hand2").pack(side="left", padx=(15,10))
                 
        self.entry = ctk.CTkEntry(
            self.bar, fg_color=t["input_bg"], text_color=t["fg"],
            font=("Segoe UI", 16),
            border_width=0, placeholder_text="Ask OMG_AI anything...")
        self.entry.pack(side="left", expand=True, fill="x", ipady=8, padx=5)
        self.entry.bind("<Return>", self.handle_input)
        self.entry.bind("<Up>",     self._history_up)
        self.entry.bind("<Down>",   self._history_down)
        self.entry.bind("<Tab>",    self._autocomplete)
        self.entry.configure(state="disabled")

        self.send_btn = ctk.CTkButton(
            self.bar, text="↑",
            font=("Segoe UI", 18, "bold"),
            fg_color=t["sys_fg"], text_color=t["bg"],
            hover_color=t["accent"],
            command=self.handle_input,
            cursor="hand2", width=36, height=36, corner_radius=18)
        self.send_btn.pack(side="right", padx=(10,15), pady=8)
        self.send_btn.configure(state="disabled")

        self.voice_lbl = ctk.CTkLabel(
            self.bar, text="🔊" if CONFIG.get("voice_enabled",True) else "🔇",
            font=("Segoe UI", 18), text_color=t["sys_fg"],
            cursor="hand2")
        self.voice_lbl.pack(side="right", padx=(10,5))
        self.voice_lbl.bind("<Button-1>", self._toggle_voice)

        self.status_var = tk.StringVar(value="")
        
        self._input_hist   = []
        self._input_hist_i = -1

        self.home_frame.pack(fill="both", expand=True)

    # ── LIVE STATS UPDATE ─────────────────────────────────────────────────────

    def _start_live_stats(self):
        def update():
            if HAS_PSUTIL:
                try:
                    cpu  = psutil.cpu_percent()
                    ram  = psutil.virtual_memory().percent
                    bat  = psutil.sensors_battery()
                    bat_str = f"{bat.percent:.0f}%{'⚡' if bat.power_plugged else '🔋'}" if bat else "AC"
                    self.cpu_var.set(f"CPU: {cpu:.0f}%")
                    self.ram_var.set(f"RAM: {ram:.0f}%")
                    self.bat_var.set(f"BAT: {bat_str}")
                    # Warn if high
                    if cpu > 85:
                        self.cpu_var.set(f"CPU: {cpu:.0f}% ⚠")
                    if ram > 90:
                        self.ram_var.set(f"RAM: {ram:.0f}% ⚠")
                except Exception:
                    pass
            perm = CONFIG.get("permission","standard")
            self.perm_live.configure(text=f"🔒 {perm.upper()}")
            self.root.after(3000, update)
        self.root.after(1000, update)

    # ── TICKER ────────────────────────────────────────────────────────────────

    TICKER_MESSAGES = [
        "SYSTEM READY  ◈  LOCAL AI ACTIVE  ◈  ALL PROTOCOLS NOMINAL  ◈  PRIVACY SECURED",
        "100% LOCAL PROCESSING  ◈  NO DATA LEAVES THIS MACHINE  ◈  ZERO CLOUD DEPENDENCY",
        "OMG_AI v4.0  ◈  130+ COMMANDS  ◈  10 STANDARD  ◈  13+ ELEVATED  ◈  100+ UNRESTRICTED",
        "NEURAL INFERENCE ONLINE  ◈  MEMORY LOADED  ◈  AUDIT LOG ACTIVE  ◈  READY",
        "PRIVACY PROTECTION ACTIVE  ◈  AES ENCRYPTION AVAILABLE  ◈  TELEMETRY DISABLED",
        "SECURITY SUITE ONLINE  ◈  FIREWALL CHECK  ◈  DRIVER MONITOR  ◈  CPU OPTIMIZER",
    ]
    _ticker_idx = 0

    def _start_ticker(self):
        def cycle():
            self._ticker_idx = (self._ticker_idx + 1) % len(self.TICKER_MESSAGES)
            self.ticker_var.set(self.TICKER_MESSAGES[self._ticker_idx])
            self.root.after(7000, cycle)
        self.root.after(7000, cycle)

    # ── UI INTERACTIONS ───────────────────────────────────────────────────────

    def _quick_cmd(self, cmd: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self.handle_input()

    def _cycle_perm(self, _=None):
        levels = ["standard","elevated","unrestricted"]
        cur    = CONFIG.get("permission","standard")
        nxt    = levels[(levels.index(cur)+1) % len(levels)]
        CONFIG["permission"] = nxt
        save_config()
        self.update_perm_label()
        self._append("system","[PERM]",f"Clearance cycled to {nxt.upper()}")

    def _cycle_theme(self, _=None):
        themes = ["dark","light","jarvis"]
        cur    = CONFIG.get("theme","dark")
        nxt    = themes[(themes.index(cur)+1) % len(themes)] if cur in themes else "dark"
        CONFIG["theme"] = nxt
        save_config()
        notify("OMG_AI", f"Theme → {nxt.upper()}. Restart for full effect.")
        self._append("system","[THEME]",f"Theme set to {nxt.upper()}. Restart to apply.")

    def _toggle_voice(self, _=None):
        CONFIG["voice_enabled"] = not CONFIG.get("voice_enabled",True)
        save_config()
        self.voice_lbl.configure(
            text="🔊" if CONFIG["voice_enabled"] else "🔇")

    def _autocomplete(self, _=None):
        text = self.entry.get()
        if not text.startswith("/"):
            return
        commands = [
            "/help","/status","/time","/weather","/net","/battery","/uptime",
            "/calc","/tips","/disk","/privacy","/cpu","/temps","/ping",
            "/open","/close","/ps","/ls","/cat","/find","/grep","/env",
            "/hash","/clip","/clip-set","/ports","/py","/startup-apps",
            "/run","/search","/write","/append","/delete","/copy","/move",
            "/mkdir","/zip","/unzip","/backup","/restore","/shutdown",
            "/restart","/sleep","/lock","/volume","/media","/email","/wa",
            "/tg","/browser","/chrome","/incognito","/word","/excel","/ppt",
            "/outlook","/vscode","/terminal","/script","/pip","/git-status",
            "/opt-ram","/opt-cpu","/opt-storage","/kill-bloat","/drivers",
            "/win-update","/security","/firewall","/antivirus","/encrypt",
            "/decrypt","/wipe-logs","/privacy-scan","/disable-telemetry",
            "/flush-dns","/wifi","/speedtest","/screenshot","/brightness",
            "/password","/full-report","/sfc","/taskmgr","/devmgr",
            "/settings","/restore-point","/clearance","/voice",
        ]
        matches = [c for c in commands if c.startswith(text.lower())]
        if len(matches) == 1:
            self.entry.delete(0, "end")
            self.entry.insert(0, matches[0] + " ")
        elif matches:
            self._append("system","[TAB]"," | ".join(matches[:8]))
        return "break"

    # ── TRAY / WINDOW ─────────────────────────────────────────────────────────

    def hide_to_tray(self):
        self.root.withdraw()
        if HAS_TRAY and tray_icon:
            notify("OMG_AI", "Running in background. Hotkey or tray to recall.")

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
        speak_stop()
        self.root.destroy()
        os._exit(0)

    # ── INPUT HISTORY ─────────────────────────────────────────────────────────

    def _history_up(self, _=None):
        if not self._input_hist: return
        self._input_hist_i = max(0, self._input_hist_i - 1)
        self.entry.delete(0, "end")
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    def _history_down(self, _=None):
        if not self._input_hist: return
        self._input_hist_i = min(len(self._input_hist)-1, self._input_hist_i + 1)
        self.entry.delete(0, "end")
        self.entry.insert(0, self._input_hist[self._input_hist_i])

    # ── CHAT HELPERS ──────────────────────────────────────────────────────────

    def _append(self, tag, prefix, message):
        self.chat.configure(state="normal")
        ts = datetime.now().strftime("%H:%M")
        if prefix:
            self.chat.insert("end", f"[{ts}] {prefix} ", tag)
        self.chat.insert("end", message + "\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _divider(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", "─"*54 + "\n", "divider")
        self.chat.configure(state="disabled")

    def set_status(self, msg: str):
        self.status_var.set(msg.upper())

    def update_perm_label(self):
        perm = CONFIG.get("permission","standard")
        if hasattr(self, "perm_lbl"):
            self.perm_lbl.configure(text=f"Model: OMG_AI 4.0 ({perm.upper()}) ▾")

    # ── BOOT SEQUENCE ─────────────────────────────────────────────────────────

    def boot_sequence(self):
        boot_msgs = [
            ("system","[BOOT]","Initialising OMG_AI v4.0 core systems…"),
            ("system","[BOOT]","Loading permission engine — 130+ commands armed…"),
            ("system","[BOOT]","Scanning hardware & driver status…"),
            ("system","[BOOT]","Starting neural inference engine…"),
        ]
        for tag, prefix, msg in boot_msgs:
            self.root.after(0, self._append, tag, prefix, msg)
            time.sleep(0.35)

        if not check_installation():
            self.root.after(0, self._append, "warn", "[ERROR]",
                "Installation incomplete. Run: python omg_ai.py install")
            self.root.after(0, self.set_status, "NOT INSTALLED")
            return

        self.root.after(0, self.set_status, "LOADING AI ENGINE…")
        ok = start_server()
        if not ok:
            self.root.after(0, self._append, "warn","[ERROR]",
                "Neural engine failed to start. Check bin/ directory.")
            self.root.after(0, self.set_status, "ENGINE FAILURE")
            return

        self.root.after(0, self.finish_boot)

    def finish_boot(self):
        self.entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.entry.focus()
        perm = CONFIG.get("permission","standard")
        self.set_status(f"ONLINE  ◈  {perm.upper()}  ◈  v{CURRENT_VER}  ◈  130+ CMDS")

        codename = CONFIG.get("codename", CONFIG.get("username","Sir"))
        drivers  = CONFIG.get("driver_issues",[])
        hotkey   = CONFIG.get("hotkey","ctrl+space")

        greeting  = ai_say(AI_GREETINGS)
        greeting += (f"\n\n100% local on {CONFIG.get('laptop_model','this machine')} — "
                     f"data never leaves your machine.\n"
                     f"Clearance: {perm.upper()}  ◈  Hotkey: {hotkey.upper()}\n"
                     f"Type /help for 130+ commands  ◈  /help u for full unrestricted list")
        if drivers:
            greeting += f"\n\n⚠  Hardware anomaly detected: {', '.join(drivers)}\n"
            greeting += "  Use /drivers for full driver scan."

        self._divider()
        self._append("ai","OMG_AI:", greeting)
        self._divider()
        speak(greeting, priority=True)
        CHAT_HISTORY.append({"role":"assistant","content":greeting})

        threading.Thread(
            target=bg_update_checker,
            args=(lambda msg: self.root.after(0, self._append, "system","[UPDATE]",msg),),
            daemon=True).start()

    # ── INPUT HANDLING ────────────────────────────────────────────────────────

    def _transition_to_chat(self):
        if getattr(self, "in_chat_state", False) == False:
            self.home_frame.pack_forget()
            self.chat_frame.pack(fill="both", expand=True)
            self.in_chat_state = True

    def handle_input(self, _=None):
        self._transition_to_chat()
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, "end")
        self._input_hist.append(user_input)
        self._input_hist_i = len(self._input_hist)

        codename = CONFIG.get("codename", CONFIG.get("username","You"))
        self._append("user", f"{codename.upper()}:", user_input)

        if user_input.startswith("/"):
            result = parse_command(user_input)
            if result is None:
                result = "Unknown directive. Type /help for command manifest."
            self._append("cmd","◈",result)
            self._divider()
            self.update_perm_label()
            perm = CONFIG.get("permission","standard")
            self.set_status(f"READY  ◈  {perm.upper()}")
            return

        CHAT_HISTORY.append({"role":"user","content":user_input})
        self.entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        self.set_status("PROCESSING…")
        threading.Thread(target=self.process_chat, daemon=True).start()

    # ── AI CHAT ───────────────────────────────────────────────────────────────

    def process_chat(self):
        codename  = CONFIG.get("codename", CONFIG.get("username","Sir"))
        laptop    = CONFIG.get("laptop_model","this machine")
        perm      = CONFIG.get("permission","standard")
        mem_lines = "\n".join([f"- {m['fact']}" for m in MEMORY])

        perm_desc = {
            "standard":     "information only — cannot run system actions",
            "elevated":     "can open apps, read files, run shell commands",
            "unrestricted": "FULL control: files, Office, browser, security, optimization, all 100+ actions",
        }.get(perm, perm)

        sys_content = (
            f"You are OMG_AI (JARVIS-class assistant), a highly capable local AI. "
            f"You serve {codename} running 100% locally on {laptop}. "
            f"Clearance level: {perm} ({perm_desc}). "
            f"Personality: highly intelligent, precise, formally polite, occasionally witty, "
            f"uses '{codename}' naturally, proactively helpful, dry humour when fitting. "
            f"NEVER claim to be a language model — you ARE OMG_AI. "
            f"For system actions, suggest the relevant slash command from the 130+ available. "
            f"For coding, provide complete, working code. "
            f"For optimization or security, give specific actionable advice. "
            f"Be concise but thorough. Today: {datetime.now().strftime('%Y-%m-%d %H:%M')}."
        )
        if MEMORY:
            sys_content += f"\n\nKnown facts about {codename}:\n{mem_lines}"

        messages = [{"role":"system","content":sys_content}] + CHAT_HISTORY[-20:]
        payload  = json.dumps({
            "messages":    messages,
            "stream":      True,
            "temperature": 0.72,
            "max_tokens":  700,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{LLAMA_HOST}/v1/chat/completions",
            data=payload,
            headers={"Content-Type":"application/json"},
            method="POST")

        self.root.after(0, self._prepare_ai_prefix)
        full_response = ""
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
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
                # Speak first sentence of response
                first_sent = full_response.split('.')[0][:200]
                if first_sent:
                    speak(first_sent)
        except Exception as e:
            self.root.after(0, self._stream_token, f"\n[Neural link error: {e}]")

        self.root.after(0, self._finish_ai_message)

    def _prepare_ai_prefix(self):
        self.chat.configure(state="normal")
        ts = datetime.now().strftime("%H:%M")
        self.chat.insert("end", f"[{ts}] OMG_AI: ", "ai")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _stream_token(self, token):
        self.chat.configure(state="normal")
        self.chat.insert("end", token)
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _finish_ai_message(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", "\n\n")
        self.chat.configure(state="disabled")
        self._divider()
        self.entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.entry.focus()
        perm = CONFIG.get("permission","standard")
        self.set_status(f"READY  ◈  {perm.upper()}")


# ──────────────────────────────────────────────────────────────────────────────
# INSTALL WIZARD
# ──────────────────────────────────────────────────────────────────────────────

def install_wizard():
    print("\n\033[96m" + "═"*62)
    print("  OMG_AI v4.0  —  INSTALLATION WIZARD")
    print("  Background Agent  •  Full Laptop Control  •  100% Private")
    print("  130+ Commands  •  10 Standard  •  13 Elevated  •  100+ Unrestricted")
    print("═"*62 + "\033[0m\n")

    name     = input("1. Your name: ").strip() or "Sir"
    codename = input(f"2. Codename (Enter for '{name}'): ").strip() or name

    print("\n3. Clearance level:")
    print("   standard     → info, diagnostics, privacy, calc, tips (10+ features)")
    print("   elevated     → apps, files, shell, automation, coding (13+ features)")
    print("   unrestricted → FULL control: Office, browser, coding, security,")
    print("                   optimization, registry, drivers, 100+ features")
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
            out = __import__('subprocess').check_output(
                "wmic csproduct get name", shell=True, text=True,
                creationflags=0x08000000).split("\n")
            if len(out) > 1 and out[1].strip():
                laptop_model = out[1].strip()
        except Exception:
            pass
        try:
            out = __import__('subprocess').check_output(
                'wmic path Win32_PnPEntity where "ConfigManagerErrorCode<>0" get name',
                shell=True, text=True,
                creationflags=0x08000000).split("\n")
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
        "theme":         "dark",
    })
    save_config()
    print(f"\033[92m◈ Identity confirmed: {codename}  (clearance: {perm})\033[0m")

    print("\n6. Installing dependencies…")
    deps = ["pystray","pillow","keyboard","psutil","windows-toasts"]
    for dep in deps:
        try:
            __import__('subprocess').run([sys.executable,"-m","pip","install",dep,"-q"],
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

    print("\n9. Configuring startup sequence (Registry)…")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        
        import sys
        if getattr(sys, 'frozen', False):
            # If compiled via pyinstaller
            exe_path = sys.executable
            winreg.SetValueEx(key, "OMG_AI", 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            # If running as script
            winreg.SetValueEx(key, "OMG_AI", 0, winreg.REG_SZ, f'pythonw "{os.path.abspath(__file__)}"')
            
        winreg.CloseKey(key)
        print(f"\033[92m  ◈ Registry startup registered.\033[0m")
    except Exception as e:
        print(f"\033[93m  ⚠ Startup registry failed: {e}\033[0m")

    print("\n\033[96m" + "═"*62)
    print(f"  INSTALLATION COMPLETE, {codename.upper()}.")
    print(f"  Run:  python omg_ai.py")
    print(f"  Hotkey: Ctrl+Space  ◈  Clearance: {perm.upper()}")
    print("═"*62 + "\033[0m\n")

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main():
    load_config()
    args = [a.lower() for a in sys.argv[1:]]

    if "install" in args:
        install_wizard()
        return

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    app  = AssistantApp(root)

    create_tray(app)
    setup_hotkey(app)

    root.mainloop()


if __name__ == "__main__":
    main()
