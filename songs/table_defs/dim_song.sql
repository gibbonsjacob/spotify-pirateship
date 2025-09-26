

-- Song dimension
CREATE TABLE IF NOT EXISTS dim_song (
    track_id                 TEXT PRIMARY KEY,       -- Spotify track ID
    track_name               TEXT NOT NULL,
    isrc                     TEXT,
    duration_ms              INTEGER,
    explicit                 INTEGER,                -- 0 = false, 1 = true
    popularity               INTEGER,
    disc_number              INTEGER,
    track_number             INTEGER,
    preview_url              TEXT,
    spotify_url              TEXT,
    track_uri                TEXT,
    added_to_playlist        TEXT,                   -- when added to playlist
    album_id                 VARCHAR(50),
    insert_date        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(album_id) REFERENCES dim_album(album_id)
);

