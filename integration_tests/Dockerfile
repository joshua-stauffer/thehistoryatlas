FROM python:3.10-slim-buster
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY --from=pylib . /lib
COPY --from=testlib . /lib
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/abstract-domain-model
RUN pip3 install /lib/test-data
RUN pip3 install /lib/rpc-manager
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=integration-tests
CMD ["python3", "-m", "pytest", "-vvv"]

# HOST_NAME=broker;BROKER_USERNAME=guest;BROKER_PASS=guest;EXCHANGE_NAME=main;QUEUE_NAME=integration-tests;