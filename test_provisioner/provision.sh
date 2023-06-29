#!bin/sh

echo 'Provisioning databases...'
# create roles and databases
echo '...building roles and databases'
psql $THA_DB_URI -f create_roles_and_dbs.sql
# add users
echo '...adding users'
psql $THA_DB_URI -c "CREATE USER tha_test_user WITH PASSWORD '$THA_TEST_PASSWORD';"

# permissions
echo '...setting permissions'
psql $THA_DB_URI -f provision.sql
echo '...provisioning complete.'
