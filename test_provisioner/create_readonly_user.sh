#!/bin/sh

# Script to create a read-only PostgreSQL role and user

# Default values
DEFAULT_ROLE="tha_read_only"
DEFAULT_USER="tha_read_only"
DEFAULT_PASSWORD="z6JkOUhf8Z21rHDJ"
DEFAULT_DATABASE="postgres"
DEFAULT_DB_URI="postgresql://postgres:4f6WxSSoYVSWTVp3QVovWnzLTeCkj9HZ@localhost:5432"

# Use arguments if provided, otherwise use defaults
DB_URI="${1:-$DEFAULT_DB_URI}"
ROLE="${2:-$DEFAULT_ROLE}"
USER="${3:-$DEFAULT_USER}"
PASSWORD="${4:-$DEFAULT_PASSWORD}"
DATABASE="${5:-$DEFAULT_DATABASE}"

# Print configuration
echo "Creating read-only role and user with the following settings:"
echo "  Database URI: $DB_URI"
echo "  Role: $ROLE"
echo "  User: $USER"
echo "  Password: $PASSWORD"
echo "  Database: $DATABASE"
echo ""

# Create temporary SQL file with substituted values
TMP_SQL_FILE=$(mktemp)
sed -e "s/{{ROLE}}/$ROLE/g" \
    -e "s/{{USER}}/$USER/g" \
    -e "s/{{PASSWORD}}/$PASSWORD/g" \
    -e "s/{{DATABASE}}/$DATABASE/g" \
    "$(dirname "$0")/create_readonly_role.sql" > "$TMP_SQL_FILE"

# Execute the SQL file
echo "Executing SQL..."
psql "$DB_URI" -f "$TMP_SQL_FILE"
RESULT=$?

# Clean up
rm -f "$TMP_SQL_FILE"

# Exit with the psql result code
if [ $RESULT -eq 0 ]; then
    echo "✅ Successfully created read-only role and user"
else
    echo "❌ Error creating read-only role and user (exit code: $RESULT)"
fi

exit $RESULT 