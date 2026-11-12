import os
from datetime import date

import pandas as pd
import streamlit as st
from openai import OpenAI, OpenAIError
from streamlit.errors import StreamlitSecretNotFoundError

from database import (
    add_application,
    delete_application,
    get_applications,
    get_most_applied_role,
    get_status_counts,
    get_upcoming_interviews,
    initialize_database,
    update_application_status,
)


STATUS_OPTIONS = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]

initialize_database()
st.set_page_config(page_title="Placement Application Tracker")
st.title("Placement Application Tracker")

tracker_tab, chatbot_tab = st.tabs(["Applications", "Preparation Chatbot"])

with tracker_tab:
    st.header("Add Application")
    with st.form("add_application_form"):
        company_name = st.text_input("Company Name")
        job_role = st.text_input("Job Role")
        application_date = st.date_input("Application Date", value=date.today())
        status = st.selectbox("Status", STATUS_OPTIONS)
        interview_date = st.date_input("Interview Date (optional)", value=None)
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
                interview_date.isoformat() if interview_date else None,
            )
            st.success("Application added successfully!")

    applications = get_applications()

    if applications:
        application_labels = {
            row[0]: f"{row[0]} - {row[1]} - {row[2]}" for row in applications
        }

        with st.expander("Update an application status"):
            with st.form("update_status_form"):
                update_id = st.selectbox(
                    "Application",
                    options=list(application_labels),
                    format_func=lambda application_id: application_labels[application_id],
                )
                current_status = next(
                    row[4] for row in applications if row[0] == update_id
                )
                update_status = st.selectbox(
                    "New Status",
                    STATUS_OPTIONS,
                    index=(
                        STATUS_OPTIONS.index(current_status)
                        if current_status in STATUS_OPTIONS
                        else 0
                    ),
                )
                update_submitted = st.form_submit_button("Update Status")

            if update_submitted:
                if update_application_status(update_id, update_status):
                    st.success("Application status updated.")
                else:
                    st.error("The selected application could not be found.")

        with st.expander("Delete an application"):
            with st.form("delete_application_form"):
                delete_id = st.selectbox(
                    "Application to delete",
                    options=list(application_labels),
                    format_func=lambda application_id: application_labels[application_id],
                )
                confirm_delete = st.checkbox(
                    "I confirm that I want to permanently delete this application."
                )
                delete_submitted = st.form_submit_button("Delete Application")

            if delete_submitted:
                if not confirm_delete:
                    st.error("Confirm the deletion before continuing.")
                elif delete_application(delete_id):
                    st.success("Application deleted.")
                else:
                    st.error("The selected application could not be found.")

    applications = get_applications()
    st.header("View Applications")
    available_statuses = sorted(
        {
            row[4] if row[4] is not None else "Unknown"
            for row in applications
        }
        | set(STATUS_OPTIONS)
    )
    search_text = st.text_input("Search by Company Name")
    selected_statuses = st.multiselect(
        "Filter by Status",
        options=available_statuses,
        default=available_statuses,
    )
    filtered_applications = get_applications(search_text, selected_statuses)

    application_columns = [
        "Application ID",
        "Company Name",
        "Job Role",
        "Application Date",
        "Status",
        "Interview Date",
    ]
    if filtered_applications:
        applications_table = pd.DataFrame(
            filtered_applications, columns=application_columns
        )
        st.dataframe(applications_table, width="stretch", hide_index=True)
        st.download_button(
            "Download filtered applications as CSV",
            data=applications_table.to_csv(index=False).encode("utf-8-sig"),
            file_name="placement_applications.csv",
            mime="text/csv",
        )
    else:
        st.info("No applications match the selected search and status filters.")

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
    all_status_counts = {
        status_name: status_counts.get(status_name, 0)
        for status_name in STATUS_OPTIONS
    }
    all_status_counts.update(
        {
            status_name: count
            for status_name, count in status_counts.items()
            if status_name not in all_status_counts
        }
    )
    status_table = pd.DataFrame(
        [
            {"Status": status_name, "Applications": count}
            for status_name, count in all_status_counts.items()
        ]
    )
    st.dataframe(status_table, width="stretch", hide_index=True)
    st.bar_chart(status_table, x="Status", y="Applications")

    st.subheader("Upcoming Interview Dates")
    upcoming_interviews = get_upcoming_interviews()
    if upcoming_interviews:
        upcoming_table = pd.DataFrame(
            upcoming_interviews,
            columns=[
                "Application ID",
                "Company Name",
                "Job Role",
                "Interview Date",
                "Status",
            ],
        )
        st.dataframe(upcoming_table, width="stretch", hide_index=True)
    else:
        st.info("There are no upcoming interviews with a scheduled date.")


def get_openai_api_key():
    """Read the OpenAI key from the environment or Streamlit secrets."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("OPENAI_API_KEY")
    except StreamlitSecretNotFoundError:
        return None


with chatbot_tab:
    st.header("Placement Preparation Chatbot")
    st.caption("Chat history is kept for this Streamlit session only.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat_message in st.session_state.chat_history:
        with st.chat_message(chat_message["role"]):
            st.markdown(chat_message["content"])

    question = st.chat_input("Ask an interview or aptitude question")
    if question:
        api_key = get_openai_api_key()
        if not api_key:
            st.error(
                "OpenAI API key not found. Set OPENAI_API_KEY in your environment "
                "or add it to Streamlit secrets."
            )
        else:
            st.session_state.chat_history.append(
                {"role": "user", "content": question}
            )
            with st.chat_message("user"):
                st.markdown(question)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful placement preparation tutor. Give "
                        "practical interview guidance, create aptitude practice "
                        "questions when asked, and explain technical concepts "
                        "clearly for students."
                    ),
                },
                *st.session_state.chat_history,
            ]

            try:
                with st.chat_message("assistant"):
                    with st.spinner("Preparing a helpful answer..."):
                        client = OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                        )
                    answer = response.choices[0].message.content
                    if answer:
                        st.markdown(answer)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": answer}
                        )
                    else:
                        st.error("The AI returned an empty response.")
            except OpenAIError as error:
                st.error(f"OpenAI request failed: {error}")
