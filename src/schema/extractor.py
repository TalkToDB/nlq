"""
Schema extraction utilities using LangChain's built-in tools.
Leverages existing LangChain SQL database tools instead of reinventing.
"""

from typing import List, Dict, Optional
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
)
from langchain_mongodb.agent_toolkit import MongoDBDatabase
from langchain_mongodb.agent_toolkit.tool import (
    InfoMongoDBDatabaseTool,
    ListMongoDBDatabaseTool,
)
from src.schema.schemas import SQLSchemaStructure, NoSQLSchemaStructure
from src.database.manager import DatabaseManager
from src.agent.tools.sql_tools import build_connection_uri
from src.agent.tools.mongodb_tools import build_mongodb_uri


class SQLSchemaExtractor:
    """Extract schema information using LangChain's built-in tools."""
    
    def __init__(self, db: SQLDatabase):
        """
        Initialize with a SQLDatabase connection.
        
        Args:
            db: LangChain SQLDatabase instance
        """
        self.db = db
        self.list_tool = ListSQLDatabaseTool(db=db)
        self.info_tool = InfoSQLDatabaseTool(db=db)
    
    def get_table_names(self) -> List[str]:
        """
        Get all table names from the database.
        
        Returns:
            List of table name strings
        """
        # ListSQLDatabaseTool returns comma-separated table names
        result = self.list_tool.invoke("")
        if result:
            return [table.strip() for table in result.split(",")]
        return []
    
    def get_table_schemas(self, table_names: List[str] = None) -> Dict[str, str]:
        """
        Get schema information for specific tables or all tables.
        
        Args:
            table_names: Optional list of specific tables. If None, gets all tables.
        
        Returns:
            Dictionary mapping table names to their schema information
        """
        if table_names is None:
            table_names = self.get_table_names()
        
        if not table_names:
            return {}
        
        # InfoSQLDatabaseTool expects comma-separated table names
        tables_input = ", ".join(table_names)
        schema_info = self.info_tool.invoke(tables_input)
        
        # Parse the schema info into a dict
        # The tool returns schema and sample rows for each table
        table_schemas = {}
        if schema_info:
            # Store the full schema info for each table
            # You might want to parse this more granularly based on your needs
            for table_name in table_names:
                table_schemas[table_name] = schema_info
        
        return table_schemas
    
    def get_full_schema_structure(self) -> SQLSchemaStructure:
        """
        Get complete schema structure compatible with DBSchemaCacheManager.
        
        Returns:
            SQLSchemaStructure with all schema information
        """
        table_names = self.get_table_names()
        table_schemas = {}
        
        # Get schema for each table individually for better organization
        for table_name in table_names:
            schema_info = self.info_tool.invoke(table_name)
            table_schemas[table_name] = schema_info
        
        return SQLSchemaStructure(
            db_type=self.db.dialect,  # e.g., "postgresql", "mysql", etc.
            table_names=table_names,
            table_schema=table_schemas,
            functions=[]  # Can be extended to fetch stored procedures/functions
        )
    
    def get_context_for_llm(self) -> Dict:
        """
        Get database context optimized for LLM consumption.
        Uses the built-in get_context method from SQLDatabase.
        
        Returns:
            Dictionary with database context information
        """
        return self.db.get_context()

class MongoSchemaExtractor:
    """Extract schema information using LangChain's built-in MongoDB tools."""
    
    def __init__(self, db: MongoDBDatabase):
        """
        Initialize with a MongoDBDatabase connection.
        
        Args:
            db: LangChain MongoDBDatabase instance
        """
        self.db = db
        self.list_tool = ListMongoDBDatabaseTool(db=db)
        self.info_tool = InfoMongoDBDatabaseTool(db=db)
    
    def get_collection_names(self) -> List[str]:
        """
        Get all collection names from the database.
        
        Returns:
            List of collection name strings
        """
        # ListMongoDBDatabaseTool returns comma-separated collection names
        result = self.list_tool.invoke("")
        if result:
            return [coll.strip() for coll in result.split(",")]
        return []
    
    def get_collection_schemas(self, collection_names: List[str] = None) -> Dict[str, str]:
        """
        Get schema information for specific collections or all collections.
        
        Args:
            collection_names: Optional list of specific collections. If None, gets all collections.
        
        Returns:
            Dictionary mapping collection names to their schema information
        """
        if collection_names is None:
            collection_names = self.get_collection_names()
        
        if not collection_names:
            return {}
        
        # InfoMongoDBDatabaseTool expects comma-separated collection names
        colls_input = ", ".join(collection_names)
        schema_info = self.info_tool.invoke(colls_input)
        
        # Parse the schema info into a dict
        # The tool returns schema and sample documents for each collection
        collection_schemas = {}
        if schema_info:
            # Store the full schema info for each collection
            for coll_name in collection_names:
                collection_schemas[coll_name] = schema_info
        
        return collection_schemas
    
    def get_full_schema_structure(self) -> NoSQLSchemaStructure:
        """
        Get complete schema structure compatible with DBSchemaCacheManager.
        
        Returns:
            NoSQLSchemaStructure with all schema information
        """
        collection_names = self.get_collection_names()
        collection_schemas = {}
        
        # Get schema for each collection individually for better organization
        for coll_name in collection_names:
            schema_info = self.info_tool.invoke(coll_name)
            collection_schemas[coll_name] = schema_info
        
        return NoSQLSchemaStructure(
            db_type="MongoDB",
            collection_names=collection_names,
            collection_schema=collection_schemas,
        )
    
    def get_context_for_llm(self) -> Dict:
        """
        Get database context optimized for LLM consumption.
        Uses the built-in get_context method from MongoDBDatabase.
        
        Returns:
            Dictionary with database context information
        """
        return self.db.get_context()

def create_schema_extractor_from_connection_name(
    connection_name: str
) -> Optional[SQLSchemaExtractor | MongoSchemaExtractor]:
    """
    Create a schema extractor using a saved connection name.
    Uses DatabaseManager to retrieve connection details and automatically
    creates the appropriate extractor (SQL or MongoDB) based on connection type.
    
    Args:
        connection_name: Name of the saved database connection
    
    Returns:
        SQLSchemaExtractor or MongoSchemaExtractor instance, or None if connection not found
    """
    # Get connection from DatabaseManager
    db_manager = DatabaseManager()
    connection = db_manager.get_connection(connection_name)
    
    if not connection:
        print(f"Error: Connection '{connection_name}' not found.")
        return None
    
    db_type = connection.get('type', '')
    
    try:
        # Create appropriate extractor based on database type
        if db_type == "MongoDB":
            # MongoDB connection
            uri = build_mongodb_uri(connection)
            database_name = connection.get('database', 'admin')
            db = MongoDBDatabase.from_connection_string(uri, database=database_name)
            return MongoSchemaExtractor(db)
        else:
            # SQL database connection (PostgreSQL, MySQL, SQLite, SQL Server)
            uri = build_connection_uri(connection)
            db = SQLDatabase.from_uri(uri)
            return SQLSchemaExtractor(db)
        
    except Exception as e:
        print(f"Error creating schema extractor for '{connection_name}': {str(e)}")
        return None
