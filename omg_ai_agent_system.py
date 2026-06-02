import logging
from typing import List, Dict, Optional
from omg_ai_core import OMGAICore, Agent

logger = logging.getLogger("OMG_AI.AgentSystemBridge")

class AgentPool:
    def __init__(self):
        # Access the global core instance or create a singleton
        self.core = initialize_core_singleton()
        
    def list_agents(self) -> List[Dict]:
        roles_mapping = {
            "File & code analysis": ("CodeGPT", "coder"),
            "Web research summariser": ("DataBot", "analyst"),
            "Calendar & task planner": ("Planner", "generic"),
            "System monitoring": ("SecShield", "security"),
            "Data extraction & formatting": ("FormatBot", "generic"),
            "Creative writing assistant": ("CreativeBot", "generic"),
            "Math & logic reasoning": ("LogicBot", "generic"),
            "General Q&A": ("QABot", "generic")
        }
        res = []
        with self.core.agents._lock:
            for ag_id, ag in self.core.agents.agents.items():
                # Use custom name/type if dynamically created
                name = getattr(ag, "custom_name", None)
                atype = getattr(ag, "custom_type", None)
                if not name or not atype:
                    name, atype = roles_mapping.get(ag.role, (f"Agent {ag_id}", "generic"))
                res.append({
                    "id": ag_id,
                    "name": name,
                    "type": atype,
                    "state": getattr(ag, "state", "idle"),
                    "accuracy": getattr(ag, "accuracy", 0.90)
                })
        return res
        
    def get_agent(self, agent_id: str):
        roles_mapping = {
            "File & code analysis": ("CodeGPT", "coder"),
            "Web research summariser": ("DataBot", "analyst"),
            "Calendar & task planner": ("Planner", "generic"),
            "System monitoring": ("SecShield", "security"),
            "Data extraction & formatting": ("FormatBot", "generic"),
            "Creative writing assistant": ("CreativeBot", "generic"),
            "Math & logic reasoning": ("LogicBot", "generic"),
            "General Q&A": ("QABot", "generic")
        }
        with self.core.agents._lock:
            ag = self.core.agents.agents.get(agent_id)
            if ag:
                name = getattr(ag, "custom_name", None)
                if not name:
                    name, _ = roles_mapping.get(ag.role, (f"Agent {agent_id}", "generic"))
                
                class AgentWrapper:
                    def __init__(self, name):
                        self.name = name
                return AgentWrapper(name)
        return None
        
    def create_agent(self, name: str, agent_type: str) -> Optional[str]:
        # Limit to max agents
        if len(self.core.agents.agents) >= self.get_max_agents():
            return None
            
        aid = f"agent_{len(self.core.agents.agents):02d}"
        roles = {
            "coder": "File & code analysis",
            "analyst": "Web research summariser",
            "security": "System monitoring",
            "optimizer": "Data extraction & formatting",
            "generic": "General Q&A"
        }
        role = roles.get(agent_type, "General Q&A")
        
        ag = Agent(aid, role, self.core.llm, self.core.kb)
        ag.custom_name = name
        ag.custom_type = agent_type
        ag.start()
        
        with self.core.agents._lock:
            self.core.agents.agents[aid] = ag
            
        return aid
        
    def get_max_agents(self) -> int:
        return self.core.agents.max_agents()

    def process_with_agent(self, agent_id: str, message: str) -> str:
        # This will call the dispatch method of AgentManager
        # which submits the task and waits for the response
        response = self.core.agents.dispatch(message, agent_id)
        return response if response else "No response received from agent."

class VoiceCommandHandler:
    def __init__(self, agent_pool: AgentPool):
        self.agent_pool = agent_pool
        
    def listen_and_route(self) -> Optional[str]:
        return None

class AgentIconAnimator:
    def __init__(self):
        pass

# Core singleton management
_core_instance = None

def initialize_core_singleton() -> OMGAICore:
    global _core_instance
    if _core_instance is None:
        _core_instance = OMGAICore()
        _core_instance.start()
    return _core_instance

def initialize_agent_system() -> AgentPool:
    return AgentPool()
