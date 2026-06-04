
"""
Memory Index Module
===================
Combines and indexes all memory stores for unified access
"""
import logging
from typing import Dict, List, Any, Optional

from jarvis.memory.session_memory import session_memory
from jarvis.memory.persistent_memory import persistent_memory
from jarvis.memory.vector_memory import vector_store

logger = logging.getLogger(__name__)


class MemoryIndex:
    """Unified interface to all memory systems."""

    def __init__(self):
        self.session = session_memory
        self.persistent = persistent_memory
        self.vector = vector_store
        logger.info("MemoryIndex initialized")

    def search_all(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search all memory stores for a query."""
        results = {
            "vector": self.vector.search(query, limit=limit),
            "session": [t for t in self.session.get_all_tasks() if query.lower() in t.user_input.lower()],
            "persistent": {k: v for k, v in self.persistent.get_all().items() if query.lower() in str(k).lower() or query.lower() in str(v).lower()}
        }
        logger.info(f"Searched all memory for '{query}'")
        return results


# Module-level singleton
memory_index = MemoryIndex()

