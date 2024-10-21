# backend/summarizer.py

import logging
import re
from typing import List, Dict
from langchain_ollama import OllamaLLM
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_summarize_chain(model: str, api_key: str = None, api_url: str = None) -> LLMChain:
    """
    Factory function to create an LLMChain based on the selected model.

    Args:
        model (str): The model to use ('ollama' or 'openai').
        api_key (str, optional): The API key for the model.
        api_url (str, optional): The API URL for Ollama.

    Returns:
        LLMChain: An instance of LLMChain configured with the selected model.
    """
    if model.lower() == "ollama":
        if not api_url:
            raise ValueError("Ollama API URL must be provided for Ollama model.")
        llm = OllamaLLM(
            model="llama3.1",
            temperature=0.3,
            api_url=api_url,
            api_key=api_key if api_key else None
        )
        logger.info("Initialized the Ollama LLM with Llama 3.1 model.")
    elif model.lower() == "openai":
        if not api_key:
            raise ValueError("OpenAI API key must be provided for OpenAI model.")
        llm = OpenAI(
            api_key=api_key,
            temperature=0.3
        )
        logger.info("Initialized the OpenAI LLM.")
    else:
        raise ValueError(f"Unsupported model: {model}")
    
    # Define a prompt template for summarization
    prompt = PromptTemplate(
        input_variables=["section_content"],
        template="""
You are an assistant that summarizes sections of a markdown document.

Summarize the following section content:

{section_content}

Summary:
"""
    )
    
    # Create a chain for summarization
    summarize_chain = LLMChain(llm=llm, prompt=prompt)
    logger.info("Created summarization chain with the given prompt template.")
    
    return summarize_chain

def read_markdown_document(file_content: bytes) -> str:
    """
    Reads a markdown document and returns its content as a string.

    Args:
        file_content (bytes): The binary content of the markdown document.

    Returns:
        str: The text content of the markdown document.
    """
    try:
        logger.debug("Reading markdown document content.")
        text = file_content.decode('utf-8')
        logger.info("Successfully extracted text from the markdown document.")
        return text
    except Exception as e:
        logger.error(f"Error reading markdown document: {str(e)}")
        raise

def extract_sections(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extracts sections based on '##' headings in the markdown.

    Args:
        markdown_text (str): The markdown content.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with section titles and content.
    """
    try:
        logger.debug("Extracting sections from markdown based on '##' headings.")
        sections = []
        current_section = {"title": "Introduction", "content": ""}  # Default section

        lines = markdown_text.split('\n')
        section_header_pattern = re.compile(r'^##\s+(.*)')

        for line in lines:
            header_match = section_header_pattern.match(line.strip())
            if header_match:
                # Save the previous section
                if current_section["title"] or current_section["content"]:
                    sections.append(current_section)
                # Start a new section
                current_section = {
                    "title": header_match.group(1).strip(),
                    "content": ""
                }
                logger.info(f"Detected new section: {current_section['title']}")
            else:
                current_section["content"] += line + '\n'

        # Add the last section
        if current_section["title"] or current_section["content"]:
            sections.append(current_section)

        logger.info(f"Successfully extracted {len(sections)} sections from markdown.")
        return sections
    except Exception as e:
        logger.error(f"Error extracting sections: {str(e)}")
        raise

def split_text_with_overlap(text: str, max_size: int = 1250, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of approximately `max_size` characters with `overlap` characters overlapping.

    Args:
        text (str): The text to split.
        max_size (int): Maximum size of each chunk.
        overlap (int): Number of overlapping characters between chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    try:
        logger.debug("Splitting text into chunks with overlapping.")
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + max_size
            if end >= text_length:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            # Find the last whitespace before the end to avoid breaking words
            split_point = text.rfind(' ', start, end)
            if split_point == -1 or split_point <= start:
                split_point = end
            chunk = text[start:split_point].strip()
            if chunk:
                chunks.append(chunk)
            start = split_point - overlap  # Move back by 'overlap' characters

        logger.info(f"Successfully split text into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting text into chunks: {str(e)}")
        raise

def summarize_sections(summarize_chain: LLMChain, sections: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Summarizes each section using LangChain and the provided LLMChain.

    Args:
        summarize_chain (LLMChain): The summarization chain configured with the desired LLM.
        sections (List[Dict[str, str]]): List of sections with titles and content.

    Returns:
        Dict[str, str]: Dictionary of section titles with their summaries.
    """
    summaries = {}
    for section in sections:
        title = section['title']
        content = section['content'].strip()
        if content:
            try:
                logger.debug(f"Summarizing section: {title}")
                # Split content into batches if it's too large
                if len(content) > 1250:
                    batches = split_text_with_overlap(content, max_size=1250, overlap=200)
                else:
                    batches = [content]

                section_summary = ""
                for batch in batches:
                    summary = summarize_chain.run(section_content=batch)
                    section_summary += summary.strip() + " "

                summaries[title] = section_summary.strip()
                logger.info(f"Successfully summarized section: {title}")
            except Exception as e:
                logger.error(f"Error summarizing section '{title}': {str(e)}")
                summaries[title] = f"Error summarizing section: {str(e)}"
        else:
            logger.warning(f"Section '{title}' has no content to summarize.")
            summaries[title] = "No content to summarize."

    return summaries

def process_markdown_document(summarize_chain: LLMChain, file_content: bytes, file_name: str) -> Dict[str, any]:
    """
    Processes the uploaded markdown document and returns both markdown and JSON summaries.

    Args:
        summarize_chain (LLMChain): The summarization chain configured with the desired LLM.
        file_content (bytes): The binary content of the markdown document.
        file_name (str): The name of the uploaded file.

    Returns:
        Dict[str, any]: Dictionary containing 'summary_markdown' and 'summaries_json'.
    """
    try:
        # Check if the file has a .md extension
        if not file_name.lower().endswith(".md"):
            logger.error(f"Uploaded file '{file_name}' is not a .md file.")
            raise ValueError("Only .md files are supported.")

        logger.info(f"Starting document processing for file: {file_name}")
        markdown_text = read_markdown_document(file_content)
        sections = extract_sections(markdown_text)
        summaries = summarize_sections(summarize_chain, sections)

        # Create a markdown summary
        summary_markdown = f"# Summaries of {file_name}\n\n"
        for title, summary in summaries.items():
            summary_markdown += f"## {title}\n\n{summary}\n\n"

        # Create a JSON summary
        summaries_json = {
            "file_name": file_name,
            "summaries": summaries
        }

        logger.info(f"Successfully processed the document '{file_name}' and generated summaries.")
        return {
            "summary_markdown": summary_markdown.strip(),
            "summaries_json": summaries_json
        }

    except Exception as e:
        logger.error(f"Error processing document '{file_name}': {str(e)}")
        raise
