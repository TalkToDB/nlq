"""
Main Gradio application.
"""

import gradio as gr
from pathlib import Path
from src.database.manager import DatabaseManager
from src.models.ollama_manager import OllamaConnectionManager
from src.ui.chat import create_chat_tab
from src.ui.connections_tab import create_connections_tab, add_db_connection_handler, delete_db_connection_handler
from src.ui.ollama_tab import create_ollama_tab, add_ollama_connection_handler, delete_ollama_connection_handler
from src.ui.sql_query_tab import create_sql_query_tab
from src.ui.theme import create_theme

# Directory for query results (must match result_storage.py)
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "query_results"

def get_allowed_paths():
    """Get list of paths that can be served by Gradio."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return [str(RESULTS_DIR)]

def create_app():
    """Create and configure the Gradio application."""
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize Ollama connection manager
    ollama_manager = OllamaConnectionManager()
    
    with gr.Blocks(
        title="Database querying in Natural Language with agentic AI",
        theme=create_theme(),
        css="""
        .gradio-container {
            max-width: 90% !important;
            width: 90% !important;
            margin: 0 auto !important;
        }
        h1, h2, h3 {
            font-weight: 600 !important;
        }
        .contain {
            max-width: 100% !important;
        }
        /* Remove number input spinners */
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
        /* Remove scrollbars from textboxes and make them cleaner */
        .scroll-hide {
            overflow: hidden !important;
        }
        input[type="text"], input[type="password"] {
            overflow: hidden !important;
        }
        /* Hide scrollbars in textbox containers */
        label textarea, label input {
            scrollbar-width: none !important;
        }
        label textarea::-webkit-scrollbar, label input::-webkit-scrollbar {
            display: none !important;
        }
        /* Fixed column widths to prevent shifting */
        .block.svelte-1t38q2d {
            min-width: 0 !important;
        }
        /* Ensure consistent spacing */
        .gap {
            gap: 1rem !important;
        }
        /* Fixed width for form columns */
        .form-column {
            min-width: 400px !important;
            max-width: 600px !important;
        }
        /* Make code blocks and history scrollable without affecting page scroll */
        .scrollable-code {
            max-height: 400px;
            overflow-y: auto !important;
        }
        .scrollable-history {
            border: 1px solid #444;
            border-radius: 5px;
            background: #0b0f19;
            overflow: hidden !important;
        }
        /* Query history styles */
        .scrollable-history:empty::before {
            content: "No queries executed yet";
            color: #888;
            font-style: italic;
            padding: 10px;
            display: block;
        }
        """
    ) as app:
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("""
                # Natural Language DB Query
                Query your databases using natural language powered by LLM agents.
                """)
            with gr.Column(scale=0, min_width=100):
                gr.Markdown("")  # Spacer
        
        with gr.Tabs():
            # Query tab
            db_connection_dropdown, ollama_connection_dropdown, model_dropdown = create_chat_tab(db_manager, ollama_manager)
            
            # SQL Query tab
            sql_connection_dropdown = create_sql_query_tab(db_manager)
            
            # Connections management tab
            (save_btn, delete_btn, conn_name, conn_type, connections_table,
             delete_dropdown, edit_dropdown, status_message, all_form_fields, 
             edit_mode_state, cancel_edit_btn) = create_connections_tab(db_manager)
            
            # Ollama backend management tab
            (save_ollama_btn, delete_ollama_btn, ollama_conn_name, ollama_base_url, 
             ollama_api_key, ollama_connections_table, 
             delete_ollama_dropdown, edit_ollama_dropdown, ollama_status_message, 
             edit_ollama_mode_state, cancel_ollama_edit_btn) = create_ollama_tab(ollama_manager)
        
        # Wire up the save connection button (add or update)
        save_btn.click(
            fn=lambda name, db_type, *args: add_db_connection_handler(
                db_manager, name, db_type, *args
            ),
            inputs=[conn_name, conn_type] + all_form_fields + [edit_mode_state],
            outputs=[connections_table, status_message, conn_name, save_btn, cancel_edit_btn,
                    edit_mode_state, db_connection_dropdown, delete_dropdown, edit_dropdown,
                    sql_connection_dropdown] + all_form_fields
        )
        
        # Wire up the delete connection button
        delete_btn.click(
            fn=lambda name: delete_db_connection_handler(db_manager, name),
            inputs=[delete_dropdown],
            outputs=[connections_table, status_message, 
                    db_connection_dropdown, delete_dropdown, edit_dropdown,
                    sql_connection_dropdown]
        )
        
        # Wire up the save Ollama connection button (add or update)
        save_ollama_btn.click(
            fn=lambda name, base_url, api_key, edit_mode: add_ollama_connection_handler(
                ollama_manager, name, base_url, api_key, edit_mode
            ),
            inputs=[ollama_conn_name, ollama_base_url, ollama_api_key, edit_ollama_mode_state],
            outputs=[ollama_connections_table, ollama_status_message, ollama_conn_name, 
                    ollama_base_url, ollama_api_key, save_ollama_btn, 
                    cancel_ollama_edit_btn, edit_ollama_mode_state, ollama_connection_dropdown,
                    delete_ollama_dropdown, edit_ollama_dropdown, model_dropdown]
        )
        
        # Wire up the delete Ollama connection button
        delete_ollama_btn.click(
            fn=lambda name: delete_ollama_connection_handler(ollama_manager, name),
            inputs=[delete_ollama_dropdown],
            outputs=[ollama_connections_table, ollama_status_message, 
                    ollama_connection_dropdown, delete_ollama_dropdown, edit_ollama_dropdown, model_dropdown]
        )
    
    return app


def create_fastapi_app():
    """Create FastAPI app with custom routes, then mount Gradio on it."""
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, JSONResponse
    
    # Create FastAPI app
    fastapi_app = FastAPI()
    
    @fastapi_app.get("/results/{filename}")
    async def serve_result_file(filename: str):
        """Serve a query result JSON file."""
        # Security: only allow .json files and no path traversal
        if not filename.endswith('.json') or '/' in filename or '\\' in filename or '..' in filename:
            return JSONResponse({"error": "Invalid filename"}, status_code=400)
        
        filepath = RESULTS_DIR / filename
        
        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)
        
        return FileResponse(
            path=str(filepath),
            media_type="application/json",
            filename=filename
        )
    
    # Create and mount Gradio app
    gradio_app = create_app()
    fastapi_app = gr.mount_gradio_app(fastapi_app, gradio_app, path="/")
    
    return fastapi_app
