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
    """
    Execute query on MongoDB database - supports both local and MongoDB Atlas (cloud).
    
    The query parameter is expected to be a JSON string with structured parameters:
    {
        "collection_name": "users",
        "operation": "find",  # find, aggregate, count, insert_one, insert_many, update_one, update_many, delete_one, delete_many
        "filter": "{}",  # JSON string
        "projection": "{}",  # JSON string  
        "sort": "{}",  # JSON string
        "limit": 100,
        "skip": 0,
        "update": "{}",  # JSON string for update operations
        "document": "",  # JSON string for insert operations
        "pipeline": "[]"  # JSON string for aggregation pipeline
    }
    """
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
            if username and password:
                clean_host = host.replace('mongodb+srv://', '').replace('mongodb://', '')
                conn_str = f"mongodb+srv://{username}:{password}@{clean_host}/{database}?retryWrites=true&w=majority"
            else:
                return False, "MongoDB Atlas (cloud) requires both username and password", None
        else:
            port = connection_data.get('port', '27017')
            auth_source = connection_data.get('auth_source', 'admin')
            
            try:
                port = int(port) if port else 27017
            except ValueError:
                port = 27017
            
            if username and password:
                conn_str = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource={auth_source}"
            else:
                conn_str = f"mongodb://{host}:{port}/"
        
        client = MongoClient(conn_str, serverSelectionTimeoutMS=30000, socketTimeoutMS=None, connectTimeoutMS=20000)
        
        # Test connection
        client.server_info()
        
        db = client[database]
        
        # Parse the structured query parameters
        try:
            query_params = json.loads(query)
        except json.JSONDecodeError as e:
            client.close()
            return False, f"Invalid query JSON format: {str(e)}", None
        
        collection_name = query_params.get('collection_name', '')
        if not collection_name:
            client.close()
            return False, "collection_name is required", None
        
        collection = db[collection_name]
        operation = query_params.get('operation', 'find').lower()
        
        # Helper function to safely parse JSON strings
        def parse_json_param(param_str: str, default=None):
            if not param_str or param_str in ('{}', '[]', ''):
                return default if default is not None else ({} if param_str != '[]' else [])
            try:
                return json.loads(param_str)
            except json.JSONDecodeError:
                return default if default is not None else {}
        
        # Parse common parameters
        filter_doc = parse_json_param(query_params.get('filter', '{}'), {})
        projection_doc = parse_json_param(query_params.get('projection', '{}'), None)
        sort_doc = parse_json_param(query_params.get('sort', '{}'), None)
        limit_val = min(int(query_params.get('limit', 100)), 1000)  # Cap at 1000 for safety
        skip_val = int(query_params.get('skip', 0))
        
        results = None
        
        # Execute based on operation type
        if operation == 'find':
            cursor = collection.find(filter_doc, projection_doc)
            if sort_doc:
                cursor = cursor.sort(list(sort_doc.items()))
            if skip_val > 0:
                cursor = cursor.skip(skip_val)
            cursor = cursor.limit(limit_val)
            results = list(cursor)
            
        elif operation == 'aggregate':
            pipeline = parse_json_param(query_params.get('pipeline', '[]'), [])
            if not isinstance(pipeline, list):
                pipeline = [pipeline]
            # Block write stages in aggregation pipeline
            write_stages = {'$out', '$merge'}
            for stage in pipeline:
                if any(ws in stage for ws in write_stages):
                    client.close()
                    return False, "Write operations ($out, $merge) are not allowed in aggregation pipeline", None
            # Add $limit stage if not present for safety
            has_limit = any('$limit' in stage for stage in pipeline)
            if not has_limit:
                pipeline.append({'$limit': limit_val})
            results = list(collection.aggregate(pipeline))
            
        elif operation == 'count':
            count = collection.count_documents(filter_doc)
            results = [{"count": count}]
            
        elif operation == 'distinct':
            field = query_params.get('field', '')
            if not field:
                client.close()
                return False, "field is required for distinct operation", None
            distinct_values = collection.distinct(field, filter_doc)
            results = [{"field": field, "distinct_values": distinct_values, "count": len(distinct_values)}]
            
        elif operation == 'find_one':
            result = collection.find_one(filter_doc, projection_doc)
            results = [result] if result else []
            
        else:
            client.close()
            return False, f"Unsupported operation: {operation}. Only read operations allowed: find, find_one, aggregate, count, distinct", None
        
        # Convert ObjectId and other BSON types to JSON-serializable format
        if results is not None:
            if isinstance(results, list):
                results = json.loads(json_util.dumps(results))
            elif isinstance(results, dict):
                results = json.loads(json_util.dumps(results))
        else:
            results = []
        
        client.close()
        return True, "Query executed successfully", results
        
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
