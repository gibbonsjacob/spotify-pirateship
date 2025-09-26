


CREATE TABLE fact_error_log (
    error_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id        INTEGER NOT NULL,
    track_id        TEXT,  
    error_ts        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message   TEXT NOT NULL,
    error_code      TEXT,   
    context         TEXT, 
    stage           TEXT,  
    insert_date     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (batch_id) REFERENCES fact_batch_execution(batch_id),
    FOREIGN KEY (track_id) REFERENCES fact_song_download(track_id)
);