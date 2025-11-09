# we will create a class to interact with the Ollama API for language model operations with ollama models and langchain-ollama integration

import os
import base64
import requests
from langchain_ollama import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from typing import List, Dict

class OllamaAPI:
    """Class to interact with Ollama API for language model operations."""
    
    def __init__(self, base_url: str, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = ChatOllama(base_url=base_url, model=model_name, temperature=temperature) if model_name and base_url else None

    def get_models(self) -> List[Dict]:
        """Return list of available Ollama models.
            [{
                "id": "gemma:2b",
                "object": "model",
                "created": 1757934271,
                "owned_by": "library"
            }]
        """
        response = requests.get(f"{self.base_url}/v1/models")

        if response.status_code == 200:
            data = response.json().get("data", [])

            if data:
                # filter object type model
                models = [model for model in data if model.get("object") == "model"]
                return models
        return []

    def generate_text(self, prompt: str) -> str:
        """Generate text using the specified Ollama model."""
        if not self.llm:
            raise ValueError("OllamaLLM is not initialized. Please provide valid base_url and model_name.")
        
        # Use invoke instead of generate for simpler response handling
        response = self.llm.invoke(prompt)
        
        # Extract text content from the AIMessage object
        # Handle both string and list content types
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Join list items into a single string
            return " ".join([str(item) for item in content])
        else:
            return str(content)
        
class OllamaAPINew:

    def __init__(self, base_url: str, model_name: str, username: str = None, password: str = None, should_authenticate: bool = False):
        self.model_name = model_name
        self.base_url = base_url
        self.username = username
        self.password = password
        self.text_embedding_model_name = "nomic-embed-text"
        
        if should_authenticate and (not username or not password):
            raise ValueError("Username and password must be provided for authentication.")
        
        if should_authenticate:
            self.auth_token = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.headers = {
                "Authorization": f"Basic {self.auth_token}"
            }
            self.llm = ChatOllama(model=model_name, base_url=base_url, 
            temperature=0.7, client_kwargs={ "headers": self.headers })

            self.embeddings = OllamaEmbeddings(model=self.text_embedding_model_name, base_url=base_url, client_kwargs={ "headers" : self.headers})

        else:
            self.llm = ChatOllama(model=model_name, base_url=base_url, temperature=0.7)
            self.embeddings = OllamaEmbeddings(model=self.text_embedding_model_name, base_url=base_url)
        

    def get_models(self) -> List[Dict]:
        """Return list of available Ollama models.
            [{
                "id": "gemma:2b",
                "object": "model",
                "created": 1757934271,
                "owned_by": "library"
            }]
        """
        response = requests.get(f"{self.base_url}/v1/models", headers=self.headers if hasattr(self, 'headers') else {})

        if response.status_code == 200:
            data = response.json().get("data", [])

            if data:
                # filter object type model
                models = [model for model in data if model.get("object") == "model"]
                return models
        return []