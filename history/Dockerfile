FROM python:3.9-slim-buster
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# get local python packages
COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/event-schema
COPY . .
ENV HOST_NAME=broker

ENV TESTING=False
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=sqlite:////data/db/tha-store-dev.db
ENV TEST_DB_URI=sqlite:////data/db/tha-test-dev.db
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=history
CMD ["python3", "-m", "app.history"]