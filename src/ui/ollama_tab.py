"""
Ollama backend connections management tab UI component.
"""

import gradio as gr

def add_ollama_connection_handler(ollama_manager, name, base_url, api_key, edit_mode):
    """Handle adding or updating an Ollama backend connection."""
    
    # Check if we're editing or adding
    if edit_mode:
        success, message = ollama_manager.update_connection(name, base_url, api_key)
    else:
        success, message = ollama_manager.add_connection(name, base_url, api_key)
    
    # Reload connections to get updated list
    ollama_manager.reload_connections()
    connection_names = ollama_manager.get_connection_names()
    
    # Clear form after successful addition/update
    if success:
        return (
            ollama_manager.get_connections_table(),  # Update table
            message,  # Status message
            "",  # conn_name - clear
            "",  # base_url - clear
            "",  # api_key - clear
            gr.update(value="Add Connection", variant="primary"),  # Reset button
            gr.update(visible=False),  # Hide cancel button
            False,  # edit_mode = False
            gr.update(choices=connection_names, value=None),  # chat tab dropdown
            gr.update(choices=connection_names, value=None),  # delete dropdown
            gr.update(choices=connection_names, value=None),  # edit dropdown
            gr.update(choices=[], value=None),  # model dropdown - clear choices
        )
    else:
        return (
            ollama_manager.get_connections_table(),
            message,
            name,  # keep the name
            base_url,  # keep the base_url
            api_key,  # keep the api_key
            gr.update(),  # keep button as is
            gr.update(),  # keep cancel button as is
            edit_mode,  # keep edit mode
            gr.update(choices=connection_names, value=None),
            gr.update(choices=connection_names, value=None),
            gr.update(choices=connection_names, value=None),
            gr.update(choices=[], value=None),  # model dropdown - clear choices
        )

def delete_ollama_connection_handler(ollama_manager, name):
    """Handle deleting an Ollama backend connection."""
    if not name:
        connection_names = ollama_manager.get_connection_names()
        return (
            ollama_manager.get_connections_table(),
            "Error: Please select a connection to delete.",
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),  # chat tab dropdown
            gr.update(choices=[], value=None),  # model dropdown - clear choices
        )
    
    # Delete the connection
    success, message = ollama_manager.delete_connection(name)
    
    # Get fresh connection names after deletion
    connection_names = ollama_manager.get_connection_names()
    
    # Return updates with the new connection list
    return (
        ollama_manager.get_connections_table(),  # Update connections table
        message,  # Status message
        gr.update(choices=connection_names, value=None),  # chat tab dropdown
        gr.update(choices=connection_names, value=None),  # Delete dropdown (this tab)
        gr.update(choices=connection_names, value=None),  # Edit dropdown (this tab)
        gr.update(choices=[], value=None),  # model dropdown - clear choices
    )

def load_ollama_connection_for_edit(ollama_manager, name):
    """Load connection details into the form for editing."""
    if not name:
        return ["", "", "", gr.update(), gr.update(visible=False), False]
    
    conn = ollama_manager.get_connection(name)
    if not conn:
        return ["", "", "", gr.update(), gr.update(visible=False), False]
    
    # Return: conn_name, base_url, api_key, save_btn, cancel_edit_btn, edit_mode
    return [
        conn.get('name', ''),
        conn.get('base_url', ''),
        conn.get('api_key', ''),
        gr.update(value="Update Connection", variant="secondary"),
        gr.update(visible=True),  # Show cancel button
        True  # edit_mode = True
    ]

def cancel_ollama_edit_mode():
    """Cancel edit mode and clear form."""
    return (
        "",  # conn_name
        "",  # base_url
        "",  # api_key
        gr.update(value="Add Connection", variant="primary"),  # Reset save button
        gr.update(visible=False),  # Hide cancel button
        False  # edit_mode = False
    )

def create_ollama_tab(ollama_manager):
    """Create the manage Ollama connections tab."""
    
    with gr.Tab("Manage Ollama"):
        gr.Markdown("### Ollama Backend Management")
        
        # Hidden state to track edit mode
        edit_mode_state = gr.State(False)
        
        with gr.Row():
            with gr.Column(scale=1, min_width=400):
                gr.Markdown("#### Add/Edit Ollama Backend")
                
                ollama_conn_name = gr.Textbox(
                    label="Connection Name",
                    placeholder="e.g., Local Ollama",
                    max_lines=1,
                    show_copy_button=False
                )
                
                ollama_base_url = gr.Textbox(
                    label="Base URL",
                    placeholder="http://localhost:11434",
                    max_lines=1,
                    show_copy_button=False,
                    info="Ollama backend URL"
                )
                
                ollama_api_key = gr.Textbox(
                    label="API Key (Optional)",
                    type="password",
                    placeholder="Enter API key if required",
                    max_lines=1,
                    show_copy_button=False,
                    info="Leave blank if authentication is not required"
                )
                
                with gr.Row():
                    save_ollama_btn = gr.Button("Add Connection", variant="primary", size="lg")
                    cancel_ollama_edit_btn = gr.Button("Cancel Edit", variant="secondary", size="lg", visible=False)
            
            with gr.Column(scale=1, min_width=500):
                gr.Markdown("#### Existing Ollama Backends")
                
                ollama_connections_table = gr.Dataframe(
                    headers=["Name", "Base URL", "Authentication"],
                    value=ollama_manager.get_connections_table(),
                    label="Ollama Connections",
                    interactive=False,
                    wrap=True
                )
                
                gr.Markdown("#### Actions")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        edit_ollama_dropdown = gr.Dropdown(
                            choices=ollama_manager.get_connection_names(),
                            label="Edit Connection"
                        )
                        edit_ollama_btn = gr.Button("Load for Edit", variant="secondary", size="sm")
                    
                    with gr.Column(scale=1):
                        delete_ollama_dropdown = gr.Dropdown(
                            choices=ollama_manager.get_connection_names(),
                            label="Delete Connection"
                        )
                        delete_ollama_btn = gr.Button("Delete", variant="stop", size="sm")
                
                ollama_status_message = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2
                )
        
        # Event handler: Load connection for editing
        edit_ollama_btn.click(
            fn=lambda name: load_ollama_connection_for_edit(ollama_manager, name),
            inputs=[edit_ollama_dropdown],
            outputs=[ollama_conn_name, ollama_base_url, ollama_api_key, 
                    save_ollama_btn, cancel_ollama_edit_btn, edit_mode_state]
        )
        
        # Event handler: Cancel edit mode
        cancel_ollama_edit_btn.click(
            fn=cancel_ollama_edit_mode,
            outputs=[ollama_conn_name, ollama_base_url, ollama_api_key, 
                    save_ollama_btn, cancel_ollama_edit_btn, edit_mode_state]
        )
    
    return (save_ollama_btn, delete_ollama_btn, ollama_conn_name, ollama_base_url, 
            ollama_api_key, ollama_connections_table, 
            delete_ollama_dropdown, edit_ollama_dropdown, ollama_status_message, 
            edit_mode_state, cancel_ollama_edit_btn)
