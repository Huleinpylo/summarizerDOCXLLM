# backend/app.py

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from summarizer import process_document  # Ensure this function is correctly updated
import uvicorn
from typing import Dict
import uuid
import logging

app = FastAPI(title="Document Summarizer API")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You may limit origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (replace with persistent storage for production)
session_storage: Dict[str, Dict] = {}

@app.post("/summarize")
async def summarize(file: UploadFile = File(...), session_id: str = Query(None)):
    """
    Endpoint to upload a Word document and receive chapter-wise summaries.
    
    Args:
        file (UploadFile): The uploaded document.
        session_id (str, optional): Unique identifier for the session.
    
    Returns:
        dict: Summaries and the session ID.
    """
    try:
        # Read the uploaded file content
        content = await file.read()
        logger.debug(f"File uploaded: {file.filename}")

        # Process the document and get summaries
        summaries = process_document(content, file.filename)  # Pass 'file.filename'

        # Assign a new session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Store summaries in the session storage
        session_storage[session_id] = summaries

        # Return the summaries as JSON along with the session ID
        return {"summaries": summaries, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error in /summarize endpoint: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
