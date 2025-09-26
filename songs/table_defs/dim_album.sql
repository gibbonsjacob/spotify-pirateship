

CREATE TABLE dim_album (
    album_id                VARCHAR(50) PRIMARY KEY,
    album_name              TEXT,
    album_type              VARCHAR(50),
    release_date            DATE,
    release_date_precision  VARCHAR(20),
    total_tracks            INT,
    spotify_url             TEXT,
    href                    TEXT,
    type                    VARCHAR(50),
    uri                     TEXT, 
    insert_date        TEXT DEFAULT (datetime('now'))
);