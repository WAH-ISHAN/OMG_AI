import psutil
from typing import Dict
from .base import BaseAgent

class AgentManager:
    def __init__(self):
        self.active_agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self.active_agents[agent.name] = agent

    def remove_agent(self, agent_name: str):
        if agent_name in self.active_agents:
            del self.active_agents[agent_name]

    def monitor_resources(self) -> dict:
        """Monitor RAM and CPU usage of the system to scale agents."""
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        # Enforce memory constraints dynamically
        # If RAM > 90%, we should start swapping or sleeping idle agents
        return {
            "ram_percent": ram.percent,
            "cpu_percent": cpu,
            "active_agents": list(self.active_agents.keys())
        }

agent_manager = AgentManager()
