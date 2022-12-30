FROM python:3.10-slim-buster
COPY --from=pylib . /lib
COPY --from=testlib . /lib
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY test-requirements.txt test-requirements.txt
COPY requirements.txt requirements.txt
RUN pip3 install -r test-requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/abstract-domain-model
RUN pip3 install /lib/test-data
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=readmodel
CMD ["python3", "-m", "readmodel.server"]
