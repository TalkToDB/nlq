"""
Database connections management tab UI component.
"""

import gradio as gr
from src.database.schemas import get_schema_for_db_type, get_supported_databases

def create_dynamic_form_fields(db_type: str):
    """Create form fields dynamically based on database type."""
    schema_class = get_schema_for_db_type(db_type)
    fields = schema_class.get_fields()
    
    # Create visibility updates for all possible fields
    updates = {
        "connection_type": gr.update(visible=False),
        "host": gr.update(visible=False),
        "port": gr.update(visible=False),
        "database": gr.update(visible=False),
        "username": gr.update(visible=False),
        "password": gr.update(visible=False),
        "schema": gr.update(visible=False),
        "database_path": gr.update(visible=False),
        "driver": gr.update(visible=False),
        "auth_source": gr.update(visible=False),
    }
    
    # Update fields that should be visible for this database type
    for field in fields:
        field_update = {
            "visible": True,
            "label": field.label,
            "placeholder": field.placeholder,
            "value": field.default
        }
        
        if field.field_type == "password":
            field_update["type"] = "password"
        
        updates[field.name] = gr.update(**field_update)
    
    return [updates[key] for key in [
        "connection_type", "host", "port", "database", "username", "password",
        "schema", "database_path", "driver", "auth_source"
    ]]

def add_db_connection_handler(db_manager, name, db_type, connection_type, host, port, database, 
                              username, password, schema, database_path, driver, auth_source,
                              edit_mode):
    """Handle adding or updating a database connection."""
    
    # Collect only the relevant fields for this database type
    schema_class = get_schema_for_db_type(db_type)
    field_names = [f.name for f in schema_class.get_fields()]
    
    connection_data = {}
    field_values = {
        "connection_type": connection_type,
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
        "schema": schema,
        "database_path": database_path,
        "driver": driver,
        "auth_source": auth_source,
    }
    
    for field_name in field_names:
        if field_name in field_values and field_values[field_name]:
            connection_data[field_name] = field_values[field_name]
    
    # Check if we're editing or adding
    if edit_mode:
        success, message = db_manager.update_connection(name, db_type, connection_data)
    else:
        success, message = db_manager.add_connection(name, db_type, connection_data)
    
    # Reload connections to get updated list
    db_manager.reload_connections()
    connection_names = db_manager.get_connection_names()
    
    # Clear form after successful addition/update
    if success:
        # Return empty values for all form fields
        return (
            db_manager.get_connections_table(),  # Update table
            message,  # Status message
            "",  # conn_name - clear
            gr.update(value="Add Connection", variant="primary"),  # Reset button
            gr.update(visible=False),  # Hide cancel button
            False,  # edit_mode = False
            gr.update(choices=connection_names, value=None),  # query tab dropdown
            gr.update(choices=connection_names, value=None),  # delete dropdown
            gr.update(choices=connection_names, value=None),  # edit dropdown
            gr.update(choices=connection_names, value=None),  # sql query tab dropdown
            # Clear all form fields (10 fields now with connection_type)
            "", "", "", "", "", "", "", "", "", ""  # 10 empty strings for all fields
        )
    else:
        return (
            db_manager.get_connections_table(),
            message,
            name,  # keep the name
            gr.update(),  # keep button as is
            gr.update(),  # keep cancel button as is
            edit_mode,  # keep edit mode
            gr.update(choices=connection_names, value=None),
            gr.update(choices=connection_names, value=None),
            gr.update(choices=connection_names, value=None),
            gr.update(choices=connection_names, value=None),
            # Keep current field values
            connection_type, host, port, database, username, password, schema, database_path, driver, auth_source
        )

def delete_db_connection_handler(db_manager, name):
    """Handle deleting a database connection."""
    if not name:
        # Get current state for empty selection
        connection_names = db_manager.get_connection_names()
        return (
            db_manager.get_connections_table(),
            "Error: Please select a connection to delete.",
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),
            gr.update(choices=connection_names),
        )
    
    # Delete the connection (this already reloads internally)
    success, message = db_manager.delete_connection(name)
    
    # Get fresh connection names after deletion
    connection_names = db_manager.get_connection_names()
    
    # Return updates with the new connection list
    return (
        db_manager.get_connections_table(),  # Update connections table
        message,  # Status message
        gr.update(choices=connection_names, value=None),  # Query tab dropdown
        gr.update(choices=connection_names, value=None),  # Delete dropdown (this tab)
        gr.update(choices=connection_names, value=None),  # Edit dropdown (this tab)
        gr.update(choices=connection_names, value=None),  # SQL query tab dropdown
    )

def load_connection_for_edit(db_manager, name):
    """Load connection details into the form for editing."""
    if not name:
        return ["", "PostgreSQL"] + [""] * 10 + [gr.update(), gr.update(visible=False), False]
    
    conn = db_manager.get_connection(name)
    if not conn:
        return ["", "PostgreSQL"] + [""] * 10 + [gr.update(), gr.update(visible=False), False]
    
    db_type = conn.get('type', 'PostgreSQL')
    
    # Get the dynamic field updates for this database type
    field_updates = create_dynamic_form_fields(db_type)
    
    # Create the values for each field
    field_values = [
        conn.get('connection_type', 'local'),
        conn.get('host', ''),
        conn.get('port', ''),
        conn.get('database', ''),
        conn.get('username', ''),
        conn.get('password', ''),
        conn.get('schema', ''),
        conn.get('database_path', ''),
        conn.get('driver', ''),
        conn.get('auth_source', ''),
    ]
    
    # Merge field updates with actual values
    merged_fields = []
    for i, (field_update, field_value) in enumerate(zip(field_updates, field_values)):
        # field_update is a gr.update() with visibility and other properties
        # We need to add the value to it
        if isinstance(field_update, dict):
            field_update['value'] = field_value
            merged_fields.append(gr.update(**field_update))
        else:
            merged_fields.append(field_value)
    
    # Return: conn_name, conn_type, all_form_fields (with visibility), save_btn, cancel_edit_btn, edit_mode
    return [
        conn.get('name', ''),
        db_type,
    ] + merged_fields + [
        gr.update(value="Update Connection", variant="secondary"),
        gr.update(visible=True),  # Show cancel button
        True  # edit_mode = True
    ]

def cancel_edit_mode():
    """Cancel edit mode and clear form."""
    return (
        "",  # conn_name
        "PostgreSQL",  # conn_type
        "", "", "", "", "", "", "", "", "", "",  # Clear all form fields (10 fields)
        gr.update(value="Add Connection", variant="primary"),  # Reset save button
        gr.update(visible=False),  # Hide cancel button
        False  # edit_mode = False
    )

def create_connections_tab(db_manager):
    """Create the manage connections tab."""
    
    with gr.Tab("Manage Connections"):
        gr.Markdown("### Database Connection Management")
        
        # Hidden state to track edit mode
        edit_mode_state = gr.State(False)
        
        with gr.Row():
            with gr.Column(scale=1, min_width=400):
                gr.Markdown("#### Add/Edit Connection")
                
                conn_name = gr.Textbox(
                    label="Connection Name",
                    placeholder="e.g., Production DB",
                    max_lines=1,
                    show_copy_button=False
                )
                
                conn_type = gr.Dropdown(
                    choices=get_supported_databases(),
                    value="PostgreSQL",
                    label="Database Type",
                    info="Select your database type to see relevant fields"
                )
                
                gr.Markdown("#### Connection Details")
                
                # MongoDB-specific connection type field
                conn_connection_type = gr.Textbox(
                    label="Connection Type",
                    placeholder="local",
                    visible=False,
                    max_lines=1,
                    show_copy_button=False,
                    info="Enter 'local' for local MongoDB or 'cloud' for MongoDB Atlas"
                )
                
                # Common fields (shown/hidden based on DB type) - Two per row
                with gr.Group():
                    with gr.Row():
                        conn_host = gr.Textbox(
                            label="Host",
                            placeholder="localhost",
                            visible=True,
                            max_lines=1,
                            show_copy_button=False
                        )
                        conn_port = gr.Textbox(
                            label="Port",
                            placeholder="5432",
                            visible=True,
                            max_lines=1,
                            show_copy_button=False
                        )
                    
                    with gr.Row():
                        conn_database = gr.Textbox(
                            label="Database Name",
                            placeholder="my_database",
                            visible=True,
                            max_lines=1,
                            show_copy_button=False
                        )
                        conn_username = gr.Textbox(
                            label="Username",
                            placeholder="db_user",
                            visible=True,
                            max_lines=1,
                            show_copy_button=False
                        )
                    
                    conn_password = gr.Textbox(
                        label="Password",
                        type="password",
                        placeholder="Enter password",
                        visible=True,
                        max_lines=1,
                        show_copy_button=False
                    )
                
                # Optional/Database-specific fields
                with gr.Group():
                    with gr.Row():
                        conn_schema = gr.Textbox(
                            label="Schema",
                            placeholder="public",
                            visible=False,
                            max_lines=1,
                            show_copy_button=False
                        )
                        conn_auth_source = gr.Textbox(
                            label="Auth Source",
                            placeholder="admin",
                            visible=False,
                            max_lines=1,
                            show_copy_button=False
                        )
                    
                    conn_database_path = gr.Textbox(
                        label="Database Path",
                        placeholder="/path/to/database.db",
                        visible=False,
                        max_lines=1,
                        show_copy_button=False
                    )
                    
                    conn_driver = gr.Textbox(
                        label="Driver",
                        placeholder="ODBC Driver 17 for SQL Server",
                        visible=False,
                        max_lines=1,
                        show_copy_button=False
                    )
                
                with gr.Row():
                    save_btn = gr.Button("Add Connection", variant="primary", size="lg")
                    cancel_edit_btn = gr.Button("Cancel Edit", variant="secondary", size="lg", visible=False)
            
            with gr.Column(scale=1, min_width=500):
                gr.Markdown("#### Existing Connections")
                
                connections_table = gr.Dataframe(
                    headers=["Name", "Type", "Host/Path", "Database"],
                    value=db_manager.get_connections_table(),
                    label="Database Connections",
                    interactive=False,
                    wrap=True
                )
                
                gr.Markdown("#### Actions")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        edit_dropdown = gr.Dropdown(
                            choices=db_manager.get_connection_names(),
                            label="Edit Connection"
                        )
                        edit_btn = gr.Button("Load for Edit", variant="secondary", size="sm")
                    
                    with gr.Column(scale=1):
                        delete_dropdown = gr.Dropdown(
                            choices=db_manager.get_connection_names(),
                            label="Delete Connection"
                        )
                        delete_btn = gr.Button("Delete", variant="stop", size="sm")
                
                status_message = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2
                )
        
        # Store all form fields for easier access
        all_form_fields = [
            conn_connection_type, conn_host, conn_port, conn_database, conn_username, conn_password,
            conn_schema, conn_database_path, conn_driver, conn_auth_source
        ]
        
        # Event handler: Update form fields when database type changes
        conn_type.change(
            fn=create_dynamic_form_fields,
            inputs=[conn_type],
            outputs=all_form_fields
        )
        
        # Event handler: Load connection for editing
        edit_btn.click(
            fn=lambda name: load_connection_for_edit(db_manager, name),
            inputs=[edit_dropdown],
            outputs=[conn_name, conn_type] + all_form_fields + [save_btn, cancel_edit_btn, edit_mode_state]
        )
        
        # Event handler: Cancel edit mode
        cancel_edit_btn.click(
            fn=cancel_edit_mode,
            outputs=[conn_name, conn_type] + all_form_fields + [save_btn, cancel_edit_btn, edit_mode_state]
        )
    
    return (save_btn, delete_btn, conn_name, conn_type, connections_table, 
            delete_dropdown, edit_dropdown, status_message, all_form_fields, 
            edit_mode_state, cancel_edit_btn)
