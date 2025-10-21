"""
Main Gradio application.
"""

import gradio as gr
from src.database.manager import DatabaseManager
from src.ui.chat import create_chat_tab
from src.ui.connections_tab import create_connections_tab, add_db_connection_handler, delete_db_connection_handler
from src.ui.sql_query_tab import create_sql_query_tab
from src.ui.theme import create_theme

def create_app():
    """Create and configure the Gradio application."""
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    with gr.Blocks(
        title="Database Querying with Natural Language",
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
            connection_dropdown = create_chat_tab(db_manager)
            
            # SQL Query tab
            sql_connection_dropdown = create_sql_query_tab(db_manager)
            
            # Connections management tab
            (save_btn, delete_btn, conn_name, conn_type, connections_table,
             delete_dropdown, edit_dropdown, status_message, all_form_fields, 
             edit_mode_state, cancel_edit_btn) = create_connections_tab(db_manager)
        
        # Wire up the save connection button (add or update)
        save_btn.click(
            fn=lambda name, db_type, *args: add_db_connection_handler(
                db_manager, name, db_type, *args
            ),
            inputs=[conn_name, conn_type] + all_form_fields + [edit_mode_state],
            outputs=[connections_table, status_message, conn_name, save_btn, cancel_edit_btn,
                    edit_mode_state, connection_dropdown, delete_dropdown, edit_dropdown,
                    sql_connection_dropdown] + all_form_fields
        )
        
        # Wire up the delete connection button
        delete_btn.click(
            fn=lambda name: delete_db_connection_handler(db_manager, name),
            inputs=[delete_dropdown],
            outputs=[connections_table, status_message, 
                    connection_dropdown, delete_dropdown, edit_dropdown,
                    sql_connection_dropdown]
        )
    
    return app
