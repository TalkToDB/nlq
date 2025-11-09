"""
Query engine for processing natural language queries.
"""

import uuid
import gradio as gr
from src.database.manager import DatabaseManager
from src.models.ollama_manager import OllamaConnectionManager

def execute_agent_query_with_graph(
    connection_name: str,
    llama_connection_name: str,
    model_name: str,
    query: str,
    chat_history: list
) -> tuple:
    """Execute query using LangGraph with full tool usage transparency."""

    if not model_name:
        gr.Warning("Please select a model first")
        return chat_history, query

    if not llama_connection_name:
        gr.Warning("Please select an Ollama connection first")
        return chat_history, query
    
    if not connection_name:
        gr.Warning("Please select a database connection first")
        return chat_history, query
    
    if not query.strip():
        gr.Warning("Please enter a query")
        return chat_history, query
    
    try:
        # Execute query using the graph
        from src.agent.graph import graph
        
        query_id = str(uuid.uuid4())
        db_manager = DatabaseManager()
        ollama_manager = OllamaConnectionManager()
        ollama_manager.reload_connections()
        
        llama = ollama_manager.get_connection(llama_connection_name)
        if not llama:
            gr.Warning(f"Ollama connection '{llama_connection_name}' not found")
            return chat_history, query
            
        connection_details = db_manager.get_connection(connection_name)
        if not connection_details:
            gr.Warning(f"Database connection '{connection_name}' not found")
            return chat_history, query
        
        initial_state = {
            "ollama_connection_name": llama_connection_name,
            "ollama_model_name": model_name,
            
            "query_id": query_id,
            "connection_name": connection_name,
            "query_text": query,
            "database_type": connection_details['type'],
            "agent_response": {}
        }

        # Run with a thread_id for persistence
        config = {"configurable": {"thread_id": query_id}}

        result = graph.invoke(initial_state, config)
        
        # Format the response
        formatted_response = ""
        
        # Add classification info if available
        classification = result.get('classification', {})
        if classification:
            intent = classification.get('intent', 'unknown')
            formatted_response += f"**Intent:** {intent}\n\n"
        
        # Add database query info if available
        agent_response = result.get('agent_response', {})
        if agent_response and agent_response.get('db_query'):
            formatted_response += "### 🔧 Generated Query:\n\n"
            formatted_response += f"```sql\n{agent_response['db_query']}\n```\n\n"
            
            if agent_response.get('reasoning'):
                formatted_response += f"**Reasoning:** {agent_response['reasoning']}\n\n"
            
            if agent_response.get('execution_result'):
                exec_result = agent_response['execution_result']
                result_count = len(exec_result) if isinstance(exec_result, list) else 0
                formatted_response += f"**Execution:** ✅ Success ({result_count} results)\n\n"
            elif agent_response.get('execution_error'):
                errors = agent_response['execution_error']
                formatted_response += f"**Execution:** ❌ Error - {errors[-1] if errors else 'Unknown error'}\n\n"
            
            formatted_response += "---\n\n"
        
        # Add the final response
        response_text = result.get('response', 'No response generated')
        formatted_response += f"### Response:\n\n{response_text}"
        
        chat_history.append((query, formatted_response))
        return chat_history, ""
        
    except Exception as e:
        import traceback
        error_msg = f"Error executing query: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)  # Print to console for debugging
        gr.Warning(f"Error: {str(e)}")
        chat_history.append((query, f"❌ **Error:** {str(e)}"))
        return chat_history, ""
