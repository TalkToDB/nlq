"""
Database connection schemas for different database types.
Each database type has its own required fields and default ports.
"""

from typing import Dict, List, Any, Literal
from dataclasses import dataclass

@dataclass
class DatabaseField:
    """Represents a form field for database connection."""
    name: str
    label: str
    placeholder: str
    field_type: str = "text"  # text, password, number
    required: bool = True
    default: str = ""

class DatabaseSchema:
    """Base class for database connection schemas."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        """Return list of fields required for this database type."""
        raise NotImplementedError
    
    @staticmethod
    def get_default_port() -> str:
        """Return default port for this database type."""
        raise NotImplementedError
    
    @staticmethod
    def validate_connection(data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate connection data. Returns (is_valid, error_message)."""
        return True, ""

class PostgreSQLSchema(DatabaseSchema):
    """PostgreSQL connection schema."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        return [
            DatabaseField("host", "Host", "e.g., localhost or 192.168.1.100"),
            DatabaseField("port", "Port", "5432"),
            DatabaseField("database", "Database Name", "my_database"),
            DatabaseField("username", "Username", "postgres"),
            DatabaseField("password", "Password", "Enter password", field_type="password"),
            DatabaseField("schema", "Schema (Optional)", "public", required=False),
        ]
    
    @staticmethod
    def get_default_port() -> str:
        return "5432"

class MySQLSchema(DatabaseSchema):
    """MySQL connection schema."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        return [
            DatabaseField("host", "Host", "e.g., localhost or 192.168.1.100"),
            DatabaseField("port", "Port", "3306"),
            DatabaseField("database", "Database Name", "my_database"),
            DatabaseField("username", "Username", "root"),
            DatabaseField("password", "Password", "Enter password", field_type="password"),
        ]
    
    @staticmethod
    def get_default_port() -> str:
        return "3306"

class SQLiteSchema(DatabaseSchema):
    """SQLite connection schema."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        return [
            DatabaseField("database_path", "Database File Path", "e.g., /path/to/database.db or C:\\data\\db.sqlite"),
        ]
    
    @staticmethod
    def get_default_port() -> str:
        return ""  # SQLite doesn't use ports

class SQLServerSchema(DatabaseSchema):
    """SQL Server connection schema."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        return [
            DatabaseField("host", "Host", "e.g., localhost or server.domain.com"),
            DatabaseField("port", "Port", "1433"),
            DatabaseField("database", "Database Name", "master"),
            DatabaseField("username", "Username", "sa"),
            DatabaseField("password", "Password", "Enter password", field_type="password"),
            DatabaseField("driver", "Driver (Optional)", "ODBC Driver 17 for SQL Server", required=False),
        ]
    
    @staticmethod
    def get_default_port() -> str:
        return "1433"

class MongoDBSchema(DatabaseSchema):
    """MongoDB connection schema - supports both local and cloud (Atlas)."""
    
    @staticmethod
    def get_fields() -> List[DatabaseField]:
        return [
            DatabaseField("connection_type", "Connection Type (local/cloud)", "local", required=True),
            DatabaseField("host", "Host (Local) or Cluster URL (Cloud)", "e.g., localhost or cluster0.xxxxx.mongodb.net"),
            DatabaseField("port", "Port (Local only)", "27017", required=False),
            DatabaseField("database", "Database Name", "admin"),
            DatabaseField("username", "Username", "mongodb_user", required=False),
            DatabaseField("password", "Password", "Enter password", field_type="password", required=False),
            DatabaseField("auth_source", "Auth Source (Local only)", "admin", required=False),
        ]
    
    @staticmethod
    def get_default_port() -> str:
        return "27017"

# Registry of all supported database types
DATABASE_SCHEMAS = {
    "PostgreSQL": PostgreSQLSchema,
    "MySQL": MySQLSchema,
    "SQLite": SQLiteSchema,
    "SQL Server": SQLServerSchema,
    "MongoDB": MongoDBSchema,
}

# Type aliases for database types
SQL_DATABASES = Literal["PostgreSQL", "MySQL", "SQLite", "SQL Server"]

DATABASE_TYPES = Literal["PostgreSQL", "MySQL", "SQLite", "SQL Server", "MongoDB"]

NOSQL_DATABASES = Literal["MongoDB"]

SQL_DATABASE_NAMES = ["PostgreSQL", "MySQL", "SQLite", "SQL Server"]

NOSQL_DATABASE_NAMES = ["MongoDB"]

def get_schema_for_db_type(db_type: str) -> DatabaseSchema:
    """Get the schema class for a given database type."""
    return DATABASE_SCHEMAS.get(db_type, PostgreSQLSchema)

def get_supported_databases() -> List[str]:
    """Get list of supported database types."""
    return list(DATABASE_SCHEMAS.keys())
