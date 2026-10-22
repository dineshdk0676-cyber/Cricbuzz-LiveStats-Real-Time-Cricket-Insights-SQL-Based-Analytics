import sqlite3

import pandas as pd
import streamlit as st

from utils.analytics_queries import QUERIES
from utils.db_connection import get_connection, initialize_database

initialize_database()
st.title("🧮 SQL Queries & Analytics")
st.caption("The 25 exercises from the project brief, implemented for the included SQLite schema.")

labels = [f"Q{number}: {title}" for number, (title, _) in QUERIES.items()]
selected = st.selectbox("Choose a documented query", labels)
number = int(selected.split(":")[0][1:])
_, sql = QUERIES[number]
with st.expander("View SQL"):
    st.code(sql, language="sql")

try:
    with get_connection() as connection:
        rows = connection.execute(sql).fetchall()
except sqlite3.Error as exc:
    st.error(f"Query {number} could not be executed: {exc}")
else:
    if rows:
        st.dataframe(pd.DataFrame([dict(row) for row in rows]), hide_index=True, width="stretch")
    else:
        st.info("This query returned no rows for the current dataset. Try another exercise or add more data.")
    st.caption(f"{len(rows)} result row(s)")

with st.expander("Run a read-only custom query"):
    custom_sql = st.text_area("Enter a SELECT or WITH ... SELECT statement", height=140)
    if st.button("Run custom query"):
        normalized = custom_sql.strip().lower()
        if not (normalized.startswith("select ") or normalized.startswith("with ")):
            st.error("Only SELECT or WITH queries are permitted.")
        elif ";" in custom_sql.rstrip().rstrip(";"):
            st.error("Run one statement at a time; multiple statements are not permitted.")
        else:
            try:
                with get_connection() as connection:
                    connection.execute("PRAGMA query_only = ON")
                    custom_rows = connection.execute(custom_sql).fetchall()
                st.dataframe(
                    pd.DataFrame([dict(row) for row in custom_rows]),
                    hide_index=True,
                    width="stretch",
                )
            except sqlite3.Error as exc:
                st.error(f"Custom query failed: {exc}")
