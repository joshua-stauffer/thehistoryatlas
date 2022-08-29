FROM python:3.9-slim-buster

## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# get local python packages
COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib

COPY test-requirements.txt test-requirements.txt
COPY requirements.txt requirements.txt
RUN pip3 install -r test-requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/abstract-domain-model
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=readmodel
CMD ["python3", "-m", "readmodel.read_model"]
