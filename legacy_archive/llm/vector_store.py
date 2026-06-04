
"""
vector_store.py
===============
Simple in-memory vector store for semantic retrieval (production-ready with Chroma/FAISS ready).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from llm.embedding_manager import embedding_manager

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """A document stored in the vector store with embedding and metadata."""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    Vector store for semantic retrieval.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "vector_store"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._documents: Dict[str, VectorDocument] = {}
        self._load()

    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a document to the vector store.
        """
        doc_id = doc_id or str(len(self._documents) + 1)
        embedding = embedding_manager.generate_embedding(text)
        doc = VectorDocument(
            id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
        )
        self._documents[doc_id] = doc
        self._save()
        return doc_id

    def search(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.0,
    ) -> List[VectorDocument]:
        """
        Search the vector store for similar documents.
        """
        query_embedding = embedding_manager.generate_embedding(query)
        results = []

        for doc in self._documents.values():
            similarity = embedding_manager.compute_similarity(query_embedding, doc.embedding)
            if similarity >= min_similarity:
                results.append((doc, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in results[:limit]]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._save()
            return True
        return False

    def _save(self) -> None:
        """Save the vector store to disk."""
        data = {
            "documents": [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "embedding": doc.embedding,
                    "metadata": doc.metadata,
                }
                for doc in self._documents.values()
            ]
        }
        with open(self._storage_path / "vector_store.json", "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load the vector store from disk."""
        storage_file = self._storage_path / "vector_store.json"
        if storage_file.exists():
            try:
                with open(storage_file, "r") as f:
                    data = json.load(f)
                    self._documents = {
                        doc_data["id"]: VectorDocument(
                            id=doc_data["id"],
                            text=doc_data["text"],
                            embedding=doc_data["embedding"],
                            metadata=doc_data["metadata"],
                        )
                        for doc_data in data.get("documents", [])
                    }
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")


# Module-level singleton
vector_store = VectorStore()

