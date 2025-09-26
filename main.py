from re import search
import sqlite3
import datetime
import pandas as pd
import spotify_fetcher
import get_video_url
import json
import uuid
from db_management import Database
from pathlib import Path
from download_songs import download_audio
# import ML_genre_classifier.genre_predictor as genre_predictor




############################ CONFIGS ##############################

playlist_of_interest = 'dezyDUBBBBB'
min_genre_confidence_val = 0.7



###################################################################



def check_for_tables(songs_db, tables: list) -> dict:
    """
    Check for existence of core tables (defined below) 

    Args:
        songs_db (sqlite3 database): Database file housing all related information
        tables (list): List of tables to check for
    Returns:
        Dict: Keys = values from tables, Values = T/F regarding whether the object exists or not
    """
    table_existence = {}

    for table in tables:
        sql_template = f"""
        
            SELECT 1 
            FROM sqlite_master 
            WHERE type='table' AND name='{table}';
        
        """

        temp = songs_db.select_sql(sql_template)

        table_existence[table] = (isinstance(temp, pd.DataFrame) 
                                  and not temp.empty)
        
    return table_existence



def parse_tracks(items: list[dict]) -> pd.DataFrame:
    """Extract normalized track fields from raw Spotify track payloads."""
    records = []

    for item in items:
        track = item.get("track", {})
        if not track:
            continue

        records.append({
            "track_id": track.get("id"),
            "track_name": track.get("name"),
            "isrc": track.get("external_ids", {}).get("isrc"),
            "duration_ms": track.get("duration_ms"),
            "explicit": int(track.get("explicit", False)),  # convert bool → int
            "popularity": track.get("popularity"),
            "disc_number": track.get("disc_number"),
            "track_number": track.get("track_number"),
            "preview_url": track.get("preview_url"),
            "spotify_url": track.get("external_urls", {}).get("spotify"),
            "track_uri": track.get("uri"),
            "added_to_playlist": item.get("added_at"),
            "album_id": track.get("album", {}).get("id")
        })

    df = pd.DataFrame.from_records(records).drop_duplicates(subset=["track_id"])
    return df


def parse_albums(items: list) -> pd.DataFrame:
    """
    Extract normalized album fields from raw Spotify album payloads.

    Args:
        items (list): List of raw album payloads (dicts).
    
    Returns:
        pd.DataFrame: Normalized album information for dim_album.
    """
    records = []

    for album in items:
        if not album:
            continue
        records.append({
            "album_id": album.get("id"),
            "album_name": album.get("name"),
            "album_type": album.get("album_type"),
            "release_date": album.get("release_date"),
            "release_date_precision": album.get("release_date_precision"),
            "total_tracks": album.get("total_tracks"),
            "spotify_url": album.get("external_urls", {}).get("spotify"),
            "href": album.get("href"),
            "type": album.get("type"),
            "uri": album.get("uri")
        })

    return pd.DataFrame.from_records(records).drop_duplicates(subset=['album_id'])




def parse_artists(items: list[dict]) -> tuple:
    """
    Extract normalized artist fields from raw Spotify artist payloads.
    
    Args:
        items (list): List of raw artist payloads (dicts).
    
    Returns:
        pd.DataFrame: Normalized artist information.
    """
    artist_records = []
    genre_records = []


    for artist in items:
        if not artist:
            continue
        artist_records.append({
            "artist_id": artist.get("id"),
            "artist_name": artist.get("name"),
            "artist_url": artist.get("external_urls", {}).get("spotify"),
            "artist_href": artist.get("href"),
            "popularity": artist.get("popularity"),
            "artist_type": artist.get("type"),
            "artist_uri": artist.get("uri"),
            "followers_total": artist.get("followers", {}).get("total"),
        })

        # Doing genre mappings here too so we don't have to parse the artist payload twice
        for genre in artist.get("genres", []):
            genre_records.append({
                "artist_id": artist.get("id"),
                "genre_name": genre
            })



    artists_df = pd.DataFrame.from_records(artist_records).drop_duplicates(subset=["artist_id"])
    artist_genres = pd.DataFrame.from_records(genre_records).drop_duplicates(subset=['artist_id', 'genre_name'])

    return artists_df, artist_genres



def parse_song_to_artist_map(items: list[dict]) -> pd.DataFrame:
    """Extract normalized artist to track maps from raw Spotify track payloads."""

    records = []

    for item in items:
        track = item.get("track", {})
        track_id = track.get("id")
        for artist in track.get("artists", []):
            artist_id = artist.get("id")
            if track_id and artist_id:
                records.append((track_id, artist_id))

    
    df = pd.DataFrame(records, columns=["track_id", "artist_id"]).drop_duplicates()
    return df




def main():

    ## Batch configs
    batch_id = str(uuid.uuid4())
    batch_start_ts = datetime.datetime.now()

    ## Database stuff 
    songs_db = Database('songs/songs_management.db')
    tables_path = Path('songs/table_defs/')

    #key is the table name, value is the CREATE TABLE sql statement in the file
    tables = {filepath.stem: filepath.read_text() for filepath in tables_path.iterdir() if filepath.is_file()}

    table_existence = check_for_tables(songs_db, tables.keys())

    for table, existence in table_existence.items():
        if not existence:
            #if table doesn't exist, run the create table sql 
            #this should only ever hit the very first time we run
            songs_db.execute_sql(tables[table])



    ### Next let's get all songs from our playlist of interest
    all_playlists = spotify_fetcher.get_user_playlists()
    playlist_to_iterate = [p for p in all_playlists if p.get('name') == playlist_of_interest][0].get('url')

    
    raw_track_payload = spotify_fetcher.get_song_details(playlist_to_iterate)

    # some cleanup because this is messy 
    all_tracks = parse_tracks(raw_track_payload)
    song_to_artist_map = parse_song_to_artist_map(raw_track_payload)


    ## Now let's get a list of the tracks, albums, and artists we already have in our db
    ## we can skip the xref because if we already have the track we have the xref

    existing_songs = songs_db.select_sql(Path('songs/sql_queries/distinct_track_id.sql').read_text())


    ## left join existing songs with all_songs to figure out which ones are new, then drop
    ## all the existing ones that match both df's so we're left with only new songs
    new_songs = all_tracks.merge(existing_songs, on="track_id", how='left', indicator=True)
    new_songs = new_songs[new_songs['_merge'] == 'left_only'].drop(columns=['_merge'])
    if not new_songs.empty:
        new_songs_insert_sql = songs_db.build_insert_into_sql('dim_song', new_songs)
        songs_db.execute_sql(new_songs_insert_sql)


    ## Next we'll handle the track to artist map - this will also let us cheat a bit downstream by doing this now 
    ## Here we'll leverage SQL's ON CONFLICT clause rather than building new unique pairs
    ## There's no real reason to go either way, I just thought of it here
    song_to_artist_map_insert_sql = songs_db.build_insert_into_sql(
                                    dest_table='xref_song_to_artist',
                                    df=song_to_artist_map, 
                                    on_conflict=f"(track_id, artist_id) DO NOTHING")

    songs_db.execute_sql(song_to_artist_map_insert_sql)



    ## Now let's handle albums - we can cheat a little here and only use SQL
    ## since we've already inserted all our new tracks, we can just compare album_ids
    ## that exist in dim_song vs. those that exist in dim_album and then hit the API 
    ## endpoint for any album_id's that are leftover
    existing_albums = songs_db.select_sql(Path('songs/sql_queries/distinct_album_id.sql').read_text())
    new_album_ids = songs_db.select_sql(Path('songs/sql_queries/get_new_albums.sql').read_text())['album_id'].to_list()    
    raw_albums_payload = spotify_fetcher.get_album_details(new_album_ids)
    cleaned_albums = parse_albums(raw_albums_payload)
    if not cleaned_albums.empty: 
        new_albums_insert_sql = songs_db.build_insert_into_sql('dim_album', cleaned_albums)
        songs_db.execute_sql(new_albums_insert_sql)
    




    ### Finally we handle artists and genres - we can do this exactly the same way as we did albums
    ### we'll cheat by comparing what's in our xref table to what's in dim_artist - anything that's
    ### in our xref table but not in dim_artist is a "new" artist
    existing_artists =  songs_db.select_sql(Path('songs/sql_queries/distinct_artist_id.sql').read_text())
    new_artist_ids = songs_db.select_sql(Path('songs/sql_queries/get_new_artists.sql').read_text())['artist_id'].to_list()    
    raw_artist_payload = spotify_fetcher.get_artist_details(new_artist_ids)
    cleaned_artists, artist_genres = parse_artists(raw_artist_payload)
    if not cleaned_artists.empty:
        new_artist_insert_sql = songs_db.build_insert_into_sql('dim_artist', cleaned_artists)
        songs_db.execute_sql(new_artist_insert_sql)

    if not artist_genres.empty:

        new_genre_insert_sql = songs_db.build_insert_into_sql(
                                        dest_table='xref_artist_genres',
                                        df = artist_genres, 
                                        on_conflict='(artist_id, genre_name) DO NOTHING', 
                                        )
        songs_db.execute_sql(new_genre_insert_sql)



    ################################################################################
    
    ## Now that we have all of our information pulled in and recorded from Spotify
    ## Let's do something with it! 

    # First we'll get the track_id of every track that doesn't have a
    # record in fact_youtube_search (any song without a youtube_url found)

    tracks_to_search_raw = songs_db.select_sql(Path('songs/sql_queries/get_tracks_to_search.sql').read_text())
    

    ## Note - this step is essentially undoing the creation of xref_song_to_artist, but this step helps keep our database
    ## agnostic of our usage for this specific use case. We could not (and arguably should not) 
    ## have done this step at the same time as our ingestion 
    joined_artist_names = tracks_to_search_raw.groupby('track_id', as_index=True)['artist_name'].agg(lambda artist_name: ' x '.join(artist_name))
    tracks_to_search_stg = tracks_to_search_raw.drop(columns=['artist_name']).drop_duplicates()
    stg_youtube_search = tracks_to_search_stg.merge(joined_artist_names, how='left', on='track_id')
    stg_youtube_search['search_query'] = stg_youtube_search.apply(lambda row: f"{row['track_name']} - {row['artist_name']}", axis=1)
    
    
    ## Then, we'll search for everything that doesn't have a youtube_url yet
    
    search_successes = []
    errors = []

    for index, row in stg_youtube_search.iterrows():
        try: 
            search_ts = datetime.datetime.now()
            payload = get_video_url.search(row['search_query'])
            if payload.get('status', 0) == 1: 
                ## this should only happen if we hit a rate limit error
                ## Since the error just goes to the JSON payload no Error is raised in our execution. 

                search_successes.append({
                    "track_id": row['track_id'],
                    'batch_id': batch_id,
                    'search_ts': search_ts,
                    'search_status': 'success',
                    'search_query': row['search_query'],
                    "youtube_url": payload['youtube_url']

                })

            else:
                
                errors.append({
                    "batch_id": batch_id,
                    "track_id": row['track_id'],
                    "error_ts": search_ts,
                    "error_message": payload['error_message'],
                    "error_code": payload['error_code'],
                    "context": payload['context'],
                    "stage": "youtube_search"
                })
                break ## if this gets hit every subsequent row will fail too

        except Exception as e:
            # Finally let's catch anything else random that happens and throw it here
            errors.append({
                "batch_id": batch_id,
                "track_id": row['track_id'],
                "error_ts": datetime.datetime.now(),
                "error_message": str(e),
                "error_code": type(e).__name__,
                "context": None,
                "stage": "youtube_search"
            })
    
    ## Finally we'll write our search successes to our fact table so downstream processes can use it
    fact_youtube_search = pd.DataFrame(search_successes)
    if not fact_youtube_search.empty:
        fys_insert_sql = songs_db.build_insert_into_sql('fact_youtube_search', fact_youtube_search)
        songs_db.execute_sql(fys_insert_sql)

    
    ######################################################################

    ## Here, we'll download any track that has a youtube_url and does not 
    ## have a successful record in fact_song_download


    tracks_to_download_raw = songs_db.select_sql(Path('songs/sql_queries/get_tracks_to_download.sql').read_text())


    
    stg_song_download = tracks_to_download_raw.copy()
    stg_song_download['file_format'] = '.mp3' ## every file will be .mp3 for this project
    download_successes = []
    for index, row in stg_song_download.iterrows():
        try: 
            root = Path(
                f"song_downloads_raw/{datetime.datetime.today().strftime('%m.%d.%Y')}"
            ).joinpath(row['search_query'])
            download_path = root.absolute().as_posix()
            file_path = download_path + row['file_format']
            download_ts =  datetime.datetime.now()
            download_status_payload = download_audio(row['youtube_url'], download_path)
            download_success_status = download_status_payload.get('download_status')
            download_error = download_status_payload.get('exception')

            if download_success_status: 
                download_successes.append({

                    "track_id": row['track_id'],
                    "youtube_url": row['youtube_url'],
                    "download_status": "Downloaded",
                    "downloaded_to_file_path": file_path,
                    "file_format": row['file_format'],
                    "download_ts": download_ts,
                    "batch_id": batch_id
                })
                print(f"✅ Success downloading: {row['search_query']}")

            else:
                errors.append({
                    "batch_id": batch_id,
                    "track_id": row['track_id'],
                    "error_ts": download_ts,
                    "error_message": download_error,
                    "error_code": "DownloadFailed",
                    "context": None,
                    "stage": "Download"
                })
                print(f"Error downloading: {row['search_query']}")


        except Exception as e:
            # Any other miscellaneous errors get caught here as needed
            errors.append({
                "batch_id": batch_id,
                "track_id": row['track_id'],
                "error_ts": datetime.datetime.now(),
                "error_message": str(e),
                "error_code": type(e).__name__,
                "context": None,
                "stage": "Download"
            })


    fact_song_download = pd.DataFrame(download_successes)
    error_df = pd.DataFrame(errors) ## note this is all errors for the whole batch 

    if not fact_song_download.empty:
        fsd_insert_sql = songs_db.build_insert_into_sql('fact_song_download', fact_song_download)
        songs_db.execute_sql(fsd_insert_sql)

    if not error_df.empty:
        fel_insert_sql = songs_db.build_insert_into_sql('fact_error_log', error_df)
        songs_db.execute_sql(fel_insert_sql)
    
    
    batch_summary = {
        "batch_id": batch_id,
        "batch_start_ts": batch_start_ts,
        "batch_end_ts": datetime.datetime.now(),
        "input_count": len(stg_youtube_search), ## all tracks that didn't have a youtube_url before this batch - using stage because this includes all records prior to recording the success/failure of search
        "success_count": len(fact_song_download), ## all tracks that successfully downloaded
        "error_count": len(error_df), 
        "runtime_host": "LOCAL_PC",   
        "triggered_by": "user_script" 
    }

    batch_df = pd.DataFrame([batch_summary])
    batch_insert_sql = songs_db.build_insert_into_sql('fact_batch_execution', batch_df)
    songs_db.execute_sql(batch_insert_sql)
    







    ########################################################
    
    ## Next we can apply our ML algorithm we wrote to classify each mp3 file to a genre
    ## This will tell us what folder the file needs to go to
    




   



    ##### All that's left to do is move files! We'll just do this based on our genre assignment
    ##### we should also decide on some way to check genres (this may be manual) and also rerun the training if enough new songs have been added or time has passed
    






def delete_tables():
    """ Just using this function for db management as needed"""
    songs_db = Database('songs/songs_management.db')
    # # print(songs_db.select_sql("select * from sqlite_master"))
    # songs_db.execute_sql("DROP TABLE IF EXISTS dim_album")
    # songs_db.execute_sql("DROP TABLE IF EXISTS dim_artist")
    # songs_db.execute_sql("DROP TABLE IF EXISTS dim_song")
    # songs_db.execute_sql("DROP TABLE IF EXISTS fact_batch_execution")
    # songs_db.execute_sql("DROP TABLE IF EXISTS fact_error_log")
    songs_db.execute_sql("DROP TABLE IF EXISTS fact_song_download")
    # songs_db.execute_sql("DROP TABLE IF EXISTS fact_song_features")
    # songs_db.execute_sql("DROP TABLE IF EXISTS fact_youtube_search")
    # songs_db.execute_sql("DROP TABLE IF EXISTS xref_artist_genres") 
    # songs_db.execute_sql("DROP TABLE IF EXISTS xref_song_to_artist")

    # songs_db.execute_sql("DROP TABLE IF EXISTS dim_song_genre")
    # songs_db.execute_sql("DROP TABLE IF EXISTS fact_genre_assignment")

    # songs_db.execute_sql('delete from fact_song_download where download_id >= 271')




def create_tables():
    songs_db = Database('songs/songs_management.db')
    tables_path = Path('songs/table_defs/')

    #key is the table name, value is the CREATE TABLE sql statement in the file
    tables = {filepath.stem: filepath.read_text() for filepath in tables_path.iterdir() if filepath.is_file()}

    table_existence = check_for_tables(songs_db, tables.keys())

    for table, existence in table_existence.items():
        if not existence:
            #if table doesn't exist, run the create table sql 
            #this should only ever hit the very first time we run
            songs_db.execute_sql(tables[table])




if __name__ == "__main__":
    main()
    # create_tables()
    # delete_tables()