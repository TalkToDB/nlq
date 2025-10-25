import os
import json
from pathlib import Path
from src.database.manager import DatabaseManager
from src.schema.schemas import SQLSchemaStructure, NoSQLSchemaStructure
from src.schema.extractor import create_schema_extractor_from_connection_name

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_CACHE_FILE = PROJECT_ROOT / "schema_cache.json"

class DBSchemaCacheManager:
    
    def __init__(self, ):
        self.schema_cache: dict[str, SQLSchemaStructure | NoSQLSchemaStructure] = {}
        self.load_state()

    def add_schema(self, connection_name: str, schema: SQLSchemaStructure | NoSQLSchemaStructure):
        self.schema_cache[connection_name] = schema

    def get_schema(self, connection_name: str) -> SQLSchemaStructure | NoSQLSchemaStructure | None:
        return self.schema_cache.get(connection_name, None)
    
    def exists(self, connection_name: str) -> bool:
        return connection_name in self.schema_cache

    def update_schema(self, connection_name: str, schema: SQLSchemaStructure | NoSQLSchemaStructure):
        self.schema_cache[connection_name] = schema
    
    def remove_schema(self, connection_name: str):
        if connection_name in self.schema_cache:
            del self.schema_cache[connection_name]

    def clear_cache(self):
        self.schema_cache.clear()

    def save_state(self):
        with open(SCHEMA_CACHE_FILE, "w") as f:
            json.dump(self.schema_cache, f)

    def load_state(self):
        try:
            if os.path.exists(SCHEMA_CACHE_FILE):
                with open(SCHEMA_CACHE_FILE, "r") as f:
                    self.schema_cache = json.load(f)
        except FileNotFoundError:
            self.schema_cache = {}

    def get_table_schema(self, connection_name: str, table_names: list[str]) -> list[str]:
        """Get schemas for given table names in a SQL database connection."""

        schema = self.get_schema(connection_name)

        if schema:

            table_schemas = schema.get('table_schema', [])

            if table_schemas:
                return [table_schemas.get(table_name, "") for table_name in table_names]

        return []

    def get_table_names(self, connection_name: str) -> list[str]:
        """Get all table names for a SQL database connection."""

        schema = self.get_schema(connection_name)

        if schema:
            return schema['table_names']

        return []

    def get_collection_schema(self, connection_name: str, collection_names: list[str]) -> list[str]:
        """Get schemas for given collection names in a NoSQL database connection."""

        schema = self.get_schema(connection_name)

        if schema:
            collection_schemas = schema.get('collection_schema', [])
            if collection_names:
                return [collection_schemas.get(collection_name, "") for collection_name in collection_names]

        return []

    def get_collection_names(self, connection_name: str) -> list[str]:
        """Get all collection names for a NoSQL database connection."""

        schema = self.get_schema(connection_name)

        if schema:
            return schema['collection_names']
        
        return []
    
    def sync(self):
        try:
            db_manager = DatabaseManager()
            for connection_name in db_manager.get_connection_names():
                connection_details = db_manager.get_connection(connection_name)
                extractor = create_schema_extractor_from_connection_name(connection_name)
                if extractor:
                    schema = extractor.get_full_schema_structure()
                    schema['db_type'] = connection_details.get('type', '')
                    if self.exists(connection_name):
                        self.update_schema(connection_name, schema)
                    else:
                        self.add_schema(connection_name, schema)
            self.save_state()
        except Exception as e:
            print(f"Error syncing schema cache: {str(e)}")