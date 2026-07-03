import os
import pandas as pd
from sqlalchemy import create_engine
import logging
import time

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

engine = create_engine('sqlite:///churn.db')

def ingest_db(df, table_name, engine):
    """Ingests a dataframe into a SQLite database table"""
    df.to_sql(table_name, con=engine, if_exists='replace', index=False, chunksize=500, method='multi')
    logging.info(f"Successfully ingested {table_name} into database")

def load_raw_data():
    """Loads all CSV files from raw_data folder and ingests into database"""
    start = time.time()
    
    for file in os.listdir('raw_data'):
        if file.endswith('.csv'):
            file_path = os.path.join('raw_data', file)
            df = pd.read_csv(file_path)
            logging.info(f"Ingesting {file} into database")
            ingest_db(df, file[:-4], engine)
    
    end = time.time()
    total_time = (end - start) / 60
    logging.info('---------------------Ingestion Complete---------------------')
    logging.info(f'Total time taken: {total_time} minutes')

if __name__ == '__main__':
    load_raw_data()