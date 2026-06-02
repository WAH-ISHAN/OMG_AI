# OMG_AI 🚀

**OMG_AI** is a powerful, 100% private, and fully local AI personal assistant for Windows. It runs entirely on your laptop without sending any data to the internet, giving you complete control over your privacy and your machine.

---

## 🔒 100% Privacy Guaranteed
Unlike cloud-based assistants (like ChatGPT or Copilot), **OMG_AI runs offline** on your machine using a local LLM (Qwen 2.5 via `llama.cpp`). 
- **Zero data tracking:** Your chats, files, and system information never leave your computer.
- **No accounts required:** No sign-ups, no API keys, and no subscriptions.

---

## 🌟 Key Features & Benefits
- **Siri-Style Interface:** A sleek, always-on-top chat panel that you can toggle anytime using `Ctrl + Space`.
- **System Control:** Use natural language or slash commands to open apps, check hardware, control volume, or shut down your PC.
- **Permission Levels:** 
  - `Normal`: Chat only.
  - `Middle`: Open apps, read files, list processes.
  - `Full`: Write files, send emails, control PC power.
- **Voice Output:** Speaks to you using built-in Windows text-to-speech.
- **WhatsApp & Email:** Send emails or open WhatsApp Web chats directly via commands.

---

## 🛠️ Installation

You don't need NPM, Node.js, or complex setups. Just open your **Windows Terminal** or **PowerShell** and run this single command:

```powershell
irm https://raw.githubusercontent.com/WAH-ISHAN/OMG_AI/main/install.ps1 | iex
```

### What happens during installation?
1. The AI engine and intelligence modules are downloaded directly to your PC.
2. A setup wizard will ask for your Name and desired Permission Level.
3. OMG_AI is added to your System PATH and Windows Startup.
4. Once done, the AI panel will open automatically!

---

## 🚀 How to Use

- **Global Hotkey:** Press `Ctrl + Space` from anywhere on your PC to show or hide the AI panel.
- **Start Manually:** If you closed the app completely, just type `OMG_AI` in your Terminal/CMD.
- **Slash Commands:** Type `/help` in the chat panel to see all available commands, such as:
  - `/sysinfo` - Check CPU, RAM, and Battery.
  - `/open notepad` - Launch an application.
  - `/volume 50` - Set PC volume.
  - `/shutdown` - Turn off your PC.
  - `/remember [fact]` - Save things for the AI to remember.

---

## 🗑️ Uninstallation

If you want to completely remove OMG_AI from your laptop, open **PowerShell** and run the following command. This stops the AI and deletes all its files and startup entries:

```powershell
Stop-Process -Name "pythonw", "python", "llama-server" -Force -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force "$env:USERPROFILE\OMG_AI" -ErrorAction SilentlyContinue; Remove-Item -Force "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\omg_ai.bat" -ErrorAction SilentlyContinue; Write-Host "OMG_AI Uninstall Complete!" -ForegroundColor Green
```

---
*Created by [WAH-ISHAN](https://github.com/WAH-ISHAN)*
