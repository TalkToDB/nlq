from src.models.ollama_api import OllamaAPI
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from src.agent.tools.sql_tools import get_sql_tools
from src.agent.tools.mongodb_tools import get_mongodb_tools
from src.database.manager import DatabaseManager
from typing import List

class MasterAgent:
    """
    Master agent that orchestrates database queries across multiple database types.
    Supports PostgreSQL, MySQL, SQLite, SQL Server, and MongoDB.
    """
    
    def __init__(self, db_manager: DatabaseManager, llm_api:OllamaAPI):
        """
        Initialize the master agent with database connections.
        """
        self.db_manager = db_manager
        self.llm_api = llm_api

    def get_agent(self, tools: List, model: str | BaseChatModel):
        """
        Create and return a LangChain agent with the provided tools and model.
        
        Args:
            tools: List of LangChain tools for database operations
            model: Language model instance
            
        Returns:
            Configured LangChain agent
        """
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt="You are a helpful assistant",
        )

        return agent
    
    def run(self,  query: str, connection_name: str):
        """
        Execute a natural language query against the databases.
        
        Args:
            query: Natural language query from user
            connection_name: Name of the database connection to use
        Returns:
            Agent's response with query results
        """
        try:

            if not self.llm_api.llm:
                raise ValueError("Language model is not initialized in OllamaAPI")

            if not connection_name:
                raise ValueError("Connection name must be provided")
            
            connection_details = self.db_manager.get_connection(connection_name)
            
            connection_type = connection_details.get("type", None) if connection_details else None

            if not connection_type:
                raise ValueError(f"Connection type not specified for connection '{connection_name}'")
            
            tools = []

            if connection_type in ["PostgreSQL", "MySQL", "SQLite", "SQL Server"]:
                tools = get_sql_tools(connection_details, self.llm_api.llm)

            else:
                tools = get_mongodb_tools(connection_details, self.llm_api.llm)

            agent = self.get_agent(tools, self.llm_api.llm)

            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user", 
                            "content": query
                        }
                    ]
                }
            )

            return result
        except Exception as e:
            return f"Error executing query: {str(e)}"