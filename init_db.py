import sqlite3
from pathlib import Path


# Keep the database in the same folder as this Python file.
DATABASE_PATH = Path(__file__).with_name("placements.db")


def main():
    # Connect to the database (SQLite creates the file if it is missing).
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        # Create the applications table only when it does not already exist.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT
            )
            """
        )

        # Save the table creation to the database.
        connection.commit()
    finally:
        # Always close the database connection when finished.
        connection.close()

    print("Database and table created successfully!")


if __name__ == "__main__":
    main()
