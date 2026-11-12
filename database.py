import os
import sqlite3
from datetime import date
from pathlib import Path


DATABASE_PATH = Path(
    os.environ.get(
        "PLACEMENTS_DB_PATH", Path(__file__).with_name("placements.db")
    )
)


def initialize_database(database_path=DATABASE_PATH):
    """Create the applications table and add new columns to older databases."""
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT,
                interview_date TEXT
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(applications)")
        }
        if "interview_date" not in columns:
            connection.execute(
                "ALTER TABLE applications ADD COLUMN interview_date TEXT"
            )

        connection.commit()
    finally:
        connection.close()


def add_application(
    company_name,
    job_role,
    application_date,
    status,
    interview_date=None,
    database_path=DATABASE_PATH,
):
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            INSERT INTO applications (
                company_name, job_role, application_date, status, interview_date
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                company_name,
                job_role,
                application_date,
                status,
                interview_date,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_applications(
    company_search="", statuses=None, database_path=DATABASE_PATH
):
    query = """
        SELECT application_id, company_name, job_role,
               application_date, status, interview_date
        FROM applications
    """
    conditions = []
    parameters = []

    if company_search:
        conditions.append("company_name LIKE ? COLLATE NOCASE")
        parameters.append(f"%{company_search}%")

    if statuses is not None:
        include_unknown = "Unknown" in statuses
        selected_statuses = [status for status in statuses if status != "Unknown"]
        if include_unknown and selected_statuses:
            placeholders = ", ".join("?" for _ in selected_statuses)
            conditions.append(f"(status IS NULL OR status IN ({placeholders}))")
            parameters.extend(selected_statuses)
        elif include_unknown:
            conditions.append("status IS NULL")
        elif selected_statuses:
            placeholders = ", ".join("?" for _ in selected_statuses)
            conditions.append(f"status IN ({placeholders})")
            parameters.extend(selected_statuses)
        else:
            return []

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY application_date DESC, application_id DESC"

    connection = sqlite3.connect(database_path)
    try:
        return connection.execute(query, parameters).fetchall()
    finally:
        connection.close()


def update_application_status(application_id, status, database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.execute(
            "UPDATE applications SET status = ? WHERE application_id = ?",
            (status, application_id),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def delete_application(application_id, database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.execute(
            "DELETE FROM applications WHERE application_id = ?",
            (application_id,),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def get_most_applied_role(database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    try:
        return connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC,
                     job_role COLLATE NOCASE ASC,
                     job_role ASC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()


def get_status_counts(database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status"
        ).fetchall()
    finally:
        connection.close()

    return {
        status if status is not None else "Unknown": count
        for status, count in rows
    }


def get_upcoming_interviews(today=None, database_path=DATABASE_PATH):
    if today is None:
        today = date.today().isoformat()

    connection = sqlite3.connect(database_path)
    try:
        return connection.execute(
            """
            SELECT application_id, company_name, job_role,
                   interview_date, status
            FROM applications
            WHERE interview_date IS NOT NULL AND interview_date >= ?
            ORDER BY interview_date ASC, application_id ASC
            """,
            (today,),
        ).fetchall()
    finally:
        connection.close()
