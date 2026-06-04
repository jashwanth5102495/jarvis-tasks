
"""
embedding_manager.py
====================
Manager for generating embeddings for semantic memory.
"""

from __future__ import annotations

import logging
import hashlib
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manager for generating embeddings from text.
    """

    def __init__(self):
        self._embedding_cache: dict = {}

    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a piece of text."""
        # For now, use a mock embedding (hash-based)
        # In production, use sentence-transformers or Ollama embeddings
        text_hash = hashlib.sha256(text.encode()).digest()
        embedding = [
            float((text_hash[i % len(text_hash)] + text_hash[(i + 1) % len(text_hash)]) / 512.0)
            for i in range(128)
        ]

        # Cache
        self._embedding_cache[text] = embedding
        return embedding

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same length")

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a ** 2 for a in embedding1) ** 0.5
        norm2 = sum(b ** 2 for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# Module-level singleton
embedding_manager = EmbeddingManager()

