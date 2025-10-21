"""
Query tab UI component.
"""

import gradio as gr
from src.models.config import get_all_providers
from src.models.ollama_api import OllamaAPI
from src.agent.agent import MasterAgent
from src.models.query_engine import execute_agent_query

def update_model_choices(provider: str, ollama_url: str):
    """Update model dropdown based on provider selection."""
    if provider == "Ollama":
        if not ollama_url or not ollama_url.strip():
            gr.Warning("Please enter Ollama URL and click Refresh to load models")
            return gr.update(choices=[], value=None)
        
        # Try to get real models from Ollama API
        try:
            ollama_api = OllamaAPI(base_url=ollama_url.strip(), model_name="")
            models_data = ollama_api.get_models()
            
            if models_data:
                # Extract model IDs from the response
                models = [model["id"] for model in models_data]
                default_model = models[0] if models else None
                gr.Info(f"✅ Successfully loaded {len(models)} models from Ollama")
                return gr.update(choices=models, value=default_model)
            else:
                gr.Warning("No models found. Please ensure Ollama is running and has models installed")
                return gr.update(choices=[], value=None)
        except Exception as e:
            gr.Warning(f"Failed to connect to Ollama: {str(e)}")
            return gr.update(choices=[], value=None)
    
    return gr.update(choices=[], value=None)

def toggle_ollama_url_visibility(provider: str):
    """Show/hide Ollama URL field based on provider selection."""
    if provider == "Ollama":
        return gr.update(visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)

def update_ollama_api_instance(provider: str, ollama_url: str, model_name: str):
    """Create or update Ollama API instance when URL or model changes."""
    if provider == "Ollama" and ollama_url and model_name:
        try:
            return OllamaAPI(base_url=ollama_url.strip(), model_name=model_name)
        except Exception as e:
            gr.Warning(f"Failed to initialize Ollama API: {str(e)}")
            return None
    return None

def update_master_agent(ollama_api: OllamaAPI, db_manager):
    """Create or update MasterAgent instance when Ollama API changes."""
    if ollama_api and ollama_api.llm:
        try:
            return MasterAgent(db_manager=db_manager, llm_api=ollama_api)
        except Exception as e:
            gr.Warning(f"Failed to initialize MasterAgent: {str(e)}")
            return None
    return None

def create_chat_tab(db_manager):
    """Create the chat tab."""
    
    with gr.Tab("Chat"):
        # State to store Ollama API instance and MasterAgent
        ollama_api_state = gr.State(None)
        master_agent_state = gr.State(None)
        
        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                gr.Markdown("### Configuration")
                
                connection_dropdown = gr.Dropdown(
                    choices=db_manager.get_connection_names(),
                    label="Database Connection",
                    info="Select a connection to query"
                )
                
                gr.Markdown("### Model Settings")
                
                model_provider = gr.Radio(
                    choices=get_all_providers(),
                    value=get_all_providers()[0],
                    label="Provider"
                )
                
                # Ollama backend URL (only visible when Ollama is selected)
                with gr.Row():
                    ollama_url = gr.Textbox(
                        label="Ollama Backend URL",
                        placeholder="http://localhost:11434",
                        value="http://localhost:11434",
                        visible=True if get_all_providers()[0] == "Ollama" else False,
                        info="URL where Ollama is running",
                        max_lines=1,
                        scale=3
                    )
                    refresh_models_btn = gr.Button(
                        "🔄 Refresh",
                        size="sm",
                        visible=True if get_all_providers()[0] == "Ollama" else False,
                        scale=1
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
        
        # Toggle Ollama URL visibility based on provider
        model_provider.change(
            fn=toggle_ollama_url_visibility,
            inputs=[model_provider],
            outputs=[ollama_url, refresh_models_btn]
        )
        
        # Update model choices when provider changes
        model_provider.change(
            fn=lambda provider, url: update_model_choices(provider, url),
            inputs=[model_provider, ollama_url],
            outputs=[model_name]
        )
        
        # Refresh models button click event
        refresh_models_btn.click(
            fn=lambda provider, url: update_model_choices(provider, url),
            inputs=[model_provider, ollama_url],
            outputs=[model_name]
        )
        
        # Update Ollama API instance when URL or model changes
        def update_api_state(provider, url, model):
            return update_ollama_api_instance(provider, url, model)
        
        ollama_url.change(
            fn=update_api_state,
            inputs=[model_provider, ollama_url, model_name],
            outputs=[ollama_api_state]
        )
        
        model_name.change(
            fn=update_api_state,
            inputs=[model_provider, ollama_url, model_name],
            outputs=[ollama_api_state]
        )
        
        # Update MasterAgent when Ollama API changes
        ollama_api_state.change(
            fn=lambda api: update_master_agent(api, db_manager),
            inputs=[ollama_api_state],
            outputs=[master_agent_state]
        )
        
        # Submit handlers
        submit_btn.click(
            fn=lambda conn, query, history, agent: execute_agent_query(conn, query, history, agent),
            inputs=[connection_dropdown, query_input, chatbot, master_agent_state],
            outputs=[chatbot, query_input]
        )
        
        query_input.submit(
            fn=lambda conn, query, history, agent: execute_agent_query(conn, query, history, agent),
            inputs=[connection_dropdown, query_input, chatbot, master_agent_state],
            outputs=[chatbot, query_input]
        )
        
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, query_input]
        )
    
    return connection_dropdown
