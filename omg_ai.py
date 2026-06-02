#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║   OMG_AI - Local AI Personal Assistant   ║
║   100% Private, Llama.cpp Powered        ║
╚══════════════════════════════════════════╝
"""

import sys
import os
import json
import urllib.request
import urllib.error
import threading
import time
import subprocess
import zipfile
import atexit
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

# ─── CONFIG ───────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
BIN_DIR = os.path.join(BASE_DIR, "bin")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

CHAT_HISTORY = []
MEMORY = []
CONFIG = {"username": "User", "laptop_model": "Unknown", "driver_issues": []}

LLAMA_PORT = 8080
LLAMA_HOST = f"http://127.0.0.1:{LLAMA_PORT}"

DEFAULT_MODEL = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
server_process = None

# ─── TEXT TO SPEECH (TTS) ─────────────────────────────────────────────────────

def speak(text):
    if sys.platform == "win32":
        def run_tts():
            try:
                text_escaped = text.replace("'", "''")
                ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text_escaped}')"
                subprocess.run(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
        threading.Thread(target=run_tts, daemon=True).start()

# ─── UTILS ────────────────────────────────────────────────────────────────────

def load_config():
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                CONFIG = json.load(f)
        except:
            pass

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f, ensure_ascii=False, indent=2)

def get_llama_exe():
    return os.path.join(BIN_DIR, "llama-server.exe" if sys.platform == "win32" else "llama-server")

def check_installation():
    if not os.path.exists(get_llama_exe()): return False
    if not os.path.exists(os.path.join(MODELS_DIR, DEFAULT_MODEL)): return False
    if not os.path.exists(CONFIG_FILE): return False
    return True

# ─── SERVER MANAGEMENT ────────────────────────────────────────────────────────

def kill_server():
    global server_process
    if server_process:
        try:
            server_process.terminate()
            server_process.wait(timeout=2)
        except:
            pass
        server_process = None

atexit.register(kill_server)

def start_server():
    global server_process
    kill_server()
    exe_path = get_llama_exe()
    model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL)
    if not os.path.exists(model_path): return False
    
    cmd = [exe_path, "-m", model_path, "--port", str(LLAMA_PORT), "-c", "2048", "--threads", "4"]
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    server_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
    
    for _ in range(30):
        try:
            req = urllib.request.Request(f"{LLAMA_HOST}/health")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200: return True
        except:
            time.sleep(0.5)
    return False

# ─── SETUP WIZARD (CLI) ───────────────────────────────────────────────────────

def install_wizard():
    print("\n\033[96m" + "="*50)
    print(" OMG_AI INSTALLATION WIZARD")
    print("="*50 + "\033[0m\n")

    name = input("1. What is your name? (How should I address you?): ").strip()
    if not name: name = "User"
    
    print("\n2. Scanning your system details...")
    laptop_model = "Unknown Laptop"
    driver_issues = []
    
    if sys.platform == "win32":
        try:
            out = subprocess.check_output("wmic csproduct get name", shell=True, text=True).split("\n")
            if len(out) > 1 and out[1].strip(): laptop_model = out[1].strip()
        except: pass
        
        try:
            out = subprocess.check_output('wmic path Win32_PnPEntity where "ConfigManagerErrorCode<>0" get name', shell=True, text=True).split("\n")
            issues = [l.strip() for l in out if l.strip()]
            if len(issues) > 1: driver_issues = issues[1:]
        except: pass
        
    CONFIG["username"] = name
    CONFIG["laptop_model"] = laptop_model
    CONFIG["driver_issues"] = driver_issues
    save_config()
    print(f"\033[92m✓ System check complete. Hello {name}!\033[0m")
    
    print("\n3. Downloading AI Core Engine...")
    if not os.path.exists(get_llama_exe()):
        try:
            req = urllib.request.Request("https://api.github.com/repos/ggerganov/llama.cpp/releases/latest")
            data = json.loads(urllib.request.urlopen(req).read())
            url = next(a["browser_download_url"] for a in data["assets"] if "bin-win-cpu-x64.zip" in a["name"])
            zip_path = os.path.join(BIN_DIR, "llama.zip")
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(BIN_DIR)
            os.remove(zip_path)
            print("\033[92m✓ AI Engine downloaded.\033[0m")
        except Exception as e:
            print(f"\033[91m✗ Engine download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m✓ Engine already exists.\033[0m")
        
    print("\n4. Downloading Intelligence Modules...")
    model_path = os.path.join(MODELS_DIR, DEFAULT_MODEL)
    if not os.path.exists(model_path):
        try:
            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    print(f"\rDownloading... {percent}%", end="", flush=True)
            urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
            print("\n\033[92m✓ Brain downloaded.\033[0m")
        except Exception as e:
            print(f"\n\033[91m✗ Brain download failed: {e}\033[0m")
            sys.exit(1)
    else:
        print("\033[92m✓ Brain already exists.\033[0m")
        
    print("\n5. Setting up Windows Startup...")
    startup_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ai_assistant.bat")
    try:
        with open(startup_path, "w") as f:
            f.write(f'@echo off\ncd /d "{BASE_DIR}"\nstart "" pythonw "{os.path.abspath(__file__)}" start\n')
        print("\033[92m✓ Startup configured.\033[0m")
    except Exception as e:
        print(f"\033[93m⚠ Startup setup failed: {e}\033[0m")
        
    print("\n\033[96m" + "="*50)
    print(" INSTALLATION COMPLETE! ")
    print(" Run 'OMG_AI start' or restart your computer.")
    print("="*50 + "\033[0m\n")

# ─── GUI APPLICATION ──────────────────────────────────────────────────────────

class AssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMG_AI")
        self.root.geometry("400x550")
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1e1e1e")
        
        self.chat_display = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 10), bd=0, padx=10, pady=10
        )
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        self.chat_display.tag_config("user", foreground="#4cc9f0", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("ai", foreground="#fca311", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#8d99ae", font=("Segoe UI", 9, "italic"))
        
        self.input_frame = tk.Frame(root, bg="#1e1e1e")
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.entry = tk.Entry(
            self.input_frame, bg="#2b2b2b", fg="#ffffff", font=("Segoe UI", 11), insertbackground="#ffffff", bd=0, relief="flat"
        )
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5)
        self.entry.bind("<Return>", self.handle_input)
        self.entry.focus()
        
        self.send_btn = tk.Button(
            self.input_frame, text="Send", bg="#4cc9f0", fg="#1e1e1e", font=("Segoe UI", 10, "bold"), bd=0, command=self.handle_input
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5, ipadx=10, ipady=2)
        
        self.entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE) as f:
                global CHAT_HISTORY; CHAT_HISTORY = json.load(f)
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                global MEMORY; MEMORY = json.load(f)
                
        threading.Thread(target=self.boot_sequence, daemon=True).start()

    def append_message(self, tag, prefix, message):
        self.chat_display.config(state=tk.NORMAL)
        if prefix: self.chat_display.insert(tk.END, prefix + " ", tag)
        self.chat_display.insert(tk.END, message + "\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def boot_sequence(self):
        if not check_installation():
            self.root.after(0, self.append_message, "system", "[System]", "OMG_AI is not installed. Please run 'OMG_AI install' in your terminal.")
            return
            
        self.root.after(0, self.append_message, "system", "[System]", "Initializing local AI Engine...")
        if not start_server():
            self.root.after(0, self.append_message, "system", "[System]", "Failed to start AI Engine.")
            return
            
        self.root.after(0, self.finish_boot)
        
    def finish_boot(self):
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        
        username = CONFIG.get("username", "User")
        drivers = CONFIG.get("driver_issues", [])
        
        now = datetime.now()
        greeting = f"Hello {username}. Your data is completely secure and will never be leaked."
        if drivers:
            greeting += f" By the way, I noticed an issue with your drivers: {', '.join(drivers)}."
        greeting += f" What tasks do we have for today?"
        
        self.append_message("ai", "AI:", greeting)
        speak(greeting)
        CHAT_HISTORY.append({"role": "assistant", "content": greeting})

    def handle_input(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input: return
        self.entry.delete(0, tk.END)
        self.append_message("user", "You:", user_input)
        
        if user_input.startswith("/"):
            cmd = user_input.split(" ", 1)
            c = cmd[0].lower()
            if c == "/clear":
                global CHAT_HISTORY; CHAT_HISTORY = []
                if os.path.exists(CHAT_HISTORY_FILE): os.remove(CHAT_HISTORY_FILE)
                self.append_message("system", "[System]", "Chat history cleared.")
            elif c == "/remember":
                if len(cmd) > 1:
                    MEMORY.append(cmd[1].strip())
                    with open(MEMORY_FILE, "w") as f: json.dump(MEMORY, f)
                    self.append_message("system", "[System]", f"I will remember: {cmd[1].strip()}")
            elif c == "/memories":
                mem_str = "\n".join([f"{i+1}. {m}" for i, m in enumerate(MEMORY)]) if MEMORY else "No memories yet."
                self.append_message("system", "[System]", f"Saved Memories:\n{mem_str}")
            return

        CHAT_HISTORY.append({"role": "user", "content": user_input})
        self.entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.process_chat, daemon=True).start()

    def process_chat(self):
        username = CONFIG.get("username", "User")
        laptop = CONFIG.get("laptop_model", "Unknown")
        memories = "\n".join([f"- {m}" for m in MEMORY])
        sys_content = f"You are {username}'s personal AI assistant named OMG_AI. Running 100% locally on {laptop}."
        if MEMORY: sys_content += f"\nFacts about {username}:\n{memories}"
        
        messages = [{"role": "system", "content": sys_content}] + CHAT_HISTORY[-20:]
        payload = json.dumps({"messages": messages, "stream": True, "temperature": 0.7, "max_tokens": 512}).encode("utf-8")
        req = urllib.request.Request(f"{LLAMA_HOST}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        
        self.root.after(0, self.prepare_ai_message)
        full_response = ""
        try:
            with urllib.request.urlopen(req) as resp:
                for line in resp:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            delta = json.loads(line[6:])["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"] is not None:
                                token = str(delta["content"])
                                full_response += token
                                self.root.after(0, self.stream_token, token)
                        except: pass
            if full_response:
                CHAT_HISTORY.append({"role": "assistant", "content": full_response})
                with open(CHAT_HISTORY_FILE, "w") as f: json.dump(CHAT_HISTORY, f)
        except Exception as e:
            self.root.after(0, self.stream_token, f"\n[Error: {e}]")
            
        self.root.after(0, self.finish_ai_message)

    def prepare_ai_message(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "AI: ", "ai")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def stream_token(self, token):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, token)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def finish_ai_message(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.entry.focus()

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def main():
    load_config()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "install":
        install_wizard()
    else:
        root = tk.Tk()
        app = AssistantApp(root)
        def on_close():
            kill_server()
            root.destroy()
            os._exit(0)
        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()

if __name__ == "__main__":
    main()
