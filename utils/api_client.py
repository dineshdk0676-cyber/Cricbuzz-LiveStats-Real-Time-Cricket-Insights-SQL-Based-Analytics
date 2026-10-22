"""Optional Cricbuzz Cricket API client using a RapidAPI key from the environment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from utils.db_connection import get_connection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class CricbuzzAPIError(RuntimeError):
    """Raised when a Cricbuzz API request cannot be completed."""


def _setting(name: str, default: str = "") -> str:
    try:
        secret = st.secrets.get(name)
    except (FileNotFoundError, StreamlitSecretNotFoundError):
        secret = None
    return str(secret) if secret else os.getenv(name, default)


def fetch_live_matches() -> Any:
    """Fetch live matches from the Cricbuzz Cricket API via RapidAPI."""
    api_key = _setting("CRICBUZZ_API_KEY")
    if not api_key:
        raise CricbuzzAPIError(
            "Live API is not configured. Add CRICBUZZ_API_KEY to .env or Streamlit secrets."
        )

    host = _setting("CRICBUZZ_API_HOST", "cricbuzz-cricket.p.rapidapi.com")
    path = _setting("CRICBUZZ_LIVE_PATH", "/matches/v1/live")
    url = f"https://{host}/{path.lstrip('/')}"
    try:
        response = requests.get(
            url,
            headers={"x-rapidapi-key": api_key, "x-rapidapi-host": host},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise CricbuzzAPIError(f"Live match request failed: {exc}") from exc
    except ValueError as exc:
        raise CricbuzzAPIError("The live match endpoint returned invalid JSON.") from exc


def _nested_values(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _nested_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_values(child)


def _match_records(payload: Any) -> list[dict[str, Any]]:
    """Extract known Cricbuzz matchInfo objects from common response envelopes."""
    records = []
    seen_ids = set()
    for item in _nested_values(payload):
        match_id = item.get("matchId") or item.get("match_id")
        description = item.get("matchDescription") or item.get("match_desc") or item.get("matchDesc")
        if match_id is None or description is None:
            continue
        if str(match_id) in seen_ids:
            continue
        seen_ids.add(str(match_id))
        team1 = item.get("team1") or {}
        team2 = item.get("team2") or {}
        venue_info = item.get("venueInfo") or item.get("venue") or {}
        records.append(
            {
                "external_match_id": str(match_id),
                "match_description": str(description),
                "team1": team1.get("teamName") or team1.get("name") if isinstance(team1, dict) else str(team1),
                "team2": team2.get("teamName") or team2.get("name") if isinstance(team2, dict) else str(team2),
                "match_format": item.get("matchFormat") or item.get("matchType"),
                "status": item.get("status") or item.get("state"),
                "venue": venue_info.get("ground") or venue_info.get("venue") if isinstance(venue_info, dict) else str(venue_info),
                "start_time": item.get("startDate") or item.get("startTime"),
                "response_json": json.dumps(item, ensure_ascii=False),
            }
        )
    return records


def save_live_matches(payload: Any) -> int:
    """Persist parsed live match records and return their count."""
    records = _match_records(payload)
    if not records:
        raise CricbuzzAPIError(
            "The API response contained no recognizable match records; it was not saved."
        )
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.executemany(
            """INSERT INTO live_match_snapshots
               (external_match_id,match_description,team1,team2,match_format,status,venue,
                start_time,fetched_at,response_json)
               VALUES (:external_match_id,:match_description,:team1,:team2,:match_format,
                :status,:venue,:start_time,:fetched_at,:response_json)""",
            [{**record, "fetched_at": fetched_at} for record in records],
        )
        connection.execute(
            """DELETE FROM live_match_snapshots
            WHERE id NOT IN (SELECT id FROM live_match_snapshots ORDER BY fetched_at DESC,id DESC LIMIT 1000)"""
        )
    return len(records)


def get_latest_live_matches():
    """Return the most recent persisted live-match snapshot rows."""
    with get_connection() as connection:
        return connection.execute(
            """SELECT external_match_id,match_description,team1,team2,match_format,status,
            venue,start_time,fetched_at,response_json FROM live_match_snapshots
            WHERE fetched_at=(SELECT MAX(fetched_at) FROM live_match_snapshots)
            ORDER BY match_description"""
        ).fetchall()
