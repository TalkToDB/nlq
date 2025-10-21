"""
Query engine for processing natural language queries.
This is a mock implementation to be replaced with LangChain later.
"""

from typing import List, Tuple

def execute_query(
    connection_name: str,
    model_provider: str,
    model_name: str,
    query: str,
    chat_history: List[Tuple[str, str]]
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
        response = "Please select a database connection first."
    elif not query.strip():
        response = "Please enter a query."
    else:
        # Mock response
        response = f"""Query processed successfully!

**Connection:** {connection_name}
**Model:** {model_provider} - {model_name}
**Your question:** {query}

**Mock SQL Generated:**
```sql
SELECT * FROM users WHERE name LIKE '%example%' LIMIT 10;
```

**Mock Results:**
| ID | Name | Email |
|---|---|---|
| 1 | John Doe | john@example.com |
| 2 | Jane Smith | jane@example.com |

*Note: This is a mock response. Real database querying will be implemented with LangChain.*
"""
    
    chat_history.append((query, response))
    return chat_history, ""
