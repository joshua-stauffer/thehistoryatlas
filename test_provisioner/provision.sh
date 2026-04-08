#!/bin/sh

# Print all arguments for debugging
printf "Argument 1 (DB_URI): %s\n" "$1"
printf "Argument 2 (PASSWORD): %s\n" "$2"
printf "Argument 3 (USER): %s\n" "$3"
printf "Argument 4 (DB_NAME): %s\n" "$4"
printf "Argument 5 (ROLE): %s\n" "$5"

# Default values from environment variables or hardcoded defaults
DB_URI="$1"  # Use first argument directly
DB_PASSWORD="$2"  # Use second argument directly
DB_USER="$3"
DB_NAME="$4"
DB_ROLE="$5"

# If no arguments provided, fall back to environment variables or defaults
if [ -z "$DB_URI" ]; then DB_URI="$THA_DB_URI"; fi
if [ -z "$DB_PASSWORD" ]; then DB_PASSWORD="$THA_TEST_PASSWORD"; fi
if [ -z "$DB_USER" ]; then DB_USER="tha_test_user"; fi
if [ -z "$DB_NAME" ]; then DB_NAME="tha_test_db"; fi
if [ -z "$DB_ROLE" ]; then DB_ROLE="readwrite_tha_test"; fi

# Export variables for SQL scripts to use
export DB_USER DB_NAME DB_ROLE

echo "Final configuration:"
echo "Using database URI: $DB_URI"
echo "Using database name: $DB_NAME"
echo "Using role: $DB_ROLE"
echo "Using user: $DB_USER"

echo 'Provisioning databases...'
# create roles and databases
echo '...building roles and databases'
psql "$DB_URI" -f create_roles_and_dbs.sql

# add users
echo '...adding users'
psql "$DB_URI" -c "DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;"

# permissions
echo '...setting permissions'
psql "$DB_URI" -f provision.sql
echo '...provisioning complete.'
