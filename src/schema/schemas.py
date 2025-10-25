"""Schema type definitions for database schema structures."""

from typing import TypedDict, List
from src.database.schemas import SQL_DATABASES, NOSQL_DATABASES


class SQLSchemaStructure(TypedDict):
    """Type definition for SQL database schema structure."""
    
    # database type
    db_type: SQL_DATABASES

    # stores all table names
    table_names: List[str]

    # maps table name to its schema
    table_schema: dict[str, str]

    # stores all the function definitions
    functions: List[str]


class NoSQLSchemaStructure(TypedDict):
    """Type definition for NoSQL database schema structure."""
    
    # database type
    db_type: NOSQL_DATABASES

    # stores all collection names
    collection_names: List[str]

    # maps collection name to its schema
    collection_schema: dict[str, str]
