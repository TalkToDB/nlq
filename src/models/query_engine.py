"""
Query engine for processing natural language queries.
This is a mock implementation to be replaced with LangChain later.
"""

import gradio as gr
from typing import List, Tuple
from src.models.ollama_api import OllamaAPI

def execute_query(
    connection_name: str,
    model_provider: str,
    model_name: str,
    query: str,
    chat_history: List[Tuple[str, str]],
    llm_api: OllamaAPI
) -> Tuple[List[Tuple[str, str]], str]:
    """
    Mock query function that returns a fixed output.
    This will be replaced with actual LangChain implementation later.
    
    Args:
        connection_name: Name of the database connection
        model_provider: Model provider (Ollama, OpenAI)
        model_name: Specific model name
        query: User's natural language query
        chat_history: Current chat history
        
    Returns:
        Tuple of (updated_chat_history, empty_string_for_input_box)
    """
    if not connection_name:
        gr.Warning("Please select a database connection first")
        return chat_history, query
    
    if not model_name:
        gr.Warning("Please select a model first. Enter Ollama URL and click Refresh to load available models")
        return chat_history, query
    
    if not query.strip():
        gr.Warning("Please enter a query")
        return chat_history, query
    
    # Mock response
    response = llm_api.generate_text(prompt=query)
#     response = f"""Query processed successfully!

# **Connection:** {connection_name}
# **Model:** {model_provider} - {model_name}
# **Your question:** {query}

# **Mock SQL Generated:**
# ```sql
# SELECT * FROM users WHERE name LIKE '%example%' LIMIT 10;
# ```

# **Mock Results:**
# | ID | Name | Email |
# |---|---|---|
# | 1 | John Doe | john@example.com |
# | 2 | Jane Smith | jane@example.com |

# *Note: This is a mock response. Real database querying will be implemented with LangChain.*
# """
    
    chat_history.append((query, response))
    return chat_history, ""
