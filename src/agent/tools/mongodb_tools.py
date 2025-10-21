from langchain_mongodb.agent_toolkit import MongoDBDatabase, MongoDBDatabaseToolkit
from typing import List, Dict
from urllib.parse import quote_plus

def build_mongodb_uri(connection: Dict) -> str:
    """
    Build MongoDB connection URI from connection data.
    Properly encodes special characters in username and password.
    
    Args:
        connection: Connection dictionary with MongoDB connection details
        
    Returns:
        MongoDB connection URI string with properly encoded components
    """
    connection_type = connection.get('connection_type', 'local')
    host = connection.get('host', 'localhost')
    database = connection.get('database', 'admin')
    username = connection.get('username', '')
    password = connection.get('password', '')
    
    # Detect if it's MongoDB Atlas (cloud) based on connection type or host
    is_cloud = (connection_type == 'cloud' or 'mongodb.net' in host.lower())
    
    # Build connection string based on connection type
    if is_cloud:
        # MongoDB Atlas uses mongodb+srv:// protocol and doesn't need port
        # Format: mongodb+srv://username:password@cluster.mongodb.net/database
        if username and password:
            # Clean up host if it already has protocol
            clean_host = host.replace('mongodb+srv://', '').replace('mongodb://', '')
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            return f"mongodb+srv://{encoded_username}:{encoded_password}@{clean_host}/{database}?retryWrites=true&w=majority"
        else:
            # Clean up host if it already has protocol
            clean_host = host.replace('mongodb+srv://', '').replace('mongodb://', '')
            return f"mongodb+srv://{clean_host}/{database}?retryWrites=true&w=majority"
    else:
        # Local MongoDB connection with standard mongodb:// protocol
        port = connection.get('port', '27017')
        auth_source = connection.get('auth_source', 'admin')
        
        # Build connection string for local MongoDB
        if username and password:
            encoded_username = quote_plus(username)
            encoded_password = quote_plus(password)
            return f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{database}?authSource={auth_source}"
        else:
            return f"mongodb://{host}:{port}/{database}"


def get_mongodb_tools(connection: Dict[str, str] | None, llm) -> list:
    """
    Creates LangChain MongoDB database tools for multiple MongoDB connections.
    Supports both local MongoDB and MongoDB Atlas (cloud).
    
    Args:
        connections: List of connection dictionaries with MongoDB connection details
        llm: Language model instance
        
    Returns:
        List of LangChain tools for MongoDB operations
    """
    all_tools = []
    
    if not connection:
        return all_tools

    try:
        # Build MongoDB connection URI
        uri = build_mongodb_uri(connection)
        database_name = connection.get('database', 'admin')
        conn_name = connection.get('name', 'unknown')
        
        # Create MongoDB toolkit using LangChain's MongoDB toolkit
        try:
            db = MongoDBDatabase.from_connection_string(uri, database=database_name)

            # Create toolkit
            toolkit = MongoDBDatabaseToolkit(db=db, llm=llm)
            tools = toolkit.get_tools()
            
            # Rename tools to include connection name for clarity
            for tool in tools:
                original_name = tool.name
                tool.name = f"{original_name}_{conn_name}"
                tool.description = f"{tool.description} [MongoDB Connection: {conn_name}]"
            
            all_tools.extend(tools)
            
        except ImportError:
            # Fallback if langchain_mongodb is not available
            print(f"Warning: langchain_mongodb not installed. Install with: pip install langchain-mongodb")
            print(f"Skipping MongoDB connection '{conn_name}'")
            
    except Exception as e:
        print(f"Warning: Failed to create tools for MongoDB connection '{connection.get('name')}': {str(e)}")

    return all_tools
