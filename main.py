"""
Database Querying With Natural Language
Main entry point for the Gradio UI.
"""

from src.ui.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.launch(share=False, server_name="127.0.0.1", server_port=8080)
