import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os 
import argparse
import json

def load_env_vars():
    load_dotenv()
    spotify_client_id = os.getenv('spotify_client_id')
    spotify_client_secret = os.getenv('spotify_client_secret')
    spotify_redirect_url = os.getenv('spotify_redirect_url')
    return spotify_client_id, spotify_client_secret, spotify_redirect_url



###### CONFIGS ######

spotify_client_id, spotify_client_secret, spotify_redirect_url = load_env_vars()
scopes = """
        user-read-private
        user-read-email
        ugc-image-upload 
        user-read-playback-state 
        user-modify-playback-state 
        user-read-currently-playing 
        playlist-read-private 
        playlist-read-collaborative 
        user-read-recently-played
        """

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                            client_secret=spotify_client_secret,
                                            redirect_uri=spotify_redirect_url,
                                            scope=scopes))

artist_id_limit = 50
album_id_limit = 20



######################################################


def get_user_playlists():
    """Retrieve all playlists from the user's Spotify account with names and URLs."""
    playlists = sp.current_user_playlists()

    
    return [
        {"name": playlist["name"], "url": playlist["external_urls"]["spotify"]}
        for playlist in playlists["items"]
    ]




def get_song_details(playlist_url):
    """Fetch song details for every track in a Spotify playlist.
        limit of 100 ID's per call"""
    
    playlist_id = playlist_url.split("/")[-1].split("?")[0]  # Playlist ID from URL
    results = []
    offset = 0
    limit = 100  

    ## because this endpoint is paginated, we call it as many times 
    ## as we need to until there's no tracks left to hit
    while True:
        response = sp.playlist_items(
            playlist_id,
            offset=offset,
            limit=limit
        )
        items = response.get("items", [])
        results.extend(items)

        # If fewer than 'limit' items returned, we’re at the end
        if len(items) < limit:
            break

        offset += limit

    return results
    


def get_album_details(album_ids: list):
    """ limit of 20 ID's per call"""

    results = []
    for i in range(0, len(album_ids), album_id_limit):
        chunk = album_ids[i:i + album_id_limit]
        resp = sp.albums(chunk)
        results.extend(resp.get('albums', []))
         
    return results



def get_artist_details(artist_ids: list):
    """ Limit of 50 ID's per call so we batch our calls """
    results = []
    for i in range(0, len(artist_ids), artist_id_limit):
        chunk = artist_ids[i:i + artist_id_limit]
        resp = sp.artists(chunk)
        results.extend(resp.get('artists', []))
         
    return results



    



def main(args):
    
    print(args)

    if args.get_playlists:
    
        results = get_user_playlists(sp)

        for r in results: 
            print(r)


    if args.artist: 
        print(get_artist_details([args.artist]))


    if args.album: 
        print(get_album_details([args.album]))



    if args.playlist_details: 
        print(f"Writing playlist details to {args.playlist_details}.json")
        with open(f"{args.playlist_details}.json", 'w') as f: 
            json.dumps(get_song_details(args.playlist_details))
    
    
    





if __name__ == '__main__': 

    parser = argparse.ArgumentParser(description='Get Spotify API Information')
    parser.add_argument('--artist',   action="store_true", help="Provide an Artist ID to search for")
    parser.add_argument('--album',   action="store_true", help="Provide an Album ID to search for")
    parser.add_argument('--playlist-details',   action="store_true", help="Provide a playlist ID to get data about all songs in the playlist")
    parser.add_argument('--get-playlists',   action="store_true", help="Running this will return the name of all user playlists from Spotify")


    args = parser.parse_args()

    main(args)