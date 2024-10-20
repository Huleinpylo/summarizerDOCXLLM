# backend/summarizer.py

import logging
from docx import Document
from io import BytesIO
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Ollama LLM with Llama 3
llm = OllamaLLM(model="llama3.1", temperature=0.3)
logger.info("Initialized the Ollama LLM with Llama 3.1 model.")

# Define a prompt template for summarization
prompt = PromptTemplate(
    input_variables=["section_content"],
    template="""
    You are an assistant that summarizes chapters of a document.

    Summarize the following chapter content:

    {section_content}

    Summary:
    """
)

# Create a chain for summarization
summarize_chain = LLMChain(llm=llm, prompt=prompt)
logger.info("Created summarization chain with the given prompt template.")

def read_word_document(file_content: bytes) -> Document:
    """
    Reads a Word document and returns the Document object.

    Args:
        file_content (bytes): The binary content of the Word document.

    Returns:
        Document: The parsed Word document.
    """
    try:
        logging.debug("Reading Word document content.")
        doc = Document(BytesIO(file_content))  # Correctly parse the .docx content
        logging.info("Successfully extracted text from the Word document.")
        return doc
    except Exception as e:
        logging.error(f"Error reading Word document: {str(e)}")
        raise

def split_into_chapters(doc: Document) -> list:
    """
    Splits the document into chapters based on specific paragraph styles.

    Args:
        doc (Document): The parsed Word document.

    Returns:
        list: A list of dictionaries with chapter titles and content.
    """
    try:
        logging.debug("Splitting document into chapters based on styles.")
        chapters = []
        current_chapter = None

        # Define the styles that represent chapter titles
        chapter_styles = ['Title', 'Heading 1', 'Heading 2']  # Adjust based on your document

        for paragraph in doc.paragraphs:
            paragraph_text = paragraph.text.strip()
            paragraph_style = paragraph.style.name

            if paragraph_style in chapter_styles and paragraph_text:
                # Start of a new chapter
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    'title': paragraph_text,
                    'content': ''
                }
                logging.info(f"Detected new chapter: {paragraph_text}")
            elif current_chapter and paragraph_text:
                # Append the paragraph to the current chapter content
                current_chapter['content'] += paragraph_text + '\n'

        # Add the last chapter if it exists
        if current_chapter:
            chapters.append(current_chapter)

        logging.info("Successfully split the document into chapters.")
        return chapters
    except Exception as e:
        logging.error(f"Error splitting document into chapters: {str(e)}")
        raise

def summarize_chapters(chapters: list) -> dict:
    """
    Summarizes each chapter using LangChain and the LLM.

    Args:
        chapters (list): List of chapters with titles and content.

    Returns:
        dict: Dictionary of chapters with their summaries.
    """
    summaries = {}
    for chapter in chapters:
        chapter_title = chapter['title']
        content = chapter['content']
        if content:
            try:
                logging.debug(f"Summarizing chapter: {chapter_title}")
                summary = summarize_chain.run(section_content=content)
                summaries[chapter_title] = summary.strip()
                logging.info(f"Successfully summarized chapter: {chapter_title}")
            except Exception as e:
                logging.error(f"Error summarizing chapter '{chapter_title}': {str(e)}")
                summaries[chapter_title] = f"Error summarizing chapter: {str(e)}"
        else:
            logging.warning(f"Chapter '{chapter_title}' has no content to summarize.")
            summaries[chapter_title] = "No content to summarize."
    return summaries

def process_document(file_content: bytes, file_name: str) -> dict:
    """
    Processes the uploaded Word document and returns chapter-wise summaries.

    Args:
        file_content (bytes): The binary content of the Word document.
        file_name (str): The name of the uploaded file.

    Returns:
        dict: Chapter-wise summaries.
    """
    try:
        # Check if the file has a .docx extension
        if not file_name.lower().endswith(".docx"):
            logging.error(f"Uploaded file '{file_name}' is not a .docx file.")
            raise ValueError("Only .docx files are supported.")

        logging.info(f"Starting document processing for file: {file_name}")
        doc = read_word_document(file_content)  # Get the Document object
        chapters = split_into_chapters(doc)      # Split into chapters
        summaries = summarize_chapters(chapters)
        logging.info(f"Successfully processed the document '{file_name}' and generated summaries.")
        return summaries

    except Exception as e:
        logging.error(f"Error processing document '{file_name}': {str(e)}")
        raise
