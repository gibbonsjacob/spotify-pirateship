

SELECT

    y.track_id, 
    y.youtube_url, 
    y.search_query  -- this will also be our file name

FROM 

    fact_youtube_search y 
    LEFT JOIN fact_song_download d on y.track_id = d.track_id
    

WHERE 

    (d.track_id IS NULL 
    OR lower(d.download_status) != 'downloaded')

    AND (lower(y.search_status) = 'success' 
        OR y.youtube_url IS NOT NULL)

GROUP BY 
    y.track_id, 
    y.youtube_url, 
    y.search_query