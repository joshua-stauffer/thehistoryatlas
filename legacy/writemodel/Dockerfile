FROM python:3.10-slim-buster
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY --from=pylib ../../accounts /lib
COPY --from=testlib ../../accounts /lib
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/abstract-domain-model
RUN pip3 install /lib/test-data
RUN pip3 install /lib/rpc-manager
COPY ../../accounts .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=writemodel
CMD ["python3", "-m", "writemodel.server"]
