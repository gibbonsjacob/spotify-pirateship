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







def change_spotify_to_computer():
    
    
    scope = "user-modify-playback-state user-read-playback-state"
    
    # 1. Get available devices
    devices = sp.devices()
    computer_id = None
    
    # 2. Find your computer (name may vary, check in app)
    for device in devices['devices']:
        if device['type'] == 'Computer':
            computer_id = device['id']
            break
            
    if computer_id:
        # 3. Transfer playback to computer
        sp.transfer_playback(device_id=computer_id, force_play=True)
        print(f"Switched to {device['name']}")
    else:
        print("Computer device not found.")








if __name__ == '__main__':

    change_spotify_to_computer()