"""
Model provider configurations.
"""

from typing import Dict, List

MODEL_PROVIDERS = {
    "Ollama": {
        "models": [
            "llama2",
            "llama3",
            "codellama",
            "mistral",
            "mixtral",
            "phi",
            "neural-chat",
            "gemma",
        ],
        "default": "llama2"
    },
    "OpenAI": {
        "models": [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-3.5-turbo"
        ],
        "default": "gpt-4"
    }
}

def get_models_for_provider(provider: str) -> List[str]:
    """Get available models for a provider."""
    return MODEL_PROVIDERS.get(provider, {}).get("models", [])

def get_default_model(provider: str) -> str:
    """Get default model for a provider."""
    return MODEL_PROVIDERS.get(provider, {}).get("default", "")

def get_all_providers() -> List[str]:
    """Get list of all model providers."""
    return list(MODEL_PROVIDERS.keys())
