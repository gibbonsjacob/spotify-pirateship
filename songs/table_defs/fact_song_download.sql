


CREATE TABLE fact_song_download (
    download_id                 INTEGER PRIMARY KEY AUTOINCREMENT, -- surrogate key
    track_id                    TEXT NOT NULL,                     -- FK to dim_song
    youtube_url                 TEXT NOT NULL,
    download_ts                 TEXT DEFAULT (datetime('now')),    -- when download occurred
    download_status             TEXT,                              -- e.g., success, failed, pending
    downloaded_to_file_path     TEXT,                              -- local path of saved file
    file_format                 TEXT,                              -- e.g., mp3, wav
    batch_id                    TEXT NOT NULL,                     -- FK to fact_batch_execution
    insert_date                 TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(track_id) REFERENCES dim_song(track_id),
    FOREIGN KEY(batch_id) REFERENCES fact_batch_execution(batch_id)
);