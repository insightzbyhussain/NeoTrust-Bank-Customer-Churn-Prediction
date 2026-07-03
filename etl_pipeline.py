import sqlite3
import pandas as pd
import logging
import time
from ingestion_db import ingest_db, engine

logger = logging.getLogger('etl_pipeline')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('logs/etl_pipeline.log')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger.addHandler(file_handler)

conn = sqlite3.connect('churn.db')

def create_master_table(conn):
    """Merges customer, transaction and support ticket tables into one master table"""
    
    query = """
    WITH transaction_summary AS (
        SELECT
            customer_id,
            COUNT(transaction_id)        AS total_transactions,
            SUM(CAST(REPLACE(REPLACE(amount, 'Rs. ', ''), ',', '') AS FLOAT)) AS total_transaction_amount,
            MAX(transaction_date)        AS last_transaction_date
        FROM transaction_log
        GROUP BY customer_id
    ),
    ticket_summary AS (
        SELECT
            customer_id,
            COUNT(ticket_id)             AS total_tickets,
            SUM(CASE WHEN issue_type IN ('Account Closure Request', 
                'Complaint - Hidden Charges', 
                'Complaint - Poor Service') 
                THEN 1 ELSE 0 END)       AS high_risk_tickets
        FROM support_tickets
        GROUP BY customer_id
    )
    SELECT
        c.customer_id,
        c.signup_date,
        c.age,
        c.city,
        c.acquisition_channel,
        c.employment_type,
        c.monthly_income,
        c.active_lending_relationships,
        c.kyc_status,
        c.primary_product,
        COALESCE(t.total_transactions, 0)        AS total_transactions,
        COALESCE(t.total_transaction_amount, 0)  AS total_transaction_amount,
        t.last_transaction_date,
        COALESCE(tk.total_tickets, 0)            AS total_tickets,
        COALESCE(tk.high_risk_tickets, 0)        AS high_risk_tickets
    FROM customer_master c
    LEFT JOIN transaction_summary t  ON TRIM(UPPER(c.customer_id)) = TRIM(UPPER(t.customer_id))
    LEFT JOIN ticket_summary tk      ON TRIM(UPPER(c.customer_id)) = TRIM(UPPER(tk.customer_id))
    """
    
    df = pd.read_sql_query(query, conn)
    logger.info(f"Master table created with {len(df)} rows and {df.shape[1]} columns")
    return df

def clean_data(df):
    """Cleans the merged master table"""
    
    logger.info(f"Shape before cleaning: {df.shape}")
    
    # 1. Remove duplicate customer IDs
    df['customer_id'] = df['customer_id'].astype(str).str.strip().str.upper()
    df = df.drop_duplicates(subset='customer_id', keep='first')
    logger.info(f"After removing duplicates: {len(df)} rows")
    
    # 2. Standardize city names
    city_mapping = {
        'MUMBAI'      : 'Mumbai',
        'BANDRA WEST' : 'Mumbai',
        'BKC'         : 'Mumbai',
        'PUNE'        : 'Pune',
        'BENGALURU'   : 'Bengaluru',
        'DELHI'       : 'Delhi',
        'HYDERABAD'   : 'Hyderabad',
        'CHENNAI'     : 'Chennai',
        'AHMEDABAD'   : 'Ahmedabad',
        'KOLKATA'     : 'Kolkata'
    }
    df['city'] = df['city'].astype(str).str.strip().str.upper().map(city_mapping)
    
    # 3. Standardize categorical columns
    df['acquisition_channel'] = df['acquisition_channel'].astype(str).str.strip().str.title()
    df['employment_type']     = df['employment_type'].astype(str).str.strip().str.title()
    df['kyc_status']          = df['kyc_status'].astype(str).str.strip().str.title()
    df['primary_product']     = df['primary_product'].astype(str).str.strip().str.title()
    
    # 4. Clean monthly income — strip ₹ symbol and commas, convert to float
    df['monthly_income'] = (
        df['monthly_income']
        .astype(str)
        .str.replace('₹', '', regex=False)
        .str.replace(',', '', regex=False)
        .str.strip()
    )
    df['monthly_income'] = pd.to_numeric(df['monthly_income'], errors='coerce')
    
    # 5. Fill missing values
    df['age']            = df['age'].fillna(df['age'].median())
    df['monthly_income'] = df['monthly_income'].fillna(df['monthly_income'].median())
    df['employment_type'] = df['employment_type'].replace('Nan', 'Unknown')
    df['kyc_status']      = df['kyc_status'].replace('Nan', 'Unknown')
    
    # 6. Convert signup_date to datetime
    df['signup_date'] = pd.to_datetime(df['signup_date'], dayfirst=True, errors='coerce')
    
    # 7. Convert last_transaction_date to datetime
    df['last_transaction_date'] = pd.to_datetime(
        df['last_transaction_date'], dayfirst=True, errors='coerce'
    )
    
    logger.info(f"Shape after cleaning: {df.shape}")
    logger.info("Data cleaning complete")
    return df

def define_churn(df):
    """Creates churn label based on transaction inactivity"""
    
    reference_date = pd.Timestamp('2024-09-30')
    
    df['days_since_last_transaction'] = (
        reference_date - df['last_transaction_date']
    ).dt.days
    
    # Churn = 1 if no transaction in last 90 days or no transaction at all
    df['churn'] = (
        (df['days_since_last_transaction'] > 90) |
        (df['last_transaction_date'].isna())
    ).astype(int)
    
    churn_rate = df['churn'].mean() * 100
    logger.info(f"Churn label created. Churn rate: {churn_rate:.2f}%")
    logger.info(f"Total churned customers: {df['churn'].sum()}")
    logger.info(f"Total active customers: {(df['churn'] == 0).sum()}")
    
    return df

if __name__ == '__main__':
    start = time.time()
    
    logger.info('---------------------ETL Pipeline Started---------------------')
    
    logger.info('Step 1: Creating master table by merging 3 tables...')
    master_df = create_master_table(conn)
    
    logger.info('Step 2: Cleaning data...')
    clean_df = clean_data(master_df)
    
    logger.info('Step 3: Defining churn label...')
    final_df = define_churn(clean_df)
    
    logger.info('Step 4: Saving clean master table to database...')
    ingest_db(final_df, 'clean_master', engine)
    
    logger.info('Step 5: Saving clean master table to CSV...')
    final_df.to_csv('clean_master.csv', index=False)
    
    end = time.time()
    total_time = (end - start) / 60
    logger.info(f'Total time taken: {total_time:.2f} minutes')
    logger.info('---------------------ETL Pipeline Complete---------------------')