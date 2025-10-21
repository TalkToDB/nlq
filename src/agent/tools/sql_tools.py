from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Dict
from urllib.parse import quote_plus

def build_connection_uri(connection: Dict) -> str:
    """
    Build SQLAlchemy connection URI from connection data.
    Properly encodes special characters in username, password, and other components.
    
    Args:
        connection: Connection dictionary with type and connection details
        
    Returns:
        SQLAlchemy connection URI string with properly encoded components
    """
    db_type = connection.get('type')
    
    if db_type == 'PostgreSQL':
        # postgresql://username:password@host:port/database
        username = quote_plus(connection.get('username', ''))
        password = quote_plus(connection.get('password', ''))
        host = connection.get('host', 'localhost')
        port = connection.get('port', '5432')
        database = connection.get('database', '')

        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    elif db_type == 'MySQL':
        # mysql+mysqlconnector://username:password@host:port/database
        username = quote_plus(connection.get('username', ''))
        password = quote_plus(connection.get('password', ''))
        host = connection.get('host', 'localhost')
        port = connection.get('port', '3306')
        database = connection.get('database', '')
        
        return f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    
    elif db_type == 'SQLite':
        # sqlite:///path/to/database.db
        # SQLite paths don't need encoding
        return f"sqlite:///{connection.get('database_path')}"
    
    elif db_type == 'SQL Server':
        # mssql+pyodbc://username:password@host:port/database?driver=ODBC+Driver+17+for+SQL+Server
        username = quote_plus(connection.get('username', ''))
        password = quote_plus(connection.get('password', ''))
        host = connection.get('host', 'localhost')
        port = connection.get('port', '1433')
        database = connection.get('database', '')
        driver = connection.get('driver', 'ODBC Driver 17 for SQL Server')
        
        # Driver name also needs encoding for URL
        encoded_driver = quote_plus(driver)
        
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={encoded_driver}"
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def get_sql_tools(connection: Dict[str, str] | None, llm) -> list:
    """
    Creates LangChain SQL database tools for multiple SQL database connections.
    Supports PostgreSQL, MySQL, SQLite, and SQL Server.
    
    Args:
        connections: List of connection dictionaries with connection details
        llm: Language model instance
        
    Returns:
        List of LangChain tools for database operations
    """
    all_tools = []
    
    if not connection:
        return all_tools

    try:
        # Build connection URI
        uri = build_connection_uri(connection)
        
        # Create SQLDatabase instance
        db = SQLDatabase.from_uri(uri)
        
        # Create toolkit with unique tool names based on connection name
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()
        
        # Rename tools to include connection name for clarity
        conn_name = connection.get('name', 'unknown')
        for tool in tools:
            # Append connection name to tool name and description
            original_name = tool.name
            tool.name = f"{original_name}_{conn_name}"
            tool.description = f"{tool.description} [Connection: {conn_name}]"
        
        all_tools.extend(tools)
        
    except Exception as e:
        print(f"Warning: Failed to create tools for connection '{connection.get('name')}': {str(e)}")

    return all_tools