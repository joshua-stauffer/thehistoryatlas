#!bin/sh

echo 'Provisioning databases...'
# create roles and databases
echo '...building roles and databases'
psql $THA_DB_URI -f create_roles_and_dbs.sql
# add users
echo '...adding users'
psql $THA_DB_URI -c "CREATE USER readmodel_service WITH PASSWORD '$READMODEL_SERVICE_PASSWORD';"
psql $THA_DB_URI -c "CREATE USER writemodel_service WITH PASSWORD '$WRITEMODEL_SERVICE_PASSWORD';"
psql $THA_DB_URI -c "CREATE USER accounts_service WITH PASSWORD '$ACCOUNTS_SERVICE_PASSWORD';"
psql $THA_DB_URI -c "CREATE USER geo_service WITH PASSWORD '$GEO_SERVICE_PASSWORD';"
psql $THA_DB_URI -c "CREATE USER nlp_service WITH PASSWORD '$NLP_SERVICE_PASSWORD';"
psql $THA_DB_URI -c "CREATE USER eventstore_service WITH PASSWORD '$EVENTSTORE_SERVICE_PASSWORD';"
# permissions
echo '...setting permissions'
psql $THA_DB_URI -f provision.sql
echo '...provisioning complete.'
