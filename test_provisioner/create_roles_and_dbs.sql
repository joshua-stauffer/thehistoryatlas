\set ON_ERROR_STOP off
\set db_name `echo "$DB_NAME"`
\set role_name `echo "$DB_ROLE"`

CREATE DATABASE :"db_name";
CREATE ROLE :"role_name";
