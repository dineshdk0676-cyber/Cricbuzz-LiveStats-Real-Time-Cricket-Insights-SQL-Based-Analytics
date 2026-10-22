# 🏏 Cricbuzz LiveStats

**Real-Time Cricket Insights & SQL-Based Analytics**

A Python and Streamlit cricket analytics dashboard with historical international scorecards, a SQLite database, 25 SQL analytics exercises, player and match management, and an optional Cricbuzz live-match API integration.

> **Historical data is not live data.** Historical scorecards are sourced from Cricsheet. Current live matches are requested separately from the Cricbuzz Cricket API via RapidAPI and require your own API subscription and key.

<!-- Replace USERNAME/REPOSITORY if you fork this project. -->
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=dineshdk0676-cyber/Cricbuzz-LiveStats-Real-Time-Cricket-Insights-SQL-Based-Analytics&branch=main&mainModule=app.py)

## Project overview

Cricbuzz LiveStats is an educational sports analytics project. It combines a Streamlit web interface, a relational SQLite database, historical scorecard data, SQL analysis, and an optional REST API feed for live matches.

### Main features

- **Home dashboard** with project overview and database summary.
- **Live Matches** page that fetches from the configured Cricbuzz Cricket API and stores timestamped API snapshots in SQLite.
- **Top Player Stats** with format-specific batting and bowling leaderboards.
- **SQL Analytics** with all 25 exercises from the project brief, plus a read-only custom SQL query runner.
- **CRUD Management** for player and match records, with confirmation before deletion.
- **SQLite database** containing historical match, innings, batting, bowling, and fielding records.

## Historical dataset

The included database is populated with **3,732 men's international matches** from Cricsheet's downloaded Test, ODI, and T20I JSON archives:

| Format | Matches |
| --- | ---: |
| Test | 896 |
| ODI | 2,596 |
| T20I | 240 |

The source ball-by-ball data is transformed into relational SQLite tables. Player roles and styles, venue seating capacities, and venue countries are not consistently provided by these archives; the application leaves unavailable facts unknown rather than inventing them. As a result, analytics that require those fields may return incomplete or empty results.

### Attribution and license

Historical data source: [Cricsheet downloads](https://cricsheet.org/downloads/), downloaded 2026-10-19.

- [Men's Test JSON archive](https://cricsheet.org/downloads/tests_male_json.zip)
- [Men's ODI JSON archive](https://cricsheet.org/downloads/odis_male_json.zip)
- [Men's T20I JSON archive](https://cricsheet.org/downloads/it20s_male_json.zip)

Cricsheet data is licensed under the [Open Data Commons Attribution License (ODC-By 1.0)](https://opendatacommons.org/licenses/by/1.0/). The source records have been transformed into relational SQLite tables. The source files and a local attribution notice are available in the project workspace; the public repository package includes the populated SQLite database and attribution notice.

## Run locally

### Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux

### Installation

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install packages and start the dashboard:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>.

The app uses `data/cricbuzz_real.db` by default. Its schema is initialized automatically if missing. Set `CRICBUZZ_DB_PATH` to use a different SQLite file.

## Enable Cricbuzz live matches

The live page uses the Cricbuzz Cricket API through RapidAPI. You must have your own account/subscription and API key; the project does not contain one.

1. Subscribe to the [Cricbuzz Cricket API on RapidAPI](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket) and check the current plan, quota, and endpoint access.
2. Copy `.env.example` to `.env`.
3. Set your key in `.env`:

   ```dotenv
   CRICBUZZ_API_KEY=your_rapidapi_key
   CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com
   CRICBUZZ_LIVE_PATH=/matches/v1/live
   ```

4. Restart Streamlit and choose **Live Matches → Refresh live matches**.

Keep `.env` private. It is ignored by Git. Never paste API keys into a public repository, screenshots, or chat. For Streamlit Community Cloud, configure the key as an app secret in the deployment settings rather than committing `.env`.

The API endpoint and its response are controlled by the provider and may change. The application reports request errors and stores recognized Cricbuzz match records as timestamped snapshots; these snapshots are historical API responses, not a continuously streaming score feed.

## Deploy on Streamlit Community Cloud

Use the **Open in Streamlit** badge near the top of this README or visit [Streamlit Community Cloud](https://share.streamlit.io/):

1. Sign in with GitHub and authorize the public repository.
2. Select this repository, the `main` branch, and `app.py`.
3. Deploy the app.
4. In the deployed app's **Settings → Secrets**, add your RapidAPI key if you want live matches:

   ```toml
   CRICBUZZ_API_KEY = "your_rapidapi_key"
   CRICBUZZ_API_HOST = "cricbuzz-cricket.p.rapidapi.com"
   CRICBUZZ_LIVE_PATH = "/matches/v1/live"
   ```

5. Save the settings and reboot the app.

The Streamlit deployment URL is assigned by Streamlit after deployment; the badge above opens the deployment flow and is not itself the running-app URL. Do not publish credentials in GitHub.

## SQL analytics

The 25 exercises cover:

- **Beginner (1–8):** player lookup, recent matches, run leaders, large venues, team wins, player roles, highest scores, and series.
- **Intermediate (9–16):** all-rounders, completed matches, format comparisons, home/away records, batting pairs, venue bowling, close matches, and yearly trends.
- **Advanced (17–25):** toss outcomes, economical bowlers, batting consistency, format averages, weighted rankings, head-to-head records, recent form, partnerships, and quarterly career trends.

Query definitions are in `utils/analytics_queries.py`. They use SQLite SQL and disclose assumptions for ambiguous requirements:

- Batting average is runs divided by dismissals; strike rate is runs per 100 balls.
- Bowling economy is runs conceded per six legal deliveries.
- Partnership scores use the sum of adjacent batters' individual runs, which is a proxy because the schema does not track every partnership ball.
- Form labels and career-trend thresholds are illustrative.
- The player ranking uses the weights in the project brief; unavailable components contribute zero.

## Database schema

The schema in `database/schema.sql` contains:

- `teams`, `players`, `venues`, and `series`
- `matches`
- `batting_innings`, `bowling_figures`, and `fielding_figures`
- `live_match_snapshots` for persisted API responses

The populated database is `data/cricbuzz_real.db`. `scripts/import_cricsheet.py` can recreate it from the original archives when those are available. The importer refuses to overwrite an existing database.

## Project structure

```text
app.py
pages/
  1_Live_Matches.py
  2_Top_Player_Stats.py
  3_SQL_Analytics.py
  4_CRUD_Operations.py
utils/
  analytics_queries.py
  api_client.py
  db_connection.py
  seed_data.py
database/
  schema.sql
data/
  cricbuzz_real.db
  CRICSHEET_ATTRIBUTION.txt
scripts/
  import_cricsheet.py
tests/
  test_project.py
```

## Tests

Run the project tests with:

```bash
python -m unittest discover -s tests -v
```

The tests cover the SQL exercises, sample database operations, CRUD basics, and persistence of parsed live API match records.

## Security and limitations

- SQLite is the supported database configuration in this version.
- The live API requires a separately configured RapidAPI credential and may have rate limits or subscription costs.
- Historical data is not a live Cricbuzz feed.
- The custom query page only accepts read-only `SELECT` or `WITH` queries; it is intended for local learning, not as a multi-user SQL security boundary.
- Add authentication, authorization, audit logs, and operational monitoring before exposing CRUD functions in a public production service.
- Historical match analysis is informational and does not guarantee future match outcomes.
