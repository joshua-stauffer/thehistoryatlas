"""data_migration_populate_summary_columns

Revision ID: 0deb2c3901a6
Revises: e4f7a2d6b159
Create Date: 2025-05-20 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "0deb2c3901a6"
down_revision: Union[str, None] = "e4f7a2d6b159"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get a handle on the connection and create a session
    connection = op.get_bind()
    session = Session(bind=connection)

    try:
        # Update location data (latitude and longitude) from places table
        # Join path: summaries -> tag_instances -> tags -> places
        location_migration_sql = """
        UPDATE summaries
        SET 
            latitude = places.latitude,
            longitude = places.longitude
        FROM tag_instances
        JOIN tags ON tag_instances.tag_id = tags.id
        JOIN places ON places.id = tags.id
        WHERE 
            summaries.id = tag_instances.summary_id 
            AND tags.type = 'PLACE';
        """

        # Execute the location migration
        location_result = session.execute(text(location_migration_sql))
        print(f"Updated location data for {location_result.rowcount} summaries")

        # Update time data (datetime, calendar_model, and precision) from times table
        # Join path: summaries -> tag_instances -> tags -> times
        time_migration_sql = """
        UPDATE summaries
        SET 
            datetime = times.datetime,
            calendar_model = times.calendar_model,
            precision = times.precision
        FROM tag_instances
        JOIN tags ON tag_instances.tag_id = tags.id
        JOIN times ON times.id = tags.id
        WHERE 
            summaries.id = tag_instances.summary_id 
            AND tags.type = 'TIME';
        """

        # Execute the time migration
        time_result = session.execute(text(time_migration_sql))
        print(f"Updated time data for {time_result.rowcount} summaries")

        # Commit the changes
        session.commit()

        # Verify that there are no null values in the migrated columns
        verification_sql = """
        SELECT 
            COUNT(*) as total_summaries,
            COUNT(datetime) as datetime_count,
            COUNT(calendar_model) as calendar_model_count,
            COUNT(precision) as precision_count,
            COUNT(latitude) as latitude_count,
            COUNT(longitude) as longitude_count
        FROM summaries;
        """

        result = session.execute(text(verification_sql)).fetchone()
        total = result[0]
        datetime_count = result[1]
        calendar_model_count = result[2]
        precision_count = result[3]
        latitude_count = result[4]
        longitude_count = result[5]

        print(f"Migration verification results:")
        print(f"Total summaries: {total}")
        print(f"Summaries with datetime: {datetime_count}")
        print(f"Summaries with calendar_model: {calendar_model_count}")
        print(f"Summaries with precision: {precision_count}")
        print(f"Summaries with latitude: {latitude_count}")
        print(f"Summaries with longitude: {longitude_count}")

        # Check if any of the columns have null values
        if (
            datetime_count < total
            or calendar_model_count < total
            or precision_count < total
            or latitude_count < total
            or longitude_count < total
        ):
            print("WARNING: Some columns still have NULL values after migration.")

    except Exception as e:
        session.rollback()
        raise e


def downgrade() -> None:
    # This data migration doesn't need a downgrade function
    # The actual columns will be removed in the previous migration's downgrade function
    pass
