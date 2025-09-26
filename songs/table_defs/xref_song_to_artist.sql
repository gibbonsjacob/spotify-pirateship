



-- xref for many-to-many relationship between songs and artists

CREATE TABLE IF NOT EXISTS xref_song_to_artist (
    track_id    TEXT,
    artist_id   TEXT,
    insert_date        TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (track_id, artist_id),
    FOREIGN KEY(track_id) REFERENCES dim_song(track_id),
    FOREIGN KEY(artist_id) REFERENCES dim_artist(artist_id)
    
);