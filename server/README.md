# The History Atlas Server

## Database Migrations with Alembic

The History Atlas server uses Alembic for database migration management. This allows us to track and apply schema changes consistently across all environments.

### Setting Up

1. Make sure you have the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Set the database connection environment variable:
   ```
   export THA_DB_URI=postgresql://username:password@localhost:5432/dbname
   ```

### Running Migrations

To apply all pending migrations to bring your database to the latest schema version:

```bash
# From the server directory
alembic upgrade head
```

Or you can use the helper script:

```bash
# From the project root
./run_migrations.sh
```

### Creating New Migrations

To create a new migration after changing the SQLAlchemy models:

```bash
# From the server directory
alembic revision --autogenerate -m "Description of your changes"
```

This will automatically generate a migration script based on the differences between your models and the current database schema.

### Migration Commands

- `alembic current`: Show current revision
- `alembic history`: Show migration history
- `alembic upgrade +1`: Apply the next migration
- `alembic downgrade -1`: Rollback the last migration
- `alembic upgrade <revision>`: Apply migrations up to a specific revision
- `alembic downgrade <revision>`: Rollback migrations down to a specific revision

### Manual Migrations

To create a manual migration (without auto-generation):

```bash
alembic revision -m "Description of your manual migration"
```

Then edit the generated file in `alembic/versions/` to add your specific migration logic. 