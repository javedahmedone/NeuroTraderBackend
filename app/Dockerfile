# Use official Python image
FROM python:3.13.5-slim

# Set working directory
WORKDIR /app

# Install system deps if needed (optional, e.g. for pandas, numpy)
RUN apt-get update && apt-get install -y build-essential

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose FastAPI default port
EXPOSE 5000

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
