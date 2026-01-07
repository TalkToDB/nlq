import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from src.models.ollama_api import OllamaAPI
from src.models.ollama_manager import OllamaConnectionManager

def get_ollama_api(connection_name:str, model_name:str) -> OllamaAPI:
    """Get OllamaAPI instance from state connection details."""
    ollama_manager = OllamaConnectionManager()

    conn = ollama_manager.get_connection(connection_name)
    
    if not conn:
        raise ValueError(f"Ollama connection '{connection_name}' not found")
    
    return OllamaAPI(
        base_url=conn['base_url'],
        model_name=model_name,
        api_key=conn.get('api_key', None),
        should_authenticate=conn.get('should_authenticate', False)
    )

DOCUMENTATIONS="documentations"
VECTOR_STORE_DB="chroma_db"


class RAGManager:
    
    def __init__(self):
        self.embedding_model_name = "nomic-embed-text"

    def load_directory(self, path: str):
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
            print(f"Error loading documents: {str(e)}")
            raise

    def chunk_documents(self, documents, chunk_size=1024, chunk_overlap=150):
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_documents(documents)
    
    def create_vector_store(self, llama_conn: str, model_name: str, db_type: str):
        ollama_api = get_ollama_api(llama_conn, model_name)

        vectorstore_db = os.path.join(PROJECT_ROOT, VECTOR_STORE_DB, db_type)
        documentations_path = os.path.join(PROJECT_ROOT, DOCUMENTATIONS, db_type)
        
        try:
            documents = self.load_directory(documentations_path)
            if not documents:
                raise ValueError(f"No .pdf documents found in {documentations_path}. Cannot create vector store.")
            
            chunked_docs = self.chunk_documents(documents)
            embeddings = ollama_api.embeddings

            # Try to load existing DB if present
            vectorstore = Chroma(
                persist_directory=vectorstore_db,
                embedding_function=embeddings
            )

            # Add new documents
            vectorstore.add_documents(chunked_docs)
            vectorstore.persist()

            return True, "Vector store updated successfully."
        except Exception as e:
            return False, f"Error creating vector store: {str(e)}"
        
if __name__ == "__main__":

    rag_manager = RAGManager()
    success, message = rag_manager.create_vector_store(
        llama_conn="llama_conn",
        model_name="gpt-oss:20b",
        db_type="MySQL"
    )