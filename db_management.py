
import pandas as pd
import sqlite3
import numpy as np 
from datetime import datetime




class Database: 
    def __init__(self, name):
        self.name = name
        self.connection = None
        self.cursor = None 
        self._ensure()




            

    def _initialize(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]: 
        try:
            connection = sqlite3.connect(self.name)
            cursor = connection.cursor()

            return connection, cursor
        except Exception as e: 
            print(f"An error occurred while connecting: {e}")
            return False
        
    def _kill(self):
        self.cursor.close()
        self.connection.close()


    def _ensure(self) -> None:
        # Ensures the db file exists, and creates it if not
        try:
            self.connection, self.cursor = self._initialize()
            if not self.connection:
                return
        finally:
            self._kill()

    def execute_sql(self, sql: str) -> None: 
        
        try:
            self.connection, self.cursor = self._initialize()

            self.cursor.execute(sql)
            self.connection.commit()
            

        except Exception as e: 
            print(f"An error occurred while running query: {e}")
            print(sql)
            return False
        
        finally: 
            self._kill()

    def select_sql(self, sql: str) -> pd.DataFrame:

        try:
            self.connection, self.cursor = self._initialize()

            self.cursor.execute(sql)
            columns = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()
            return pd.DataFrame(results, columns=columns)

        except Exception as e: 
            print(f"An error occurred while running query: {e}")
            print(sql)
            return False
        
        finally: 
            self._kill()


    def build_insert_into_sql(
        self,
        dest_table: str,
        df: pd.DataFrame,
        on_conflict: str = "",
        add_insert_date: bool = True
    ) -> str:
        """Accepts a pandas df and builds an INSERT INTO sql statement
        (Assumes resulting table has the same schema as the df)

        Args:
            dest_table (str): name of table to insert to
            df (pd.DataFrame): df to build SQL from
            on_conflict (str): Args passed to the ON CONFLICT SQL Clause
            add_insert_date (bool): adds a column to the df with today's date if True

        Returns:
            str: SQL string with INSERT INTO statement
        """
        if len(on_conflict) > 0:
            on_conflict = f"ON CONFLICT {on_conflict}"

        df = df.replace({np.nan: None})

        if add_insert_date:
            df["insert_date"] = str(datetime.today().strftime("%Y-%m-%d"))

        df = self._sanitize_dates(df)

        columns = ", ".join(df.columns)

        value_strings = []
        for _, row in df.iterrows():
            formatted = []
            for val in tuple(row):
                if val is None:
                    formatted.append("NULL")
                elif isinstance(val, str):
                    safe_val = val.replace("'", "''")
                    formatted.append(f"'{safe_val}'")
                else:
                    formatted.append(str(val))
            value_strings.append(f"({', '.join(formatted)})")

        sql = f"INSERT INTO {dest_table} ({columns}) VALUES {', '.join(value_strings)} {on_conflict}".strip()
        return sql







    def _sanitize_dates(self, df: pd.DataFrame) -> pd.DataFrame: 
        """ Sanitizes date columns in a pandas df to strings rather than date objects 
        so they place nicely with a SQL INSERT INTO statement """

        for col in df.columns: 
            df[col] = df[col].apply(
                lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (datetime, pd.Timestamp)) else x
            )

        return df















def main():

    songs_db = Database('songs_management.db')


if __name__ == '__main__': 
    main()