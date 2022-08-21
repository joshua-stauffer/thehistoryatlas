FROM alpine:3.16
RUN apk add --no-cache postgresql-client
WORKDIR /opt/provisioner/
COPY provision.sh /opt/provisioner/
COPY provision.sql /opt/provisioner/
CMD ["/bin/sh", "provision.sh"]
