# bot.py
# Core logic for the Auto Rename Telegram Bot
# Manages the queue system and coordinates processing of PDF files in memory

import logging
from queue import Queue
import concurrent.futures
from rename import RenameProcessor
from config import Config
from pyrogram.types import Message

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoRenameBot:
    """
    Core bot class for queuing and processing PDF files in memory.
    """
    def __init__(self, max_workers=Config.MAX_WORKERS):
        """
        Initialize the bot with queue and configuration.

        :param max_workers: Maximum number of concurrent workers.
        """
        self.max_workers = max_workers
        self.pdf_queue = Queue()  # Queue for (message, pdf_data, file_name) tuples

    def process_queue(self, filename_format: str, chat_id: int, db: 'Database', client: 'Client'):
        """
        Process the queue with concurrent workers (max_workers).
        
        :param filename_format: Filename format to use.
        :param chat_id: Telegram chat ID for storing thumbnails.
        :param db: Database instance for storing thumbnails.
        :param client: Pyrofork client for sending messages/files.
        :return: Number of files processed.
        """
        if self.pdf_queue.empty():
            logger.warning("No PDF files in queue.")
            return 0

        processor = RenameProcessor(filename_format)
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            while not self.pdf_queue.empty():
                message, pdf_data, file_name = self.pdf_queue.get()
                future = executor.submit(processor.process_file_in_memory, pdf_data, file_name, chat_id, db, message, client)
                futures.append(future)
                logger.info(f"Queued for processing: {file_name} (Queue size: {self.pdf_queue.qsize()})")
                processed_count += 1

            concurrent.futures.wait(futures)
            logger.info("All files processed.")
        return processed_count
