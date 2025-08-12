# # Use official Python image
# FROM python:3.13.5-slim

# # Set working directory to project root (one level above "app")
# WORKDIR /code

# # Install system deps if needed
# RUN apt-get update && apt-get install -y build-essential

# # Copy requirements from app folder
# COPY app/requirements.txt .

# RUN pip install --no-cache-dir -r requirements

# # Copy everything from project root
# COPY . .

# # Make sure Python can see "app" package
# ENV PYTHONPATH=/code

# # Expose FastAPI default port
# EXPOSE 5000

# # Start FastAPI
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]


# Use official Python slim image
FROM python:3.13.5-slim

# Set working directory inside container
WORKDIR /code

# Install system dependencies (optional, only if needed for builds)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements file from current folder (app/)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code from app/ into /code
COPY . .

# Ensure Python can see our app module
ENV PYTHONPATH=/code

# Expose FastAPI port
EXPOSE 5000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
