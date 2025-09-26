SELECT 
    dim_song.album_id 
FROM 
    dim_song 
    LEFT JOIN dim_album ON dim_song.album_id = dim_album.album_id 
WHERE 
    dim_album.album_id IS NULL 
GROUP BY dim_song.album_id;