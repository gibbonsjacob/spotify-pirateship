

-- Artist dimension
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_id       TEXT PRIMARY KEY,       -- Spotify artist ID
    artist_name     TEXT,
    artist_url      TEXT,
    artist_href     TEXT,
    popularity      INT,
    artist_type     VARCHAR(50),
    artist_uri      TEXT,
    followers_total BIGINT,
    insert_date        TEXT DEFAULT (datetime('now'))
);