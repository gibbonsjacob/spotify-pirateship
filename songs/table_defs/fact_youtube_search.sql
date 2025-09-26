

CREATE TABLE fact_youtube_search (
    search_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id            TEXT NOT NULL,         -- FK to dim_song
    batch_id            TEXT NOT NULL,         -- FK to fact_batch_execution
    search_ts           TEXT DEFAULT (datetime('now')),
    search_status       TEXT,                  -- e.g., "Success", "Failed"
    search_query        TEXT,                   
    youtube_url         TEXT,                  -- NULL if failed
    insert_date         TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(track_id) REFERENCES dim_song(track_id),
    FOREIGN KEY(batch_id) REFERENCES fact_batch_execution(batch_id)
);
