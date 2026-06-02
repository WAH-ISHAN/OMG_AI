from .base import BaseAgent

class VoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="VoiceAgent", role="Voice Controller and TTS/STT Handler", memory_limit_mb=1024)

    def process(self, input_text: str) -> str:
        return f"Voice engine processing: {input_text}"

voice_agent = VoiceAgent()
