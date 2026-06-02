import os
from llama_cpp import Llama
from core.config import settings

class LocalLLM:
    def __init__(self):
        self.llm = None
        
    def load_model(self):
        if not os.path.exists(settings.LLM_MODEL_PATH):
            print(f"Warning: Model not found at {settings.LLM_MODEL_PATH}")
            return False
            
        try:
            self.llm = Llama(
                model_path=settings.LLM_MODEL_PATH,
                n_gpu_layers=-1, # Accelerate completely on GPU
                n_ctx=4096,      # Max context
                verbose=False
            )
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 512, stream: bool = True):
        if not self.llm:
            return "Error: AI Model is offline."
            
        return self.llm.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            stream=stream,
            temperature=0.7
        )

local_llm = LocalLLM()
