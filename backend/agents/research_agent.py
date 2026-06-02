from .base import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ResearchAgent", role="Web and Document Researcher", memory_limit_mb=1024)

    def process(self, input_text: str) -> str:
        return f"Researching: {input_text}"

research_agent = ResearchAgent()
