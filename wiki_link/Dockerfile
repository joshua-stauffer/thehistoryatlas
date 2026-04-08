FROM python:3.10-slim-buster

WORKDIR /app

# Copy the service code
COPY . /app/wiki_link

# Install requirements
RUN pip3 install -r /app/wiki_link/requirements.txt
RUN pip3 install /app/wiki_link

# Add the app directory to Python path
ENV PYTHONPATH=/app

# Run tests
CMD ["python3", "-m", "pytest", "-vvv", "/app/wiki_link/tests"]