#!bin/sh

echo 'Provisioning databases...'

# eventstore
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'eventstore'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE eventstore"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_eventstore'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_eventstore"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'eventstore_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER eventstore_service WITH PASSWORD '$EVENTSTORE_SERVICE_PASSWORD'"
#
## readmodel
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'readmodel'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE readmodel"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_readmodel'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_readmodel"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readmodel_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER readmodel_service WITH PASSWORD '$READMODEL_SERVICE_PASSWORD'"
#
## writemodel
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'writemodel'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE writemodel"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_writemodel'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_writemodel"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'writemodel_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER writemodel_service WITH PASSWORD '$WRITEMODEL_SERVICE_PASSWORD'"
#
## accounts
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'accounts'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE accounts"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_accounts'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_accounts"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'accounts_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER accounts_service WITH PASSWORD '$ACCOUNTS_SERVICE_PASSWORD'"
#
## geo
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'geo'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE geo"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_geo'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_geo"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'geo_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER geo_service WITH PASSWORD '$GEO_SERVICE_PASSWORD'"
#
## nlp
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_database WHERE datname = 'nlp'" | grep -q 1 || psql $THA_DB_URI "CREATE DATABASE nlp"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'readwrite_nlp'" | grep -q 1 || psql $THA_DB_URI "CREATE ROLE readwrite_nlp"
#psql $THA_DB_URI -tc "SELECT 1 FROM pg_roles WHERE rolname = 'nlp_service'" | grep -q 1 || psql $THA_DB_URI "CREATE USER nlp_service WITH PASSWORD '$NLP_SERVICE_PASSWORD'"

# permissions
psql $THA_DB_URI -f provision.sql
echo '...provisioning complete.'