FROM ilriccio/thehistoryatlas:ner_base
COPY /app /app

FROM conda/miniconda3
RUN conda install -c conda-forge spacy spacy-model-en_core_web_lg
COPY --from=0 /app/base-models /app/base-models
COPY --from=0 /app/train /app/train

WORKDIR /app
# get local python packages
COPY --from=pylib /lib /lib
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
RUN pip3 install sqlalchemy
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