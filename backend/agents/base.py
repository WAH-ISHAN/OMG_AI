from typing import List, Dict, Any

class BaseAgent:
    def __init__(self, name: str, role: str, memory_limit_mb: int = 1024):
        self.name = name
        self.role = role
        self.memory_limit_mb = memory_limit_mb
        self.history: List[Dict[str, Any]] = []

    def process(self, input_text: str) -> str:
        """Process the input text and return a response."""
        raise NotImplementedError("Each agent must implement its own process method.")

    def get_context(self) -> str:
        """Returns the current context window for the agent."""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[-10:]])
