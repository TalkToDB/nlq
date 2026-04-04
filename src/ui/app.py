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
from src.agent.result_storage import RESULTS_DIR

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

        # Re-hydrate all dropdowns and tables on every page load / refresh.
        # Without this, Gradio resets components to their app-creation-time initial
        # values, so connections added after startup would be missing until restart.
        def _refresh_on_load():
            db_manager.reload_connections()
            ollama_manager.reload_connections()
            db_names = db_manager.get_connection_names()
            ollama_names = ollama_manager.get_connection_names()
            return (
                gr.update(choices=db_names),           # db_connection_dropdown (chat tab)
                gr.update(choices=ollama_names),        # ollama_connection_dropdown (chat tab)
                gr.update(choices=db_names),            # sql_connection_dropdown
                db_manager.get_connections_table(),     # connections_table
                gr.update(choices=db_names),            # delete_dropdown
                gr.update(choices=db_names),            # edit_dropdown
                ollama_manager.get_connections_table(), # ollama_connections_table
                gr.update(choices=ollama_names),        # delete_ollama_dropdown
                gr.update(choices=ollama_names),        # edit_ollama_dropdown
            )

        app.load(
            fn=_refresh_on_load,
            outputs=[
                db_connection_dropdown,
                ollama_connection_dropdown,
                sql_connection_dropdown,
                connections_table,
                delete_dropdown,
                edit_dropdown,
                ollama_connections_table,
                delete_ollama_dropdown,
                edit_ollama_dropdown,
            ]
        )

    return app


def create_fastapi_app():
    """Create FastAPI app with custom routes, then mount Gradio on it."""
    import json
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
    
    # Create FastAPI app
    fastapi_app = FastAPI()
    
    @fastapi_app.get("/results/{filename}")
    async def serve_result_file(filename: str):
        """Serve a query result JSON file as a styled HTML page."""
        # Security: only allow .json files and no path traversal
        if not filename.endswith('.json') or '/' in filename or '\\' in filename or '..' in filename:
            return JSONResponse({"error": "Invalid filename"}, status_code=400)
        
        filepath = RESULTS_DIR / filename
        
        if not filepath.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        json_str = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{filename}</title>
<style>
  body {{
    margin: 0; padding: 20px;
    background: #0d1117; color: #e6edf3;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  }}
  h1 {{
    font-size: 1.1rem; color: #58a6ff;
    border-bottom: 1px solid #30363d; padding-bottom: 10px;
    word-break: break-all;
  }}
  .meta {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 16px; }}
  .meta span {{ margin-right: 18px; }}
  pre {{
    background: #161b22; border: 1px solid #30363d;
    border-radius: 6px; padding: 16px;
    overflow-x: auto; font-size: 0.85rem;
    line-height: 1.5;
  }}
  .key {{ color: #ff7b72; }}
  .str {{ color: #a5d6ff; }}
  .num {{ color: #79c0ff; }}
  .bool {{ color: #f0883e; }}
  .null {{ color: #8b949e; }}
</style>
</head>
<body>
<h1>{filename}</h1>
<div class="meta">
  <span>Query: {data.get('query_text', 'N/A')}</span>
  <span>Database: {data.get('database_type', 'N/A')}</span>
  <span>Rows: {data.get('row_count', 'N/A')}</span>
</div>
<pre id="json"></pre>
<script>
const data = {json_str};
function highlight(obj, indent) {{
  const s = JSON.stringify(obj, null, 2);
  return s
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"([^"]+)"(?=\\s*:)/g, '<span class="key">"$1"</span>')
    .replace(/: "(.*?)"/g, ': <span class="str">"$1"</span>')
    .replace(/: (\\d+\\.?\\d*)/g, ': <span class="num">$1</span>')
    .replace(/: (true|false)/g, ': <span class="bool">$1</span>')
    .replace(/: (null)/g, ': <span class="null">$1</span>');
}}
document.getElementById('json').innerHTML = highlight(data);
</script>
</body>
</html>"""
        return HTMLResponse(content=html)
    
    # Create and mount Gradio app
    gradio_app = create_app()
    fastapi_app = gr.mount_gradio_app(fastapi_app, gradio_app, path="/")
    
    return fastapi_app
