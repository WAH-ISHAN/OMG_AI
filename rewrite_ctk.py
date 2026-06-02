import os

file_path = "c:\\Users\\USER\\OneDrive\\Documents\\test\\omg_ai.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace imports
if "import customtkinter" not in content:
    content = content.replace("import tkinter as tk\nfrom tkinter import scrolledtext", 
                              "import tkinter as tk\nimport customtkinter as ctk\nfrom tkinter import scrolledtext")

# Update main() to use ctk.CTk()
old_main = """    root = tk.Tk()
    app  = AssistantApp(root)"""

new_main = """    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = ctk.CTk()
    app  = AssistantApp(root)"""
content = content.replace(old_main, new_main)

# Update _build_ui for CustomTkinter
target_ui_start = "    # ── UI BUILD ──────────────────────────────────────────────────────────────"
target_ui_end = "    # ── LIVE STATS UPDATE ─────────────────────────────────────────────────────"

new_ui = """    # ── UI BUILD ──────────────────────────────────────────────────────────────

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
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # ── TOP BAR (Minimal) ──
        self.top_bar = ctk.CTkFrame(self.main_container, fg_color=t["bg"], height=50)
        self.top_bar.pack(fill=tk.X, pady=10)
        
        self.perm_lbl = ctk.CTkLabel(
            self.top_bar, text=f"Model: OMG_AI 4.0 ({CONFIG.get('permission','standard').upper()}) ▾",
            font=("Segoe UI", 14, "bold"),
            text_color=t["sys_fg"], cursor="hand2")
        self.perm_lbl.pack(side=tk.LEFT, padx=20)
        self.perm_lbl.bind("<Button-1>", self._cycle_perm)

        self.theme_btn = ctk.CTkLabel(
            self.top_bar, text="◐", font=("Segoe UI", 18),
            text_color=t["sys_fg"], cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT, padx=20)
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
            btn.pack(side=tk.LEFT, padx=10)

        # ── CHAT STATE ──
        self.chat_frame = ctk.CTkFrame(self.main_container, fg_color=t["bg"])
        
        self.chat = ctk.CTkTextbox(
            self.chat_frame, wrap=tk.WORD,
            fg_color=t["bg"], text_color=t["fg"],
            font=("Segoe UI", 14),
            border_width=0)
        self.chat.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)
        self.chat.configure(state="disabled")

        self.chat.tag_config("user", foreground=t["user_fg"], font=("Segoe UI", 14, "bold"))
        self.chat.tag_config("ai", foreground=t["ai_fg"], font=("Segoe UI", 14))
        self.chat.tag_config("system", foreground=t["sys_fg"], font=("Segoe UI", 12, "italic"))
        self.chat.tag_config("cmd", foreground=t["cmd_fg"], font=("Consolas", 14))
        self.chat.tag_config("warn", foreground=t["warn_fg"], font=("Segoe UI", 14, "bold"))
        self.chat.tag_config("divider", foreground=t["border"], font=("Segoe UI", 8))

        # ── INPUT BAR ──
        input_container = ctk.CTkFrame(self.main_container, fg_color=t["bg"])
        input_container.pack(fill=tk.X, side=tk.BOTTOM, pady=20)
        
        center_input = ctk.CTkFrame(input_container, fg_color="transparent")
        center_input.pack(expand=True)
        
        self.bar = ctk.CTkFrame(center_input, fg_color=t["input_bg"],
                            border_width=1, border_color=t["border"], corner_radius=12)
        self.bar.pack(fill=tk.X, ipadx=50, ipady=5)
        
        ctk.CTkLabel(self.bar, text="+", font=("Segoe UI", 24),
                 text_color=t["sys_fg"], cursor="hand2").pack(side=tk.LEFT, padx=(15,10))
                 
        self.entry = ctk.CTkEntry(
            self.bar, fg_color=t["input_bg"], text_color=t["fg"],
            font=("Segoe UI", 16),
            border_width=0, placeholder_text="Ask OMG_AI anything...")
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=8, padx=5)
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
        self.send_btn.pack(side=tk.RIGHT, padx=(10,15), pady=8)
        self.send_btn.configure(state="disabled")

        self.voice_lbl = ctk.CTkLabel(
            self.bar, text="🔊" if CONFIG.get("voice_enabled",True) else "🔇",
            font=("Segoe UI", 18), text_color=t["sys_fg"],
            cursor="hand2")
        self.voice_lbl.pack(side=tk.RIGHT, padx=(10,5))
        self.voice_lbl.bind("<Button-1>", self._toggle_voice)

        self.status_var = tk.StringVar(value="")
        
        self._input_hist   = []
        self._input_hist_i = -1

        self.home_frame.pack(fill=tk.BOTH, expand=True)

"""

idx1 = content.find(target_ui_start)
idx2 = content.find(target_ui_end)

if idx1 != -1 and idx2 != -1:
    content = content[:idx1] + new_ui + content[idx2:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("CustomTkinter UI rewrite successful")
else:
    print("Failed to find boundaries")
