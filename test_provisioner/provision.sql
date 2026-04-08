\set db_name `echo "$DB_NAME"`
\set role_name `echo "$DB_ROLE"`
\set user_name `echo "$DB_USER"`

GRANT CONNECT ON DATABASE :"db_name" TO :"role_name";
GRANT USAGE, CREATE ON SCHEMA public TO :"role_name";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"role_name";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"role_name";
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO :"role_name";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO :"role_name";
ALTER DATABASE :"db_name" SET timezone TO 'UTC';
GRANT :"role_name" TO :"user_name";

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;

