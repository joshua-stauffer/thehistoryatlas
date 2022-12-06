FROM python:3.10-slim-buster
WORKDIR /app
COPY --from=pylib . .
COPY --from=testlib . .
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /app/lib/pybroker
RUN pip3 install /app/lib/tha-config
RUN pip3 install /app/lib/abstract-domain-model
RUN pip3 install /app/lib/test-data
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=writemodel
CMD ["python3", "-m", "writemodel.server"]
