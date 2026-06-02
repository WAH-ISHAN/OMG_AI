"""
OMG_AI Service Installer
=========================
Installs OMG_AI as a persistent system service that survives
login/logout and reboots, on Linux (systemd), macOS (launchd),
and Windows (Task Scheduler / NSSM).

Usage:
    python omg_ai_service.py install    – install & enable service
    python omg_ai_service.py start      – start immediately
    python omg_ai_service.py stop       – stop
    python omg_ai_service.py status     – show status
    python omg_ai_service.py uninstall  – remove service
"""

import os
import sys
import platform
import subprocess
import textwrap
import shutil
from pathlib import Path

THIS_DIR  = Path(__file__).parent.resolve()
VENV_PY   = THIS_DIR / ".venv" / ("Scripts" if platform.system() == "Windows" else "bin") / "python"
PY_EXE    = str(VENV_PY) if VENV_PY.exists() else sys.executable
AVATAR_PY = THIS_DIR / "omg_ai_avatar.py"
SERVICE   = "omg_ai"


# ─────────────────────────────────────────────────────────────────────────────
# Linux – systemd user service
# ─────────────────────────────────────────────────────────────────────────────
SYSTEMD_UNIT = """\
[Unit]
Description=OMG_AI Local AI Assistant
After=graphical-session.target network.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart={py} {avatar}
Restart=always
RestartSec=5
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

def install_linux():
    unit_dir  = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_file = unit_dir / f"{SERVICE}.service"
    unit_file.write_text(SYSTEMD_UNIT.format(py=PY_EXE, avatar=AVATAR_PY))
    _run(["systemctl", "--user", "daemon-reload"])
    _run(["systemctl", "--user", "enable", SERVICE])
    _run(["systemctl", "--user", "start",  SERVICE])
    # Ensure service survives logout (linger)
    _run(["loginctl", "enable-linger", os.environ.get("USER", "user")])
    print(f"[✓] systemd user service installed: {unit_file}")

def uninstall_linux():
    _run(["systemctl", "--user", "stop",    SERVICE], check=False)
    _run(["systemctl", "--user", "disable", SERVICE], check=False)
    unit_file = Path.home() / ".config" / "systemd" / "user" / f"{SERVICE}.service"
    unit_file.unlink(missing_ok=True)
    _run(["systemctl", "--user", "daemon-reload"])
    print("[✓] Service removed.")

def status_linux():
    _run(["systemctl", "--user", "status", SERVICE], check=False)

def start_linux():
    _run(["systemctl", "--user", "start", SERVICE])

def stop_linux():
    _run(["systemctl", "--user", "stop", SERVICE])


# ─────────────────────────────────────────────────────────────────────────────
# macOS – launchd plist
# ─────────────────────────────────────────────────────────────────────────────
LAUNCHD_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>          <string>com.omgai.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{py}</string>
        <string>{avatar}</string>
    </array>
    <key>RunAtLoad</key>      <true/>
    <key>KeepAlive</key>      <true/>
    <key>StandardOutPath</key>
    <string>{log}/omg_ai_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{log}/omg_ai_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key><string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
"""

def install_macos():
    log_dir  = Path.home() / ".omg_ai" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    agents   = Path.home() / "Library" / "LaunchAgents"
    agents.mkdir(parents=True, exist_ok=True)
    plist    = agents / "com.omgai.assistant.plist"
    plist.write_text(LAUNCHD_PLIST.format(py=PY_EXE, avatar=AVATAR_PY, log=log_dir))
    _run(["launchctl", "load", "-w", str(plist)])
    print(f"[✓] LaunchAgent installed: {plist}")

def uninstall_macos():
    plist = Path.home() / "Library" / "LaunchAgents" / "com.omgai.assistant.plist"
    if plist.exists():
        _run(["launchctl", "unload", str(plist)], check=False)
        plist.unlink()
    print("[✓] LaunchAgent removed.")

def status_macos():
    _run(["launchctl", "list", "com.omgai.assistant"], check=False)

def start_macos():
    _run(["launchctl", "start", "com.omgai.assistant"])

def stop_macos():
    _run(["launchctl", "stop", "com.omgai.assistant"])


# ─────────────────────────────────────────────────────────────────────────────
# Windows – Task Scheduler
# ─────────────────────────────────────────────────────────────────────────────
TASK_XML = """\
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4"
  xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>OMG_AI Local AI Assistant</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled></LogonTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT30S</Interval><Count>9999</Count>
    </RestartOnFailure>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
  </Settings>
  <Actions>
    <Exec>
      <Command>{py}</Command>
      <Arguments>"{avatar}"</Arguments>
    </Exec>
  </Actions>
</Task>
"""

def install_windows():
    import tempfile
    xml_path = Path(tempfile.gettempdir()) / "omg_ai_task.xml"
    xml_path.write_text(
        TASK_XML.format(py=PY_EXE, avatar=AVATAR_PY),
        encoding="utf-16",
    )
    _run(["schtasks", "/Create", "/TN", "OMG_AI", "/XML", str(xml_path), "/F"])
    _run(["schtasks", "/Run",    "/TN", "OMG_AI"])
    xml_path.unlink(missing_ok=True)
    print("[✓] Windows Scheduled Task created and started.")

def uninstall_windows():
    _run(["schtasks", "/End",    "/TN", "OMG_AI"], check=False)
    _run(["schtasks", "/Delete", "/TN", "OMG_AI", "/F"], check=False)
    print("[✓] Scheduled Task removed.")

def status_windows():
    _run(["schtasks", "/Query", "/TN", "OMG_AI", "/FO", "LIST", "/V"], check=False)

def start_windows():
    _run(["schtasks", "/Run", "/TN", "OMG_AI"])

def stop_windows():
    _run(["schtasks", "/End", "/TN", "OMG_AI"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _run(cmd, check=True):
    result = subprocess.run(cmd, capture_output=False)
    if check and result.returncode != 0:
        print(f"[!] Command failed: {' '.join(str(c) for c in cmd)}")
    return result


def _platform_funcs():
    p = platform.system()
    if p == "Linux":
        return install_linux, uninstall_linux, start_linux, stop_linux, status_linux
    elif p == "Darwin":
        return install_macos, uninstall_macos, start_macos, stop_macos, status_macos
    elif p == "Windows":
        return install_windows, uninstall_windows, start_windows, stop_windows, status_windows
    else:
        raise RuntimeError(f"Unsupported platform: {p}")


# ─────────────────────────────────────────────────────────────────────────────
# Dependency installer (run once)
# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_PACKAGES = [
    "pyttsx3",
    "SpeechRecognition",
    "psutil",
    # Optional but recommended:
    # "pyaudio",      # needed by SpeechRecognition for mic input
    # "whisper",      # OpenAI Whisper for offline STT
]

def install_dependencies():
    print("Installing Python dependencies …")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    subprocess.run([sys.executable, "-m", "pip", "install"] + REQUIRED_PACKAGES, check=False)
    print("[✓] Dependencies installed.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()
    fn_install, fn_uninstall, fn_start, fn_stop, fn_status = _platform_funcs()

    if cmd == "install":
        install_dependencies()
        fn_install()
    elif cmd == "uninstall":
        fn_uninstall()
    elif cmd == "start":
        fn_start()
    elif cmd == "stop":
        fn_stop()
    elif cmd == "status":
        fn_status()
    elif cmd == "deps":
        install_dependencies()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
