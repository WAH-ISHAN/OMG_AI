import os

class Settings:
    PROJECT_NAME: str = "OMG_AI V10"
    API_PORT: int = 8000
    LLM_MODEL_PATH: str = os.path.join("models", "llama-2-7b-chat.gguf")
    DB_PATH: str = os.path.join("memory", "chroma_db")

settings = Settings()
