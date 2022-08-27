#!bin/sh

echo 'Provisioning databases...'
# permissions
psql $THA_DB_URI -f provision.sql
echo '...provisioning complete.'
