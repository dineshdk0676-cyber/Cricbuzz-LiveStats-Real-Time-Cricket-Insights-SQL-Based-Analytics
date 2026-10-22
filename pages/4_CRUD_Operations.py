from datetime import date
import sqlite3

import pandas as pd
import streamlit as st

from utils.db_connection import get_connection, initialize_database

initialize_database()
st.title("🛠️ CRUD Management")
st.caption("Manage player records. Changes are written to the local SQLite database.")

with get_connection() as connection:
    teams = connection.execute("SELECT id,name FROM teams ORDER BY name").fetchall()
    players = connection.execute(
        """SELECT p.id,p.name,t.name team,p.role,p.batting_style,p.bowling_style
        FROM players p JOIN teams t ON t.id=p.team_id ORDER BY p.name"""
    ).fetchall()
team_names = {row["name"]: row["id"] for row in teams}

st.subheader("Player records")
st.dataframe(pd.DataFrame([dict(row) for row in players]), hide_index=True, width="stretch")

add_tab, edit_tab, delete_tab = st.tabs(["Create", "Update", "Delete"])
with add_tab:
    with st.form("create_player"):
        name = st.text_input("Full name")
        team = st.selectbox("Team", list(team_names))
        role = st.selectbox("Playing role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
        batting_style = st.text_input("Batting style")
        bowling_style = st.text_input("Bowling style")
        submitted = st.form_submit_button("Add player")
        if submitted:
            if not name.strip():
                st.error("Player name is required.")
            else:
                try:
                    with get_connection() as connection:
                        connection.execute(
                            """INSERT INTO players(name,team_id,role,batting_style,bowling_style)
                            VALUES (?,?,?,?,?)""",
                            (name.strip(), team_names[team], role, batting_style.strip(), bowling_style.strip()),
                        )
                    st.success("Player added.")
                    st.rerun()
                except sqlite3.Error as exc:
                    st.error(f"Could not add player: {exc}")

with edit_tab:
    player_options = {f"{row['name']} (#{row['id']})": row for row in players}
    selected_player = st.selectbox("Select player to update", list(player_options), key="edit_player")
    current = player_options[selected_player]
    with st.form("update_player"):
        updated_name = st.text_input("Full name", value=current["name"])
        updated_team = st.selectbox(
            "Team", list(team_names), index=list(team_names).index(current["team"])
        )
        roles = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Unknown"]
        updated_role = st.selectbox("Playing role", roles, index=roles.index(current["role"]))
        updated_batting = st.text_input("Batting style", value=current["batting_style"] or "")
        updated_bowling = st.text_input("Bowling style", value=current["bowling_style"] or "")
        submitted = st.form_submit_button("Save changes")
        if submitted:
            if not updated_name.strip():
                st.error("Player name is required.")
            else:
                try:
                    with get_connection() as connection:
                        connection.execute(
                            """UPDATE players SET name=?,team_id=?,role=?,batting_style=?,bowling_style=?
                            WHERE id=?""",
                            (
                                updated_name.strip(),
                                team_names[updated_team],
                                updated_role,
                                updated_batting.strip(),
                                updated_bowling.strip(),
                                current["id"],
                            ),
                        )
                    st.success("Player updated.")
                    st.rerun()
                except sqlite3.Error as exc:
                    st.error(f"Could not update player: {exc}")

with delete_tab:
    delete_label = st.selectbox("Select player to delete", list(player_options), key="delete_player")
    target = player_options[delete_label]
    confirmed = st.checkbox(f"I understand this permanently deletes {target['name']}.")
    if st.button("Delete player", type="primary", disabled=not confirmed):
        try:
            with get_connection() as connection:
                connection.execute("DELETE FROM players WHERE id=?", (target["id"],))
            st.success("Player deleted.")
            st.rerun()
        except sqlite3.Error as exc:
            st.error(f"Could not delete player. Existing scorecard records may reference this player: {exc}")

st.divider()
st.subheader("Match records")
with get_connection() as connection:
    matches = connection.execute(
        """SELECT m.id,m.description,m.format,m.match_date,m.status,
        t1.name team1,t2.name team2,v.name venue
        FROM matches m JOIN teams t1 ON t1.id=m.team1_id
        JOIN teams t2 ON t2.id=m.team2_id JOIN venues v ON v.id=m.venue_id
        ORDER BY m.match_date DESC,m.id DESC"""
    ).fetchall()
    venues = connection.execute("SELECT id,name FROM venues ORDER BY name").fetchall()

st.dataframe(pd.DataFrame([dict(row) for row in matches]), hide_index=True, width="stretch")
match_create, match_edit, match_delete = st.tabs(["Create match", "Update match", "Delete match"])
with match_create:
    with st.form("create_match"):
        description = st.text_input("Match description")
        col_a, col_b = st.columns(2)
        with col_a:
            first_team = st.selectbox("Team 1", list(team_names), key="new_match_team1")
        with col_b:
            second_team = st.selectbox("Team 2", list(team_names), index=1, key="new_match_team2")
        venue_options = {row["name"]: row["id"] for row in venues}
        venue_name = st.selectbox("Venue", list(venue_options))
        match_format = st.selectbox("Format", ["Test", "ODI", "T20I"])
        match_date = st.date_input("Match date")
        match_status = st.selectbox("Status", ["Upcoming", "Live", "Completed", "Abandoned"])
        create_match = st.form_submit_button("Add match")
        if create_match:
            if not description.strip():
                st.error("Match description is required.")
            elif first_team == second_team:
                st.error("Select two different teams.")
            else:
                try:
                    with get_connection() as connection:
                        connection.execute(
                            """INSERT INTO matches
                            (description,format,match_date,status,team1_id,team2_id,venue_id)
                            VALUES (?,?,?,?,?,?,?)""",
                            (
                                description.strip(),
                                match_format,
                                match_date.isoformat(),
                                match_status,
                                team_names[first_team],
                                team_names[second_team],
                                venue_options[venue_name],
                            ),
                        )
                    st.success("Match added.")
                    st.rerun()
                except sqlite3.Error as exc:
                    st.error(f"Could not add match: {exc}")

with match_edit:
    match_options = {
        f"{row['match_date']} — {row['description']} (#{row['id']})": row for row in matches
    }
    selected_match = st.selectbox("Select match to update", list(match_options), key="edit_match")
    match = match_options[selected_match]
    with st.form("update_match"):
        updated_description = st.text_input("Match description", value=match["description"])
        team1_options = list(team_names)
        updated_team1 = st.selectbox(
            "Team 1", team1_options, index=team1_options.index(match["team1"]), key="updated_match_team1"
        )
        updated_team2 = st.selectbox(
            "Team 2", team1_options, index=team1_options.index(match["team2"]), key="updated_match_team2"
        )
        venue_options = {row["name"]: row["id"] for row in venues}
        updated_venue = st.selectbox(
            "Venue", list(venue_options), index=list(venue_options).index(match["venue"])
        )
        updated_format = st.selectbox(
            "Format", ["Test", "ODI", "T20I"], index=["Test", "ODI", "T20I"].index(match["format"])
        )
        updated_date = st.date_input(
            "Match date", value=date.fromisoformat(match["match_date"])
        )
        updated_status = st.selectbox(
            "Status",
            ["Upcoming", "Live", "Completed", "Abandoned"],
            index=["Upcoming", "Live", "Completed", "Abandoned"].index(match["status"]),
        )
        save_match = st.form_submit_button("Save match changes")
        if save_match:
            if not updated_description.strip():
                st.error("Match description is required.")
            elif updated_team1 == updated_team2:
                st.error("Select two different teams.")
            else:
                try:
                    with get_connection() as connection:
                        connection.execute(
                            """UPDATE matches SET description=?,format=?,match_date=?,status=?,
                            team1_id=?,team2_id=?,venue_id=? WHERE id=?""",
                            (
                                updated_description.strip(),
                                updated_format,
                                updated_date.isoformat(),
                                updated_status,
                                team_names[updated_team1],
                                team_names[updated_team2],
                                venue_options[updated_venue],
                                match["id"],
                            ),
                        )
                    st.success("Match updated.")
                    st.rerun()
                except sqlite3.Error as exc:
                    st.error(f"Could not update match: {exc}")

with match_delete:
    delete_match_label = st.selectbox(
        "Select match to delete", list(match_options), key="delete_match"
    )
    match_to_delete = match_options[delete_match_label]
    match_confirmed = st.checkbox(
        f"I understand this permanently deletes {match_to_delete['description']} and its scorecards."
    )
    if st.button("Delete match", type="primary", disabled=not match_confirmed):
        try:
            with get_connection() as connection:
                connection.execute("DELETE FROM matches WHERE id=?", (match_to_delete["id"],))
            st.success("Match and associated scorecard rows deleted.")
            st.rerun()
        except sqlite3.Error as exc:
            st.error(f"Could not delete match: {exc}")
