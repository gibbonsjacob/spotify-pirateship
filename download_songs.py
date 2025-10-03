import argparse
import re
import requests
from pathlib import Path
import yt_dlp
import os
from dotenv import load_dotenv
# import get_song_features
import get_video_url
import browser_cookie3 
import pickle





def get_cookies() -> Path:
    cj = browser_cookie3.chrome(domain_name='youtube.com')

    # Save to a file in Netscape/Mozilla format for yt-dlp
    
    with open('cookies.txt', 'w') as f:
        for cookie in cj:
            f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\tFALSE\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
    return Path('cookies.txt')










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
        'quiet': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',  # kbps
            },
        ],
        # Force Rekordbox-safe format
        'postprocessor_args': [
            '-ar', '44100',   # 44.1 kHz sample rate
            '-ac', '2',       # stereo
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        return {'download_status': True, 'exception': None}
    except Exception as e:
        print(f"Error downloading: {youtube_url}")
        print(e)
        return {'download_status': False, 'exception': e}


def main(args):

    if args.track:
        d = download_audio(args.track, Path('Downloads/'))
    
        print(d)
    if args.get_cookies:
        print(f"Full cookies.txt path: {get_cookies().absolute().as_posix()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download an mp3 file from a given youtube URL')
    parser.add_argument('--track', action='store_true', help="Download a youtube video to a local mp3 file")
    parser.add_argument('--get-cookies', action='store_true', help='Creates a cookies.txt file from Youtube')

    args = parser.parse_args()

    main(args)















