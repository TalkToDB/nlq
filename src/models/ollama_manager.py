"""
Ollama backend connection manager.
Handles saving, loading, and managing Ollama backend connections.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OLLAMA_CONNECTIONS_FILE = PROJECT_ROOT / "ollama_connections.json"

def load_ollama_connections() -> List[Dict]:
    """Load Ollama connections from file."""
    if OLLAMA_CONNECTIONS_FILE.exists():
        try:
            with open(OLLAMA_CONNECTIONS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_ollama_connections(connections: List[Dict]):
    """Save Ollama connections to file."""
    with open(OLLAMA_CONNECTIONS_FILE, 'w') as f:
        json.dump(connections, f, indent=2)

class OllamaConnectionManager:
    """Manages Ollama backend connections."""
    
    def __init__(self):
        self.connections = load_ollama_connections()
    
    def reload_connections(self):
        """Reload connections from file."""
        self.connections = load_ollama_connections()
    
    def add_connection(self, name: str, base_url: str, username: str = "", password: str = "") -> tuple[bool, str]:
        """
        Add a new Ollama backend connection.
        
        Args:
            name: Connection name
            base_url: Ollama backend URL
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            Tuple of (success, message)
        """
        if not name or not base_url:
            return False, "Error: Name and Base URL are required."
        
        # Check if connection with same name exists
        if any(conn['name'] == name for conn in self.connections):
            return False, f"Error: Connection '{name}' already exists."
        
        connection = {
            "name": name,
            "base_url": base_url.strip(),
            "username": username.strip() if username else "",
            "password": password.strip() if password else "",
            "should_authenticate": bool(username and password)
        }
        
        self.connections.append(connection)
        save_ollama_connections(self.connections)
        self.reload_connections()
        
        return True, f"Successfully added Ollama connection '{name}'."
    
    def update_connection(self, name: str, base_url: str, username: str = "", password: str = "") -> tuple[bool, str]:
        """Update an existing Ollama backend connection."""
        for i, conn in enumerate(self.connections):
            if conn['name'] == name:
                self.connections[i] = {
                    "name": name,
                    "base_url": base_url.strip(),
                    "username": username.strip() if username else "",
                    "password": password.strip() if password else "",
                    "should_authenticate": bool(username and password)
                }
                save_ollama_connections(self.connections)
                self.reload_connections()
                return True, f"Successfully updated Ollama connection '{name}'."
        
        return False, f"Error: Connection '{name}' not found."
    
    def delete_connection(self, name: str) -> tuple[bool, str]:
        """Delete an Ollama backend connection."""
        if not name:
            return False, "Error: Please select a connection to delete."
        
        initial_count = len(self.connections)
        self.connections = [conn for conn in self.connections if conn['name'] != name]
        
        if len(self.connections) < initial_count:
            save_ollama_connections(self.connections)
            self.reload_connections()
            return True, f"Successfully deleted Ollama connection '{name}'."
        
        return False, f"Error: Connection '{name}' not found."
    
    def get_connection(self, name: str) -> Optional[Dict[str, str]]:
        """Get a specific connection by name."""
        for conn in self.connections:
            if conn['name'] == name:
                return conn
        return None
    
    def get_connections_table(self) -> List[List]:
        """Get connections as a list for display in table format."""
        if not self.connections:
            return []
        
        table_data = []
        for conn in self.connections:
            auth_status = "✓ Yes" if conn.get('should_authenticate', False) else "✗ No"
            table_data.append([
                conn['name'],
                conn['base_url'],
                auth_status
            ])
        
        return table_data
    
    def get_connection_names(self) -> List[str]:
        """Get list of connection names."""
        return [conn['name'] for conn in self.connections]
    
    def connection_exists(self, name: str) -> bool:
        """Check if a connection with given name exists."""
        return any(conn['name'] == name for conn in self.connections)
