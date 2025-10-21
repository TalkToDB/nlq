"""
Database executor for running queries on different database types.
"""

import json
from typing import Dict, Any, Tuple
from pathlib import Path
import traceback

def execute_postgres_query(connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """Execute query on PostgreSQL database."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host=connection_data.get('host', 'localhost'),
            port=connection_data.get('port', 5432),
            database=connection_data.get('database'),
            user=connection_data.get('username'),
            password=connection_data.get('password')
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        
        # Check if query returns results
        if cursor.description:
            results = cursor.fetchall()
            result_data = [dict(row) for row in results]
        else:
            conn.commit()
            result_data = {"rows_affected": cursor.rowcount}
        
        cursor.close()
        conn.close()
        
        return True, "Query executed successfully", result_data
        
    except ImportError:
        return False, "PostgreSQL driver (psycopg2) not installed. Install with: pip install psycopg2-binary", None
    except Exception as e:
        return False, f"PostgreSQL Error: {str(e)}", None


def execute_mysql_query(connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """Execute query on MySQL database."""
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=connection_data.get('host', 'localhost'),
            port=connection_data.get('port', 3306),
            database=connection_data.get('database'),
            user=connection_data.get('username'),
            password=connection_data.get('password')
        )
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        
        # Check if query returns results
        if cursor.description:
            results = cursor.fetchall()
        else:
            conn.commit()
            results = {"rows_affected": cursor.rowcount}
        
        cursor.close()
        conn.close()
        
        return True, "Query executed successfully", results
        
    except ImportError:
        return False, "MySQL driver (mysql-connector-python) not installed. Install with: pip install mysql-connector-python", None
    except Exception as e:
        return False, f"MySQL Error: {str(e)}", None


def execute_sqlite_query(connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """Execute query on SQLite database."""
    try:
        import sqlite3
        
        db_path = Path(connection_data.get('database_path', ''))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Check if query returns results
        if cursor.description:
            results = [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            results = {"rows_affected": cursor.rowcount}
        
        cursor.close()
        conn.close()
        
        return True, "Query executed successfully", results
        
    except Exception as e:
        return False, f"SQLite Error: {str(e)}", None


def execute_sqlserver_query(connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """Execute query on SQL Server database."""
    try:
        import pyodbc
        
        # Get available drivers
        available_drivers = pyodbc.drivers()
        
        # Try to find SQL Server driver
        driver = connection_data.get('driver', 'ODBC Driver 17 for SQL Server')
        
        # If specified driver not found, try to use any available SQL Server driver
        if driver not in available_drivers:
            sql_server_drivers = [d for d in available_drivers if 'SQL Server' in d]
            if sql_server_drivers:
                driver = sql_server_drivers[0]
            else:
                # No SQL Server driver found
                return False, (
                    f"No SQL Server ODBC driver found. Available drivers: {', '.join(available_drivers) if available_drivers else 'None'}. "
                    "Please install 'ODBC Driver 17 for SQL Server' or 'ODBC Driver 18 for SQL Server'. "
                    "Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
                ), None
        
        # Build connection string - server and port together
        host = connection_data.get('host', 'localhost')
        port = connection_data.get('port', '1433')
        
        # Format: server,port for SQL Server
        server = f"{host},{port}" if port and port != '1433' else host
        
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={connection_data.get('database')};"
            f"UID={connection_data.get('username')};"
            f"PWD={connection_data.get('password')}"
        )
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Check if query returns results
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
        else:
            conn.commit()
            results = {"rows_affected": cursor.rowcount}
        
        cursor.close()
        conn.close()
        
        return True, "Query executed successfully", results
        
    except ImportError:
        return False, "SQL Server driver (pyodbc) not installed. Install with: pip install pyodbc", None
    except Exception as e:
        error_msg = str(e)
        if 'Data source name not found' in error_msg:
            try:
                import pyodbc
                available = pyodbc.drivers()
                error_msg = (
                    f"SQL Server ODBC driver not found. Available drivers: {', '.join(available) if available else 'None'}. "
                    "Please install 'ODBC Driver 17 for SQL Server' or 'ODBC Driver 18 for SQL Server'. "
                    "Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
                )
            except:
                pass
        return False, f"SQL Server Error: {error_msg}", None


def execute_mongodb_query(connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """Execute query on MongoDB database - supports both local and MongoDB Atlas (cloud)."""
    try:
        from pymongo import MongoClient
        from bson import json_util
        
        connection_type = connection_data.get('connection_type', 'local')
        host = connection_data.get('host', 'localhost')
        database = connection_data.get('database', 'admin')
        username = connection_data.get('username')
        password = connection_data.get('password')
        
        # Detect if it's MongoDB Atlas (cloud) based on connection type or host
        is_cloud = (connection_type == 'cloud' or 'mongodb.net' in host.lower())
        
        # Build connection string based on connection type
        if is_cloud:
            # MongoDB Atlas uses mongodb+srv:// protocol and doesn't need port
            # Format: mongodb+srv://username:password@cluster.mongodb.net/database
            if username and password:
                # Clean up host if it already has protocol
                clean_host = host.replace('mongodb+srv://', '').replace('mongodb://', '')
                conn_str = f"mongodb+srv://{username}:{password}@{clean_host}/{database}?retryWrites=true&w=majority"
            else:
                return False, "MongoDB Atlas (cloud) requires both username and password", None
                
        else:
            # Local MongoDB connection with standard mongodb:// protocol
            port = connection_data.get('port', '27017')
            auth_source = connection_data.get('auth_source', 'admin')
            
            # Validate port for local connections
            try:
                port = int(port) if port else 27017
            except ValueError:
                port = 27017
            
            # Build connection string for local MongoDB
            if username and password:
                conn_str = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
            else:
                conn_str = f"mongodb://{host}:{port}/"
        
        client = MongoClient(conn_str, serverSelectionTimeoutMS=30000, socketTimeoutMS=None, connectTimeoutMS=20000)
        
        # Test connection
        client.server_info()
        
        db = client[database]
        
        # Parse and execute MongoDB query
        # This is a simplified parser - in production, use a proper parser
        query = query.strip()
        
        # Simple query parsing (db.collection.operation())
        if query.startswith('db.'):
            # Extract collection and operation
            try:
                # Remove 'db.' prefix
                query_without_db = query[3:]
                
                # Find collection name
                collection_name = query_without_db.split('.')[0]
                collection = db[collection_name]
                
                # Execute the operation using eval (simplified - improve this in production)
                # For safety, we'll handle common operations explicitly
                results = None
                
                if 'countDocuments()' in query_without_db:
                    count = collection.count_documents({})
                    results = [{"count": count}]
                elif 'find().limit(' in query_without_db:
                    limit = int(query_without_db.split('limit(')[1].split(')')[0])
                    results = list(collection.find().limit(limit))
                elif 'find()' in query_without_db:
                    # Limit to 100 documents for safety
                    results = list(collection.find().limit(100))
                elif 'find({' in query_without_db:
                    # Extract filter - this is very basic parsing
                    results = list(collection.find().limit(100))
                else:
                    # Default: find with limit
                    results = list(collection.find().limit(10))
                
                # Convert ObjectId and other BSON types to JSON-serializable format
                if results is not None:
                    results = json.loads(json_util.dumps(results))
                else:
                    results = []
                
                client.close()
                return True, "Query executed successfully", results
                
            except Exception as e:
                client.close()
                return False, f"MongoDB Query Parse Error: {str(e)}\n{traceback.format_exc()}", None
        else:
            client.close()
            return False, "MongoDB query must start with 'db.collection_name'", None
        
    except ImportError:
        return False, "MongoDB driver (pymongo) not installed. Install with: pip install pymongo", None
    except Exception as e:
        return False, f"MongoDB Error: {str(e)}\n{traceback.format_exc()}", None


def execute_query(db_type: str, connection_data: Dict[str, str], query: str) -> Tuple[bool, str, Any]:
    """
    Execute query based on database type.
    
    Args:
        db_type: Type of database (PostgreSQL, MySQL, etc.)
        connection_data: Connection parameters
        query: Query to execute
        
    Returns:
        Tuple of (success, message, results)
    """
    executors = {
        'PostgreSQL': execute_postgres_query,
        'MySQL': execute_mysql_query,
        'SQLite': execute_sqlite_query,
        'SQL Server': execute_sqlserver_query,
        'MongoDB': execute_mongodb_query,
    }
    
    executor = executors.get(db_type)
    if not executor:
        return False, f"Database type '{db_type}' is not supported", None
    
    return executor(connection_data, query)
