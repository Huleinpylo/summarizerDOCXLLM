# backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY ../requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port 8001 to the outside world
EXPOSE 8001

# Set environment variables for the app
ENV OLLAMA_API_URL=$OLLAMA_API_URL
ENV OLLAMA_API_KEY=$OLLAMA_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV CELERY_BROKER_URL=$CELERY_BROKER_URL
ENV CELERY_RESULT_BACKEND=$CELERY_RESULT_BACKEND

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
