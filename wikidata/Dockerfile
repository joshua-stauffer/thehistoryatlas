FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for RocksDB
RUN apt-get update && apt-get install -y \
    build-essential \
    librocksdb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code and setup.py
COPY ./wikidata/*.py ./wikidata/
COPY setup.py .

# Install the local package
RUN pip install -e .

# Expose the port
EXPOSE 8020

# Run the FastAPI app with Uvicorn
CMD uvicorn wikidata.main:app --host 0.0.0.0 --port 8020 --workers ${NUM_WORKERS} 