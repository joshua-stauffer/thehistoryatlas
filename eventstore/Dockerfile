FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
ENV HOST_NAME=tha-test-broker
ARG test=True
ENV TESTING=$test
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=sqlite:////etc/db/tha-test.db
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV RECV_QUEUE=emitted_events_queue
ENV SEND_QUEUE=persisted_events_queue
CMD ["python3", "app/event_store.py"]