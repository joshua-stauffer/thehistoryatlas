#FROM ilriccio/thehistoryatlas:ner_base
#COPY /app /nlp

FROM python:3.10-slim-buster

# install dependencies
#RUN apt-get update && \
#    apt-get upgrade -y && \
#    apt-get install -y netcat-openbsd gcc && \
#    apt-get clean && \
#    apt install -y build-essential libpq-dev

RUN pip3 install spacy
#COPY --from=0 /app/base-models /app/base-models/model-best
#COPY --from=0 /app/train /app/train

WORKDIR /app
COPY --from=pylib . /lib
COPY --from=testlib . /lib
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install /lib/abstract-domain-model
RUN pip3 install /lib/test-data
RUN pip3 install sqlalchemy
RUN pip3 install psycopg2-binary
COPY . .
ENV HOST_NAME=broker
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=nlp
CMD ["python3", "-m", "nlp_service.nlp"]