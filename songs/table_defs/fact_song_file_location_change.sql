


CREATE TABLE IF NOT EXISTS fact_song_file_location_change (
    change_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id                TEXT NOT NULL,
    source_path             TEXT,
    target_path             TEXT NOT NULL,
    file_hash               TEXT, 
    change_reason           TEXT,
    confidence              REAL DEFAULT -1,
    changed_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    insert_date             TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (track_id) REFERENCES dim_song_file_location (track_id)
);
