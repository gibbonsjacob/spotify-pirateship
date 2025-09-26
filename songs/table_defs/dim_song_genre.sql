



-- dim_song_genre
CREATE TABLE dim_song_genre (
    track_id         TEXT PRIMARY KEY,
    genre_name       TEXT NOT NULL,
    confidence       REAL, 
    insert_date      TEXT DEFAULT (datetime('now'))
);