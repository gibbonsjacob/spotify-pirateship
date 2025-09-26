


CREATE TABLE IF NOT EXISTS fact_song_features (
    track_id            TEXT PRIMARY KEY,      -- FK to dim_song
    danceability        REAL,
    energy              REAL,
    key                 INTEGER,               -- musical key (0=C, 1=C#, etc.)
    loudness            REAL,
    mode                INTEGER,               -- 1 = major, 0 = minor
    speechiness         REAL,
    acousticness        REAL,
    instrumentalness    REAL,
    liveness            REAL,
    valence             REAL,
    tempo               REAL,
    time_signature      INTEGER,
    insert_date        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(track_id) REFERENCES dim_song(track_id)
);
