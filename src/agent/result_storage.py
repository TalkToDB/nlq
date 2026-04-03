"""
Result storage for query execution results.
Stores query results as JSON files for viewing in the UI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import uuid


# Directory for storing query results
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "query_results"


def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_query_result(
    query_id: str,
    query_text: str,
    db_query: str,
    results: Any,
    database_type: str,
    connection_name: str
) -> Optional[str]:
    """
    Save query results to a JSON file.
    
    Args:
        query_id: Unique identifier for the query
        query_text: The natural language query
        db_query: The generated database query
        results: The query execution results
        database_type: Type of database (PostgreSQL, MySQL, MongoDB, etc.)
        connection_name: Name of the database connection
        
    Returns:
        Path to the saved file, or None if save failed
    """
    try:
        ensure_results_dir()
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id = query_id[:8] if query_id else str(uuid.uuid4())[:8]
        filename = f"result_{timestamp}_{short_id}.json"
        filepath = RESULTS_DIR / filename
        
        # Prepare the data to save
        result_data = {
            "query_id": query_id,
            "timestamp": datetime.now().isoformat(),
            "query_text": query_text,
            "database_query": db_query,
            "database_type": database_type,
            "connection_name": connection_name,
            "row_count": len(results) if isinstance(results, list) else 1,
            "results": results
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)
        
        return str(filepath)
        
    except Exception as e:
        print(f"Error saving query result: {e}")
        return None


def load_query_result(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load query results from a JSON file.
    
    Args:
        filepath: Path to the result file
        
    Returns:
        The loaded result data, or None if load failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading query result: {e}")
        return None


def get_recent_results(limit: int = 10) -> list:
    """
    Get the most recent query results.
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of (filepath, metadata) tuples
    """
    try:
        ensure_results_dir()
        
        # Get all JSON files in the results directory
        files = list(RESULTS_DIR.glob("result_*.json"))
        
        # Sort by modification time (most recent first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        results = []
        for filepath in files[:limit]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = {
                        "filepath": str(filepath),
                        "filename": filepath.name,
                        "timestamp": data.get("timestamp"),
                        "query_text": data.get("query_text", "")[:50] + "...",
                        "row_count": data.get("row_count", 0),
                        "database_type": data.get("database_type")
                    }
                    results.append((str(filepath), metadata))
            except Exception:
                continue
        
        return results
        
    except Exception as e:
        print(f"Error getting recent results: {e}")
        return []


def format_results_as_markdown_table(results: list, max_rows: int = 50) -> str:
    """
    Format query results as a Markdown table.
    
    Args:
        results: List of dictionaries (query results)
        max_rows: Maximum number of rows to display
        
    Returns:
        Markdown formatted table string
    """
    if not results or not isinstance(results, list):
        return "*No results to display*"
    
    if len(results) == 0:
        return "*Empty result set*"
    
    # Get headers from the first result
    if isinstance(results[0], dict):
        headers = list(results[0].keys())
    else:
        return f"*Results:* {results}"
    
    # Build the markdown table
    lines = []
    
    # Header row
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    lines.append(header_line)
    
    # Separator row
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    lines.append(separator)
    
    # Data rows (limit to max_rows)
    display_results = results[:max_rows]
    for row in display_results:
        if isinstance(row, dict):
            values = []
            for h in headers:
                val = row.get(h, "")
                # Truncate long values
                val_str = str(val)
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                # Escape pipe characters
                val_str = val_str.replace("|", "\\|").replace("\n", " ")
                values.append(val_str)
            lines.append("| " + " | ".join(values) + " |")
    
    # Add note if results were truncated
    if len(results) > max_rows:
        lines.append(f"\n*Showing {max_rows} of {len(results)} rows. Full data saved to file.*")
    
    return "\n".join(lines)


def cleanup_old_results(max_age_days: int = 7):
    """
    Remove result files older than the specified age.
    
    Args:
        max_age_days: Maximum age of files to keep
    """
    try:
        ensure_results_dir()
        
        import time
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        for filepath in RESULTS_DIR.glob("result_*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                filepath.unlink()
                print(f"Cleaned up old result file: {filepath.name}")
                
    except Exception as e:
        print(f"Error cleaning up old results: {e}")
