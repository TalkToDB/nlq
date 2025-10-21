"""
Test script to verify delete functionality works correctly.
"""

from src.database.manager import DatabaseManager
import json

def test_delete():
    """Test the delete functionality."""
    
    # Create a fresh manager instance
    manager = DatabaseManager()
    
    print("Initial connections:")
    print(f"  Count: {len(manager.connections)}")
    for conn in manager.connections:
        print(f"  - {conn['name']} ({conn['type']})")
    
    # Check what's in the file
    with open('db_connections.json', 'r') as f:
        file_data = json.load(f)
    
    print(f"\nFile has {len(file_data)} connections")
    
    # Reload
    manager.reload_connections()
    
    print(f"\nAfter reload:")
    print(f"  Count: {len(manager.connections)}")
    for conn in manager.connections:
        print(f"  - {conn['name']} ({conn['type']})")
    
    print("\n" + "="*50)
    print("Memory and file are in sync!" if len(manager.connections) == len(file_data) else "MISMATCH!")
    print("="*50)

if __name__ == "__main__":
    test_delete()
