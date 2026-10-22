import json
import sqlite3

import pandas as pd
import streamlit as st

from utils.api_client import (
    CricbuzzAPIError,
    fetch_live_matches,
    get_latest_live_matches,
    save_live_matches,
)
from utils.db_connection import initialize_database

initialize_database()
st.title("🌐 Live Matches")
st.caption("Live data is requested from the configured Cricbuzz Cricket API. No sample score is presented as live.")

if st.button("Refresh live matches", type="primary"):
    try:
        payload = fetch_live_matches()
        saved_count = save_live_matches(payload)
    except CricbuzzAPIError as exc:
        st.error(str(exc))
    except sqlite3.Error as exc:
        st.error(f"Could not save live matches to the SQLite database: {exc}")
    else:
        st.success(f"Fetched and saved {saved_count} live match record(s) to SQLite.")

try:
    matches = get_latest_live_matches()
except sqlite3.Error as exc:
    st.error(f"Could not read saved live matches from the SQLite database: {exc}")
else:
    if matches:
        fetched_at = matches[0]["fetched_at"]
        st.caption(f"Most recent API snapshot (UTC): {fetched_at}")
        display_rows = []
        for match in matches:
            display_rows.append(
                {
                    "Match": match["match_description"],
                    "Team 1": match["team1"],
                    "Team 2": match["team2"],
                    "Format": match["match_format"],
                    "Status": match["status"],
                    "Venue": match["venue"],
                    "Start time": match["start_time"],
                }
            )
        st.dataframe(pd.DataFrame(display_rows), hide_index=True, width="stretch")
        with st.expander("View saved API response details"):
            for match in matches:
                st.markdown(f"**{match['match_description']}**")
                st.json(json.loads(match["response_json"]))
    else:
        st.info("No live API snapshots are stored yet. Configure your API key and refresh.")
        st.caption("The API key and account/subscription are supplied by you; none is bundled with this project.")

st.caption("Saved API snapshots are historical API responses, not a substitute for a continuously updating score feed.")
