import sys
import os
import threading
import uvicorn
import webview
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

# Initialize FastAPI app for the brain
app = FastAPI(title="OMG_AI V10 Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def get_status():
    return {"status": "online", "version": "10.0"}

def run_api():
    uvicorn.run(app, host="127.0.0.1", port=settings.API_PORT, log_level="info")

def main():
    # Start the API server in a daemon thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Determine if running in development or production
    dev_mode = os.environ.get("DEV_MODE") == "1"
    frontend_url = "http://localhost:5173" if dev_mode else f"http://127.0.0.1:{settings.API_PORT}/"
    
    # Create a frameless, transparent window for the glassmorphism UI
    window = webview.create_window(
        'OMG_AI',
        url=frontend_url,
        frameless=True,
        transparent=True,
        easy_drag=True,
        on_top=True,
        width=400,
        height=600,
        x=20,
        y=20
    )
    
    # Start the webview application
    webview.start(debug=dev_mode)

if __name__ == "__main__":
    main()
