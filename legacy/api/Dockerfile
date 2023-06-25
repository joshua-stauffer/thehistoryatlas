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
ENV DEV_DB_URI=
ENV TESTING_DB_URI=
ENV BROKER_USERNAME=guest
ENV BROKER_PASS=guest
ENV DB_USERNAME=''
ENV DB_PASS=''
ENV RECV_QUEUE=
ENV SEND_QUEUE=
ENV DB_TIMEOUT=
ENV DB_RETRY=
CMD ["node", "/app/index.js"]