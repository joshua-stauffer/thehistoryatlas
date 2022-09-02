FROM python:3.10-slim-buster
WORKDIR /app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# get local python packages
#COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib
#COPY --from=ilriccio/thehistoryatlas:testlib /lib /lib

COPY --from=pylib . /lib
COPY --from=testlib . /lib

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/event-schema
RUN pip3 install /lib/abstract-domain-model
RUN pip3 install /lib/test-data
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=history
CMD ["python3", "-m", "history_service.history"]