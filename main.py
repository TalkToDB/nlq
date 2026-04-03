"""
Database Querying With Natural Language
Main entry point for the Gradio UI.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import os
from src.ui.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.launch(
        share=False,
        server_name=os.getenv("HOST", "0.0.0.0"),
        server_port=int(os.getenv("PORT", 7860)),
    )
