

-- xref for one to many relationship between an artist and their genres
CREATE TABLE xref_artist_genres (
    genre_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id   VARCHAR(50) REFERENCES dim_artist(artist_id),
    genre_name  TEXT, 
    insert_date TEXT DEFAULT (datetime('now')),
    UNIQUE (artist_id, genre_name)

);