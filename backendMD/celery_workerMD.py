# backend/celery_worker.py

from celery import Celery
from summarizer import read_markdown_document, extract_sections, summarize_sections, split_text_with_overlap
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
    Celery task to summarize a markdown document with progress tracking.
    
    Progress is tracked at three levels:
    1. Global progress (overall task)
    2. Section progress (progress within each section)
    3. Chunk progress (progress within chunks of each section)
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 3, 'status': 'Starting summarization.'})
        
        # Step 1: Read Document
        markdown_text = read_markdown_document(file_content)
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3, 'status': 'Extracting sections.'})

        # Step 2: Extract Sections
        sections = extract_sections(markdown_text)
        total_sections = len(sections)
        global_progress = 2  # Section extraction is complete (2/3 overall progress)
        section_progress = 0

        # Store overall progress
        self.update_state(state='PROGRESS', meta={
            'current': global_progress, 'total': 3, 'status': 'Summarizing sections...',
            'section_total': total_sections,
            'section_current': section_progress
        })

        # Step 3: Summarize Sections
        summaries = {}
        total_chunks = 0  # We'll calculate the total number of chunks across all sections
        
        # Summarize each section
        for section_index, section in enumerate(sections):
            section_title = section['title']
            section_content = section['content'].strip()

            if section_content:
                # Split the section into chunks
                chunks = split_text_with_overlap(section_content, max_size=1250, overlap=200)
                num_chunks = len(chunks)
                total_chunks += num_chunks
                chunk_progress = 0
                
                section_summary = ""
                for chunk_index, chunk in enumerate(chunks):
                    # Process each chunk and update chunk progress
                    summary = summarize_sections([{'title': section_title, 'content': chunk}])
                    section_summary += summary[section_title].strip() + " "
                    
                    chunk_progress += 1
                    section_progress = (chunk_index + 1) / num_chunks * 100  # Section percentage
                    self.update_state(state='PROGRESS', meta={
                        'current': global_progress, 'total': 3, 
                        'status': f'Summarizing section: {section_title}',
                        'section_total': total_sections,
                        'section_current': section_index + 1,
                        'section_progress': section_progress, 
                        'chunk_total': num_chunks,
                        'chunk_current': chunk_progress
                    })

                summaries[section_title] = section_summary.strip()

            else:
                summaries[section_title] = "No content to summarize."
            
            # Update global progress after each section is summarized
            global_progress += 1
            self.update_state(state='PROGRESS', meta={
                'current': global_progress, 'total': total_sections + 3,
                'status': 'Summarizing sections...',
                'section_total': total_sections,
                'section_current': section_index + 1,
                'section_progress': 100,
            })
        
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
        raise self.retry(exc=e, countdown=60, max_retries=3)
