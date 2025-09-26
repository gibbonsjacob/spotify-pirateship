


-- fact_genre_assignment table: records when a genre was assigned to a song
CREATE TABLE fact_genre_assignment (
    genre_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT,
    genre_name TEXT,                  -- current genre assigned
    confidence          REAL,
    insert_date                 TEXT DEFAULT (datetime('now'))
);