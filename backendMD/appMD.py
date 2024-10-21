# backend/app.py

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from summarizer import process_markdown_document, get_summarize_chain
from celery.result import AsyncResult
from celery_worker import celery_app, summarize_document_task
import uvicorn
import logging

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

@app.post("/summarize")
async def summarize(
    file: UploadFile = File(...),
    model: str = Query("ollama", regex="^(ollama|openai)$"),
    api_key: str = Query(None, description="API Key for the selected model"),
    api_url: str = Query(None, description="API URL for Ollama (required if model is Ollama)"),
    format: str = Query("markdown", regex="^(markdown|json)$")
):
    """
    Endpoint to upload a markdown document and initiate a summarization job.

    Args:
        file (UploadFile): The uploaded markdown file.
        model (str, optional): The model to use ('ollama' or 'openai'). Defaults to 'ollama'.
        api_key (str, optional): The API key for the selected model.
        api_url (str, optional): The API URL for Ollama. Required if model is 'ollama'.
        format (str, optional): Desired output format ('markdown' or 'json'). Defaults to 'markdown'.

    Returns:
        JSONResponse: A JSON response containing the job ID.
    """
    try:
        # Validate model-specific parameters
        if model.lower() == "ollama":
            if not api_url:
                raise HTTPException(status_code=400, detail="Ollama API URL must be provided for Ollama model.")
        elif model.lower() == "openai":
            if not api_key:
                raise HTTPException(status_code=400, detail="OpenAI API key must be provided for OpenAI model.")

        # Validate file type
        if not file.filename.lower().endswith(".md"):
            logger.error(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(status_code=400, detail="Invalid file type. Only .md files are supported.")

        # Read the uploaded file content
        content = await file.read()
        logger.debug(f"File uploaded: {file.filename} (Size: {len(content)} bytes)")

        # Initiate Celery task
        task = summarize_document_task.delay(
            file_content=content,
            file_name=file.filename,
            model=model,
            api_key=api_key,
            api_url=api_url
        )
        logger.info(f"Summarization task initiated with ID: {task.id}")

        return JSONResponse(content={"job_id": task.id}, status_code=202)

    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
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
            global_progress = int((meta_info.get('current', 0) / meta_info.get('total', 1)) * 100)
            response = {
                "status": task_result.state,
                "progress": global_progress,
                "status_message": meta_info.get('status', ''),
                "model": meta_info.get('model', ''),
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
        JSONResponse: The summarized content in the requested format.
    """
    try:
        task_result = AsyncResult(job_id, app=celery_app)
        if not task_result.ready():
            raise HTTPException(status_code=202, detail="Job is still in progress.")

        if task_result.state == 'SUCCESS':
            result = task_result.result
            return JSONResponse(content=result, status_code=200)
        elif task_result.state == 'FAILURE':
            raise HTTPException(status_code=500, detail=str(task_result.info))
        else:
            raise HTTPException(status_code=202, detail="Job is still in progress.")
    except Exception as e:
        logger.error(f"Error in /result/{job_id} endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
