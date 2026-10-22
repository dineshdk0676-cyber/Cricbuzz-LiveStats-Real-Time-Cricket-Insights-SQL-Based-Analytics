import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.analytics_queries import QUERIES
from utils.api_client import get_latest_live_matches, save_live_matches
from utils import db_connection
from utils.seed_data import seed_database


ROOT = Path(__file__).resolve().parents[1]


class ProjectDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.create_function("SQRT", 1, lambda value: value**0.5 if value is not None else None)
        self.connection.executescript((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
        seed_database(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_demo_data_has_expected_entities(self):
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0], 4)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM players").fetchone()[0], 20)
        self.assertGreater(self.connection.execute("SELECT COUNT(*) FROM matches").fetchone()[0], 100)

    def test_all_documented_queries_execute(self):
        self.assertEqual(len(QUERIES), 25)
        for number, (_, sql) in QUERIES.items():
            with self.subTest(query=number):
                self.connection.execute(sql).fetchall()

    def test_analytics_queries_return_expected_leaderboards(self):
        odi_leaders = self.connection.execute(QUERIES[3][1]).fetchall()
        recent_matches = self.connection.execute(QUERIES[10][1]).fetchall()
        rankings = self.connection.execute(QUERIES[21][1]).fetchall()
        self.assertEqual(len(odi_leaders), 10)
        self.assertEqual(len(recent_matches), 20)
        self.assertTrue(rankings)
        for format_name in ("Test", "ODI", "T20I"):
            format_ranks = [row["rank"] for row in rankings if row["format"] == format_name]
            self.assertTrue(format_ranks)
            self.assertEqual(min(format_ranks), 1)

    def test_player_crud(self):
        team_id = self.connection.execute("SELECT id FROM teams LIMIT 1").fetchone()[0]
        cursor = self.connection.execute(
            "INSERT INTO players(name,team_id,role) VALUES (?,?,?)",
            ("Test Player", team_id, "Batsman"),
        )
        player_id = cursor.lastrowid
        self.connection.execute("UPDATE players SET role='All-rounder' WHERE id=?", (player_id,))
        self.assertEqual(
            self.connection.execute("SELECT role FROM players WHERE id=?", (player_id,)).fetchone()[0],
            "All-rounder",
        )
        self.connection.execute("DELETE FROM players WHERE id=?", (player_id,))

    def test_match_crud(self):
        team1, team2 = [
            row[0] for row in self.connection.execute("SELECT id FROM teams ORDER BY id LIMIT 2")
        ]
        venue_id = self.connection.execute("SELECT id FROM venues LIMIT 1").fetchone()[0]
        cursor = self.connection.execute(
            """INSERT INTO matches(description,format,team1_id,team2_id,venue_id,match_date)
            VALUES ('Test fixture','ODI',?,?,?,'2026-01-01')""",
            (team1, team2, venue_id),
        )
        match_id = cursor.lastrowid
        self.connection.execute("UPDATE matches SET status='Completed' WHERE id=?", (match_id,))
        self.assertEqual(
            self.connection.execute("SELECT status FROM matches WHERE id=?", (match_id,)).fetchone()[0],
            "Completed",
        )
        self.connection.execute("DELETE FROM matches WHERE id=?", (match_id,))

    def test_live_api_matches_are_saved_and_read_from_sqlite(self):
        payload = {
            "typeMatches": [
                {
                    "seriesMatches": [
                        {
                            "seriesAdWrapper": {
                                "matches": [
                                    {
                                        "matchInfo": {
                                            "matchId": 9876,
                                            "matchDescription": "Final",
                                            "team1": {"teamName": "India"},
                                            "team2": {"teamName": "Australia"},
                                            "matchFormat": "T20I",
                                            "status": "India need 10 runs",
                                            "venueInfo": {"ground": "Demo Ground"},
                                            "startDate": "1770000000000",
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(db_connection, "DB_PATH", Path(directory) / "live.sqlite"):
                db_connection.initialize_database()
                self.assertEqual(save_live_matches(payload), 1)
                rows = get_latest_live_matches()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["external_match_id"], "9876")
                self.assertEqual(rows[0]["team1"], "India")
                self.assertEqual(rows[0]["team2"], "Australia")
                self.assertEqual(rows[0]["venue"], "Demo Ground")


if __name__ == "__main__":
    unittest.main()
