"""
Query engine for processing natural language queries.
"""

import uuid
import gradio as gr
import time
import datetime
from src.database.manager import DatabaseManager
from src.models.ollama_manager import OllamaConnectionManager
from src.agent.result_storage import save_query_result

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

        # result = graph.invoke(initial_state, config)
        
        # Track timing information
        node_timings = {}
        overall_start = time.time()
        
        # Stream events to capture node execution times
        for event in graph.stream(initial_state, config, stream_mode="debug"):
            event_type = event.get("type")
            current_time = time.time()
            
            if event_type == "task":
                payload = event.get("payload", {})
                node_name = payload.get("name")
                
                if node_name:
                    # Track start time
                    if node_name not in node_timings:
                        node_timings[node_name] = {"start": current_time, "end": None, "duration": 0}
            
            elif event_type == "task_result":
                payload = event.get("payload", {})
                node_name = payload.get("name")
                
                if node_name and node_name in node_timings:
                    node_timings[node_name]["end"] = current_time
                    if node_timings[node_name]["start"]:
                        node_timings[node_name]["duration"] = current_time - node_timings[node_name]["start"]
        
        overall_end = time.time()
        total_duration = overall_end - overall_start
        
        # Get final result
        result = graph.get_state(config)
        result = result.values
        
        # Write to log file
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent.parent
        log_path = project_root / "output.log"
        
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"=" * 80 + "\n")
            log_file.write(f"Graph Execution Log\n")
            log_file.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Query ID: {query_id}\n")
            log_file.write(f"=" * 80 + "\n\n")
            
            log_file.write(f"TOTAL RUNTIME: {total_duration:.4f} seconds\n\n")
            
            log_file.write(f"PER-NODE RUNTIME:\n")
            log_file.write(f"-" * 80 + "\n")
            
            # Sort by execution order (start time)
            sorted_nodes = sorted(
                [(name, data) for name, data in node_timings.items() if data.get("duration", 0) > 0],
                key=lambda x: x[1].get("start", 0)
            )
            
            for node_name, timing_data in sorted_nodes:
                duration = timing_data.get("duration", 0)
                percentage = (duration / total_duration * 100) if total_duration > 0 else 0
                log_file.write(f"  {node_name:<30} {duration:>10.4f}s  ({percentage:>6.2f}%)\n")
            
            log_file.write(f"-" * 80 + "\n\n")
        
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
            
            # Format query based on database type
            db_type = result.get('database_type', 'sql')
            if db_type == 'MongoDB':
                formatted_response += f"```json\n{agent_response['db_query']}\n```\n\n"
            else:
                formatted_response += f"```sql\n{agent_response['db_query']}\n```\n\n"
            
            if agent_response.get('reasoning'):
                formatted_response += f"**Reasoning:** {agent_response['reasoning']}\n\n"
            
            if agent_response.get('execution_result'):
                exec_result = agent_response['execution_result']
                result_count = len(exec_result) if isinstance(exec_result, list) else 1
                formatted_response += f"**Execution:** ✅ Success ({result_count} results)\n\n"
                
                # Save results to file
                saved_filepath = save_query_result(
                    query_id=query_id,
                    query_text=query,
                    db_query=agent_response['db_query'],
                    results=exec_result,
                    database_type=connection_details['type'],
                    connection_name=connection_name
                )
                
                # Show link to view raw data
                if saved_filepath:
                    # Extract just the filename for the URL
                    import os
                    filename = os.path.basename(saved_filepath)
                    formatted_response += f"📁 **[View Raw Results](/results/{filename})**\n\n"
                    
            elif agent_response.get('execution_error'):
                errors = agent_response['execution_error']
                formatted_response += f"**Execution:** Error - {errors[-1] if errors else 'Unknown error'}\n\n"
            
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
        chat_history.append((query, f"**Error:** {str(e)}"))
        return chat_history, ""
