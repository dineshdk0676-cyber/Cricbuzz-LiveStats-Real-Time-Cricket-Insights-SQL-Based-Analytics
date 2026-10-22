"""Create a clearly marked, deterministic sample dataset for first-run demos."""

from __future__ import annotations

import random
import sqlite3
from datetime import date


TEAMS = [
    ("India", "India"),
    ("Australia", "Australia"),
    ("England", "England"),
    ("New Zealand", "New Zealand"),
]
PLAYERS = {
    "India": [
        ("Aarav Sharma", "Batsman", "Right-hand bat", "Right-arm offbreak"),
        ("Ishan Mehta", "Batsman", "Left-hand bat", "Right-arm medium"),
        ("Dev Patel", "All-rounder", "Right-hand bat", "Right-arm medium"),
        ("Kabir Rao", "Bowler", "Right-hand bat", "Right-arm fast"),
        ("Neel Kapoor", "Wicket-keeper", "Right-hand bat", "None"),
    ],
    "Australia": [
        ("Liam Clarke", "Batsman", "Right-hand bat", "Right-arm legbreak"),
        ("Noah Wilson", "All-rounder", "Left-hand bat", "Left-arm orthodox"),
        ("Ethan Brooks", "Batsman", "Right-hand bat", "Right-arm medium"),
        ("Oliver Hayes", "Bowler", "Right-hand bat", "Right-arm fast"),
        ("Jack Turner", "Wicket-keeper", "Left-hand bat", "None"),
    ],
    "England": [
        ("Theo Bennett", "Batsman", "Right-hand bat", "Right-arm medium"),
        ("Harry Foster", "All-rounder", "Left-hand bat", "Right-arm medium"),
        ("George Ellis", "Batsman", "Right-hand bat", "None"),
        ("Charlie Reed", "Bowler", "Right-hand bat", "Right-arm fast"),
        ("Alfie Morgan", "Wicket-keeper", "Right-hand bat", "None"),
    ],
    "New Zealand": [
        ("Finn Carter", "Batsman", "Left-hand bat", "Right-arm legbreak"),
        ("Lucas Ward", "All-rounder", "Right-hand bat", "Right-arm medium"),
        ("James Cooper", "Batsman", "Right-hand bat", "None"),
        ("Mason King", "Bowler", "Right-hand bat", "Left-arm fast"),
        ("Oscar Wright", "Wicket-keeper", "Left-hand bat", "None"),
    ],
}
VENUES = [
    ("Demo Cricket Ground", "Mumbai", "India", 55000),
    ("Harbour Oval", "Sydney", "Australia", 48000),
    ("County Park", "London", "England", 32000),
    ("Southern Field", "Auckland", "New Zealand", 41000),
]


def seed_database(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT 1 FROM teams LIMIT 1").fetchone():
        return

    team_ids: dict[str, int] = {}
    for name, country in TEAMS:
        cursor = connection.execute("INSERT INTO teams(name, country) VALUES (?, ?)", (name, country))
        team_ids[name] = cursor.lastrowid

    player_ids: dict[str, list[tuple[int, str]]] = {team: [] for team, _ in TEAMS}
    for team_name, team_players in PLAYERS.items():
        for name, role, batting, bowling in team_players:
            cursor = connection.execute(
                """INSERT INTO players(name, team_id, role, batting_style, bowling_style)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, team_ids[team_name], role, batting, bowling),
            )
            player_ids[team_name].append((cursor.lastrowid, role))

    venue_ids = [
        connection.execute(
            "INSERT INTO venues(name, city, country, capacity) VALUES (?, ?, ?, ?)", venue
        ).lastrowid
        for venue in VENUES
    ]
    series_ids = {}
    for year in range(2020, date.today().year + 1):
        series_ids[year] = connection.execute(
            """INSERT INTO series(name, host_country, format, start_date, planned_matches)
               VALUES (?, ?, ?, ?, ?)""",
            (f"Demo International Series {year}", TEAMS[year % len(TEAMS)][1], "ODI", f"{year}-01-01", 6),
        ).lastrowid

    rng = random.Random(20260314)
    pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    match_number = 0
    end_year = date.today().year
    for year in range(2020, end_year + 1):
        for month in range(1, 13, 3):
            quarter_start = date(year, month, 1)
            if quarter_start > date.today():
                continue
            for pair_no, (left, right) in enumerate(pairs):
                match_day = min(5 + pair_no * 4, 25)
                match_date = date(year, month, match_day)
                if match_date > date.today():
                    match_date = date.today()
                team1, team2 = TEAMS[left][0], TEAMS[right][0]
                toss_team = team1 if rng.random() < 0.5 else team2
                toss_decision = "bat" if rng.random() < 0.5 else "field"
                winner = team1 if rng.random() < 0.5 else team2
                won_by_runs = winner == team1
                status = "Completed"
                cursor = connection.execute(
                    """INSERT INTO matches
                       (series_id, format, description, team1_id, team2_id, venue_id, match_date,
                        status, toss_winner_team_id, toss_decision, winner_team_id,
                        win_margin_runs, win_margin_wickets)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        series_ids[year],
                        ("Test", "ODI", "T20I")[match_number % 3],
                        f"Demo {team1} vs {team2} - Match {match_number + 1}",
                        team_ids[team1],
                        team_ids[team2],
                        venue_ids[(match_number + pair_no) % len(venue_ids)],
                        match_date.isoformat(),
                        status,
                        team_ids[toss_team],
                        toss_decision,
                        team_ids[winner],
                        rng.randint(5, 140) if won_by_runs else None,
                        None if won_by_runs else rng.randint(1, 8),
                    ),
                )
                match_id = cursor.lastrowid
                batting_first = (
                    toss_team
                    if toss_decision == "bat"
                    else (team2 if toss_team == team1 else team1)
                )
                batting_second = team2 if batting_first == team1 else team1
                for innings_no, batting_team, bowling_team in (
                    (1, batting_first, batting_second),
                    (2, batting_second, batting_first),
                ):
                    for position, (player_id, role) in enumerate(player_ids[batting_team], 1):
                        runs = rng.randint(0, 110) if position < 5 else rng.randint(0, 60)
                        balls = max(runs, rng.randint(1, 85)) if runs else rng.randint(1, 20)
                        is_out = int(rng.random() < 0.72)
                        connection.execute(
                            """INSERT INTO batting_innings
                               (match_id, player_id, team_id, innings_no, batting_position, runs,
                                balls_faced, is_out, catches, stumpings)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                match_id,
                                player_id,
                                team_ids[batting_team],
                                innings_no,
                                position,
                                runs,
                                balls,
                                is_out,
                                int(rng.random() < 0.12),
                                int(role == "Wicket-keeper" and rng.random() < 0.08),
                            ),
                        )
                    for player_id, role in player_ids[bowling_team]:
                        balls_bowled = rng.randint(18, 60) if role != "Batsman" else rng.randint(0, 18)
                        connection.execute(
                            """INSERT INTO bowling_figures
                               (match_id, player_id, team_id, innings_no, balls_bowled,
                                runs_conceded, wickets)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                match_id,
                                player_id,
                                team_ids[bowling_team],
                                innings_no,
                                balls_bowled,
                                rng.randint(0, max(1, balls_bowled * 2)),
                                rng.randint(0, 4) if balls_bowled else 0,
                            ),
                        )
                match_number += 1
