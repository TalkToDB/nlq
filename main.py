"""
Database Querying With Natural Language
Main entry point for the Gradio UI.
"""

import uvicorn
from src.ui.app import create_fastapi_app

if __name__ == "__main__":
    app = create_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8080)
