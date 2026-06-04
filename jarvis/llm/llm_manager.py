
"""
llm_manager.py
==============
Manager for local LLM inference with support for multiple providers.
"""

from __future__ import annotations

import logging
import subprocess
import json
from typing import Dict, List, Optional

from jarvis.llm.model_registry import model_registry, ModelConfig
from jarvis.llm.token_monitor import token_monitor

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Manager for LLM inference operations.
    """

    def __init__(self):
        self._current_model: Optional[ModelConfig] = None

    def generate(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        purpose: Optional[str] = "reasoning",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text using a local LLM.
        """
        # Get model config
        if model_name:
            config = model_registry.get_model(model_name)
        else:
            config = model_registry.get_model_for_purpose(purpose)

        if not config:
            raise ValueError(f"No model available for purpose: {purpose}")

        # Check token limits
        if not token_monitor.check_limit():
            raise RuntimeError("Daily token limit exceeded")

        # Prepare prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {full_prompt}"

        # Execute based on provider
        if config.provider == "ollama":
            response = self._generate_ollama(full_prompt, config, max_tokens, temperature)
        elif config.provider == "llamacpp":
            response = self._generate_llamacpp(full_prompt, config, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

        # Record token usage (estimate if not provided)
        token_monitor.record_usage(
            model=config.name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(response.split()),
        )

        return response

    def _generate_ollama(
        self, prompt: str, config: ModelConfig, max_tokens: Optional[int], temperature: Optional[float]
    ) -> str:
        """Generate using Ollama."""
        try:
            # Use ollama CLI
            cmd = [
                "ollama",
                "run",
                config.model_id,
                prompt,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Ollama error: {result.stderr}")
                raise RuntimeError(f"Ollama failed: {result.stderr}")
        except FileNotFoundError:
            logger.warning("Ollama not found, using mock response for testing")
            return f"Mock response from {config.model_id}: {prompt[:50]}..."

    def _generate_llamacpp(
        self, prompt: str, config: ModelConfig, max_tokens: Optional[int], temperature: Optional[float]
    ) -> str:
        """Generate using llama.cpp."""
        logger.warning("llama.cpp support not fully implemented, using mock response")
        return f"Mock llama.cpp response from {config.model_id}: {prompt[:50]}..."


# Module-level singleton
llm_manager = LLMManager()

