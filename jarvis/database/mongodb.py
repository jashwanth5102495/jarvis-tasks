import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from core.config import config


logger = logging.getLogger(__name__)


class MongoDB:
    _instance: Optional['MongoDB'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        if self._client is None:
            try:
                self._client = MongoClient(config.mongodb_uri)
                self._db = self._client[config.database_name]
                logger.info(f"Connected to MongoDB database: {config.database_name}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

    def get_collection(self, collection_name: str) -> Collection:
        if self._db is None:
            self.connect()
        return self._db[collection_name]

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def find_many(self, collection_name: str, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        cursor = collection.find(filter or {}).sort("timestamp", -1)
        return list(cursor)

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


mongodb = MongoDB()
