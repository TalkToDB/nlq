"""
Query tab UI component.
"""

import gradio as gr
from src.models.config import get_models_for_provider, get_default_model, get_all_providers
from src.models.query_engine import execute_query

def update_model_choices(provider: str):
    """Update model dropdown based on provider selection."""
    models = get_models_for_provider(provider)
    default_model = get_default_model(provider)
    return gr.update(choices=models, value=default_model)

def create_query_tab(db_manager):
    """Create the query database tab."""
    
    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=1, min_width=350):
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
                model_name = gr.Dropdown(
                    choices=get_models_for_provider(get_all_providers()[0]),
                    value=get_default_model(get_all_providers()[0]),
                    label="Model"
                )
            
            with gr.Column(scale=2, min_width=600):
                gr.Markdown("### Ask Your Question [Mock Response Only]")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=450,
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
        model_provider.change(
            fn=update_model_choices,
            inputs=[model_provider],
            outputs=[model_name]
        )
        
        submit_btn.click(
            fn=execute_query,
            inputs=[connection_dropdown, model_provider, model_name, query_input, chatbot],
            outputs=[chatbot, query_input]
        )
        
        query_input.submit(
            fn=execute_query,
            inputs=[connection_dropdown, model_provider, model_name, query_input, chatbot],
            outputs=[chatbot, query_input]
        )
        
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, query_input]
        )
    
    return connection_dropdown
