# backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ../requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application code
COPY . /app

# Expose port 8001 for FastAPI
EXPOSE 8001

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
