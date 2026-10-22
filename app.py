"""Cricbuzz LiveStats - Streamlit entry point."""

import streamlit as st

from utils.db_connection import DB_PATH, get_connection, initialize_database

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")
initialize_database()

st.title("🏏 Cricbuzz LiveStats")
st.subheader("Real-time cricket insights and SQL-based analytics")
st.write(
    "Explore international Test, ODI, and T20I scorecards, player performance, "
    "live Cricbuzz API snapshots, and 25 SQL analytics exercises."
)

with get_connection() as connection:
    match_count = connection.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    player_count = connection.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    format_count = connection.execute("SELECT COUNT(DISTINCT format) FROM matches").fetchone()[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("International matches", f"{match_count:,}")
with col2:
    st.metric("Players", f"{player_count:,}")
with col3:
    st.metric("Formats", format_count)

st.info(f"SQLite database: `{DB_PATH}`. Historical ball-by-ball scorecards are from Cricsheet.")
st.caption(
    "Cricsheet data is licensed under the Open Data Commons Attribution License (ODC-By 1.0). "
    "See the dataset attribution in the README."
)
st.warning(
    "Live scores require your own Cricbuzz Cricket API subscription and RapidAPI key. "
    "Historical Cricsheet records are not live updates."
)
st.write("Use the page navigation to open Live Matches, Top Player Stats, SQL Analytics, or CRUD Management.")
st.markdown(
    "For setup and API configuration, see the project [README](README.md). "
    "Add your own RapidAPI key to `.env` to enable live scores."
)
