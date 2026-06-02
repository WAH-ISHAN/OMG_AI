import os
import psutil
from .base import BaseAgent

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="SystemAgent", role="Desktop Operating Companion", memory_limit_mb=512)

    def process(self, input_text: str) -> str:
        cmd = input_text.lower().strip()
        
        # Simple OS control routing
        if "volume" in cmd:
            return "Controlling volume is not fully implemented in V10 yet, but hooked up!"
        elif "brightness" in cmd:
            return "Brightness control hooked up."
        elif "open" in cmd:
            target = cmd.replace("open", "").strip()
            return f"Attempting to open {target}..."
        elif "status" in cmd:
            ram = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent()
            return f"System Status: CPU {cpu}%, RAM {ram}%"
        
        return "I can manage your desktop, open apps, and monitor the system. What would you like to do?"

system_agent = SystemAgent()
