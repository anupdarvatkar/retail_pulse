import pandas as pd
from google.cloud import bigquery
import datetime

# --- Configuration ---
# Replace with your actual project ID, dataset ID, and table ID
PROJECT_ID = "your-gcp-project-id"
DATASET_ID = "your_dataset_name"
TABLE_ID = "your_table_name"

# The full table ID in the format 'project.dataset.table'
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# --- 1. Prepare Sample Raw Data (as a Pandas DataFrame) ---
raw_data = {
    'event_id': [1001, 1002, 1003, 1004],
    'user_session_id': ['abc-123', 'def-456', 'abc-123', 'ghi-789'],
    'event_name': ['click', 'purchase', 'view', 'click'],
    'event_timestamp': [
        datetime.datetime(2025, 10, 5, 10, 0, 0, tzinfo=datetime.timezone.utc),
        datetime.datetime(2025, 10, 5, 10, 5, 30, tzinfo=datetime.timezone.utc),
        datetime.datetime(2025, 10, 5, 10, 1, 15, tzinfo=datetime.timezone.utc),
        datetime.datetime(2025, 10, 5, 11, 0, 0, tzinfo=datetime.timezone.utc),
    ],
    'price_usd': [None, 9.99, None, None]
}

df = pd.DataFrame(raw_data)
print("Sample DataFrame to load:")
print(df)
print("-" * 30)

# --- 2. Initialize BigQuery Client ---
client = bigquery.Client(project=PROJECT_ID)

# --- 3. Configure the Load Job ---
job_config = bigquery.LoadJobConfig(
    # Specify the action if the table already exists:
    # 'WRITE_TRUNCATE': Overwrite the table
    # 'WRITE_APPEND': Append new data to the table (most common for raw data)
    # 'WRITE_EMPTY': Only write if the table is empty
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    
    # Optional: Define schema for better control, otherwise BigQuery tries to infer it.
    # It's good practice to explicitly define the schema for raw data.
    schema=[
        bigquery.SchemaField("event_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("user_session_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("event_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("price_usd", "FLOAT", mode="NULLABLE"),
    ]
)

# --- 4. Load the Data from DataFrame to BigQuery ---
print(f"Starting load job for table: {FULL_TABLE_ID}")
try:
    # Start the load job
    job = client.load_table_from_dataframe(
        df, FULL_TABLE_ID, job_config=job_config
    ) 

    # Wait for the job to complete
    job.result() 

    # Check for successful completion
    print("Load job completed.")
    print(f"Successfully loaded {job.output_rows} rows into {FULL_TABLE_ID}.")

except Exception as e:
    print(f"An error occurred during the BigQuery load job: {e}")