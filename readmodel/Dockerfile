FROM python:3.9-slim-buster

## install dependencies
# RUN apt-get update && \
#     apt-get upgrade -y && \
#     apt-get install -y netcat-openbsd gcc && \
#     apt-get clean && \
#     apt install -y build-essential libpq-dev


## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# get local python packages
COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
COPY . .
ENV HOST_NAME=broker
ARG test=True
# ENV TESTING=$test
ENV TESTING=False
ENV DEBUG=True
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=sqlite:////data/db/readmodel.db
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=readmodel
CMD ["python3", "-m", "app.read_model"]