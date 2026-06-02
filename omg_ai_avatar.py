"""
OMG_AI Avatar – Animated Desktop Widget
========================================
• Floating, click-through avatar window (always on top)
• Single-click  → open/close chat panel
• Double-click  → toggle voice-command mode
• Smooth orb animation using tkinter canvas
"""

import os
import sys
import math
import time
import threading
import queue
import logging
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("OMG_AI.Avatar")

# ── Colour palette (matching the reference Siri-style orb) ───────────────────
COLORS = {
    "bg":          "#1a1a2e",
    "orb_core":    "#ffffff",
    "orb_pink":    "#e91e8c",
    "orb_teal":    "#00bcd4",
    "orb_blue":    "#3f51b5",
    "chat_bg":     "#12121f",
    "chat_input":  "#1e1e35",
    "chat_border": "#2d2d50",
    "text":        "#e8e8f0",
    "accent":      "#7c4dff",
    "user_bubble": "#2d2d50",
    "ai_bubble":   "#1a2040",
    "voice_active":"#e91e8c",
}

AVATAR_SIZE   = 140     # px – diameter of the floating orb window
CHAT_W        = 400
CHAT_H        = 560
FONT_CHAT     = ("Segoe UI", 11)
FONT_MONO     = ("Consolas",  10)


# ─────────────────────────────────────────────────────────────────────────────
# Lazy import helper
# ─────────────────────────────────────────────────────────────────────────────
def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# VOICE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self):
        self.sr       = _try_import("speech_recognition")
        self.pyttsx3  = _try_import("pyttsx3")
        self._tts_eng = None
        self._lock    = threading.Lock()
        self._init_tts()

    def _init_tts(self):
        if self.pyttsx3:
            try:
                self._tts_eng = self.pyttsx3.init()
                self._tts_eng.setProperty("rate", 165)
            except Exception as e:
                logger.warning("TTS init failed: %s", e)

    def speak(self, text: str) -> None:
        def _run():
            with self._lock:
                if self._tts_eng:
                    try:
                        self._tts_eng.say(text)
                        self._tts_eng.runAndWait()
                    except Exception as e:
                        logger.warning("TTS error: %s", e)
        threading.Thread(target=_run, daemon=True).start()

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        if not self.sr:
            return None
        r = self.sr.Recognizer()
        try:
            with self.sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.3)
                audio = r.listen(src, timeout=timeout, phrase_time_limit=15)
            return r.recognize_google(audio)
        except self.sr.WaitTimeoutError:
            return None
        except self.sr.UnknownValueError:
            return None
        except Exception as e:
            logger.warning("STT error: %s", e)
            return None

    @property
    def available(self) -> bool:
        return self.sr is not None


# ─────────────────────────────────────────────────────────────────────────────
# ORB CANVAS ANIMATION
# ─────────────────────────────────────────────────────────────────────────────
class OrbCanvas:
    """
    Draws an animated Siri-style orb on a tk.Canvas.
    Uses overlapping semi-transparent ovals rotated over time.
    """

    def __init__(self, canvas, size: int):
        self.canvas = canvas
        self.size   = size
        self.cx     = size // 2
        self.cy     = size // 2
        self.t      = 0.0
        self._items = []
        self._voice_mode = False
        self._pulse      = 0.0

    def draw(self):
        c  = self.canvas
        sz = self.size
        cx = self.cx
        cy = self.cy
        t  = self.t
        for item in self._items:
            c.delete(item)
        self._items.clear()

        # Glow background
        glow_r = sz // 2 - 2
        self._items.append(c.create_oval(
            cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
            fill="#0d0d1a", outline="", width=0
        ))

        # Three petal blobs
        blobs = [
            (COLORS["orb_pink"],  0.0,  0.38),
            (COLORS["orb_teal"],  2.09, 0.38),
            (COLORS["orb_blue"],  4.19, 0.38),
        ]
        scale = 1.0 + 0.06 * math.sin(t * 1.8) + (0.08 * self._pulse)
        for color, phase, rel in blobs:
            angle = t * 0.9 + phase
            off   = sz * rel * scale
            bx    = cx + off * math.cos(angle)
            by    = cy + off * math.sin(angle)
            br    = sz * 0.30 * scale
            # simulate transparency with a lighter version
            self._items.append(c.create_oval(
                bx - br, by - br, bx + br, by + br,
                fill=color, outline="", stipple="gray50"
            ))
            self._items.append(c.create_oval(
                bx - br * 0.6, by - br * 0.6, bx + br * 0.6, by + br * 0.6,
                fill=color, outline=""
            ))

        # Central bright core
        core_r = sz * 0.15 * (1 + 0.04 * math.sin(t * 3))
        self._items.append(c.create_oval(
            cx - core_r, cy - core_r, cx + core_r, cy + core_r,
            fill="white", outline=""
        ))

        # Voice-mode ring
        if self._voice_mode:
            vr = sz // 2 - 4
            dash_anim = int(t * 10) % 20
            self._items.append(c.create_oval(
                cx - vr, cy - vr, cx + vr, cy + vr,
                outline=COLORS["voice_active"], width=3,
                dash=(10 + dash_anim, 6)
            ))

        # Outer shell
        shell_r = sz // 2 - 3
        self._items.append(c.create_oval(
            cx - shell_r, cy - shell_r, cx + shell_r, cy + shell_r,
            outline="#ffffff22", width=1
        ))

        self.t += 0.04
        if self._pulse > 0:
            self._pulse = max(0, self._pulse - 0.05)

    def pulse(self):
        self._pulse = 1.0

    def set_voice_mode(self, active: bool):
        self._voice_mode = active


# ─────────────────────────────────────────────────────────────────────────────
# CHAT PANEL
# ─────────────────────────────────────────────────────────────────────────────
class ChatPanel:
    def __init__(self, root, on_send, position: tuple):
        import tkinter as tk
        from tkinter import scrolledtext

        self.root    = root
        self.on_send = on_send
        self.tk      = tk
        self.win     = tk.Toplevel(root)
        self.win.title("OMG_AI Chat")
        self.win.geometry(f"{CHAT_W}x{CHAT_H}+{position[0]}+{position[1]}")
        self.win.configure(bg=COLORS["chat_bg"])
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        # ── Message log ───────────────────────────────────────────────────────
        self.log = scrolledtext.ScrolledText(
            self.win,
            bg=COLORS["chat_bg"],
            fg=COLORS["text"],
            font=FONT_CHAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            padx=10, pady=10,
            cursor="arrow",
            bd=0,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))

        # Tag styles
        self.log.tag_configure("user",  foreground="#a0c4ff", font=(FONT_CHAT[0], FONT_CHAT[1], "bold"))
        self.log.tag_configure("ai",    foreground=COLORS["text"])
        self.log.tag_configure("sys",   foreground="#666688", font=FONT_MONO)
        self.log.tag_configure("time",  foreground="#444466", font=(FONT_MONO[0], 8))

        # ── Input row ─────────────────────────────────────────────────────────
        row = tk.Frame(self.win, bg=COLORS["chat_bg"])
        row.pack(fill=tk.X, padx=6, pady=6)

        self.entry = tk.Entry(
            row, bg=COLORS["chat_input"], fg=COLORS["text"],
            font=FONT_CHAT, relief=tk.FLAT, bd=8,
            insertbackground=COLORS["text"],
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)

        send_btn = tk.Button(
            row, text="▶", command=self._on_send_btn,
            bg=COLORS["accent"], fg="white",
            relief=tk.FLAT, bd=0, padx=10, pady=4,
            activebackground="#6040dd", cursor="hand2",
        )
        send_btn.pack(side=tk.LEFT, padx=(4, 0))

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(
            self.win, textvariable=self.status_var,
            bg=COLORS["chat_bg"], fg="#555577",
            font=(FONT_MONO[0], 8), anchor="w",
        )
        status.pack(fill=tk.X, padx=8, pady=(0, 2))

        self._append_sys("OMG_AI online. Type a message or double-click the orb for voice.")
        self.win.withdraw()   # start hidden

    def show(self):
        self.win.deiconify()
        self.win.lift()
        self.entry.focus()

    def hide(self):
        self.win.withdraw()

    def is_visible(self) -> bool:
        return self.win.state() != "withdrawn"

    def _on_enter(self, event=None):
        self._on_send_btn()

    def _on_send_btn(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, self.tk.END)
        self._append("You", text, "user")
        self.status_var.set("Thinking …")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text: str):
        response = self.on_send(text)
        self.win.after(0, lambda: self._append("OMG_AI", response, "ai"))
        self.win.after(0, lambda: self.status_var.set("Ready"))

    def _append(self, speaker: str, text: str, tag: str):
        import tkinter as tk
        ts = datetime.now().strftime("%H:%M")
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"\n{ts}  ", "time")
        self.log.insert(tk.END, f"{speaker}\n", tag)
        self.log.insert(tk.END, text + "\n", tag)
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def _append_sys(self, text: str):
        import tkinter as tk
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"[system] {text}\n", "sys")
        self.log.configure(state=tk.DISABLED)

    def append_voice(self, speaker: str, text: str):
        tag = "user" if speaker == "You" else "ai"
        self.win.after(0, lambda: self._append(speaker, text, tag))


# ─────────────────────────────────────────────────────────────────────────────
# AVATAR WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class AvatarWindow:
    CLICK_THRESHOLD = 300   # ms – double-click detection

    def __init__(self, core):
        """
        core – an OMGAICore instance (or a compatible duck-type).
        """
        import tkinter as tk
        self.core   = core
        self.tk     = tk
        self.voice  = VoiceEngine()

        self.root   = tk.Tk()
        self.root.title("OMG_AI")
        self.root.geometry(f"{AVATAR_SIZE}x{AVATAR_SIZE}+80+80")
        self.root.configure(bg="#1a1a2e")
        self.root.attributes("-topmost",      True)
        self.root.attributes("-alpha",        0.93)
        self.root.overrideredirect(True)      # borderless
        try:
            self.root.attributes("-transparentcolor", "#1a1a2e")
        except Exception:
            pass

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=AVATAR_SIZE, height=AVATAR_SIZE,
            bg="#1a1a2e", highlightthickness=0
        )
        self.canvas.pack()

        self.orb  = OrbCanvas(self.canvas, AVATAR_SIZE)
        self.chat = ChatPanel(
            self.root,
            on_send=self._on_chat_send,
            position=(80 + AVATAR_SIZE + 10, 80),
        )

        # Drag support
        self._drag_x = self._drag_y = 0
        self.canvas.bind("<ButtonPress-1>",   self._drag_start)
        self.canvas.bind("<B1-Motion>",       self._drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._click_release)

        # Double-click
        self._last_click   = 0.0
        self._voice_active = False
        self._voice_q: queue.Queue = queue.Queue()

        self.root.after(20, self._animate)
        self.root.after(100, self._poll_voice_q)

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y
        self._moved  = False

    def _drag_motion(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        if abs(dx) + abs(dy) > 3:
            self._moved = True
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _click_release(self, e):
        if self._moved:
            return
        now = time.time() * 1000
        if now - self._last_click < self.CLICK_THRESHOLD:
            # double-click
            self._toggle_voice()
        else:
            # schedule single-click
            self.root.after(
                self.CLICK_THRESHOLD,
                lambda t=now: self._single_click_if_no_dbl(t),
            )
        self._last_click = now

    def _single_click_if_no_dbl(self, t: float):
        if abs(t - self._last_click) < 10:   # same click, no dbl followed
            self._toggle_chat()

    # ── Chat ──────────────────────────────────────────────────────────────────
    def _toggle_chat(self):
        if self.chat.is_visible():
            self.chat.hide()
        else:
            # Position chat beside avatar
            ax = self.root.winfo_x()
            ay = self.root.winfo_y()
            self.chat.win.geometry(f"{CHAT_W}x{CHAT_H}+{ax + AVATAR_SIZE + 10}+{ay}")
            self.chat.show()

    def _on_chat_send(self, text: str) -> str:
        self.orb.pulse()
        response = self.core.process(text)
        return response

    # ── Voice ─────────────────────────────────────────────────────────────────
    def _toggle_voice(self):
        self._voice_active = not self._voice_active
        self.orb.set_voice_mode(self._voice_active)
        if self._voice_active:
            self.voice.speak("Voice mode activated. I'm listening.")
            threading.Thread(target=self._voice_loop, daemon=True).start()
        else:
            self.voice.speak("Voice mode off.")
            logger.info("Voice mode deactivated")

    def _voice_loop(self):
        while self._voice_active:
            spoken = self.voice.listen_once(timeout=7)
            if spoken:
                logger.info("Voice input: %s", spoken)
                self._voice_q.put(spoken)
            elif self._voice_active:
                time.sleep(0.2)

    def _poll_voice_q(self):
        try:
            while True:
                spoken = self._voice_q.get_nowait()
                self.chat.show()
                self.chat.append_voice("You", spoken)
                self.orb.pulse()
                # process in background
                def _respond(text=spoken):
                    resp = self.core.process(text)
                    self.chat.append_voice("OMG_AI", resp)
                    self.voice.speak(resp[:300])   # cap TTS length
                threading.Thread(target=_respond, daemon=True).start()
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_voice_q)

    # ── Animation loop ────────────────────────────────────────────────────────
    def _animate(self):
        self.orb.draw()
        self.root.after(40, self._animate)   # ~25 fps

    # ── Run ───────────────────────────────────────────────────────────────────
    def run(self):
        logger.info("Avatar window starting …")
        self.root.mainloop()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Import core (assumes same directory)
    sys.path.insert(0, str(Path(__file__).parent))
    from omg_ai_core import OMGAICore

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    core = OMGAICore()
    core.start()

    avatar = AvatarWindow(core)
    avatar.run()
