import re
import requests
from pathlib import Path
import yt_dlp
import os
from dotenv import load_dotenv
# import get_song_features
import get_video_url



















def song_mp3_file_exists(base_directory, artist, song_name):
    """Recursively search for a matching MP3 file based on artist & song name."""
    
    # Normalize search key (lowercase, replace spaces)
    search_key = f"{song_name.lower()} - {artist.lower()}.mp3"


    # Walk through all subdirectories
    for root, _, files in os.walk(base_directory):
        for file in files:
            if file.lower() == search_key:  # Compare normalized filename
                return os.path.join(root, file)  # Return full file path if found
    
    return None  







def download_audio(youtube_url: str, save_path: str):
    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': f"{save_path}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        # 'no_warnings': True
        'verbose': True
    }   

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        return {
                'download_status': True,
                'exception': None 
                }
    except Exception as e:
        print(e)
        return {
                'download_status': False,
                'exception': e 
                }

def main():
    # get playlist to iterate 
    # loop over playlist to find all songs 
    # check if file for song already exists following naming convention <song_name> - <artist_name>.mp3
    # if file exists skip
    # if file does not exist then download file and put in a folder called "songs to move" 



    
   
    for song in songs:
        song_title = song['title']
        song_artist = song['artist']

        # we should change this to check a status in the db rather than doing it like this
        
        existence = song_mp3_file_exists(base_dir, song_artist, song_title)

        if not song_mp3_file_exists(base_dir, song_artist, song_title):
            url = get_video_url.search(search_query=f"{song_title} - {song_artist}")
            # print(f"title: {title}")    
            # print(f"song_artist: {song_artist}")    
            # print(f"url: {url}")   
            
            if download_audio(song_title, song_artist, url):
                print(f"{song_title} downloaded successfully") 

if __name__ == "__main__":
    main()












