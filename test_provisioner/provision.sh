#!/bin/sh
set -e  # Exit on error

echo 'Provisioning databases...'
# create roles and databases
echo '...building roles and databases'
psql $THA_DB_URI -f create_roles_and_dbs.sql || { echo "Failed to create roles and databases"; exit 1; }

# add users
echo '...adding users'
psql $THA_DB_URI -c "CREATE USER tha_test_user WITH PASSWORD '$THA_TEST_PASSWORD';" || { echo "Failed to create user"; exit 1; }

# permissions
echo '...setting permissions'
psql $THA_DB_URI -f provision.sql || { echo "Failed to set permissions"; exit 1; }
echo '...provisioning complete.'
