# backend/app.py

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from summarizer import process_markdown_document
from celery.result import AsyncResult
from celery_worker import celery_app, summarize_document_task
import uvicorn
from typing import Dict
import uuid
import logging
import json

app = FastAPI(title="Document Summarizer API")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to restrict allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (optional, since Celery handles task states)
# session_storage: Dict[str, Dict] = {}


@app.post("/summarize")
async def summarize(
    file: UploadFile = File(...),
    format: str = Query("markdown", regex="^(markdown|json)$")
):
    """
    Endpoint to upload a markdown document and initiate a summarization job.

    Args:
        file (UploadFile): The uploaded markdown file.
        format (str, optional): Desired output format ('markdown' or 'json'). Defaults to 'markdown'.

    Returns:
        JSONResponse: A JSON response containing the job ID.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".md"):
            logger.error(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(status_code=400, detail="Invalid file type. Only .md files are supported.")

        # Read the uploaded file content
        content = await file.read()
        logger.debug(f"File uploaded: {file.filename} (Size: {len(content)} bytes)")

        # Initiate Celery task
        task = summarize_document_task.delay(content, file.filename)
        logger.info(f"Summarization task initiated with ID: {task.id}")

        return JSONResponse(content={"job_id": task.id}, status_code=202)

    except Exception as e:
        logger.error(f"Error in /summarize endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/status/{job_id}")
def get_status(job_id: str):
    """
    Endpoint to check the status of a summarization job.

    Args:
        job_id (str): The unique identifier of the job.

    Returns:
        JSONResponse: A JSON response containing the job status and progress.
    """
    try:
        task_result = AsyncResult(job_id, app=celery_app)
        if task_result.state == 'PENDING':
            response = {
                "status": "PENDING",
                "progress": 0,
                "status_message": "Job is pending."
            }
        elif task_result.state != 'FAILURE':
            meta_info = task_result.info or {}
            global_progress = meta_info.get('current', 0) / meta_info.get('total', 1) * 100
            response = {
                "status": task_result.state,
                "progress": global_progress,
                "status_message": meta_info.get('status', ''),
                "section_total": meta_info.get('section_total', 0),
                "section_current": meta_info.get('section_current', 0),
                "section_progress": meta_info.get('section_progress', 0),
                "chunk_total": meta_info.get('chunk_total', 0),
                "chunk_current": meta_info.get('chunk_current', 0)
            }
            if task_result.state == 'SUCCESS':
                response['result'] = task_result.result
        else:
            # Something went wrong in the background job
            response = {
                "status": task_result.state,
                "progress": 100,
                "status_message": str(task_result.info),  # this is the exception raised
            }

        return response
    except Exception as e:
        logger.error(f"Error in /status/{job_id} endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    Endpoint to retrieve the result of a summarization job.

    Args:
        job_id (str): The unique identifier of the job.

    Returns:
        Response or JSONResponse: The summarized content in the requested format.
    """
    try:
        task_result = AsyncResult(job_id, app=celery_app)
        if not task_result.ready():
            raise HTTPException(status_code=202, detail="Job is still in progress.")

        if task_result.state == 'SUCCESS':
            result = task_result.result
            # Determine the desired format based on the job's request
            # For simplicity, assume the frontend knows which format was requested
            # Alternatively, store the format in a database or pass it as a parameter

            # Here, we return both formats. The frontend can choose which one to use.
            return JSONResponse(content=result, status_code=200)
        elif task_result.state == 'FAILURE':
            raise HTTPException(status_code=500, detail=str(task_result.info))
        else:
            raise HTTPException(status_code=202, detail="Job is still in progress.")
    except Exception as e:
        logger.error(f"Error in /result/{job_id} endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
