# main.py
# FastAPI entry point for Telegram webhook using Pyrofork

import logging
import os
import io
from fastapi import FastAPI, Request
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import AutoRenameBot
from database import Database
from config import Config
import uvicorn
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

class TelegramWebhook:
    """
    Telegram webhook setup with Pyrofork and FastAPI.
    """
    def __init__(self):
        """Initialize the bot application and handlers."""
        self.client = Client(
            "manga_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.bot_instance = AutoRenameBot()
        self.db = Database()
        self.register_handlers()

    def register_handlers(self):
        """Register Pyrofork message handlers."""
        @self.client.on_message(filters.command("start"))
        async def start(client, message: Message):
            if Config.START_PICTURE and os.path.exists(Config.START_PICTURE):
                await message.reply_photo(photo=Config.START_PICTURE, caption=Config.START_MESSAGE)
            else:
                await message.reply(Config.START_MESSAGE)
            logger.info(f"Started bot for chat ID {message.chat.id}")

        @self.client.on_message(filters.command("format"))
        async def set_format(client, message: Message):
            if not message.command[1:]:
                await message.reply("Provide a format, e.g., /format {title} - Chapter {chapter}.pdf")
                return
            format_string = " ".join(message.command[1:])
            await self.db.save_user_format(message.chat.id, format_string)
            await message.reply(f"Filename format set to: {format_string}")
            logger.info(f"Set format for chat ID {message.chat.id}: {format_string}")

        # FIXED: replaced filters.mime_type() with filters.document.mime_type()
        @self.client.on_message(filters.document.mime_type("application/pdf"))
        async def handle_pdf(client, message: Message):
            file = await message.download(in_memory=True)
            pdf_data = file.read()
            self.bot_instance.pdf_queue.put((message, pdf_data, message.document.file_name))
            await message.reply(f"PDF {message.document.file_name} added to queue. Use /rename to process.")
            logger.info(f"Received PDF: {message.document.file_name} from chat ID {message.chat.id}")

        @self.client.on_message(filters.command("rename"))
        async def rename(client, message: Message):
            filename_format = await self.db.get_user_format(message.chat.id)
            count = self.bot_instance.process_queue(filename_format, message.chat.id, self.db, client)
            await message.reply(f"Processed {count} PDF(s).")
            logger.info(f"Processed {count} PDFs for chat ID {message.chat.id}")

        @self.client.on_message(filters.command("thumbnails"))
        async def list_thumbnails(client, message: Message):
            thumbnails = await self.db.get_thumbnails(message.chat.id)
            if not thumbnails:
                await message.reply("No thumbnails found.")
                return
            for thumb in thumbnails:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=io.BytesIO(thumb['data']),
                    caption=thumb['name']
                )
            logger.info(f"Listed thumbnails for chat ID {message.chat.id}")

    async def webhook_update(self, update_json: dict):
        """Process incoming webhook update."""
        await self.client.parse_update(update_json)

    async def start(self):
        """Start the Pyrofork client."""
        await self.client.start()

    async def stop(self):
        """Stop the Pyrofork client and close DB."""
        await self.client.stop()
        await self.db.close()

webhook = TelegramWebhook()

@app.post(Config.WEBHOOK_PATH)
async def webhook_endpoint(request: Request):
    """Webhook endpoint for Telegram updates."""
    update_json = await request.json()
    await webhook.webhook_update(update_json)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    """Set Telegram webhook on startup."""
    webhook_url = f"https://manga-u8wx.onrender.com{Config.WEBHOOK_PATH}"  # Replace with your Render URL
    await webhook.start()
    await webhook.client.set_webhook(webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

@app.on_event("shutdown")
async def shutdown():
    """Remove webhook and stop client on shutdown."""
    await webhook.client.delete_webhook()
    await webhook.stop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)