# rename.py
# Handles PDF renaming, metadata extraction, and thumbnail generation in memory

import fitz  # PyMuPDF
from PIL import Image
import io
import logging
from plugins.metadata import extract_metadata
from pyrogram.types import Message
from pyrogram import Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RenameProcessor:
    """
    Handles renaming, thumbnail generation, and file organization in memory.
    """
    def __init__(self, filename_format):
        """
        Initialize with filename format.

        :param filename_format: Format string with {title} and {chapter} placeholders.
        """
        self.filename_format = filename_format

    def generate_thumbnail(self, pdf_data: bytes, metadata):
        """
        Generate thumbnail from first page of PDF in memory.

        :param pdf_data: Bytes of the PDF.
        :param metadata: Dict with title and chapter.
        :return: Thumbnail bytes or None on failure.
        """
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            thumbnail_io = io.BytesIO()
            img.save(thumbnail_io, "JPEG")
            thumbnail_bytes = thumbnail_io.getvalue()
            doc.close()
            logger.info(f"Generated thumbnail for {metadata['title']}")
            return thumbnail_bytes
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    async def process_file_in_memory(self, pdf_data: bytes, original_name: str, chat_id: int, db: 'Database', message: Message, client: Client):
        """
        Process a single PDF in memory: extract metadata, generate thumbnail, rename, and send back to user.

        :param pdf_data: Bytes of the PDF.
        :param original_name: Original file name.
        :param chat_id: Telegram chat ID for storing thumbnails.
        :param db: Database instance for storing thumbnails.
        :param message: Pyrofork message for replying.
        :param client: Pyrofork client for sending files.
        :return: Success or failure.
        """
        try:
            metadata = extract_metadata(pdf_data)
            thumbnail_bytes = self.generate_thumbnail(pdf_data, metadata)

            # Format the new filename
            new_filename = self.filename_format.format(title=metadata['title'], chapter=metadata['chapter'])

            # Send renamed PDF
            await client.send_document(chat_id=chat_id, document=io.BytesIO(pdf_data), file_name=new_filename)

            # Send and save thumbnail
            if thumbnail_bytes:
                thumbnail_name = f"{metadata['title']}_Ch{int(metadata['chapter'])}.jpg"
                await client.send_photo(chat_id=chat_id, photo=io.BytesIO(thumbnail_bytes), caption=f"Thumbnail for {new_filename}")
                await db.save_thumbnail(chat_id, thumbnail_name, thumbnail_bytes)

            logger.info(f"Processed and sent {original_name} as {new_filename}")
            return True
        except Exception as e:
            logger.error(f"Error processing {original_name}: {e}")
            await message.reply(f"Error processing {original_name}: {str(e)}")
            return False
