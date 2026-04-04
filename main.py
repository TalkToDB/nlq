"""
Database Querying With Natural Language
Main entry point for the Gradio UI.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import os
import uvicorn
from src.ui.app import create_fastapi_app

if __name__ == "__main__":
    app = create_fastapi_app()
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 7860)),
    )
