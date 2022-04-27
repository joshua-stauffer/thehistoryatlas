FROM python:3.9-slim-buster
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# get local python packages
COPY --from=ilriccio/thehistoryatlas:pylib /lib /lib

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install /lib/pybroker
RUN pip3 install /lib/tha-config
COPY . .
ENV HOST_NAME=broker
ARG test=False
# ENV TESTING=$test
ENV TESTING=False
ENV DEBUG=True
ENV CONFIG=DEV
ENV PROD_DB_URI=
ENV DEV_DB_URI=sqlite:////etc/db/accounts.db
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV EXCHANGE_NAME=main
ENV QUEUE_NAME=accounts
# obviously, this key for local dev only
ENV SEC_KEY=nHECungBxXETr9hdYml6sik9Eb368q0cm2wutp644oQ=
ENV TTL=28800
ENV REFRESH_BY=7200
CMD ["python3", "-m", "app.accounts"]