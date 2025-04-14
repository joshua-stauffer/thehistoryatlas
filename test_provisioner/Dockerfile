FROM alpine:3.16
RUN apk add --no-cache postgresql-client
WORKDIR /opt/provisioner/
COPY provision.sh /opt/provisioner/
COPY create_roles_and_dbs.sql /opt/provisioner/
COPY provision.sql /opt/provisioner/

# Add a wrapper script that waits for PostgreSQL to be ready
RUN echo '#!/bin/sh\n\
echo "Waiting for PostgreSQL to be ready..."\n\
until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -c "\\q" 2>/dev/null; do\n\
  echo "PostgreSQL is unavailable - sleeping 2s"\n\
  sleep 2\n\
done\n\
echo "PostgreSQL is ready - executing provision.sh"\n\
/bin/sh provision.sh\n' > /opt/provisioner/wait-for-postgres.sh && \
chmod +x /opt/provisioner/wait-for-postgres.sh

CMD ["/bin/sh", "/opt/provisioner/wait-for-postgres.sh"]
