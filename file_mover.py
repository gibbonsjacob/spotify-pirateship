import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Tuple
import json

class FileMover:
    """
    Handles file movement and classification tracking for song downloads.
    Provides discovery, execution, and manual detection functionality.
    All configuration values are class-level but lowercase.
    """

    # ===========================
    # ===== CLASS CONFIG =======
    # ===========================
    classified_root = Path("D:/Songs")
    min_confidence_to_move_file = 0.9
    min_confidence_for_training = 0.95
    downloads_raw = Path("song_downloads_raw/")


    # ===========================
    # ===== FILE HASH UTILS =====
    # ===========================
    @staticmethod
    def generate_file_hash(file_path: Path) -> str:
        """Generate an MD5 hash for a given file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    # ===========================
    # ===== FILE MOVEMENT =======
    # ===========================
    @classmethod
    def move_file(cls, row: pd.DataFrame) -> dict:
        """
        Move a file to a classified destination based on confidence score.

        Args:
            source_file (Path): Path to the file being moved.
            destination_folder (Path): Target folder for the classified file.
            confidence (float): Confidence score for classification.

        Returns:
            dict: Fact record summarizing the file move event.
        """

        track_id = row['track_id']

        current_path = row['current_path']
        target_directory = row['target_directory']
        predicted_genre_confidence = row['predicted_genre_confidence']
        change_reason = row['last_change_reason']



        source_file = Path(current_path)
        destination_folder = Path(target_directory)
        destination_folder.mkdir(parents=True, exist_ok=True) #this shouldn't ever hit but we'll put it here just in case



        if predicted_genre_confidence >= cls.min_confidence_to_move_file:
            destination_file = destination_folder / source_file.name
            shutil.move(str(source_file), str(destination_file))
            file_hash = cls.generate_file_hash(destination_file)

            return {
                "track_id": track_id,
                "source_path": str(source_file),
                "target_path": str(destination_file) if destination_file else None,
                "file_hash": file_hash,
                "change_reason": change_reason,
                "confidence": predicted_genre_confidence,
                "timestamp": datetime.now()
            }
    
        

    # ===========================
    # ===== INITIAL DOWNLOAD ===
    # ===========================
    @classmethod
    def handle_initial_download(cls, row) -> dict:
        """Handle a file that appears for the first time in the source directory."""
        file_hash = cls.generate_file_hash(row['downloaded_to_file_path'])
        return {
            "track_id": row['track_id'],
            "source_path": None,
            "target_path": str(row['downloaded_to_file_path']),
            "file_hash": file_hash,
            "change_reason": "Initial Download", 
            "confidence": -1,
            "changed_at": datetime.now()
        }

    # ===========================
    # ===== DISCOVERY / ANALYTICS ==
    # ===========================
    @classmethod
    def discover_files_for_action(cls, df: pd.DataFrame):
        """
        Categorize files into movement, training, and manual review groups
        based on class-level confidence thresholds.

        Args:
            df (pd.DataFrame): DataFrame containing `track_id`, `confidence`, 
                               `predicted_label`, and `file_path`.

        Returns:
            dict[str, pd.DataFrame]: DataFrames categorized by action.
        """
        required_cols = {"track_id", "predicted_genre_confidence", "genre_name", "current_path"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Input DataFrame missing required columns: {required_cols - set(df.columns)}")

        to_move = df[df["predicted_genre_confidence"] >= cls.min_confidence_to_move_file].copy()
        to_review = df[df["predicted_genre_confidence"] < cls.min_confidence_to_move_file].copy()

        return {
            "to_move": to_move,
            "to_review": to_review
        }

    # ===========================
    # ===== MANUAL CLASS DETECTION ==
    # ===========================
    @classmethod
    def detect_manual_classifications(cls, dim_song_file_location: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Detect files that were manually classified: exist in classified_root
        that do not have a matching path in dim_song_file_location.

        Args:
            dim_song_file_location (pd.DataFrame): DataFrame of currently known path for each track.

        Returns:
            pd.DataFrame: Subset of new paths found in classified_root (manual classification).
        """

        # Map filenames in D:/Songs to track_ids using downloaded_to_file_path basename
        file_to_track = {Path(row["current_path"][0]).name: row["track_id"] for _, row in dim_song_file_location.iterrows()}
        dim_records = []
        fact_records = []
        no_match_files = {}
        existing_paths = set(Path(p).resolve() for paths in dim_song_file_location["current_path"] for p in paths)

        # Iterate over D:/Songs to populate dim and manual classification fact records
        for genre_folder in cls.classified_root.iterdir():
            if not genre_folder.is_dir():
                continue
 
            for file_path in genre_folder.glob("*.mp3"):
                try:
                    if file_path.resolve() in existing_paths:
                        continue 
                    file_name = file_path.name
                    print(file_path.resolve())
                    track_id = file_to_track.get(file_name)
                    if track_id:

                        dim_records.append({
                            "track_id": track_id,
                            "current_path": str(file_path),
                            "file_hash": cls.generate_file_hash(file_path),
                            "last_changed": datetime.now(),
                            "last_change_reason": "Manual Classification",
                            "last_confidence": 1.0,
                        })

                        raw_file_row = dim_song_file_location[dim_song_file_location["track_id"] == track_id]
                        raw_path = None

                        if not raw_file_row.empty:
                            paths = raw_file_row.iloc[0]["current_path"]
                            if isinstance(paths, str):
                                paths = json.loads(paths)
                            raw_path = Path(paths[0])  # pick the first path

                        else:
                            raw_path = cls.downloads_raw / file_name

                        fact_records.append({
                            "track_id": track_id,
                            "source_path": str(raw_path) if raw_path.exists() else None,
                            "target_path": str(file_path),
                            "file_hash": cls.generate_file_hash(file_path),
                            "change_reason": "Manual Classification",
                            "confidence": 1.0,
                            "changed_at": datetime.now(),
                        })
                    else:
                        no_match_files[str(file_path)] = 'no track id'

                except:
                    # some of our files were downloaded before this script was built
                    # We'll just log through those here for now
                    no_match_files[str(file_path)] = 'no matching record'





        # Lastly we'll convert everything to df's and return them with the no match dict

        dim_df = pd.DataFrame(dim_records)
        fact_df = pd.DataFrame(fact_records)


        return dim_df, fact_df, no_match_files

            

        




    # ===========================
    # ===== OUTPUT HELPERS ======
    # ===========================
    # @staticmethod
    # def records_to_dataframe(records: list[dict]) -> pd.DataFrame:
    #     """
    #     Convert a list of movement records into a standardized DataFrame.

    #     Args:
    #         records (list[dict]): List of movement/fact record dictionaries.

    #     Returns:
    #         pd.DataFrame: Structured DataFrame of movement logs.
    #     """
    #     if not records:
    #         return pd.DataFrame(
    #             columns=[
    #                 "source_path",
    #                 "destination_path",
    #                 "file_hash",
    #                 "moved",
    #                 "movement_type",
    #                 "confidence",
    #                 "timestamp",
    #             ]
    #         )
    #     return pd.DataFrame(records)


    # @staticmethod
    # def prepare_initial_download_records(df: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     Prepare initial download fact records for newly downloaded files.

    #     Args:
    #         df (pd.DataFrame): DataFrame containing at least 'track_id' and 'file_path' columns.

    #     Returns:
    #         pd.DataFrame: Structured DataFrame with initial download records.
    #     """
    #     required_cols = {"track_id", "file_path"}
    #     if not required_cols.issubset(df.columns):
    #         raise ValueError(f"Input DataFrame missing required columns: {required_cols - set(df.columns)}")

    #     records = []
    #     for _, row in df.iterrows():
    #         path = Path(row["file_path"])
    #         file_hash = FileMover.generate_file_hash(path)
    #         records.append({
    #             "track_id": row["track_id"],
    #             "source_path": None,
    #             "destination_path": str(path),
    #             "file_hash": file_hash,
    #             "moved": False,
    #             "movement_type": "initial_download",
    #             "confidence": float(-1),
    #             "timestamp": datetime.now().isoformat()
    #         })
    #     return pd.DataFrame(records)
