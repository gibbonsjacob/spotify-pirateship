SELECT 
    xref.artist_id 
FROM 
    xref_song_to_artist xref 
    LEFT JOIN dim_artist ON xref.artist_id = dim_artist.artist_id 
WHERE 
    dim_artist.artist_id IS NULL 
GROUP BY xref.artist_id;