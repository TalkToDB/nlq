# we will create a class to interact with the Ollama API for language model operations with ollama models and langchain-ollama integration

import requests
from langchain_ollama import OllamaLLM
from typing import List, Dict

class OllamaAPI:
    """Class to interact with Ollama API for language model operations."""
    
    def __init__(self, base_url: str, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = OllamaLLM(base_url=base_url, model=model_name, temperature=temperature) if model_name and base_url else None

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
        
        response = self.llm.generate(
            [prompt]
        )
        
        text = response.generations[0][0].text
        return text
