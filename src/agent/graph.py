
import sys
from pathlib import Path

import os
from typing import Literal
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy

from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

# resolves to project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.schema.manager import DBSchemaCacheManager
from src.models.ollama_api import OllamaAPI
from src.database.schemas import SQL_DATABASE_NAMES, NOSQL_DATABASE_NAMES
from src.database.schemas import DATABASE_TYPES
from src.models.ollama_manager import OllamaConnectionManager

class PredefinedSchemaContext(TypedDict):
    # for sql
    table_names: list[str]
    table_schema: list[str]

    # for no-sql
    collection_names: list[str]
    collection_schema: list[str]


class AgentResponse(TypedDict):

    # holds the exact database query to be executed
    db_query: str | None

    # holds the reasoning behind the query
    reasoning: str | None

    # holds a final response to be sent to the user
    final_response: str | None

    # whether to execute the query or not
    execute: bool | None
    
    # holds execution errors
    execution_error : list[str] | None

    # holds the result of the database query execution (table or documents)
    execution_result: list[dict] | None

    execution_retry_count: int | None

class LLMQueryResponse(TypedDict):
    # query from model
    query: str
    # reasoning behind the query
    reasoning: str
    # whether to execute the query or not
    execute: bool


class MongoDBQueryParams(TypedDict):
    """Structured parameters for MongoDB query execution (read-only operations)."""
    # Name of the collection to query
    collection_name: str
    # Operation type: find, find_one, aggregate, count, distinct (read-only operations only)
    operation: str
    # Filter criteria (JSON string) - used for find operations
    filter: str
    # Projection fields (JSON string) - which fields to include/exclude
    projection: str
    # Sort specification (JSON string) - e.g., {"name": 1} for ascending
    sort: str
    # Maximum number of documents to return
    limit: int
    # Number of documents to skip
    skip: int
    # Aggregation pipeline (JSON string) - used for aggregate operation
    pipeline: str
    # Field name for distinct operation
    field: str
    # Reasoning behind the query
    reasoning: str

class UserIntent(TypedDict):
    intent: Literal["casual", "technical_info", "db_query", 'other']

class SQL(TypedDict):
    table_names: str

class NOSQL(TypedDict):
    collection_names: str

# Define the structure for email classification
class DatabaseAgentState(TypedDict):

    # Ollama connection details (serializable)
    ollama_connection_name: str
    ollama_model_name: str

    # identifier for the query
    query_id: str

    query_text: str

    # database type - now using the imported type!
    database_type: DATABASE_TYPES

    # connection name for query execution
    connection_name: str

    # user intent
    classification: UserIntent | None

    # schema context
    predefined_schema_context: PredefinedSchemaContext

    # Raw search/API results for RAG related queries under technical_info intent
    search_results: list[str] | None

    # response for causal and technical_info intents
    response: str | None

    # response from the agent for db_query intent
    agent_response: AgentResponse | None

# Helper function to get LLM from state
def get_ollama_api(state: DatabaseAgentState) -> OllamaAPI:
    """Get OllamaAPI instance from state connection details."""
    ollama_manager = OllamaConnectionManager()
    conn = ollama_manager.get_connection(state['ollama_connection_name'])
    
    if not conn:
        raise ValueError(f"Ollama connection '{state['ollama_connection_name']}' not found")
    
    return OllamaAPI(
        base_url=conn['base_url'],
        model_name=state['ollama_model_name'],
        api_key=conn.get('api_key', None),
        should_authenticate=conn.get('should_authenticate', False)
    )

def classify_intent(state: DatabaseAgentState) -> Command[Literal["make_response", "search_documentation", "schema_context_prep"]]:
    """Use LLM to classify user intent, then route accordingly"""
    
    ollama_api = get_ollama_api(state)
    llm = ollama_api.llm

    # Create structured LLM that returns UserIntent dict
    structured_llm = llm.with_structured_output(UserIntent)

    # Format the prompt on-demand, not stored in state
    classification_prompt = f"""
    Analyze this user request and classify it.
    
    Classification Rules:
        'casual' : The request is conversational, a greeting, or completely unrelated to databases, SQL, or data.
        'technical_info' : The user is asking a "what is" or "how to" question *about* a database concept. They are seeking information, not asking for an action to be performed on a database.
        'db_query' : If the users wants to interact with a real database and make decisions. This includes creating, updating, deleting, or altering.

    Query: {state['query_text']}

    Provide classification intent.
    """
    # Get structured response directly as dict
    classification = structured_llm.invoke(classification_prompt)

    # Determine next node based on classification
    if classification['intent'] == 'casual':
        goto = "make_response"
    elif classification['intent'] == 'technical_info':
        goto = "search_documentation"
    elif classification['intent'] == 'db_query':
        goto = "schema_context_prep"
    else:
        raise ValueError(f"Unknown intent: {classification['intent']}")


    # Store classification as a single dict in state
    return Command(
        update={
            "classification": classification,
        },
        goto=goto
    )

# folder paths
DOCUMENTATIONS="documentations"
VECTOR_STORE_DB="chroma_db"


def search_documentation(state: DatabaseAgentState) -> Command[Literal["make_response"]]:
    """Search knowledge base for relevant information"""
    # Build search query from classification
    
    search_query = state.get('query_text', '')
    database_type = state.get('database_type', '')
    ollama_api = get_ollama_api(state)

    # Source documents (e.g., "documentations/mysql")
    documentations = os.path.join(PROJECT_ROOT, DOCUMENTATIONS, database_type)

    # Vector store path (e.g., "chroma_db/mysql")
    vectorstore_db = os.path.join(PROJECT_ROOT, VECTOR_STORE_DB, database_type)
    
    
    def load_directory(path: str):
        print(f"Loading documents from: {path}")
        try:
            directory_path = path
            loader = DirectoryLoader(
                path=directory_path,
                glob="**/*.pdf",
                show_progress=True
            )
            documents = loader.load()
            return documents
        except Exception as e:
            print(f"Detailed error while loading documents: {str(e)}")
            raise
    
    def chunk_documents(documents, chunk_size=1024, chunk_overlap=150):
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_documents(documents)
    
    try:

        embeddings = ollama_api.embeddings

        if os.path.exists(vectorstore_db):
            vectorstore = Chroma(
                persist_directory=vectorstore_db,
                embedding_function=embeddings
            )
        else:
                        
            if not os.path.exists(documentations):
                raise FileNotFoundError(f"Source documentation path does not exist: {documentations}")

            documents = load_directory(documentations)
            
            if not documents:
                 raise ValueError(f"No .pdf documents found in {documentations}. Cannot create vector store.")

            chunks = chunk_documents(documents)

            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=vectorstore_db  
            )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        relevant_docs = retriever.invoke(search_query)
        search_results = [doc.page_content for doc in relevant_docs]
        
    except Exception as e:
        print(f"Error during search: {e}")
        search_results = [f"Search temporarily unavailable: {str(e)}"]

    return Command(
        update={"search_results": search_results}, 
        goto="make_response"
    )


schema_manager = DBSchemaCacheManager()

def schema_context_prep(state: DatabaseAgentState) -> Command[Literal["create_query"]]:
    """Prepare database schema context for query generation"""

    database_type = state.get('database_type', '')
    connection_name = state.get('connection_name', '')
    ollama_api = get_ollama_api(state)
    llm = ollama_api.llm

    if database_type in SQL_DATABASE_NAMES:
        
        tables = schema_manager.get_table_names(connection_name)
        tables = ", ".join(tables)

        schema_context_prompt = f"""
        Analyze this user request and return the list of tables separated by comma that will be required by the query. You are provided with the list of all table names.
        If the tabels do not match with the query in that case you need to return empty string separated by comma : ,

        Query: {state['query_text']}
        Tables : {tables}
        """
        
        structured_llm = llm.with_structured_output(SQL)

        response = structured_llm.invoke(schema_context_prompt)

        if response['table_names']:
            filtered_tables = response['table_names'].split(",")
            filtered_tables = [table.strip() for table in filtered_tables if table and table.strip()]

            table_schema = schema_manager.get_table_schema(connection_name=state['connection_name'], table_names=filtered_tables)

            predefined_schema_context  = {
                'table_names' : filtered_tables,
                'table_schema' : table_schema
            }

            return Command(
                update={"predefined_schema_context": predefined_schema_context},
                goto="create_query"
            )
            
    elif database_type in NOSQL_DATABASE_NAMES:
        collections = schema_manager.get_collection_names(connection_name)
        collections = ", ".join(collections)

        schema_context_prompt = f"""
        Analyze this user request and return the list of collection name separated by comma that will be required by the query. You are provided with the list of all collection names.
        If the collections do not match with the query in that case you need to return empty string separated by comma : ,

        Query: {state['query_text']}
        Collection : {collections}
        """
        
        structured_llm = llm.with_structured_output(NOSQL)

        response = structured_llm.invoke(schema_context_prompt)

        if response['collection_names']:
            filtered_collections = response['collection_names'].split(",")
            filtered_collections = [collection.strip() for collection in filtered_collections if collection and collection.strip()]

            collection_schema = schema_manager.get_collection_schema(connection_name=state['connection_name'], collection_names=filtered_collections)

            predefined_schema_context = {
                'collection_names' : filtered_collections,
                'collection_schema' : collection_schema
            }

            return Command(
                update={"predefined_schema_context": predefined_schema_context},
                goto="create_query"
            )
         
    return Command(
        goto=END
    )

def create_query(state:DatabaseAgentState) -> Command[Literal["executor_node"]]:

    ollama_api = get_ollama_api(state)
    llm = ollama_api.llm

    execution_retry_count = state['agent_response'].get('execution_retry_count', 0) + 1
    error = state['agent_response'].get('execution_error', [])
    database_type = state['database_type']

    # Use different structured output based on database type
    if database_type == 'MongoDB':
        structured_llm = llm.with_structured_output(MongoDBQueryParams)
        
        draft_prompt = f"""
            Generate MongoDB query parameters based on the user request.

            User Query: {state['query_text']}
            
            Schema Context (Collections and their structure): {state['predefined_schema_context']}

            Previous Error: {error[-1] if (error and len(error) > 0) else 'N/A'}

            Execution Retry Count: {execution_retry_count}

            You must provide the following parameters:
            - collection_name: The name of the collection to query
            - operation: One of: find, find_one, aggregate, count, distinct (READ-ONLY operations only)
            - filter: JSON string for filter criteria, e.g., '{{"name": "John"}}' or '{{}}' for no filter
            - projection: JSON string for fields to include/exclude, e.g., '{{"name": 1, "email": 1, "_id": 0}}' or '{{}}' for all fields
            - sort: JSON string for sort order, e.g., '{{"created_at": -1}}' for descending or '{{}}' for no sort
            - limit: Maximum documents to return (default 100 for safety)
            - skip: Number of documents to skip (default 0)
            - pipeline: JSON string array for aggregation pipeline, e.g., '[{{"$match": {{}}}}, {{"$group": {{"_id": "$category"}}}}]'
            - field: Field name for distinct operation
            - reasoning: Explain why you generated this query

            IMPORTANT: Only READ operations are allowed. Do NOT generate insert, update, or delete operations.

            Guidelines:
            - Use valid JSON strings for all JSON fields (filter, projection, sort, pipeline)
            - For unused fields, use empty JSON: '{{}}' for objects, '[]' for arrays, '' for strings
            - Always set limit to 100 or less for find operations
            - Match field names exactly as shown in the schema context
            - If the previous error is not 'N/A', fix the issue that caused it
            """
        
        response = structured_llm.invoke(draft_prompt)

        # Store MongoDB params as JSON string in db_query for the executor
        import json
        mongodb_params = {
            "collection_name": response.get('collection_name', ''),
            "operation": response.get('operation', 'find'),
            "filter": response.get('filter', '{}'),
            "projection": response.get('projection', '{}'),
            "sort": response.get('sort', '{}'),
            "limit": response.get('limit', 100),
            "skip": response.get('skip', 0),
            "pipeline": response.get('pipeline', '[]'),
            "field": response.get('field', '')
        }

        agent_response: AgentResponse = {
            "db_query": json.dumps(mongodb_params),
            "reasoning": response.get('reasoning', ''),
            "execute": True,  # Always execute - only read operations allowed
            "execution_error": error
        }
    else:
        # SQL databases use the original approach
        structured_llm = llm.with_structured_output(LLMQueryResponse)
        
        draft_prompt = f"""
            Generate a database query based on the user request.

            Query: {state['query_text']}
            
            Database Type: {database_type}
            
            Schema Context: {state['predefined_schema_context']}

            Previous Error: {error[-1] if (error and len(error) > 0) else 'N/A'}

            Execution Retry Count: {execution_retry_count}

            Guidelines:
            - Use the provided context when relevant
            - Make sure to generate syntactically correct queries with no formatting with newlines or any other things which could fail query execution
            - Always limit the data fetched to 100 rows/documents
            - If the query cannot be generated based on the context, return an empty query
            - Provide reasoning for the generated query
            - Decide whether the query should be executed or not based on only one factor - if the query modifies or deleted data then do not execute otherwise execute the query
            - If the previous error is not 'N/A', take that into account to avoid repeating the same mistake and fix the error
            """
        
        response = structured_llm.invoke(draft_prompt)

        agent_response: AgentResponse = {
            "db_query": response['query'],
            "reasoning": response['reasoning'],
            "execute": response['execute'],
            "execution_error": error
        }

    return Command(
        update={"agent_response": agent_response},
        goto="executor_node"
    )

def executor_node(state:DatabaseAgentState) -> Command[Literal["make_response", "create_query", END]]:    
    """Execute the generated query if allowed and update the agent response with results"""

    connection_name = state['connection_name']
    db_type = state['database_type']
    db_query = state['agent_response']['db_query']
    execute = state['agent_response']['execute']
    execution_retry_count = state['agent_response'].get('execution_retry_count', 0) + 1

    agent_response = state['agent_response'].copy()

    execution_result = None
    error = None

    if execute and db_query:
        from src.database.executor import execute_query
        from src.database.manager import DatabaseManager
    
        db_manager = DatabaseManager()

        connection_data = db_manager.get_connection(connection_name)

        status, message, execution_result = execute_query(db_type, connection_data, db_query)
        
        if not status:
            error = message
            agent_response['execution_error'].append(error)
            agent_response['execution_retry_count'] = execution_retry_count

            if execution_retry_count <= 3:
                agent_response['execution_retry_count'] = execution_retry_count
                
                return Command(
                    update={"agent_response": agent_response},
                    goto="create_query"
                )

            return Command(
                update={"agent_response": agent_response},
                goto="make_response"
            )
        
        agent_response['execution_result'] = execution_result
    
        return Command(
            update={"agent_response": agent_response},
            goto="make_response"
        )
    
    return Command(
        goto=END
    )

def make_response(state: DatabaseAgentState) -> Command[Literal[END]]:
    """Generate response using context and route based on quality"""

    ollama_api = get_ollama_api(state)
    llm = ollama_api.llm

    classification = state.get('classification', {})
    query = state.get('query_text')
    intent  = classification.get('intent', None)

    # Format context from raw state data on-demand
    context_sections = []
    response = None
    goto = END

    if intent == "casual":
        # Build the prompt with formatted context for casual intent
        draft_prompt = f"""
        Make a response to this user query:
        {query}

        Guidelines:
        - Be professional and helpful
        - Address their specific concern
        - Use the provided documentation when relevant
        """
        
        response = llm.invoke(draft_prompt)

    elif intent == "technical_info":
        formatted_docs = "\n".join([f"- {doc}" for doc in state['search_results']])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")

        # Build the prompt with formatted context for technical_info intent
        draft_prompt = f"""
        Make a response to this query using the documentation:
        {query}

        {chr(10).join(context_sections)}

        Guidelines:
        - Be professional and helpful
        - Address their specific concern
        - Use the provided documentation when relevant
        """

        response = llm.invoke(draft_prompt)
        
    elif intent == "db_query":
        # will implement database query handling and response generation
        execute = state['agent_response']['execute']
        db_query = state['agent_response']['db_query']
        execution_result = state['agent_response']['execution_result']
        reasoning = state['agent_response']['reasoning']

        if execute and db_query:
            draft_prompt = f"""
                Make a final response to the query using the execution results and db query. The use might require answers based on the execution results.
                Do not print the table in the response rather summarize the results in a professional way.

                User Query : {query}

                Agent Generated :
                Execute : {execute}
                DB Query : {db_query}
                Reasoning : {reasoning}
                Total Rows/Documents Retrieved : {len(execution_result) if execution_result else 0}
                Execution Results : {execution_result[:100]}

                Guidelines:
                - Be professional and helpful
                - Address their specific concern
                - Use the provided documentation when relevant
                - You only get a max of 100 rows/documents so summarize accordingly
                - The total rows/documents retrieved is also provided for context
            """
            response = llm.invoke(draft_prompt)
    else:
        goto = END

    if not response:
        return Command(
            update={"response": None},
            goto=goto
        )

    return Command(
        update={"response": response.content or None},
        goto=goto
    )

# Create the graph
workflow = StateGraph(DatabaseAgentState)

# Add nodes with appropriate error handling
workflow.add_node("classify_intent", classify_intent, retry_policy=RetryPolicy(retry_on=ValueError, max_attempts=3))

# Add retry policy for nodes that might have transient failures
workflow.add_node(
    "search_documentation",
    search_documentation,
    retry_policy=RetryPolicy(retry_on=ValueError,  max_attempts=3)
)

workflow.add_node("schema_context_prep", schema_context_prep)
workflow.add_node("create_query", create_query)
workflow.add_node("executor_node", executor_node)
workflow.add_node("make_response", make_response)
workflow.add_edge(START, "classify_intent")     

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # Test with a casual response
    import uuid
    from src.database.manager import DatabaseManager
    query_id = str(uuid.uuid4())

    connection_name = 'pg_local'
    llama_connection_name = 'llama_conn'
    
    db_manager = DatabaseManager()
    ollama_manager = OllamaConnectionManager()
    ollama_manager.reload_connections()
    llama = ollama_manager.get_connection(llama_connection_name)
    
    connection_details = db_manager.get_connection(connection_name)
    
    initial_state = {
        "ollama_connection_name": llama_connection_name,
        "ollama_model_name": "gpt-oss:20b",

        "query_id": query_id,
        "connection_name": connection_name,
        "query_text": "what is 'format' function compared to in the docs?",
        "database_type": connection_details['type'],
        "agent_response": {}
    }

    # Run with a thread_id for persistence
    config = {"configurable": {"thread_id": query_id}}

    result = graph.invoke(initial_state, config)

    print(result)