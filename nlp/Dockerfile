FROM ilriccio/thehistoryatlas:ner_base
COPY /app /app

FROM python:3.9-slim-buster

# install dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y netcat-openbsd gcc && \
    apt-get clean && \
    apt install -y build-essential libpq-dev

RUN pip3 install spacy
COPY --from=0 /app/base-models /app/base-models/model-best
COPY --from=0 /app/train /app/train

WORKDIR /app
# get local python packages
COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib

RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install sqlalchemy
RUN pip3 install psycopg2-binary
COPY . .
ENV HOST_NAME=broker
ENV TESTING=False
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=
ENV TEST_DB_URI=
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=nlp
CMD ["python3", "-m", "app.nlp"]