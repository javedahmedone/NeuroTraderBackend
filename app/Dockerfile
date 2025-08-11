# Use official Python image
FROM python:3.13.5-slim

# Set working directory to project root (one level above "app")
WORKDIR /code

# Install system deps if needed
RUN apt-get update && apt-get install -y build-essential

# Copy requirements from app folder
COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements

# Copy everything from project root
COPY . .

# Make sure Python can see "app" package
ENV PYTHONPATH=/code

# Expose FastAPI default port
EXPOSE 5000

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
