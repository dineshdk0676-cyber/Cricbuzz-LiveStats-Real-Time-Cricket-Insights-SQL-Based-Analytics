import pandas as pd
import streamlit as st

from utils.db_connection import get_connection, initialize_database

initialize_database()
st.title("📊 Top Player Stats")
st.caption("Leaderboard values below are calculated from the included synthetic demo dataset.")
formats = ["All formats", "Test", "ODI", "T20I"]
selected_format = st.selectbox("Format", formats)
format_filter = "" if selected_format == "All formats" else "WHERE m.format=?"
params = () if not format_filter else (selected_format,)

with get_connection() as connection:
    batting = connection.execute(
        f"""SELECT p.name,t.name team,SUM(b.runs) runs,
        ROUND(1.0*SUM(b.runs)/NULLIF(SUM(b.is_out),0),2) average,
        ROUND(100.0*SUM(b.runs)/NULLIF(SUM(b.balls_faced),0),2) strike_rate,
        COUNT(DISTINCT m.id) matches
        FROM batting_innings b JOIN players p ON p.id=b.player_id
        JOIN teams t ON t.id=b.team_id JOIN matches m ON m.id=b.match_id
        {format_filter} GROUP BY p.id ORDER BY runs DESC LIMIT 10""",
        params,
    ).fetchall()
    bowling = connection.execute(
        f"""SELECT p.name,t.name team,SUM(b.wickets) wickets,
        ROUND(6.0*SUM(b.runs_conceded)/NULLIF(SUM(b.balls_bowled),0),2) economy,
        COUNT(DISTINCT m.id) matches FROM bowling_figures b
        JOIN players p ON p.id=b.player_id JOIN teams t ON t.id=b.team_id
        JOIN matches m ON m.id=b.match_id {format_filter}
        GROUP BY p.id ORDER BY wickets DESC,economy LIMIT 10""",
        params,
    ).fetchall()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Leading run scorers")
    st.dataframe(pd.DataFrame([dict(row) for row in batting]), hide_index=True, width="stretch")
with col2:
    st.subheader("Leading wicket takers")
    st.dataframe(pd.DataFrame([dict(row) for row in bowling]), hide_index=True, width="stretch")
