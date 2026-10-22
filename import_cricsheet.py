"""Import Cricsheet men's international JSON archives into a standalone SQLite database."""

from __future__ import annotations

import json
import sqlite3
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"
ARCHIVES = (
    ROOT / "data" / "tests_male_json.zip",
    ROOT / "data" / "odis_male_json.zip",
    ROOT / "data" / "it20s_male_json.zip",
)
DATABASE_PATH = ROOT / "data" / "cricbuzz_real.db"
NON_BOWLER_DISMISSALS = {
    "retired hurt",
    "retired out",
    "obstructing the field",
    "run out",
    "hit the ball twice",
}
NON_DISMISSALS = {"retired hurt", "obstructing the field"}


def get_or_create_team(connection: sqlite3.Connection, teams: dict[str, int], name: str) -> int:
    if name not in teams:
        cursor = connection.execute(
            "INSERT INTO teams(name,country) VALUES (?,?)", (name, name)
        )
        teams[name] = cursor.lastrowid
    return teams[name]


def get_or_create_player(
    connection: sqlite3.Connection,
    players: dict[tuple[str, str], int],
    team_id: int,
    team_name: str,
    name: str,
) -> int:
    key = (team_name, name)
    if key not in players:
        cursor = connection.execute(
            """INSERT INTO players(name,team_id,role,batting_style,bowling_style)
            VALUES (?,?, 'Unknown',NULL,NULL)""",
            (name, team_id),
        )
        players[key] = cursor.lastrowid
    return players[key]


def import_match(
    connection: sqlite3.Connection,
    filename: str,
    match: dict[str, Any],
    teams: dict[str, int],
    players: dict[tuple[str, str], int],
    venues: dict[tuple[str, str], int],
    series: dict[tuple[str, int], int],
) -> bool:
    info = match["info"]
    team_names = info.get("teams", [])
    if len(team_names) != 2:
        return False

    team1_name, team2_name = team_names
    team1_id = get_or_create_team(connection, teams, team1_name)
    team2_id = get_or_create_team(connection, teams, team2_name)
    match_type = info.get("match_type")
    match_format = {"IT20": "T20I", "ODM": "ODI", "MDM": "Test"}.get(match_type, match_type)
    if match_format not in {"Test", "ODI", "T20I"}:
        return False

    match_date = info.get("dates", [""])[0]
    if not match_date:
        return False
    city = info.get("city") or "Unknown"
    venue_name = info.get("venue") or "Unknown venue"
    venue_key = (venue_name, city)
    if venue_key not in venues:
        cursor = connection.execute(
            "INSERT INTO venues(name,city,country,capacity) VALUES (?,?,?,0)",
            (venue_name, city, "Unknown"),
        )
        venues[venue_key] = cursor.lastrowid

    event = info.get("event") or {}
    series_name = event.get("name") if isinstance(event, dict) else str(event)
    year = int(match_date[:4])
    series_id = None
    if series_name:
        series_key = (series_name, year)
        if series_key not in series:
            cursor = connection.execute(
                """INSERT INTO series(name,host_country,format,start_date,planned_matches)
                VALUES (?,?,?,?,0)""",
                (series_name, "Unknown", match_format, match_date),
            )
            series[series_key] = cursor.lastrowid
        series_id = series[series_key]

    toss = info.get("toss") or {}
    outcome = info.get("outcome") or {}
    winner_name = outcome.get("winner")
    winner_id = get_or_create_team(connection, teams, winner_name) if winner_name else None
    margin = outcome.get("by") or {}
    run_margin = margin.get("runs")
    wicket_margin = margin.get("wickets")
    status = "Completed"
    if outcome.get("result") in {"no result", "abandoned"}:
        status = "Abandoned"
    elif winner_id is None and outcome.get("result") == "tie":
        status = "Completed"

    description = f"Cricsheet {filename.removesuffix('.json')}: {team1_name} vs {team2_name}"
    cursor = connection.execute(
        """INSERT INTO matches
        (series_id,format,description,team1_id,team2_id,venue_id,match_date,status,
         toss_winner_team_id,toss_decision,winner_team_id,win_margin_runs,win_margin_wickets)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            series_id,
            match_format,
            description,
            team1_id,
            team2_id,
            venues[venue_key],
            match_date,
            status,
            get_or_create_team(connection, teams, toss["winner"]) if toss.get("winner") else None,
            toss.get("decision"),
            winner_id,
            run_margin,
            wicket_margin,
        ),
    )
    match_id = cursor.lastrowid

    for innings_no, innings in enumerate(match.get("innings", []), start=1):
        batting_team = innings.get("team")
        if batting_team not in team_names:
            continue
        bowling_team = team2_name if batting_team == team1_name else team1_name
        batting_team_id = get_or_create_team(connection, teams, batting_team)
        bowling_team_id = get_or_create_team(connection, teams, bowling_team)
        batter_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"runs": 0, "balls": 0, "outs": 0, "position": 0}
        )
        bowler_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"balls": 0, "runs": 0, "wickets": 0}
        )
        fielding_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"catches": 0, "stumpings": 0, "run_outs": 0}
        )
        batting_order: list[str] = []
        for over in innings.get("overs", []):
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")
                non_striker = delivery.get("non_striker")
                bowler = delivery.get("bowler")
                if batter and batter not in batting_order:
                    batting_order.append(batter)
                if non_striker and non_striker not in batting_order:
                    batting_order.append(non_striker)

                runs = delivery.get("runs") or {}
                extras = delivery.get("extras") or {}
                batter_stats[batter]["runs"] += int(runs.get("batter", 0))
                if "wides" not in extras:
                    batter_stats[batter]["balls"] += 1

                legal_ball = "wides" not in extras and "noballs" not in extras
                bowler_stats[bowler]["balls"] += int(legal_ball)
                bowler_stats[bowler]["runs"] += (
                    int(runs.get("total", 0))
                    - int(extras.get("byes", 0))
                    - int(extras.get("legbyes", 0))
                    - int(extras.get("penalty", 0))
                )

                for wicket in delivery.get("wickets", []):
                    dismissed = wicket.get("player_out")
                    dismissal_kind = wicket.get("kind", "").lower()
                    if dismissed:
                        batter_stats[dismissed]["outs"] += int(dismissal_kind not in NON_DISMISSALS)
                    if dismissal_kind not in NON_BOWLER_DISMISSALS:
                        bowler_stats[bowler]["wickets"] += 1
                    for fielder in wicket.get("fielders", []):
                        fielder_name = fielder.get("name") if isinstance(fielder, dict) else fielder
                        if not fielder_name:
                            continue
                        field_team_id = get_or_create_team(connection, teams, bowling_team)
                        get_or_create_player(
                            connection, players, field_team_id, bowling_team, fielder_name
                        )
                        if dismissal_kind == "caught":
                            fielding_stats[fielder_name]["catches"] += 1
                        elif dismissal_kind == "stumped":
                            fielding_stats[fielder_name]["stumpings"] += 1
                        elif dismissal_kind == "run out":
                            fielding_stats[fielder_name]["run_outs"] += 1

        for batting_position, name in enumerate(batting_order, start=1):
            player_id = get_or_create_player(
                connection, players, batting_team_id, batting_team, name
            )
            stats = batter_stats[name]
            connection.execute(
                """INSERT INTO batting_innings
                (match_id,player_id,team_id,innings_no,batting_position,runs,balls_faced,is_out)
                VALUES (?,?,?,?,?,?,?,?)""",
                (
                    match_id,
                    player_id,
                    batting_team_id,
                    innings_no,
                    batting_position,
                    stats["runs"],
                    stats["balls"],
                    min(stats["outs"], 1),
                ),
            )
        for name, stats in bowler_stats.items():
            if not name:
                continue
            player_id = get_or_create_player(
                connection, players, bowling_team_id, bowling_team, name
            )
            connection.execute(
                """INSERT INTO bowling_figures
                (match_id,player_id,team_id,innings_no,balls_bowled,runs_conceded,wickets)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    match_id,
                    player_id,
                    bowling_team_id,
                    innings_no,
                    stats["balls"],
                    max(stats["runs"], 0),
                    stats["wickets"],
                ),
            )
        for name, stats in fielding_stats.items():
            player_id = get_or_create_player(
                connection, players, bowling_team_id, bowling_team, name
            )
            connection.execute(
                """INSERT INTO fielding_figures
                (match_id,player_id,innings_no,catches,stumpings,run_outs)
                VALUES (?,?,?,?,?,?)""",
                (
                    match_id,
                    player_id,
                    innings_no,
                    stats["catches"],
                    stats["stumpings"],
                    stats["run_outs"],
                ),
            )
    return True


def main() -> int:
    missing = [path for path in ARCHIVES if not path.is_file()]
    if missing:
        print("Missing source archive(s):", *(str(path) for path in missing), file=sys.stderr)
        return 1

    if DATABASE_PATH.exists():
        print(f"Refusing to overwrite existing database: {DATABASE_PATH}", file=sys.stderr)
        print("Delete or rename it yourself if you explicitly want a fresh import.", file=sys.stderr)
        return 1

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    teams: dict[str, int] = {}
    players: dict[tuple[str, str], int] = {}
    venues: dict[tuple[str, str], int] = {}
    series: dict[tuple[str, int], int] = {}
    imported = 0
    try:
        for archive_path in ARCHIVES:
            print(f"Importing {archive_path.name}...")
            with zipfile.ZipFile(archive_path) as archive:
                json_files = [name for name in archive.namelist() if name.endswith(".json")]
                for filename in json_files:
                    match = json.loads(archive.read(filename))
                    imported += import_match(
                        connection, Path(filename).name, match, teams, players, venues, series
                    )
                    if imported and imported % 500 == 0:
                        connection.commit()
            connection.commit()
        print(f"Imported {imported} completed international matches.")
    except (OSError, sqlite3.Error, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        connection.rollback()
        connection.close()
        DATABASE_PATH.unlink(missing_ok=True)
        raise RuntimeError(f"Cricsheet import failed: {exc}") from exc

    connection.close()
    print(f"Database created: {DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
