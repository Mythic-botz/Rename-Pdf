# database.py
# MongoDB operations for storing user preferences and thumbnails (binary data)

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import bson

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    """
    MongoDB database operations for user preferences and thumbnails.
    """
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB]
        self.collection = self.db[Config.MONGODB_COLLECTION]

    async def save_user_format(self, chat_id: int, filename_format: str):
        """
        Save or update user's filename format.

        :param chat_id: Telegram chat ID.
        :param filename_format: User's preferred filename format.
        """
        try:
            await self.collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"filename_format": filename_format}},
                upsert=True
            )
            logger.info(f"Saved format '{filename_format}' for chat ID {chat_id}")
        except Exception as e:
            logger.error(f"Error saving format for chat ID {chat_id}: {e}")

    async def get_user_format(self, chat_id: int) -> str:
        """
        Retrieve user's filename format.

        :param chat_id: Telegram chat ID.
        :return: Filename format or default from Config.
        """
        try:
            user = await self.collection.find_one({"chat_id": chat_id})
            return user.get("filename_format", Config.DEFAULT_FILENAME_FORMAT) if user else Config.DEFAULT_FILENAME_FORMAT
        except Exception as e:
            logger.error(f"Error retrieving format for chat ID {chat_id}: {e}")
            return Config.DEFAULT_FILENAME_FORMAT

    async def save_thumbnail(self, chat_id: int, thumbnail_name: str, thumbnail_data: bytes):
        """
        Save thumbnail binary data for a processed PDF.

        :param chat_id: Telegram chat ID.
        :param thumbnail_name: Name of the thumbnail.
        :param thumbnail_data: Binary data of the thumbnail.
        """
        try:
            await self.collection.update_one(
                {"chat_id": chat_id},
                {"$push": {"thumbnails": {"name": thumbnail_name, "data": bson.Binary(thumbnail_data)}}},
                upsert=True
            )
            logger.info(f"Saved thumbnail {thumbnail_name} for chat ID {chat_id}")
        except Exception as e:
            logger.error(f"Error saving thumbnail for chat_id {chat_id}: {e}")

    async def get_thumbnails(self, chat_id: int) -> list:
        """
        Retrieve all thumbnails for a user.

        :param chat_id: Telegram chat ID.
        :return: List of thumbnail dicts (name, data).
        """
        try:
            user = await self.collection.find_one({"chat_id": chat_id})
            return user.get("thumbnails", []) if user else []
        except Exception as e:
            logger.error(f"Error retrieving thumbnails for chat_id {chat_id}: {e}")
            return []

    async def close(self):
        """Close MongoDB client."""
        self.client.close()
