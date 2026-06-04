
"""
model_registry.py
=================
Registry for available local LLM models and their configurations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    provider: str  # "ollama", "llamacpp", "vllm"
    model_id: str
    purpose: List[str] = field(default_factory=list)  # "reasoning", "coding", "lightweight", "embedding"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    context_window: int = 8192
    requires_api_key: bool = False
    api_key_env: Optional[str] = None


# Default model registry configuration
DEFAULT_REGISTRY: List[ModelConfig] = [
    ModelConfig(
        name="qwen2.5",
        provider="ollama",
        model_id="qwen2.5",
        purpose=["reasoning", "general"],
        max_tokens=4096,
        temperature=0.7,
        context_window=32768,
    ),
    ModelConfig(
        name="deepseek-coder",
        provider="ollama",
        model_id="deepseek-coder",
        purpose=["coding", "technical"],
        max_tokens=8192,
        temperature=0.3,
        context_window=65536,
    ),
    ModelConfig(
        name="phi",
        provider="ollama",
        model_id="phi",
        purpose=["lightweight", "fast"],
        max_tokens=2048,
        temperature=0.7,
        context_window=2048,
    ),
    ModelConfig(
        name="llama3.1",
        provider="ollama",
        model_id="llama3.1",
        purpose=["reasoning", "general", "coding"],
        max_tokens=8192,
        temperature=0.7,
        context_window=131072,
    ),
    ModelConfig(
        name="mistral",
        provider="ollama",
        model_id="mistral",
        purpose=["reasoning", "general"],
        max_tokens=8192,
        temperature=0.7,
        context_window=32768,
    ),
]


class ModelRegistry:
    """
    Registry of available LLM models and their configurations.
    """

    def __init__(self, configs: Optional[List[ModelConfig]] = None):
        self._models: Dict[str, ModelConfig] = {}
        for config in configs or DEFAULT_REGISTRY:
            self._models[config.name] = config

    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        return self._models.get(name)

    def get_model_for_purpose(self, purpose: str) -> Optional[ModelConfig]:
        """Get the best model for a specific purpose."""
        for config in self._models.values():
            if purpose in config.purpose:
                return config
        return None

    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())

    def register_model(self, config: ModelConfig) -> None:
        """Register a new model configuration."""
        self._models[config.name] = config
        logger.info(f"Registered model: {config.name}")


# Module-level singleton
model_registry = ModelRegistry()

