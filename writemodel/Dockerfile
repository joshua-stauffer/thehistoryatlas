FROM python:3.9-slim-buster
WORKDIR /app

# get pybroker lib
COPY --from=pybroker /pybroker /pybroker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /pybroker
COPY . .
ENV HOST_NAME=tha-test-broker
ARG test=True
ENV TESTING=$test
ENV DEBUG=True
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=sqlite:////etc/db/tha-test.db
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=writemodel
CMD ["python3", "app/write_model.py"]