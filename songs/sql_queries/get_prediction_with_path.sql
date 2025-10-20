


SELECT 
-- predictions
    genre.track_id,
    genre.genre_name,
    genre.confidence AS predicted_genre_confidence,
    genre.insert_date,
-- known locations
    location.current_path, 
    location.file_hash,
    location.last_changed, 
    location.last_change_reason, 
    location.last_confidence as known_genre_confidence
FROM 
    dim_song_genre genre
    JOIN dim_song_file_location location
        ON genre.track_id = location.track_id
WHERE genre.confidence = (
    SELECT MAX(confidence)
    FROM dim_song_genre g2
    WHERE g2.track_id = genre.track_id
);