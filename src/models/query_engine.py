"""
Query engine for processing natural language queries.
"""

import gradio as gr
from src.agent.agent import MasterAgent


def execute_agent_query(
    connection_name: str,
    query: str,
    chat_history: list,
    master_agent: MasterAgent
) -> tuple:
    """Execute query using MasterAgent with full tool usage transparency."""
    if not connection_name:
        gr.Warning("Please select a database connection first")
        return chat_history, query
    
    if not master_agent:
        gr.Warning("Agent not initialized. Please select a model and ensure Ollama is running")
        return chat_history, query
    
    if not query.strip():
        gr.Warning("Please enter a query")
        return chat_history, query
    
    try:
        # Execute query using the agent
        response = master_agent.run(query=query, connection_name=connection_name)
        
        # Extract response text and tool usage from the agent response
        response_text = ""
        tool_usage = []
        
        if isinstance(response, dict):
            messages = response.get("messages", [])
            
            if messages:
                # Process all messages to extract tool calls and responses
                for i, msg in enumerate(messages):
                    msg_class = msg.__class__.__name__ if hasattr(msg, '__class__') else type(msg).__name__
                    
                    # Extract AIMessage with tool calls
                    if msg_class == 'AIMessage':
                        tool_calls = getattr(msg, 'tool_calls', [])
                        if tool_calls:
                            for tool_call in tool_calls:
                                tool_name = tool_call.get('name', 'unknown')
                                tool_args = tool_call.get('args', {})
                                tool_usage.append({
                                    'type': 'tool_call',
                                    'name': tool_name,
                                    'args': tool_args
                                })
                    
                    # Extract ToolMessage (results from tool execution)
                    elif msg_class == 'ToolMessage':
                        tool_name = getattr(msg, 'name', 'unknown')
                        tool_content = getattr(msg, 'content', '')
                        tool_usage.append({
                            'type': 'tool_result',
                            'name': tool_name,
                            'content': tool_content
                        })
                
                # Get the last AIMessage (the final response from the agent)
                ai_messages = [msg for msg in messages if hasattr(msg, '__class__') and msg.__class__.__name__ == 'AIMessage']
                
                if ai_messages:
                    last_ai_message = ai_messages[-1]
                    response_text = getattr(last_ai_message, 'content', str(last_ai_message))
                else:
                    last_message = messages[-1]
                    response_text = getattr(last_message, 'content', str(last_message))
            else:
                response_text = "No response generated"
        else:
            response_text = str(response)
        
        # Ensure we have a valid response
        if not response_text or response_text.strip() == "":
            response_text = "The agent completed the task but didn't return a text response."
        
        # Format the complete response with tool usage
        formatted_response = ""
        
        # Add tool usage information if available
        if tool_usage:
            formatted_response += "### 🔧 Tools Used:\n\n"
            
            for i, tool in enumerate(tool_usage, 1):
                if tool['type'] == 'tool_call':
                    formatted_response += f"**{i}. Tool:** `{tool['name']}`\n"
                    if tool['args']:
                        formatted_response += f"   **Arguments:** `{tool['args']}`\n"
                    formatted_response += "\n"
                elif tool['type'] == 'tool_result':
                    # For SQL queries, try to identify and highlight them
                    content = tool['content']
                    if 'SELECT' in content.upper() or 'INSERT' in content.upper() or 'UPDATE' in content.upper() or 'DELETE' in content.upper():
                        formatted_response += f"   **Query Executed:**\n   ```sql\n   {content}\n   ```\n\n"
                    else:
                        # For other tool results (like table lists)
                        formatted_response += f"   **Result:** {content}\n\n"
            
            formatted_response += "---\n\n"
        
        # Add the final response
        formatted_response += f"### 💬 Response:\n\n{response_text}"
        
        chat_history.append((query, formatted_response))
        return chat_history, ""
        
    except Exception as e:
        import traceback
        error_msg = f"Error executing query: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)  # Print to console for debugging
        gr.Warning(f"Error: {str(e)}")
        chat_history.append((query, f"❌ **Error:** {str(e)}"))
        return chat_history, ""
