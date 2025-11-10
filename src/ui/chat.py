"""
Query tab UI component.
"""

import gradio as gr
from src.models.ollama_api import OllamaAPINew
from src.agent.query_engine import execute_agent_query_with_graph

def update_model_choices(ollama_manager, ollama_connection_name: str):
    """Update model dropdown based on Ollama connection selection."""
    if not ollama_connection_name or not ollama_connection_name.strip():
        gr.Warning("Please select an Ollama connection to load models")
        return gr.update(choices=[], value=None, interactive=True)
    
    # Get connection details
    conn = ollama_manager.get_connection(ollama_connection_name)
    if not conn:
        gr.Warning(f"Connection '{ollama_connection_name}' not found")
        return gr.update(choices=[], value=None, interactive=True)
    
    # Try to get real models from Ollama API
    try:
        ollama_api = OllamaAPINew(
            base_url=conn['base_url'],
            model_name="",  # Empty for getting models list
            username=conn.get('username', ''),
            password=conn.get('password', ''),
            should_authenticate=conn.get('should_authenticate', False)
        )
        models_data = ollama_api.get_models()
        
        if models_data:
            # Extract model IDs from the response
            models = [model["id"] for model in models_data]
            default_model = models[0] if models else None
            gr.Info(f"✅ Successfully loaded {len(models)} models from Ollama")
            return gr.update(choices=models, value=default_model, interactive=True)
        else:
            gr.Warning("No models found. Please ensure Ollama is running and has models installed")
            return gr.update(choices=[], value=None, interactive=True)
    except Exception as e:
        gr.Warning(f"Failed to connect to Ollama: {str(e)}")
        return gr.update(choices=[], value=None, interactive=True)

def update_ollama_api_instance(ollama_manager, ollama_connection_name: str, model_name: str):
    """Create or update Ollama API instance when connection or model changes."""
    if not ollama_connection_name or not model_name:
        return None
    
    # Get connection details
    conn = ollama_manager.get_connection(ollama_connection_name)
    if not conn:
        return None
    
    try:
        return OllamaAPINew(
            base_url=conn['base_url'],
            model_name=model_name,
            username=conn.get('username', ''),
            password=conn.get('password', ''),
            should_authenticate=conn.get('should_authenticate', False)
        )
    except Exception as e:
        gr.Warning(f"Failed to initialize Ollama API: {str(e)}")
        return None

def create_chat_tab(db_manager, ollama_manager):
    """Create the chat tab."""
    
    with gr.Tab("Chat"):
        # State to store Ollama API instance
        ollama_api_state = gr.State(None)
        
        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                gr.Markdown("### Configuration")
                
                connection_dropdown = gr.Dropdown(
                    choices=db_manager.get_connection_names(),
                    label="Database Connection",
                    info="Select a connection to query"
                )
                
                gr.Markdown("### Model Settings")
                
                # Ollama connection dropdown (replaces provider and URL input)
                ollama_connection_dropdown = gr.Dropdown(
                    choices=ollama_manager.get_connection_names(),
                    label="Ollama Connection",
                    info="Select an Ollama backend connection",
                    value=ollama_manager.get_connection_names()[0] if ollama_manager.get_connection_names() else None
                )
                
                # Refresh models button
                with gr.Row():
                    refresh_models_btn = gr.Button(
                        "🔄 Refresh Models",
                        size="sm"
                    )
                
                model_name = gr.Dropdown(
                    choices=[],
                    value=None,
                    label="Model",
                    allow_custom_value=False
                )
            
            with gr.Column(scale=3, min_width=600):
                gr.Markdown("### Ask Your Question")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=650,
                    show_copy_button=True,
                    type="tuples",
                    bubble_full_width=False,
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=assistant")
                )
                
                with gr.Row():
                    query_input = gr.Textbox(
                        label="",
                        placeholder="Ask me anything about your database... (e.g., Show me all users who registered last month)",
                        lines=2,
                        scale=4,
                        show_label=False
                    )
                    with gr.Column(scale=1, min_width=100):
                        submit_btn = gr.Button("Send", variant="primary", size="lg")
                        clear_btn = gr.Button("Clear", size="sm")
        
        # Event handlers
        
        # Refresh models button click event - load models from selected Ollama connection
        refresh_models_btn.click(
            fn=lambda conn_name: update_model_choices(ollama_manager, conn_name),
            inputs=[ollama_connection_dropdown],
            outputs=[model_name]
        )
        
        # Update model choices when Ollama connection changes
        ollama_connection_dropdown.change(
            fn=lambda conn_name: update_model_choices(ollama_manager, conn_name),
            inputs=[ollama_connection_dropdown],
            outputs=[model_name]
        )
        
        # Update Ollama API instance when connection or model changes
        def update_api_state(conn_name, model):
            return update_ollama_api_instance(ollama_manager, conn_name, model)
        
        # When connection changes, clear the API state since model will be updated
        ollama_connection_dropdown.change(
            fn=lambda: None,  # Clear API state when connection changes
            outputs=[ollama_api_state]
        )
        
        model_name.change(
            fn=update_api_state,
            inputs=[ollama_connection_dropdown, model_name],
            outputs=[ollama_api_state]
        )
        
        # Submit handlers
        submit_btn.click(
            fn=lambda db_conn, ollama_conn, model, query, history: execute_agent_query_with_graph(
                db_conn, ollama_conn, model, query, history
            ),
            inputs=[connection_dropdown, ollama_connection_dropdown, model_name, query_input, chatbot],
            outputs=[chatbot, query_input]
        )
        
        query_input.submit(
            fn=lambda db_conn, ollama_conn, model, query, history: execute_agent_query_with_graph(
                db_conn, ollama_conn, model, query, history
            ),
            inputs=[connection_dropdown, ollama_connection_dropdown, model_name, query_input, chatbot],
            outputs=[chatbot, query_input]
        )
        
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, query_input]
        )
    
    return connection_dropdown, ollama_connection_dropdown, model_name
