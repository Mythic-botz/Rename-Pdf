# plugins/metadata.py
# Plugin for extracting metadata from PDFs in memory
# Extensible for custom metadata extraction logic

import fitz
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_metadata(pdf_data: bytes):
    """
    Extract title and chapter from PDF metadata or filename (using bytes).

    :param pdf_data: Bytes of the PDF.
    :return: Dict with 'title' and 'chapter'.
    :raises ValueError: If metadata cannot be extracted.
    """
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        metadata = doc.metadata
        title = metadata.get('title', '').strip()
        chapter_str = metadata.get('chapter', '').strip()

        if not title or not chapter_str:
            # Fallback: Use defaults since no filename available
            title = "Unknown"
            chapter_str = "1"

        chapter = float(chapter_str) if chapter_str.isdigit() else 1.0
        doc.close()
        logger.info(f"Extracted metadata: title='{title}', chapter={chapter}")
        return {'title': title, 'chapter': chapter}
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        raise ValueError(f"Invalid PDF or metadata: {e}")
