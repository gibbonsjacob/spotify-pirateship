from ctypes.util import test
import random
from xml.etree.ElementPath import prepare_descendant
import numpy as np
import os 
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_management import Database
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pickle
from pathlib import Path
from collections import Counter
import librosa 
import os 
import warnings
import argparse






######################### CONFIGS ################################

## First let's make tensorflow talk less
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings('ignore')
import tensorflow as tf
import tensorflow_hub as hub
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


embedding_file = Path("ML_genre_classifier/song_embeddings.pkl")
classifier_file = Path("ML_genre_classifier/subgenre_classifier.pkl")
min_genre_confidence_val = 0.7
n_estimators = 200
random_state = 42

################################################################




class GenrePredictor:
    """
    Summary:
        Handles embedding loading, dataset preparation, model training, evaluation, 
        and prediction for song genre classification.
    """

    def __init__(self, embedding_file: Path = None, classifier_file: Path = None):
        """
        Summary:
            Initializes the classifier with optional embedding and model file paths.
        Args:
            embedding_file (Path, optional): Path to pickle containing song embeddings.
            classifier_file (Path, optional): Path to save/load trained classifier.
        """
        self.embedding_file = embedding_file
        self.embedding_model = None
        self.embeddings_dict = None
        self.classifier_file = classifier_file
        self.classifier_model = self.load_classifier_model()
        self.training_classifier = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.X = None
        self.y = None

    def load_saved_embeddings(self):
        """
        Summary:
            Loads embeddings dictionary from a pickle file.
        Raises:
            ValueError: If no embedding file is provided.
        """
        if self.embedding_file is None:
            raise ValueError("No embedding file provided")
        with open(self.embedding_file, "rb") as f:
            self.embeddings_dict = pickle.load(f)
        print(f"Loaded embeddings from {self.embedding_file}")
    
    
    def load_embedding_model(self):
        # YAMNet is a TF Hub SavedModel, load directly with hub.load
        self.embedding_model = hub.load("https://tfhub.dev/google/yamnet/1")


    def load_classifier_model(self):
        """
        Summary:
            Loads a trained classifier from pickle.
        Raises:
            ValueError: If classifier file path is not specified.
        """
        if self.classifier_file is None:
            raise ValueError("No path specified for classifier file")
        with open(self.classifier_file, "rb") as f:
            return pickle.load(f)
        print(f"Loaded classifier from {self.classifier_file}")



    def load_and_preprocess_audio_file(self, file_path, target_sr=16000):
        """
        Loads audio from file, converts to mono, and resamples to target_sr.
        Returns waveform as a float32 numpy array and the sample rate.
        """
        try:
            audio, sr = librosa.load(file_path, sr=target_sr, mono=True)  # librosa handles resampling
            return audio.astype(np.float32), sr
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None, None
    
    
    def embed_audio_file(self, audio):
        """
        Extracts embeddings using YAMNet
        """
        try:
            scores, embeddings, spectrogram = self.embedding_model(audio)
            return np.mean(embeddings.numpy(), axis=0)  # Average over frames
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None


    def build_embeddings_file(self, songs_master):
        ### Songs master has our own labeled data in it - so we use this as our 
        ### Gold standard off of which we'll make our embeddings model

        embeddings = {}
        for root, _, files in os.walk(songs_master):
            for file in files:
                if file.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                    file_path = os.path.join(root, file)
                    audio, sr = self.load_and_preprocess_audio_file(file_path)
                    if audio is None:
                        continue

                    embedding = self.embed_audio_file(audio)
                    if embedding is None:
                        continue

                    embeddings[file_path] = embedding
                    print(f"✅ Processed {file_path}")


        with open(self.embedding_file, "wb") as f:
            pickle.dump(embeddings, f)

        return embeddings




    def prepare_training_dataset(self):
        """
        Summary:
            Converts embeddings dict into feature matrix and labels, filters classes with only 1 sample.
        Raises:
            ValueError: If embeddings are not loaded.
        """
        if self.embeddings_dict is None:
            raise ValueError("Embeddings not loaded")

        X, y_labels = [], []

        for file_path, data in self.embeddings_dict.items():
            if data is None or data.size == 0:
                print(f"Skipping {file_path}: empty or None embedding")
                continue
            X.append(data)
            genre = Path(file_path).parent.name
            y_labels.append(genre)

        X = np.stack(X)
        y = np.array(y_labels)

        counts = Counter(y)
        valid_classes = [c for c in counts if counts[c] > 1]

        self.X = np.array([x for x, label in zip(X, y) if label in valid_classes])
        self.y = np.array([label for label in y if label in valid_classes])




    def train_and_evaluate(self, test_size=0.2, random_state=42, n_estimators=200):
        """
        Summary:
            Trains a RandomForestClassifier on the prepared dataset and evaluates it.
        Args:
            test_size (float): Fraction of data for testing.
            random_state (int): Random seed for reproducibility.
            n_estimators (int): Number of trees in the Random Forest.
        Raises:
            ValueError: If dataset has not been prepared.
        """
        if self.X is None or self.y is None:
            raise ValueError("Dataset not prepared")

        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state, stratify=self.y
        )

        self.training_classifier.fit(X_train, y_train)

        y_pred = self.training_classifier.predict(X_test)
        print(classification_report(y_test, y_pred))

        




    def save_training_model(self):
        """
        Summary:
            Saves the trained classifier to a pickle file.
        Raises:
            ValueError: If no model is trained or save path is not provided.
        """
        if self.training_classifier is None:
            raise ValueError("No model trained")
        if self.classifier_file is None:
            raise ValueError("No path specified to save classifier")

        with open(self.classifier_file, "wb") as f:
            pickle.dump(self.training_classifier, f)
        print(f"Saved classifier to {self.classifier_file}")





    def extract_embedding(self,file_path):

        waveform, sr = librosa.load(file_path, sr=16000, mono=True)

        waveform_tensor = tf.convert_to_tensor(waveform, dtype=tf.float32)

        _, embeddings, _ = self.embedding_model(waveform_tensor)
        embedding_vector = np.mean(embeddings.numpy(), axis=0)
        return embedding_vector


    def classify_songs(self, track_file_map: dict) -> dict:
        """
        Args:
            track_file_map (dict): {track_id: file_path}
        Returns:
            dict: {track_id: {"genre": ..., "confidence": ...}}
        """
        
        if self.embedding_model is None:
            print("Loading YAMNet model for classification...")
            self.load_embedding_model()
            
        predicted_genres = {}
        for track_id, path in track_file_map.items():
            try:
                embedding = self.extract_embedding(path).reshape(1, -1)
                pred_label = self.classifier_model.predict(embedding)[0]
                pred_proba = self.classifier_model.predict_proba(embedding).max()
                predicted_genres[track_id] = {"genre": pred_label, "confidence": float(pred_proba)}
            except Exception as e:
                print(e)
                predicted_genres[track_id] = {"genre": "Unknown", "confidence": -1.0}
        return predicted_genres        





    def run(self): 
        songs_db = Database('songs/songs_management.db')

        songs_to_classify_raw = songs_db.select_sql(Path('songs/sql_queries/get_tracks_to_add_genre.sql').read_text().format(min_genre_confidence_val=min_genre_confidence_val))
        songs_with_genre_stg = songs_to_classify_raw.copy()
        
        track_file_map = dict(
                            zip(
                                songs_with_genre_stg['track_id'], 
                                songs_with_genre_stg['downloaded_to_file_path']
                                )
                            )
        predictions = self.classify_songs(track_file_map)
        
        songs_with_genre_stg['genre_name'] = songs_with_genre_stg['track_id'].map(
            {k: v['genre'] for k, v in predictions.items()}
        )
        songs_with_genre_stg['confidence'] = songs_with_genre_stg['track_id'].map(
            {k: v['confidence'] for k, v in predictions.items()}
        )

        
        ## First let's build and insert our fact rows

        fact_genre_assignment = songs_with_genre_stg.copy().drop(columns=['downloaded_to_file_path'])
        fga_insert_sql = songs_db.build_insert_into_sql('fact_genre_assignment', fact_genre_assignment)
        songs_db.execute_sql(fga_insert_sql)


        ## Now let's do our dim table, which uses slightly more complex sql
        ## For all new track_id's, we simply add a row. For any existing track id's that reran, 
        ## we insert whichever confidence value is higher between the new and existing one, and update 
        ## metadata accordingly
        
        dim_song_genre = songs_with_genre_stg.copy().drop(columns=['downloaded_to_file_path'])
        dsg_insert_sql = songs_db.build_insert_into_sql('dim_song_genre',
                                                        dim_song_genre, 
                                                        on_conflict="""(track_id) DO UPDATE SET
                                                                        genre_name = excluded.genre_name,
                                                                        confidence = excluded.confidence,
                                                                        insert_date = excluded.insert_date
                                                                    WHERE excluded.confidence > confidence;  """) ## grab whichever one has a higher confidence value
        
        songs_db.execute_sql(dsg_insert_sql)


        print(dim_song_genre.groupby('genre_name').count())




def main(predictor: GenrePredictor, args, songs_master: Path = Path(r"D:/Songs")): 

    if args.embed:
        print('Starting new Embedding session')
        predictor.load_embedding_model()
        predictor.build_embeddings_file(songs_master)

    
    if args.train: 

        print("Starting new Training session")
        predictor.load_saved_embeddings()
        predictor.prepare_training_dataset()
        predictor.train_and_evaluate(test_size=0.2, 
                                     random_state=42, 
                                     n_estimators = 200)
        predictor.save_training_model()

    predictor.run()


if __name__ == '__main__': 

    parser = argparse.ArgumentParser(description='Work with ML Model to Predict Genre of an mp3 file')
    parser.add_argument('--train', action="store_true", help="If true model will retrain itself, otherwise this step will be skipped")
    parser.add_argument('--embed', action="store_true", help="If true model will look for new songs to embed to be used in training")
    # parser.add_argument('--', action="store_true", help="If true model will retrain itself, otherwise this step will be skipped")
    
    predictor = GenrePredictor(embedding_file=embedding_file, 
                               classifier_file=classifier_file)
    
    args = parser.parse_args()

    main(predictor, args)
