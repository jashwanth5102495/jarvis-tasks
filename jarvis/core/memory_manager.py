import logging
from typing import List
from datetime import datetime
from jarvis.database.mongodb import mongodb
from jarvis.core.models import MemoryRecord, Preference

logger = logging.getLogger(__name__)


class MemorySystem:
    def __init__(self):
        self.tasks_collection = "tasks"
        self.memories_collection = "memories"
        self.preferences_collection = "preferences"

    def save_task(self, record: MemoryRecord) -> str:
        document = {
            "task": record.task,
            "goal": record.goal.model_dump(),
            "plan": record.plan.model_dump(),
            "timestamp": record.timestamp,
            "suggested_skills": [skill.model_dump() for skill in record.suggested_skills]
        }
        inserted_id = mongodb.insert_one(self.tasks_collection, document)
        logger.info(f"Memory saved successfully with ID: {inserted_id}")
        return inserted_id

    def get_history(self, limit: int = 10) -> List[dict]:
        history = mongodb.find_many(self.tasks_collection)
        return history[:limit]

    def save_preference(self, key: str, value: str):
        document = {
            "key": key,
            "value": value,
            "timestamp": datetime.now()
        }
        inserted_id = mongodb.insert_one(self.preferences_collection, document)
        logger.info(f"Preference saved successfully: {key} = {value}")
        return inserted_id

    def get_preferences(self) -> List[dict]:
        return mongodb.find_many(self.preferences_collection)


memory_system = MemorySystem()
