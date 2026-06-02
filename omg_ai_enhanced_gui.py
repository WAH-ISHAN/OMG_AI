#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║    OMG_AI ENHANCED GUI v2.0  —  AGENT-INTEGRATED INTERFACE              ║
║  Animated Agent Icons  •  Voice Command Routing  •  Real-time Monitor    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from pathlib import Path
import json
import threading
import time
import psutil
from datetime import datetime
from typing import Optional, Callable
import base64
from PIL import Image, ImageDraw
import io

# Import agent system
try:
    from omg_ai_agent_system import (
        AgentPool, VoiceCommandHandler, AgentIconAnimator,
        initialize_agent_system
    )
except ImportError:
    print("Warning: Agent system not available. Running in basic mode.")
    AgentPool = None


# ──────────────────────────────────────────────────────────────────────────────
# ANIMATED AGENT ICON WIDGET
# ──────────────────────────────────────────────────────────────────────────────

class AnimatedAgentIcon(ctk.CTkFrame):
    """Animated agent icon with real-time state indicator"""
    
    def __init__(self, parent, agent_name: str, agent_type: str,
                 agent_id: str, on_click: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.on_click = on_click
        self.state = "idle"
        self.is_animating = True
        self.animation_step = 0
        
        # Color schemes
        self.colors = {
            "coder":     ("#00D9FF", "#001a2f"),
            "analyst":   ("#FFD700", "#2a2000"),
            "security":  ("#FF4444", "#2a0000"),
            "optimizer": ("#00FF44", "#002a00"),
            "generic":   ("#00D4FF", "#0a0a1a"),
        }
        
        self._build_ui()
        self._start_animation()
    
    def _build_ui(self):
        """Build the icon widget"""
        self.configure(fg_color="transparent", corner_radius=12)
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas for animated icon
        self.canvas = tk.Canvas(
            main_frame,
            width=120, height=120,
            bg="#0a0a0a", highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(pady=(0, 10))
        self.canvas.bind("<Button-1>", self._on_click)
        
        # Agent name
        name_label = ctk.CTkLabel(
            main_frame,
            text=self.agent_name,
            font=("Segoe UI", 13, "bold"),
            text_color="#ECECEC"
        )
        name_label.pack()
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.status_frame.pack(fill="x", pady=(5, 0))
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="● idle",
            font=("Segoe UI", 10),
            text_color="#6E6E80"
        )
        self.status_indicator.pack(side="left")
        
        self.accuracy_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Segoe UI", 9),
            text_color="#6E6E80"
        )
        self.accuracy_label.pack(side="right")
        
        # Draw initial icon
        self._draw_icon()
    
    def _draw_icon(self):
        """Draw animated agent icon on canvas"""
        self.canvas.delete("all")
        
        color, dark_color = self.colors.get(self.agent_type, self.colors["generic"])
        
        # Pulse sizing calculation based on animation step and state
        self.animation_step = (self.animation_step + 1) % 10
        pulse_diff = self.animation_step if self.state != "idle" else (self.animation_step * 0.5)
        
        # Background circle
        self.canvas.create_oval(
            10, 10, 110, 110,
            fill="#0a0a0a",
            outline=color,
            width=2
        )
        
        # Outer pulsing rings
        for base_ring in [85, 70]:
            if self.state == "active":
                ring = base_ring + pulse_diff
            elif self.state == "training":
                ring = base_ring - pulse_diff
            else:
                ring = base_ring + (pulse_diff * 0.3)
                
            self.canvas.create_oval(
                60 - ring // 2, 60 - ring // 2, 60 + ring // 2, 60 + ring // 2,
                outline=color,
                width=1,
                fill=""
            )
        
        # Core sphere
        self.canvas.create_oval(
            50, 50, 70, 70,
            fill=color,
            outline=color
        )
        
        # Inner glow
        self.canvas.create_oval(
            52, 52, 68, 68,
            fill="",
            outline=color,
            width=1
        )
        
        # Center point
        self.canvas.create_oval(
            58, 58, 62, 62,
            fill=color
        )
        
        # Agent type symbol
        self.canvas.create_text(
            60, 95,
            text=self.agent_type[0].upper(),
            font=("Arial", 10, "bold"),
            fill=color
        )
    
    def _start_animation(self):
        """Start animation loop"""
        self._animate()
    
    def _animate(self):
        """Animate icon based on state"""
        if not self.is_animating:
            return
        
        self._draw_icon()
        self.canvas.after(300, self._animate)
    
    def update_state(self, new_state: str, accuracy: float = 0.0):
        """Update agent state and accuracy"""
        self.state = new_state
        
        color_map = {
            "idle": ("#6E6E80", "● idle"),
            "active": ("#00FF44", "● active"),
            "training": ("#FFD700", "⟳ training"),
            "error": ("#FF4444", "✗ error"),
        }
        
        color, text = color_map.get(new_state, ("#6E6E80", "?"))
        self.status_indicator.configure(text_color=color, text=text)
        
        if accuracy > 0:
            self.accuracy_label.configure(text=f"{accuracy:.0%}")
    
    def _on_click(self, event=None):
        """Handle icon click"""
        if self.on_click:
            self.on_click(self.agent_id)
    
    def stop_animation(self):
        """Stop animation"""
        self.is_animating = False


# ──────────────────────────────────────────────────────────────────────────────
# AGENT PANEL WIDGET
# ──────────────────────────────────────────────────────────────────────────────

class AgentPanel(ctk.CTkFrame):
    """Side panel showing all agents with animated icons"""
    
    def __init__(self, parent, agent_pool: AgentPool,
                 on_agent_selected: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.agent_pool = agent_pool
        self.on_agent_selected = on_agent_selected
        self.agent_widgets = {}
        self.selected_agent_id = None
        
        self._build_ui()
        self._start_update_loop()
    
    def _build_ui(self):
        """Build agent panel UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 20))
        
        ctk.CTkLabel(
            header,
            text="◉ Active Agents",
            font=("Segoe UI", 14, "bold"),
            text_color="#ECECEC"
        ).pack(side="left")
        
        create_btn = ctk.CTkButton(
            header,
            text="+",
            font=("Segoe UI", 14, "bold"),
            fg_color="#10A37F",
            text_color="#FFFFFF",
            width=30,
            height=30,
            corner_radius=6,
            command=self._show_create_dialog
        )
        create_btn.pack(side="right")
        
        # Scrollable frame for agents
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10)
        
        # Stats frame
        stats_frame = ctk.CTkFrame(self, fg_color="#2F2F2F", corner_radius=8)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="#9B9B9B",
            justify="left"
        )
        self.stats_label.pack(padx=10, pady=10)
        
        self._refresh_agents()
    
    def _refresh_agents(self):
        """Refresh agent list display"""
        # Clear existing widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.agent_widgets.clear()
        
        # Create widgets for each agent
        for agent in self.agent_pool.list_agents():
            icon = AnimatedAgentIcon(
                self.scroll_frame,
                agent_name=agent["name"],
                agent_type=agent["type"],
                agent_id=agent["id"],
                on_click=self._on_agent_click,
                fg_color="#2F2F2F"
            )
            icon.pack(fill="x", pady=5)
            
            self.agent_widgets[agent["id"]] = {
                "widget": icon,
                "state": agent["state"],
                "accuracy": agent["accuracy"]
            }
            
            # Update state
            icon.update_state(agent["state"], agent["accuracy"])
    
    def _on_agent_click(self, agent_id: str):
        """Handle agent click"""
        self.selected_agent_id = agent_id
        
        # Highlight selected agent
        for aid, info in self.agent_widgets.items():
            widget = info["widget"]
            if aid == agent_id:
                widget.configure(fg_color="#424242")
            else:
                widget.configure(fg_color="#2F2F2F")
        
        if self.on_agent_selected:
            self.on_agent_selected(agent_id)
    
    def _show_create_dialog(self):
        """Show dialog to create new agent"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Agent")
        dialog.geometry("400x250")
        dialog.attributes("-topmost", True)
        
        # Name input
        ctk.CTkLabel(dialog, text="Agent Name:", font=("Segoe UI", 12)).pack(pady=(15, 0), padx=20)
        name_entry = ctk.CTkEntry(dialog, placeholder_text="Enter agent name")
        name_entry.pack(fill="x", padx=20, pady=5)
        
        # Type selection
        ctk.CTkLabel(dialog, text="Agent Type:", font=("Segoe UI", 12)).pack(pady=(10, 0), padx=20)
        type_combo = ctk.CTkComboBox(
            dialog,
            values=["coder", "analyst", "security", "optimizer", "generic"],
            state="readonly"
        )
        type_combo.set("generic")
        type_combo.pack(fill="x", padx=20, pady=5)
        
        def create():
            name = name_entry.get().strip()
            agent_type = type_combo.get()
            
            if not name:
                messagebox.showerror("Error", "Please enter agent name")
                return
            
            agent_id = self.agent_pool.create_agent(name, agent_type)
            if agent_id:
                self._refresh_agents()
                dialog.destroy()
                messagebox.showinfo("Success", f"Agent created: {agent_id}")
            else:
                messagebox.showerror("Error", "Insufficient memory or pool limit reached.")
        
        ctk.CTkButton(dialog, text="Create", command=create).pack(pady=20)
    
    def _update_stats(self):
        """Update resource stats"""
        mem = psutil.virtual_memory()
        max_agents = self.agent_pool.get_max_agents()
        
        stats_text = (
            f"Active: {len(self.agent_pool.agents)}\n"
            f"Max Possible: {max_agents}\n"
            f"RAM: {mem.percent:.0f}% | "
            f"CPU: {psutil.cpu_percent():.0f}%"
        )
        
        self.stats_label.configure(text=stats_text)
    
    def _start_update_loop(self):
        """Start background update loop"""
        def update():
            while True:
                try:
                    self._update_stats()
                    
                    # Update agent states
                    for agent in self.agent_pool.list_agents():
                        if agent["id"] in self.agent_widgets:
                            info = self.agent_widgets[agent["id"]]
                            if (info["state"] != agent["state"] or 
                                info["accuracy"] != agent["accuracy"]):
                                info["widget"].update_state(
                                    agent["state"],
                                    agent["accuracy"]
                                )
                                info["state"] = agent["state"]
                                info["accuracy"] = agent["accuracy"]
                    
                    time.sleep(2)
                except:
                    pass
        
        thread = threading.Thread(target=update, daemon=True)
        thread.start()


# ──────────────────────────────────────────────────────────────────────────────
# INTEGRATION WITH MAIN OMG_AI GUI
# ──────────────────────────────────────────────────────────────────────────────

class EnhancedOMGAIWindow(ctk.CTkToplevel):
    """Enhanced OMG_AI window with agent integration"""
    
    def __init__(self, parent=None, agent_pool: AgentPool = None):
        super().__init__(parent)
        
        self.title("OMG_AI v4.0+ with Agent System")
        self.geometry("1200x700")
        self.configure(fg_color="#212121")
        
        self.agent_pool = agent_pool or (initialize_agent_system() if AgentPool else None)
        self.voice_handler = VoiceCommandHandler(self.agent_pool) if self.agent_pool else None
        self.selected_agent_id = None
        
        self._build_layout()
        self.configure_tags()
        
        # Lift and request focus
        self.lift()
        self.focus_force()
    
    def _build_layout(self):
        """Build main window layout"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="#212121")
        main_frame.pack(fill="both", expand=True)
        
        # Left sidebar - Agent panel
        if self.agent_pool:
            left_panel = ctk.CTkFrame(main_frame, fg_color="#0a0a0a", width=200)
            left_panel.pack(side="left", fill="both", padx=10, pady=10)
            
            agent_panel = AgentPanel(
                left_panel,
                self.agent_pool,
                on_agent_selected=self._on_agent_selected,
                fg_color="#0a0a0a"
            )
            agent_panel.pack(fill="both", expand=True)
        
        # Right panel - Chat interface
        right_panel = ctk.CTkFrame(main_frame, fg_color="#212121")
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Chat header
        header = ctk.CTkFrame(right_panel, fg_color="transparent")
        header.pack(fill="x", pady=10)
        
        self.agent_label = ctk.CTkLabel(
            header,
            text="Select an agent to start",
            font=("Segoe UI", 14, "bold"),
            text_color="#ECECEC"
        )
        self.agent_label.pack(side="left")
        
        voice_btn = ctk.CTkButton(
            header,
            text="🎤 Voice",
            font=("Segoe UI", 11),
            fg_color="#10A37F",
            command=self._start_voice_input
        )
        voice_btn.pack(side="right", padx=5)
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            right_panel,
            fg_color="#2F2F2F",
            text_color="#ECECEC",
            font=("Segoe UI", 12),
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))
        self.chat_display.configure(state="disabled")
        
        # Input area
        input_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        input_container.pack(fill="x")
        
        self.input_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Type message or voice command...",
            font=("Segoe UI", 12)
        )
        self.input_entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", self._send_message)
        
        send_btn = ctk.CTkButton(
            input_container,
            text="↑",
            font=("Segoe UI", 12, "bold"),
            width=40,
            command=self._send_message
        )
        send_btn.pack(side="right")
    
    def _on_agent_selected(self, agent_id: str):
        """Handle agent selection"""
        self.selected_agent_id = agent_id
        agent = self.agent_pool.get_agent(agent_id)
        
        if agent:
            self.agent_label.configure(text=f"Speaking with {agent.name}")
            self._append_message(f"[Connected to {agent.name}]", "system")
    
    def _send_message(self, event=None):
        """Send message to selected agent"""
        if not self.selected_agent_id:
            messagebox.showwarning("Warning", "Please select an agent first")
            return
        
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.input_entry.delete(0, "end")
        
        self._append_message(message, "user")
        
        # Process with agent
        threading.Thread(
            target=self._process_message,
            args=(self.selected_agent_id, message),
            daemon=True
        ).start()
    
    def _process_message(self, agent_id: str, message: str):
        """Process message with agent (in background)"""
        try:
            # Change state to active during processing
            agent = self.agent_pool.get_agent(agent_id)
            if agent:
                agent.state = "active"
                
            response = self.agent_pool.process_with_agent(agent_id, message)
            self._append_message(response, "agent")
        except Exception as e:
            self._append_message(f"Error: {e}", "error")
    
    def _start_voice_input(self):
        """Start voice input (placeholder)"""
        self._append_message("[Voice input not yet implemented]", "system")
    
    def _append_message(self, message: str, sender: str = "agent"):
        """Append message to chat display"""
        self.chat_display.configure(state="normal")
        
        if sender == "user":
            self.chat_display.insert("end", f"You: {message}\n\n", "user")
        elif sender == "agent":
            agent = self.agent_pool.get_agent(self.selected_agent_id)
            name = agent.name if agent else "Agent"
            self.chat_display.insert("end", f"{name}: {message}\n\n", "agent")
        elif sender == "system":
            self.chat_display.insert("end", f"[{message}]\n\n", "system")
        else:
            self.chat_display.insert("end", f"Error: {message}\n\n", "error")
            
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
    
    def configure_tags(self):
        """Configure text display tags (scaling compatible: no font option)"""
        self.chat_display.tag_config("user", foreground="#00FFCC")
        self.chat_display.tag_config("agent", foreground="#FFD700")
        self.chat_display.tag_config("system", foreground="#6E6E80")
        self.chat_display.tag_config("error", foreground="#FF4444")


def launch_enhanced_gui():
    """Launch enhanced GUI"""
    root = ctk.CTk()
    root.withdraw()
    
    if AgentPool:
        pool = initialize_agent_system()
        app = EnhancedOMGAIWindow(parent=root, agent_pool=pool)
    else:
        app = EnhancedOMGAIWindow(parent=root)
    
    app.mainloop()


if __name__ == "__main__":
    launch_enhanced_gui()
