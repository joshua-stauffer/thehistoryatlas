FROM node:14
WORKDIR /app
COPY package*.json ./
RUN npm install 
# RUN npm ci --only=production <- for production use!
COPY dest/ .
ENV HOST_NAME=broker
ARG test=True
ENV TESTING=$test
ENV DEBUG=True
ENV CONFIG=DEV
ENV PROD_DB_URI=
# mongodb://<username>:<pass>@hostname(mongodb):27017:database name
#ENV DEV_DB_URI=mongodb://172.18.0.2:27017/tha-test
#ENV TESTING_DB_URI=mongodb://172.18.0.2:27017/tha-test
ENV TESTING_DB_URI=mongodb://mongodb:27017/readmodel
ENV DEV_DB_URI=mongodb://mongodb:27017/readmodel
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV DB_USERNAME=''
ENV DB_PASS=''
ENV RECV_QUEUE=
ENV SEND_QUEUE=
ENV DB_TIMEOUT=
ENV DB_RETRY=10
CMD ["node", "readModel.js"]