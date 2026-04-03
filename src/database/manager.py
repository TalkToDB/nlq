"""
Database connection manager.
Handles saving, loading, and managing database connections.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

# Get the project root directory (2 levels up from this file)
BASE_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent.parent))
DB_CONNECTIONS_FILE = BASE_DIR / "db_connections.json"

print(f"Database connections file path: {DB_CONNECTIONS_FILE}")

def load_connections() -> List[Dict]:
    """Load database connections from file."""
    if DB_CONNECTIONS_FILE.exists():
        try:
            with open(DB_CONNECTIONS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_connections(connections: List[Dict]):
    """Save database connections to file."""
    with open(DB_CONNECTIONS_FILE, 'w') as f:
        json.dump(connections, f, indent=2)

class DatabaseManager:
    """Manages database connections."""
    
    def __init__(self):
        self.connections = load_connections()
    
    def reload_connections(self):
        """Reload connections from file."""
        self.connections = load_connections()
    
    def add_connection(self, name: str, db_type: str, connection_data: Dict) -> tuple[bool, str]:
        """
        Add a new database connection.
        
        Args:
            name: Connection name
            db_type: Database type (PostgreSQL, MySQL, etc.)
            connection_data: Dictionary containing connection parameters
            
        Returns:
            Tuple of (success, message)
        """
        from src.schema.manager import DBSchemaCacheManager

        if not name or not db_type:
            return False, "Error: Name and database type are required."
        
        # Check if connection with same name exists
        if any(conn['name'] == name for conn in self.connections):
            return False, f"Error: Connection '{name}' already exists."
        
        connection = {
            "name": name,
            "type": db_type,
            **connection_data
        }
        
        self.connections.append(connection)
        save_connections(self.connections)
        self.reload_connections()  # Reload to ensure consistency
        schema_cache_manager = DBSchemaCacheManager()
        schema_cache_manager.add_new_schema(name, db_type)

        return True, f"Successfully added connection '{name}'."
    
    def update_connection(self, name: str, db_type: str, connection_data: Dict) -> tuple[bool, str]:
        """Update an existing database connection."""
        from src.schema.manager import DBSchemaCacheManager
        for i, conn in enumerate(self.connections):
            if conn['name'] == name:
                self.connections[i] = {
                    "name": name,
                    "type": db_type,
                    **connection_data
                }
                save_connections(self.connections)
                self.reload_connections()  # Reload to ensure consistency
                schema_cache_manager = DBSchemaCacheManager()
                schema_cache_manager.sync(name, db_type)
                return True, f"Successfully updated connection '{name}'."
        
        return False, f"Error: Connection '{name}' not found."
    
    def delete_connection(self, name: str) -> tuple[bool, str]:
        """Delete a database connection."""
        from src.schema.manager import DBSchemaCacheManager

        if not name:
            return False, "Error: Please select a connection to delete."
        
        initial_count = len(self.connections)
        self.connections = [conn for conn in self.connections if conn['name'] != name]
        
        if len(self.connections) < initial_count:
            schema_cache_manager = DBSchemaCacheManager()
            schema_cache_manager.delete_schema(name)
            schema_cache_manager.save_state()
            save_connections(self.connections)
            self.reload_connections()
            return True, f"Successfully deleted connection '{name}'."
        
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
            # Different display logic for different database types
            if conn['type'] == 'SQLite':
                location = conn.get('database_path', 'N/A')
            else:
                location = conn.get('host', 'N/A')
            
            database = conn.get('database', conn.get('database_path', 'N/A'))
            
            table_data.append([
                conn['name'],
                conn['type'],
                location,
                database
            ])
        
        return table_data
    
    def get_connection_names(self) -> List[str]:
        """Get list of connection names."""
        return [conn['name'] for conn in self.connections]
    
    def connection_exists(self, name: str) -> bool:
        """Check if a connection with given name exists."""
        return any(conn['name'] == name for conn in self.connections)
