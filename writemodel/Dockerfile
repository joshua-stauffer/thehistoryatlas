FROM python:3.10-slim-buster
COPY --from=pylib . .
COPY --from=testlib . .
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /pybroker
RUN pip3 install /tha-config
RUN pip3 install /abstract-domain-model
RUN pip3 install /test-data
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=writemodel
CMD ["python3", "-m", "writemodel.server"]
