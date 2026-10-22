PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    role TEXT NOT NULL,
    batting_style TEXT,
    bowling_style TEXT
);

CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity >= 0)
);

CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    host_country TEXT NOT NULL,
    format TEXT NOT NULL,
    start_date TEXT NOT NULL,
    planned_matches INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    series_id INTEGER REFERENCES series(id),
    format TEXT NOT NULL CHECK (format IN ('Test', 'ODI', 'T20I')),
    description TEXT NOT NULL,
    team1_id INTEGER NOT NULL REFERENCES teams(id),
    team2_id INTEGER NOT NULL REFERENCES teams(id),
    venue_id INTEGER NOT NULL REFERENCES venues(id),
    match_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Upcoming',
    toss_winner_team_id INTEGER REFERENCES teams(id),
    toss_decision TEXT CHECK (toss_decision IN ('bat', 'field')),
    winner_team_id INTEGER REFERENCES teams(id),
    win_margin_runs INTEGER,
    win_margin_wickets INTEGER,
    CHECK (team1_id != team2_id)
);

CREATE TABLE IF NOT EXISTS batting_innings (
    id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    innings_no INTEGER NOT NULL CHECK (innings_no > 0),
    batting_position INTEGER NOT NULL CHECK (batting_position > 0),
    runs INTEGER NOT NULL DEFAULT 0 CHECK (runs >= 0),
    balls_faced INTEGER NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
    is_out INTEGER NOT NULL DEFAULT 0 CHECK (is_out IN (0, 1)),
    catches INTEGER NOT NULL DEFAULT 0 CHECK (catches >= 0),
    stumpings INTEGER NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    UNIQUE (match_id, player_id, innings_no)
);

CREATE TABLE IF NOT EXISTS bowling_figures (
    id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    innings_no INTEGER NOT NULL CHECK (innings_no > 0),
    balls_bowled INTEGER NOT NULL DEFAULT 0 CHECK (balls_bowled >= 0),
    runs_conceded INTEGER NOT NULL DEFAULT 0 CHECK (runs_conceded >= 0),
    wickets INTEGER NOT NULL DEFAULT 0 CHECK (wickets >= 0),
    UNIQUE (match_id, player_id, innings_no)
);

CREATE TABLE IF NOT EXISTS fielding_figures (
    id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    innings_no INTEGER NOT NULL CHECK (innings_no > 0),
    catches INTEGER NOT NULL DEFAULT 0 CHECK (catches >= 0),
    stumpings INTEGER NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    run_outs INTEGER NOT NULL DEFAULT 0 CHECK (run_outs >= 0),
    UNIQUE (match_id, player_id, innings_no)
);

CREATE TABLE IF NOT EXISTS live_match_snapshots (
    id INTEGER PRIMARY KEY,
    external_match_id TEXT NOT NULL,
    match_description TEXT NOT NULL,
    team1 TEXT,
    team2 TEXT,
    match_format TEXT,
    status TEXT,
    venue TEXT,
    start_time TEXT,
    fetched_at TEXT NOT NULL,
    response_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_status_date ON matches(status, match_date);
CREATE INDEX IF NOT EXISTS idx_batting_player_match ON batting_innings(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player_match ON bowling_figures(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_fielding_player_match ON fielding_figures(player_id, match_id);
CREATE INDEX IF NOT EXISTS idx_series_start_date ON series(start_date);
CREATE INDEX IF NOT EXISTS idx_live_snapshots_fetched_at ON live_match_snapshots(fetched_at);
CREATE INDEX IF NOT EXISTS idx_live_snapshots_external_id ON live_match_snapshots(external_match_id);
