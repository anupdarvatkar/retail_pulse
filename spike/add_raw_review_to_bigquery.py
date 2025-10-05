import argparse
import datetime
import os

import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

class BigQueryTableManager:
    """A class to manage a specific BigQuery table."""

    def __init__(self):
        """Initializes the manager, loads configuration, and sets up the BQ client."""
        load_dotenv()
        self._load_and_validate_config()
        self.client = bigquery.Client(project=self.project_id)
        self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    def _load_and_validate_config(self):
        """Loads and validates required environment variables."""
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset_id = os.getenv("BIGQUERY_DATASET_ID")
        self.table_id = os.getenv("BIGQUERY_TABLE_ID")

        if not all([self.project_id, self.dataset_id, self.table_id]):
            raise ValueError(
                "Missing required environment variables. "
                "Please create a .env file and set GCP_PROJECT_ID, BIGQUERY_DATASET_ID, and BIGQUERY_TABLE_ID."
            )

    def add_sample_data(self):
        """Prepares and loads sample data into the BigQuery table."""
        # 1. Prepare Sample Raw Data (as a Pandas DataFrame)
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

        # 2. Configure the Load Job
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema=[
                bigquery.SchemaField("event_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("user_session_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("event_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("price_usd", "FLOAT", mode="NULLABLE"),
            ]
        )

        # 3. Load the Data from DataFrame to BigQuery
        print(f"Starting load job for table: {self.full_table_id}")
        try:
            job = self.client.load_table_from_dataframe(
                df, self.full_table_id, job_config=job_config
            )
            job.result()  # Wait for the job to complete
            print("Load job completed.")
            print(f"Successfully loaded {job.output_rows} rows into {self.full_table_id}.")
        except Exception as e:
            print(f"An error occurred during the BigQuery load job: {e}")

    def delete_all_data(self):
        """Deletes all data from the BigQuery table (TRUNCATE)."""
        print(f"Attempting to delete all data from table: {self.full_table_id}")
        # Using TRUNCATE is efficient for deleting all rows.
        # Note: This is a DML statement and may incur costs.
        query = f"TRUNCATE TABLE `{self.full_table_id}`"
        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for the DML statement to complete
            print(f"Successfully deleted all data from {self.full_table_id}.")
        except Exception as e:
            print(f"An error occurred while trying to delete data: {e}")


def main():
    """Main function to parse arguments and execute table actions."""
    parser = argparse.ArgumentParser(description="Manage BigQuery table data.")
    parser.add_argument(
        "--action",
        choices=["add", "delete"],
        required=True,
        help="Action to perform: 'add' sample data or 'delete' all data from the table."
    )
    args = parser.parse_args()

    try:
        manager = BigQueryTableManager()
        if args.action == "add":
            manager.add_sample_data()
        elif args.action == "delete":
            manager.delete_all_data()
    except ValueError as e:
        print(f"Configuration Error: {e}")


if __name__ == "__main__":
    main()