from file_mover import FileMover
from db_management import Database
import pandas as pd
from pathlib import Path
import json
import datetime

def ensure_list(s):
    if isinstance(s, str) and s.startswith("["):  # looks like JSON
        return json.loads(s)
    else:  # plain string, wrap in a list
        return [s]

def main():


    # need to figure out how / why dupes are being created and written still
    # data cleanup is needed so badly here. probably need to drop the tables and start over
    # it seems like everything is pretty much working as intended,
    # but dupes are coming in somewhere and we need to solve


    ## I think it's something to do with the list of paths. 
    ## Right now i think every file in D:/Songs is getting a new record
    ## every run rather than only when it actually moved




    mover = FileMover()
    songs_db = Database(Path('songs/songs_management.db'))
    
    # Load existing dim table
    dim_song_file_location = songs_db.select_sql(
        Path('songs/sql_queries/get_all_from_dim_song_file_location.sql').read_text()
    )

    dim_song_file_location["current_path"] = dim_song_file_location["current_path"].apply(ensure_list)


    dim_records = []
    fact_records = []

    ###### Step 1: Manual classifications ######



    dim_df, fact_df, no_matches = mover.detect_manual_classifications(dim_song_file_location)


    with open("test_outputs/no_matches.json", "w") as f:
        json.dump(no_matches, f, indent=2)



    for track_id, group in dim_df.groupby("track_id", group_keys=False):
        all_paths = sorted(set(group["current_path"]))  # merge all paths
        if not isinstance(all_paths, list):
            all_paths = [all_paths]
        merged_path_json = json.dumps(all_paths)


        # Even though we store a list, we don't actually care about
        # ALL the paths that exist. We only care that *one of them* exists
        best_record = group.iloc[0].copy()
        best_record["current_path"] = merged_path_json
        dim_records.append(best_record.to_dict())

    # Add fact records as-is
    fact_records.extend(fact_df.to_dict('records'))


    ###### Step 2: Predictions ######

    # Note - we don't care about ALL the predictions that have happened
    # We only care about the BEST one
    max_confidence_predictions = songs_db.select_sql(
        Path('songs/sql_queries/get_prediction_with_path.sql').read_text()
    )
    new_predictions = max_confidence_predictions[
        max_confidence_predictions['predicted_genre_confidence'] > 
        max_confidence_predictions['known_genre_confidence']
    ]

    actions = mover.discover_files_for_action(new_predictions)

    # First we'll filter out anything that's not actually moving at all
    # Note - normally we'd do this upstream but this was the easiest way to 
    # account for both manual classification and prediction in one place
    to_move = pd.DataFrame(actions["to_move"])
    to_review = actions["to_review"]



    if len(to_move) > 0:


        to_move['target_directory'] = to_move['genre_name'].apply(lambda genre: str(Path(mover.classified_root) / genre))

        to_move['last_changed'] = datetime.datetime.now()
        to_move['last_change_reason'] = 'ML Classification'
        to_move = to_move[to_move.apply(
            lambda row: str(Path(row["current_path"][0])) != row["target_path"] and
                        not Path(row["target_path"]).exists(),
            axis=1
        )]

        movements = []
        for _, row in to_move.iterrows():
            result = mover.move_file(row)
            if result: 
                movements.append(result)


        movements_df = pd.DataFrame(movements)

        # Now we'll build our dim and fact tables accordingly
        dim = movements_df.copy().drop(columns=['source_path'])


        dim_col_order = [
                    'track_id',
                    'current_path', 
                    'file_hash',  
                    'last_changed', 
                    'last_change_reason', 
                    'last_confidence'
                    ] 
        
        dim.rename(columns={'target_path': 'current_path',
                            'timestamp': 'last_changed',
                            'change_reason': 'last_change_reason', 
                            'confidence': 'last_confidence' 
                            }, inplace=True)

        dim_reordered = dim[dim_col_order]

        fact = movements_df.copy()
        fact_col_order = [
                        'track_id', 
                        'source_path', 
                        'target_path', 
                        'file_hash', 
                        'change_reason', 
                        'confidence', 
                        'changed_at'
                    ]
        
        fact.rename(columns={'timestamp': 'changed_at'}, inplace=True)
        fact_reordered = fact[fact_col_order]

        dim_records.extend(dim_reordered.to_dict('records'))
        fact_records.extend(fact_reordered.to_dict('records'))

    ###### Step 3: Insert into database ######
    merged_dim_df = pd.DataFrame(dim_records).reset_index(drop=True)
    merged_fact_df = pd.DataFrame(fact_records).reset_index(drop=True)
    if len(merged_dim_df) > 0:
        dim_sql = songs_db.build_insert_into_sql(
            'dim_song_file_location',
            merged_dim_df,
            on_conflict="""
                (track_id) DO UPDATE
                SET
                    file_hash = EXCLUDED.file_hash,
                    last_changed = EXCLUDED.last_changed,
                    last_change_reason = EXCLUDED.last_change_reason,
                    last_confidence = EXCLUDED.last_confidence,
                    current_path = EXCLUDED.current_path
                WHERE EXCLUDED.last_confidence >= dim_song_file_location.last_confidence
            """
        )
        songs_db.execute_sql(dim_sql)

    if len(merged_fact_df) > 0:
        
        fact_sql = songs_db.build_insert_into_sql(
            'fact_song_file_location_change',
            merged_fact_df
        )

        songs_db.execute_sql(fact_sql)


if __name__ == '__main__':
    main()