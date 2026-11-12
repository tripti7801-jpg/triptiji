import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


# Keep the database in the same folder as this Python file.
DATABASE_PATH = Path(__file__).with_name("placements.db")
STATUS_OPTIONS = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def add_application(company_name, job_role, application_date, status):
    """Save one application to the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications (
                company_name, job_role, application_date, status
            )
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


def get_applications():
    """Return all applications, with the newest dates shown first."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        return connection.execute(
            """
            SELECT application_id, company_name, job_role,
                   application_date, status
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """
        ).fetchall()
    finally:
        connection.close()


def get_most_applied_role():
    """Return the most applied-for role and its count, or None if empty."""
    connection = sqlite3.connect(DATABASE_PATH)
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


def get_status_counts():
    """Return counts for the listed statuses, including statuses with no records."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        rows = connection.execute(
            """
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            """
        ).fetchall()
    finally:
        connection.close()

    counts = {status: 0 for status in STATUS_OPTIONS}
    for status, count in rows:
        # Include any status already stored that is not in the current menu.
        label = status if status is not None else "Unknown"
        counts[label] = count
    return counts


st.set_page_config(page_title="Placement Application Tracker")
st.title("Placement Application Tracker")

st.header("Add Application")
with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date", value=date.today())
    status = st.selectbox("Status", STATUS_OPTIONS)
    submitted = st.form_submit_button("Add Application")

if submitted:
    if not company_name.strip() or not job_role.strip():
        st.error("Please enter both a company name and a job role.")
    else:
        add_application(
            company_name.strip(),
            job_role.strip(),
            application_date.isoformat(),
            status,
        )
        st.success("Application added successfully!")

st.header("View Applications")
applications = get_applications()
if applications:
    applications_table = pd.DataFrame(
        applications,
        columns=[
            "Application ID",
            "Company Name",
            "Job Role",
            "Application Date",
            "Status",
        ],
    )
    st.dataframe(applications_table, width="stretch", hide_index=True)
else:
    st.info("No applications are available yet. Add your first application above.")

st.header("Application Summary")
st.metric("Total Applications", len(applications))

most_applied_role = get_most_applied_role()
if most_applied_role is None:
    st.write("Most Applied Role: No applications yet.")
else:
    role, application_count = most_applied_role
    st.write(f"Most Applied Role: **{role}** ({application_count} applications)")

st.subheader("Status-wise Summary")
status_counts = get_status_counts()
status_table = pd.DataFrame(
    [
        {"Status": status_name, "Applications": count}
        for status_name, count in status_counts.items()
    ]
)
st.dataframe(status_table, width="stretch", hide_index=True)
st.bar_chart(status_table, x="Status", y="Applications")
