

import streamlit as st
import sqlite3
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Smart Student Productivity Assistant",
    page_icon="📚",
    layout="wide"
)

def recommend_task(priority, deadline):
    """Recommend urgency based on priority and deadline."""

    days_left = (date.fromisoformat(deadline) - date.today()).days

    if days_left < 0:
        return "Overdue — do this first"
    elif days_left == 0:
        return "Due today — do this first"
    elif priority == "High" and days_left <= 2:
        return "Urgent — high priority"
    elif priority == "High":
        return "High priority — plan soon"
    elif days_left <= 2:
        return "Deadline approaching"
    else:
        return "Can be scheduled later"


# Database connection
conn = sqlite3.connect("student_productivity.db")
cursor = conn.cursor()

# Create task table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    priority TEXT NOT NULL,
    deadline TEXT NOT NULL,
    completed INTEGER DEFAULT 0
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    hours REAL NOT NULL,
    study_date TEXT NOT NULL
)
""")
conn.commit()


st.title("📚 Smart Student Productivity Assistant")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Task Manager", "Study Analytics"]
)

if page == "Task Manager":
    st.header("📝 Task Manager")

    with st.form("add_task_form"):
        task = st.text_input("Task name")
        priority = st.selectbox(
            "Priority", ["High", "Medium", "Low"]
        )
        deadline = st.date_input(
            "Deadline", value=date.today()
        )
        submitted = st.form_submit_button("Add Task")

        if submitted:
            if task.strip():
                cursor.execute(
                    "INSERT INTO tasks (task, priority, deadline) VALUES (?, ?, ?)",
                    (task.strip(), priority, deadline.isoformat())
                )
                conn.commit()
                st.success("Task added successfully!")
                st.rerun()
            else:
                st.warning("Please enter a task name.")

    st.subheader("Your Tasks")

    cursor.execute(
        "SELECT id, task, priority, deadline, completed FROM tasks ORDER BY completed, deadline"
    )
    tasks = cursor.fetchall()

    if not tasks:
        st.info("No tasks yet. Add your first task above.")

    for task_id, task_name, priority, deadline, completed in tasks:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{task_name}**")
                
                st.write(f"Priority: {priority} | Deadline: {deadline}")
                st.write("Status: " + ("Completed" if completed else "Pending"))

                if not completed:
                    recommendation = recommend_task(priority, deadline)
                    st.info(f"💡 Recommendation: {recommendation}")


            with col2:
                if not completed:
                    if st.button("Complete", key=f"complete_{task_id}"):
                        cursor.execute(
                            "UPDATE tasks SET completed = 1 WHERE id = ?",
                            (task_id,)
                        )
                        conn.commit()
                        st.rerun()

                if st.button("Delete", key=f"delete_{task_id}"):
                    cursor.execute(
                        "DELETE FROM tasks WHERE id = ?", (task_id,)
                    )
                    conn.commit()
                    st.rerun()

elif page == "Dashboard":
    st.header("📊 Dashboard")

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
    completed = cursor.fetchone()[0]

    pending = total - completed
    progress = completed / total if total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", total)
    col2.metric("Completed", completed)
    col3.metric("Pending", pending)

    st.subheader("Overall Progress")
    st.progress(progress)
    st.write(f"{progress * 100:.1f}% completed")


elif page == "Study Analytics":
    st.header("📈 Study Analytics")

    # Form to record study sessions
    with st.form("study_form"):
        subject = st.text_input("Subject")
        hours = st.number_input(
            "Study hours",
            min_value=0.5,
            max_value=24.0,
            value=1.0,
            step=0.5
        )
        study_date = st.date_input(
            "Study date",
            value=date.today(),
            key="study_date"
        )

        submitted = st.form_submit_button("Record Study Session")

        if submitted:
            if subject.strip():
                cursor.execute(
                    """INSERT INTO study_sessions
                    (subject, hours, study_date)
                    VALUES (?, ?, ?)""",
                    (subject.strip(), hours, study_date.isoformat())
                )
                conn.commit()
                st.success("Study session recorded!")
                st.rerun()
            else:
                st.warning("Please enter a subject.")

    # Load saved sessions into a DataFrame
    df = pd.read_sql_query(
        "SELECT subject, hours, study_date FROM study_sessions",
        conn
    )

    if not df.empty:
        st.subheader("Your Study Statistics")

        total_hours = df["hours"].sum()
        total_sessions = len(df)

        col1, col2 = st.columns(2)
        col1.metric("Total Study Hours", f"{total_hours:.1f}")
        col2.metric("Study Sessions", total_sessions)

        # Hours studied per subject
        subject_hours = (
            df.groupby("subject")["hours"]
            .sum()
            .sort_values(ascending=False)
        )

        st.subheader("Study Hours by Subject")
        st.bar_chart(subject_hours)

        # Daily study trend
        daily_hours = (
            df.groupby("study_date")["hours"]
            .sum()
            .sort_index()
        )

        st.subheader("Daily Study Trend")
        st.line_chart(daily_hours)

        st.subheader("Recorded Sessions")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No study sessions yet. Record your first session above.")

conn.close()
