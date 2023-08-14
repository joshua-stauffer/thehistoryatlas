FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

CMD ["python3", "-m", "pytest"]
