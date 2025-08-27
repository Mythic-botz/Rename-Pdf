# config.py
# Configuration settings for the Auto Rename Telegram Bot
# Contains Telegram, MongoDB, and webhook settings

import os

class Config:
    """
    Configuration class for the Auto Rename Telegram Bot.
    """
    # Telegram settings
    API_ID = os.getenv("API_ID", "your-api-id")  # Telegram API ID
    API_HASH = os.getenv("API_HASH", "your-api-hash")  # Telegram API Hash
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")  # Telegram Bot Token
    START_MESSAGE = (
        "Welcome to the Auto Rename Manga Bot! 📚\n"
        "Use /rename to process PDFs.\n"
        "Upload PDFs to rename.\n"
        "Set filename format with /format <format> (e.g., '{title} - Chapter {chapter}.pdf')."
    )
    START_PICTURE = os.getenv("START_PICTURE", "start.jpg")  # Path to start image (optional)

    # MongoDB settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "manga_bot")
    MONGODB_COLLECTION = "users"

    # Processing settings
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))  # Max concurrent workers
    DEFAULT_FILENAME_FORMAT = "{title} - Chapter {chapter}.pdf"

    # Webhook settings for FastAPI
    WEBHOOK_PATH = "/webhook"
    PORT = int(os.getenv("PORT", 8000))  # Default port for Render
