FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for RocksDB
RUN apt-get update && apt-get install -y \
    build-essential \
    librocksdb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire wikidata directory to maintain package structure
COPY . /app

# Install the package in editable mode
RUN pip install -e .

# Expose the port
EXPOSE 8020

# Run the FastAPI app with Uvicorn
CMD uvicorn wikidata.main:app --host 0.0.0.0 --port 8020 --workers ${NUM_WORKERS} 