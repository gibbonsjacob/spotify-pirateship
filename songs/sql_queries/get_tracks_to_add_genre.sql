


SELECT 
    songs.track_id,
    fsd.downloaded_to_file_path 

FROM 

    dim_song songs
    LEFT JOIN dim_song_genre dsg 
        ON songs.track_id = dsg.track_id
    JOIN (
        SELECT 
            track_id,
            MAX(insert_date) AS insert_date
        FROM 
            fact_song_download
        GROUP BY track_id
    ) a ON songs.track_id = a.track_id
    LEFT JOIN fact_song_download fsd 
        ON fsd.track_id = a.track_id
        AND fsd.insert_date = a.insert_date

WHERE 
    dsg.track_id IS NULL
    OR dsg.confidence < {min_genre_confidence_val}
GROUP BY 
    songs.track_id, 
    fsd.downloaded_to_file_path;