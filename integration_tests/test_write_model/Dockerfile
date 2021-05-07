FROM python:3.9-slim-buster
WORKDIR /app

# get local python packages
COPY --from=testlib /lib /lib
RUN pip3 install /lib/tackle
RUN pip3 install /lib/pybroker
COPY . .
ENV HOST_NAME=broker
ARG test=True
ENV TESTING=$test

CMD ["python3", "wm_test.py"]