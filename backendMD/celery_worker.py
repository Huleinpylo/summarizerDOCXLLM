# backend/celery_worker.py

from celery import Celery
from summarizer import (
    get_summarize_chain,
    read_markdown_document,
    extract_sections,
    summarize_sections,
    split_text_with_overlap
)
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
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

@celery_app.task(bind=True)
def test_task():
    return "Task Completed"

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

@celery_app.task(bind=True)
def summarize_document_task(self, file_content: bytes, file_name: str, model: str, api_key: str = None, api_url: str = None):
    """
    Celery task to summarize a markdown document with progress tracking.

    Progress is tracked at three levels:
    1. Global progress (overall task)
    2. Section progress (progress within each section)
    3. Chunk progress (progress within chunks of each section)

    Args:
        file_content (bytes): The binary content of the markdown document.
        file_name (str): The name of the uploaded file.
        model (str): The model to use ('ollama' or 'openai').
        api_key (str, optional): The API key for the selected model.
        api_url (str, optional): The API URL for Ollama.

    Returns:
        dict: Dictionary containing 'summary_markdown' and 'summaries_json'.
    """
    try:
        self.update_state(state='PROGRESS', meta={
            'current': 0,
            'total': 3,
            'status': 'Starting summarization.',
            'model': model,
            'section_total': 0,
            'section_current': 0,
            'section_progress': 0,
            'chunk_total': 0,
            'chunk_current': 0
        })

        # Initialize the summarization sequence based on model
        summarize_sequence = get_summarize_chain(model=model, api_key=api_key, api_url=api_url)

        # Step 1: Read Document
        markdown_text = read_markdown_document(file_content)
        self.update_state(state='PROGRESS', meta={
            'current': 1,
            'total': 3,
            'status': 'Extracting sections.',
            'model': model,
            'section_total': 0,
            'section_current': 0,
            'section_progress': 0,
            'chunk_total': 0,
            'chunk_current': 0
        })

        # Step 2: Extract Sections
        sections = extract_sections(markdown_text)
        total_sections = len(sections)
        self.update_state(state='PROGRESS', meta={
            'current': 1,
            'total': 3,
            'status': 'Summarizing sections.',
            'model': model,
            'section_total': total_sections,
            'section_current': 0,
            'section_progress': 0,
            'chunk_total': 0,
            'chunk_current': 0
        })

        # Step 3: Summarize Sections
        summaries = {}
        for section_index, section in enumerate(sections, start=1):
            title = section['title']
            content = section['content'].strip()
            if content:
                try:
                    # Split content into chunks
                    if len(content) > 12500:
                        chunks = split_text_with_overlap(content, max_size=12500, overlap=200)
                    else:
                        chunks = [content]
                    total_chunks = len(chunks)
                    summaries_section = ""

                    for chunk_index, chunk in enumerate(chunks, start=1):
                        # Summarize each chunk
                        summary = summarize_sections(summarize_sequence, [{'title': title, 'content': chunk}])
                        summaries_section += summary[title].strip() + " "

                        # Update chunk progress
                        self.update_state(state='PROGRESS', meta={
                            'current': 1,
                            'total': 3,
                            'status': f'Summarizing section: {title}',
                            'model': model,
                            'section_total': total_sections,
                            'section_current': section_index,
                            'section_progress': int((section_index / total_sections) * 100),
                            'chunk_total': total_chunks,
                            'chunk_current': chunk_index
                        })

                    summaries[title] = summaries_section.strip()
                except Exception as e:
                    logger.error(f"Error summarizing section '{title}': {str(e)}")
                    summaries[title] = f"Error summarizing section: {str(e)}"
            else:
                summaries[title] = "No content to summarize."

        # Compile Summaries
        summary_markdown = f"# Summaries of {file_name}\n\n"
        for title, summary in summaries.items():
            summary_markdown += f"## {title}\n\n{summary}\n\n"

        summaries_json = {
            "file_name": file_name,
            "summaries": summaries
        }

        self.update_state(state='PROGRESS', meta={
            'current': 3,
            'total': 3,
            'status': 'Finalizing summaries.',
            'model': model,
            'section_total': total_sections,
            'section_current': total_sections,
            'section_progress': 100,
            'chunk_total': 0,
            'chunk_current': 0
        })

        logger.info(f"Task {self.request.id} completed successfully.")
        return {
            "summary_markdown": summary_markdown.strip(),
            "summaries_json": summaries_json
        }

    except Exception as e:
        logger.error(f"Error in summarization task {self.request.id}: {str(e)}")
        # Retry the task in 60 seconds, up to 3 retries
        raise self.retry(exc=e, countdown=60, max_retries=3)
