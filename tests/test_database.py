import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from database import (
    add_application,
    delete_application,
    get_applications,
    get_status_counts,
    get_upcoming_interviews,
    initialize_database,
    update_application_status,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def add_application(
        self, company, role, status, interview_date=None, application_date="2026-01-01"
    ):
        add_application(
            company,
            role,
            application_date,
            status,
            interview_date,
            self.database_path,
        )

    def test_migration_adds_interview_date_and_preserves_existing_record(self):
        legacy_path = Path(self.temporary_directory.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        connection.execute(
            """
            CREATE TABLE applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO applications (
                company_name, job_role, application_date, status
            )
            VALUES ('Existing Company', 'Analyst', '2026-01-01', 'Applied')
            """
        )
        connection.commit()
        connection.close()

        initialize_database(legacy_path)

        connection = sqlite3.connect(legacy_path)
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(applications)")
        }
        record = connection.execute(
            """
            SELECT company_name, job_role, application_date, status, interview_date
            FROM applications
            """
        ).fetchone()
        connection.close()

        self.assertIn("interview_date", columns)
        self.assertEqual(
            record,
            ("Existing Company", "Analyst", "2026-01-01", "Applied", None),
        )

    def test_search_and_status_filter(self):
        self.add_application("Acme Labs", "Analyst", "Applied")
        self.add_application("Acme Systems", "Engineer", "Interview Scheduled")
        self.add_application("Other Company", "Analyst", "Applied")

        results = get_applications(
            company_search="ACME",
            statuses=["Applied"],
            database_path=self.database_path,
        )

        self.assertEqual([row[1] for row in results], ["Acme Labs"])
        self.assertEqual(
            get_applications(statuses=[], database_path=self.database_path), []
        )

    def test_status_update_and_delete(self):
        self.add_application("Acme Labs", "Analyst", "Applied")
        application_id = get_applications(database_path=self.database_path)[0][0]

        self.assertTrue(
            update_application_status(
                application_id, "Shortlisted", self.database_path
            )
        )
        self.assertEqual(
            get_applications(database_path=self.database_path)[0][4], "Shortlisted"
        )
        self.assertTrue(delete_application(application_id, self.database_path))
        self.assertFalse(delete_application(application_id, self.database_path))
        self.assertEqual(get_applications(database_path=self.database_path), [])

    def test_upcoming_interviews_and_status_counts(self):
        today = date(2026, 11, 12)
        self.add_application(
            "Tomorrow Co",
            "Engineer",
            "Interview Scheduled",
            (today + timedelta(days=1)).isoformat(),
        )
        self.add_application(
            "Today Co",
            "Analyst",
            "Interview Scheduled",
            today.isoformat(),
        )
        self.add_application(
            "Past Co",
            "Designer",
            "Rejected",
            (today - timedelta(days=1)).isoformat(),
        )
        self.add_application("No Date Co", "Engineer", "Applied")

        upcoming = get_upcoming_interviews(
            today.isoformat(), database_path=self.database_path
        )

        self.assertEqual([row[1] for row in upcoming], ["Today Co", "Tomorrow Co"])
        self.assertEqual(
            get_status_counts(self.database_path),
            {"Applied": 1, "Interview Scheduled": 2, "Rejected": 1},
        )


if __name__ == "__main__":
    unittest.main()
