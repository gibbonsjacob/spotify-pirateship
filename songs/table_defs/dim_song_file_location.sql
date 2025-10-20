


CREATE TABLE IF NOT EXISTS dim_song_file_location (
    track_id                    TEXT PRIMARY KEY,
    current_path                TEXT NOT NULL,
    file_hash                   TEXT, 
    last_changed                DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_change_reason          TEXT,
    last_confidence             REAL DEFAULT -1,
    insert_date                 TEXT DEFAULT (datetime('now'))

);