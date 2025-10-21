"""
Database Query execution tab for testing database connections.
Supports SQL and NoSQL databases.
"""

import gradio as gr
import json
from src.database.executor import execute_query
from src.database.manager import DatabaseManager
from datetime import datetime

def execute_database_query(connection_name: str, db_manager: DatabaseManager, query: str, query_history: str) -> tuple:
    """
    Execute query on selected database.
    
    Args:
        connection_name: Name of the database connection
        db_manager: Database manager instance
        query: Query to execute (SQL or NoSQL)
        query_history: Current query history as HTML string
        
    Returns:
        Tuple of (updated_history_html, query_input, result_json, status_message)
    """
    if not connection_name:
        error_msg = "Error: Please select a database connection first."
        return query_history, query, "", error_msg
    
    if not query.strip():
        error_msg = "Error: Please enter a query."
        return query_history, query, "", error_msg
    
    # Get connection details
    connection = db_manager.get_connection(connection_name)
    if not connection:
        error_msg = f"Error: Connection '{connection_name}' not found."
        return query_history, query, "", error_msg
    
    db_type = connection.get('type', 'Unknown')
    
    # Execute the actual query
    start_time = datetime.now()
    success, message, results = execute_query(db_type, connection, query)
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # Create HTML for the new query with copy button
    escaped_query = query.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    # Escape backticks for JavaScript
    js_escaped_query = escaped_query.replace('`', '&#96;')
    
    query_html = f'''
    <div style="margin-bottom: 10px; border: 1px solid #444; border-radius: 5px; padding: 10px; background: #1e1e1e; position: relative;">
        <pre style="margin: 0; padding: 0; white-space: pre-wrap; word-wrap: break-word; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #d4d4d4;">{escaped_query}</pre>
        <button onclick="navigator.clipboard.writeText(`{js_escaped_query}`)" style="position: absolute; top: 5px; right: 5px; background: #0e639c; border: none; color: white; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 11px;">Copy</button>
    </div>
    '''
    
    # Extract content from existing history (remove wrapper if it exists)
    existing_content = query_history
    if existing_content.startswith('<div style="max-height:'):
        # Extract inner content
        start = existing_content.find('">') + 2
        end = existing_content.rfind('</div>')
        if start > 1 and end > start:
            existing_content = existing_content[start:end]
    
    # Combine queries and wrap in single scrollable container
    all_queries = query_html + existing_content
    updated_history = f'<div style="max-height: 300px; overflow-y: auto; padding: 10px;">{all_queries}</div>'
    
    # Format status message
    if success:
        status = f"✓ Success | {connection_name} ({db_type}) | {execution_time:.3f}s | Rows: {len(results) if isinstance(results, list) else 'N/A'}"
        
        # Format results as JSON
        result_output = {
            "execution_time": f"{execution_time:.3f}s",
            "rows_returned": len(results) if isinstance(results, list) else None,
            "data": results
        }
        json_result = json.dumps(result_output, indent=2, default=str)
        
    else:
        status = f"✗ Error | {connection_name} ({db_type}) | {message}"
        json_result = json.dumps({"error": message}, indent=2)
    
    return updated_history, query, json_result, status


def format_query(query: str) -> str:
    """
    Format query for better readability.
    Basic formatter - can be enhanced later.
    """
    if not query.strip():
        return query
    
    # Basic SQL formatting
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 
                'INNER JOIN', 'ON', 'GROUP BY', 'ORDER BY', 'HAVING', 
                'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                'LIMIT', 'OFFSET', 'AS', 'AND', 'OR', 'IN', 'NOT', 'NULL']
    
    formatted = query
    for keyword in keywords:
        formatted = formatted.replace(keyword.lower(), keyword)
        formatted = formatted.replace(keyword.capitalize(), keyword)
    
    return formatted


def create_sql_query_tab(db_manager):
    """Create the database query execution tab."""
    
    with gr.Tab("Database Query"):
        gr.Markdown("### Execute Database Queries")
        gr.Markdown("Test your database connections by running queries directly (SQL for relational DBs, queries for NoSQL).")
        
        with gr.Row():
            with gr.Column(scale=1, min_width=400):
                gr.Markdown("#### Database & Query")
                
                sql_connection_dropdown = gr.Dropdown(
                    choices=db_manager.get_connection_names(),
                    label="Database Connection",
                    info="Select a connection to execute queries"
                )
                
                sql_query_input = gr.Code(
                    label="Query",
                    language="sql",
                    lines=10
                )
                
                with gr.Row():
                    execute_btn = gr.Button("Execute Query", variant="primary", size="lg")
                    format_btn = gr.Button("Format", variant="secondary", size="sm")
                    clear_query_btn = gr.Button("Clear", size="sm")
                
                gr.Markdown("#### Query Templates")
                with gr.Accordion("Common Queries", open=False):
                    gr.Markdown("""
                    **SQL Databases:**
                    - `SELECT * FROM table_name LIMIT 10;`
                    - `SHOW TABLES;`
                    - `DESCRIBE table_name;`
                    
                    **MongoDB:**
                    - `db.collection.find().limit(10)`
                    - `db.collection.countDocuments()`
                    """)
                    
                    template_buttons = gr.Radio(
                        choices=[
                            "SELECT * FROM table_name LIMIT 10;",
                            "SHOW TABLES;",
                            "DESCRIBE table_name;",
                            "SELECT COUNT(*) FROM table_name;",
                            "db.collection.find().limit(10)",
                        ],
                        label="Quick Templates",
                        value=None
                    )
                    use_template_btn = gr.Button("Use Template", size="sm")
            
            with gr.Column(scale=1, min_width=500):
                gr.Markdown("#### Query Results")
                
                # Status message
                status_output = gr.Textbox(
                    label="Status",
                    value="",
                    interactive=False,
                    lines=1,
                    max_lines=1
                )
                
                # Results display as JSON
                sql_results_json = gr.Code(
                    label="Results (JSON)",
                    language="json",
                    lines=15,
                    elem_classes="scrollable-code"
                )
                
                # Query history - as HTML with individual copy buttons
                sql_query_history = gr.HTML(
                    label="Query History",
                    value="",
                    elem_classes="scrollable-history"
                )
                
                with gr.Row():
                    clear_results_btn = gr.Button("Clear Results", size="sm")
                    clear_history_btn = gr.Button("Clear History", size="sm")
        
        # Event handlers
        execute_btn.click(
            fn=lambda conn, query, hist: execute_database_query(conn, db_manager, query, hist),
            inputs=[sql_connection_dropdown, sql_query_input, sql_query_history],
            outputs=[sql_query_history, sql_query_input, sql_results_json, status_output]
        )
        
        format_btn.click(
            fn=format_query,
            inputs=[sql_query_input],
            outputs=[sql_query_input]
        )
        
        clear_query_btn.click(
            fn=lambda: "",
            outputs=[sql_query_input]
        )
        
        clear_results_btn.click(
            fn=lambda: ("", ""),
            outputs=[sql_results_json, status_output]
        )
        
        clear_history_btn.click(
            fn=lambda: "",
            outputs=[sql_query_history]
        )
        
        use_template_btn.click(
            fn=lambda template: template if template else "",
            inputs=[template_buttons],
            outputs=[sql_query_input]
        )
    
    return sql_connection_dropdown
