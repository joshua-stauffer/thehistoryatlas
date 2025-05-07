FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
RUN pip install .

EXPOSE 8000

CMD uvicorn the_history_atlas.main:app --host 0.0.0.0 --port 8000 --workers 3
