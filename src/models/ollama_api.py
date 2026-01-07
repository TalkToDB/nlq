# we will create a class to interact with the Ollama API for language model operations with ollama models and langchain-ollama integration

import requests
from langchain_ollama import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from typing import List, Dict
        
class OllamaAPI:

    def __init__(self, base_url: str, model_name: str, api_key: str = None, should_authenticate: bool = False):
        self.model_name = model_name
        self.base_url = base_url
        self.apikey = api_key
        self.text_embedding_model_name = "nomic-embed-text"
        
        if should_authenticate and (not api_key):
            raise ValueError("Username and password must be provided for authentication.")
        
        if should_authenticate:
            self.headers = {
                "Authorization": f"Bearer {self.apikey}"
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