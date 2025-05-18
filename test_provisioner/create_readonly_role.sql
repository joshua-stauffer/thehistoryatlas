-- SQL script to create a read-only role and user
-- This script creates a PostgreSQL role with read-only permissions on a database and assigns it to a user
-- 
-- Usage:
--   1. Replace the placeholders with actual values:
--      sed -e 's/{{ROLE}}/your_role/g' -e 's/{{USER}}/your_user/g' -e 's/{{PASSWORD}}/your_password/g' -e 's/{{DATABASE}}/your_database/g' create_readonly_role.sql > temp.sql
--   2. Run the resulting SQL file:
--      psql "connection-string" -f temp.sql
--   3. Or directly with provided values:
--      export ROLE=your_role USER=your_user PASSWORD=your_password DATABASE=your_database
--      sed -e "s/{{ROLE}}/$ROLE/g" -e "s/{{USER}}/$USER/g" -e "s/{{PASSWORD}}/$PASSWORD/g" -e "s/{{DATABASE}}/$DATABASE/g" create_readonly_role.sql | psql "connection-string"

-- Create role if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{{ROLE}}') THEN
    CREATE ROLE "{{ROLE}}";
  END IF;
END $$;

-- Create user if it doesn't exist (or update password)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{{USER}}') THEN
    CREATE USER "{{USER}}" WITH PASSWORD '{{PASSWORD}}';
  ELSE
    ALTER USER "{{USER}}" WITH PASSWORD '{{PASSWORD}}';
  END IF;
END $$;

-- Grant role to user if they're different
DO $$
BEGIN
  IF '{{ROLE}}' <> '{{USER}}' THEN
    GRANT "{{ROLE}}" TO "{{USER}}";
  END IF;
END $$;

-- Grant read-only permissions
-- Connect to the database
GRANT CONNECT ON DATABASE "{{DATABASE}}" TO "{{ROLE}}";

-- Schema usage
GRANT USAGE ON SCHEMA public TO "{{ROLE}}";

-- Table read permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{{ROLE}}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "{{ROLE}}";

-- Sequence usage
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO "{{ROLE}}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO "{{ROLE}}";

-- Explicitly revoke write permissions
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM "{{ROLE}}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE INSERT, UPDATE, DELETE ON TABLES FROM "{{ROLE}}";
REVOKE CREATE ON SCHEMA public FROM "{{ROLE}}"; 