# backend/celery_worker.py

from celery import Celery
from summarizer import read_markdown_document, extract_sections, summarize_sections
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'worker',
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

@celery_app.task(bind=True)
def summarize_document_task(self, file_content: bytes, file_name: str):
    """
    Celery task to summarize a markdown document.

    Args:
        file_content (bytes): The binary content of the markdown document.
        file_name (str): The name of the uploaded file.

    Returns:
        dict: Dictionary containing 'summary_markdown' and 'summaries_json'.
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 3, 'status': 'Starting summarization.'})
        
        # Step 1: Read Document
        markdown_text = read_markdown_document(file_content)
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3, 'status': 'Extracting sections.'})

        # Step 2: Extract Sections
        sections = extract_sections(markdown_text)
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 3, 'status': 'Summarizing sections.'})

        # Step 3: Summarize Sections
        summaries = summarize_sections(sections)
        self.update_state(state='PROGRESS', meta={'current': 3, 'total': 3, 'status': 'Finalizing summaries.'})

        # Compile Summaries
        summary_markdown = f"# Summaries of {file_name}\n\n"
        for title, summary in summaries.items():
            summary_markdown += f"## {title}\n\n{summary}\n\n"

        summaries_json = {
            "file_name": file_name,
            "summaries": summaries
        }

        logger.info(f"Task {self.request.id} completed successfully.")
        return {
            "summary_markdown": summary_markdown.strip(),
            "summaries_json": summaries_json
        }

    except Exception as e:
        logger.error(f"Error in summarization task {self.request.id}: {str(e)}")
        # Retry the task in 60 seconds, up to 3 retries
        raise self.retry(exc=e, countdown=60, max_retries=3)
