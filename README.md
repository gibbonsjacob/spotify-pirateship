# Spotify Pirate Ship 🏴‍☠️🎵

**Spotify Pirate Ship** is a Python-based tool designed to help users download music tracks from Spotify for personal, offline listening. The project automates the track retrieval to local file process in a way that’s fast, reliable, and extensible. Think of it as a “private library builder” for your music collection.

> ⚠️ **Disclaimer:** Use this tool responsibly. Only download tracks you have the rights to or for personal offline use. This tool is for educational purposes and personal convenience, not commercial piracy.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Architecture & Design](#architecture--design)
6. [Flow Overview](#flow-overview)
6. [Troubleshooting](#troubleshooting)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

* ✅ **Read All Playlist Names From Spotify** – Find all Playlist names in a Spotify Account
* ✅ **Get Track Metadata from Spotify** –Get track details for each song from Spotify
* ✅ **Find a Youtube Video Link for Each Song** – Search Youtube for a video of each song in the playlist
* ✅ **Track Download** – Download tracks from as local mp3 files from the given youtube URL(s)
* ✅ **(Alpha) Machine Learning to Classify Songs into EDM Subgenre** – Optionally classify each mp3 file into a different EDM subgenre
* ✅ **Local Database File for Storage / Tracking** – Track all the data needed for this project in a clean and sustainable manner


---

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/gibbonsjacob/spotify-pirateship.git
    cd spotify-pirate-ship
    ```


2. **Installing** `uv` 

    - If you don’t already have [`uv`](https://docs.astral.sh/uv/) installed, you can get it with one of the following:

        - **macOS / Linux**
            ```bash
            curl -LsSf https://astral.sh/uv/install.sh | sh
            ```

        - **Windows (PowerShell)**
            ```powershell
            irm https://astral.sh/uv/install.ps1 | iex
            ```

    - Once installed, you can confirm it’s working:
        ```bash
        uv --version
        ```
3. **Create a virtual environment (recommended)**

    ```bash
    uv init
    uv venv
    source .venv/bin/activate  # macOS/Linux
    .venv/scripts/activate     # Windows
    ```

4. **Install dependencies**

    ```bash
    uv pip install -r requirements.txt
    uv sync --all-groups
    ```



---

## Usage

1. **Register Spotify App**

    - This is a little out of scope for this project, but I do have a Medium article written about this: [Building Your First Data Pipeline (Part 1/4)
    ](https://medium.com/python-in-plain-english/building-your-first-data-pipeline-apis-arent-scary-part-1-4-eefbf033d056)
    - This article also covers what to do with your `client_id` and `client_secret` from Spotify


2. Follow the Instructions outlined in [google_project_setup.md](./google_project_setup.md) to establish your own Google Project
    - We do this so the 100 searches per day limit is ***per user*** rather than shared ***per project***




2. **Find All User Playlists**

    ```bash
    uv run spotify_fetcher.py --get-playlists
    ```
    - Note that you can also just copy / paste the playlist name from Spotify directly

3. **Playlist Download**

    - Add Playlist of interest to the Config section of [main.py](./main.py) (at the top)



4. **Download Songs from Playlist**

    ```bash
    uv run main.py
    ```

- This will create a folder called `song_downloads_raw` in the project root and will create a subfolder for downloads labeled with the day it ran  
    - (Note) Google API only allows for 100 YouTube searches per day – this file structure allows for easier organization with that in mind  
    - Searches and downloads are **decoupled**: searches write to a table (subject to the 100/day limit), while downloads only read from that table  
    - As long as a URL exists in the search table, you can download it **unlimited times** without using additional search quota  

- All data from each run will be written to ```songs/songs_management.db``` with lots of metadata to play with!



4. **(Optional) Machine Learning Model for Genre Classification**
    - Before Running this: 
        - This relies on having prelabeled genres for it to learn from. 
            - The way this code expects that to be done is with a folder for each genre name with mp3 files inside of it, like the below: 
                ```
                Songs/
                │
                ├─ House/         
                ├─ Dubstep/       
                ├─ Hardstyle/       
                ├─ Riddim/           
                └─ Techno/                        
                ```

        - Open [ML_genre_classifier/predictor_model.py](./ML_genre_classifier/predictor_model.py) and change the ```songs_master``` value at the top to reflect where the ```Songs``` folder (using the example above) is located


    - **Usage** 
        1. Embed labeled data:
        
            ```bash
            uv run ML_genre_classifier/predictor_model.py --embed
            ``` 
        2.  Train the model:
        
            ```bash
            uv run ML_genre_classifier/predictor_model.py --train
            ``` 
            
        3. Run the model:
        
            ```bash
            uv run ML_genre_classifier/predictor_model.py --run
            ``` 
            - This step will write the ***best*** genre classifications to `songs_management.dim_song_genre` and ***every*** genre classification to `songs_management.fact_genre_assignment`
    - **Notes**
        - This model uses a [Random Forest Classifier](https://en.wikipedia.org/wiki/Random_forest) to categorize genres
        - If you want to tinker with this, adjust the `min_genre_confidence_val` variable at the top of  [ML_genre_classifier/predictor_model.py](./ML_genre_classifier/predictor_model.py)
            - This variable represents the minimum confidence necessary to re-categorize a genre after the initial run
            - This value is currently set to 70%
            






---

## Architecture & Design

Spotify Pirate Ship is designed to be modular and maintainable:

```
spotify-pirate-ship/
│
├── ML_genre_classifier/
│   ├── embeddings.pkl
│   ├── predictor_model.py
│   ├── song_embeddings.pkl
│   └── subgenre_classifier.pkl
├── songs/
│   ├── sql_queries/
│   │   ├── distinct_album_id.sql
│   │   ├── distinct_artist_id.sql
│   │   ├── distinct_track_id.sql
│   │   ├── get_new_albums.sql
│   │   ├── get_new_artists.sql
│   │   ├── get_tracks_to_add_genre.sql
│   │   ├── get_tracks_to_download.sql
│   │   └── get_tracks_to_search.sql
│   ├── table_defs/
│   │   ├── dim_album.sql
│   │   ├── dim_artist.sql
│   │   ├── dim_song.sql
│   │   ├── dim_song_genre.sql
│   │   ├── fact_batch_execution.sql
│   │   ├── fact_error_log.sql
│   │   ├── fact_genre_assignment.sql
│   │   ├── fact_song_download.sql
│   │   ├── fact_song_features.sql
│   │   ├── fact_youtube_search.sql
│   │   ├── xref_artist_genres.sql
│   │   └── xref_song_to_artist.sql
│   └── songs_management.db
├── song_downloads_raw/
├── db_management.py
├── download_songs.py
├── get_video_url.py
├── google_project_setup.md
├── main.py
├── pyproject.toml
├── README.md
└── spotify_fetcher.py
```
--- 
## Flow Overview:
1. Clone Repo with link above
2. Create App in [Spotify Developer Portal](https://developer.spotify.com/)
3. Create project in [Google Cloud Console](https://console.cloud.google.com/) following the instructions laid out in [google_project_setup.md](./google_project_setup.md)
4. User provides a playlist URLname to the `playlist_of_interest` variable at the top of [main.py](./main.py).
5. Run [main.py](./main.py) as mentioned above
    - During Run 
        (Note all steps write data to database file): 
        1. [spotify_api.py](./spotify_api.py) fetches track (meta)data from the Spotify Endpoint.
        2.  Track data is written to db, and then subsequent scripting will find the relevant artist / album data
        3.  Search Query is created with the format ```<song name> x <artist name(s)>``` to search on Youtube
            - This was done to handle remixes/edits accordingly rather than returning the main song
            - e.g. In My Arms (Wooli Remix) 
                - This alone may still return the normal song as the first result. 
                - Our search query for this song becomes: 
                    - ```In My Arms (Wooli Remix) -  ILLENIUM x HAYLA x Wooli```
                - We add in all artist names to raise the chance we get the correct Youtube Video
        4. [get_video_url.py](./get_video_url.py) will find a link on Youtube using the Search Query from Step 3
        5. [download_songs.py](./download_songs.py) retrieves the audio file in .mp3 format from available sources.
        6. Logs written to database file


The modular design ensures you can swap out the downloader backend or add new features (like YouTube fallback or metadata tagging) without touching the main logic.

---

## Troubleshooting

* **Download fails:**

  * The most likely cause is the downloader needs updated. To solve this: 
    ```
    uv remove yt-dlp
    uv pip install -U yt-dlp
    uv sync yt-dlp
    ```

  * Make sure your browser matches the one used to export cookies.

* **Playlist not fully downloading:**

  * Spotify limits API requests; try playing with `artist_id_limit` and `album_id_limit` values in [spotify_fetcher.py](./spotify_fetcher.py) 
    * This shouldn't happen, but if it does this is what I'd do

* **Permission errors when saving files:**

  * Ensure you have write access to the output directory.
  

---

## Contributing

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/my-feature`.
3. Make your changes.
4. Submit a pull request with a detailed description of your changes.


---

## License

This project is licensed under the **MIT License**
