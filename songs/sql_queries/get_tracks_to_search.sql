

SELECT

    s.track_id, 
    s.track_name, 
    artist.artist_name

FROM 

    dim_song s 
    JOIN xref_song_to_artist xref on s.track_id = xref.track_id
    JOIN dim_artist artist on xref.artist_id = artist.artist_id
    LEFT JOIN fact_youtube_search f on s.track_id = f.track_id
    

WHERE 

    f.track_id IS NULL 
    OR lower(f.search_status) != 'success' 
    OR f.youtube_url is NULL

GROUP BY 
    s.track_id, 
    s.track_name, 
    artist.artist_name