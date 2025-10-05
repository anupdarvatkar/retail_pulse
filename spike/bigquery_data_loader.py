from google.cloud import bigquery
import json
import os
import argparse
import sys
import logging
from google.cloud.exceptions import NotFound
from dotenv import load_dotenv

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class BigQueryLoader:
    """
    A class to handle loading data into a BigQuery table from a configuration.
    """
    def __init__(self, schema_name: str):
        """
        Initializes the loader by reading environment and config files.
        """
        self.schema_name = schema_name
        self._load_config()
        self._initialize_client()

    def _load_config(self):
        """Loads configuration from .env and config.json."""
        load_dotenv()
        script_dir = os.path.dirname(__file__)
        config_path = os.path.join(script_dir, "config.json")

        logging.info(f"Loading configuration from: {config_path}")
        with open(config_path, 'r') as f:
            config = json.load(f)

        # --- Extract BigQuery Target Configuration ---
        bq_target = config.get("bigquery_target", {})
        self.project_id = os.getenv("GCP_PROJECT_ID") or bq_target.get("project_id")
        self.dataset_id = bq_target.get("dataset_id")

        if not all([self.project_id, self.dataset_id]):
            logging.error("'project_id' (or GCP_PROJECT_ID env var) and 'dataset_id' must be set.")
            sys.exit(1)

        # --- Extract Schema-Specific Configuration ---
        all_schemas = config.get("schemas", {})
        schema_config = all_schemas.get(self.schema_name)

        if not schema_config:
            logging.error(f"Schema configuration for '{self.schema_name}' not found in config.json.")
            logging.info(f"Available schemas are: {list(all_schemas.keys())}")
            sys.exit(1)

        self.table_id = schema_config.get("table_id")
        data_file_name = schema_config.get("data_file")
        self.schema_definition = schema_config.get("definition")

        if not all([self.table_id, data_file_name, self.schema_definition]):
            logging.error(f"Config for schema '{self.schema_name}' is malformed. It must contain 'table_id', 'data_file', and 'definition'.")
            sys.exit(1)

        self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        self.data_file_path = os.path.join(script_dir, data_file_name)
        self.write_disposition = config.get("write_disposition", "WRITE_APPEND")

        logging.info(f"Using Project ID: {self.project_id}")
        logging.info(f"Using schema: '{self.schema_name}'")
        logging.info(f"Target table: '{self.full_table_id}'")

    def _initialize_client(self):
        """Initializes the BigQuery client."""
        self.client = bigquery.Client(project=self.project_id)

    def setup_destination(self):
        """Ensures the destination dataset and table exist."""
        # Ensure dataset exists
        dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
        try:
            self.client.get_dataset(dataset.dataset_id)
            logging.info(f"Dataset '{dataset.dataset_id}' already exists.")
        except NotFound:
            logging.info(f"Dataset '{dataset.dataset_id}' not found, creating it...")
            self.client.create_dataset(dataset, timeout=30)
            logging.info(f"Dataset '{dataset.dataset_id}' created.")

        # Ensure table exists
        try:
            self.client.get_table(self.full_table_id)
            logging.info(f"Table '{self.full_table_id}' already exists.")
        except NotFound:
            logging.info(f"Table '{self.full_table_id}' not found, creating it...")
            schema = [
                bigquery.SchemaField(field["name"], field["type"], mode=field.get("mode", "NULLABLE"))
                for field in self.schema_definition
            ]
            table = bigquery.Table(self.full_table_id, schema=schema)
            self.client.create_table(table)
            logging.info(f"Table '{self.full_table_id}' created with specified schema.")

    def load_data(self):
        """Loads data from the source file into the BigQuery table."""
        logging.info(f"Loading data from: {self.data_file_path}")
        logging.info(f"Using write disposition: {self.write_disposition}")

        schema = [
            bigquery.SchemaField(field["name"], field["type"], mode=field.get("mode", "NULLABLE"))
            for field in self.schema_definition
        ]

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=self.write_disposition,
        )

        logging.info(f"Starting load job for table: {self.full_table_id}")
        try:
            with open(self.data_file_path, "rb") as source_file:
                job = self.client.load_table_from_file(
                    source_file, self.full_table_id, job_config=job_config
                )
            job.result()  # Wait for the job to complete

            logging.info("Load job completed.")
            logging.info(f"Successfully loaded {job.output_rows} rows into {self.full_table_id}.")

        except NotFound:
            logging.error(f"Table '{self.full_table_id}' not found during load. Please ensure it exists.")
            sys.exit(1)
        except Exception as e:
            logging.error(f"An error occurred during the BigQuery load job: {e}", exc_info=True)
            sys.exit(1)

def main(schema_name):
    """
    Main function to load data into BigQuery based on a specified schema.
    """
    # 1. Initialize the loader with the specified schema
    loader = BigQueryLoader(schema_name)

    # 2. Ensure the destination dataset and table are ready
    loader.setup_destination()

    # 3. Load the data
    loader.load_data()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load data into a BigQuery table using a specified schema.")
    parser.add_argument("schema_name", type=str, help="The name of the schema to use from config.json.")
    args = parser.parse_args()
    main(args.schema_name)