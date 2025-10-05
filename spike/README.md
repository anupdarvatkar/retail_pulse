# BigQuery Data Loader Spike

This directory contains a spike for a Python script to load data into Google BigQuery from local newline-delimited JSON files.

## Purpose

The `bigquery_data_loader.py` script provides a configurable way to:
1.  Define different data schemas and target tables in a `config.json` file.
2.  Automatically create the BigQuery dataset and table if they don't exist.
3.  Load data from a specified local NDJSON (`.jsonl`) file into the target BigQuery table.

This is useful for initial data seeding or bulk-loading data for development and testing environments.

## Prerequisites

1.  **Python 3**: The script is written in Python.
2.  **Google Cloud SDK**: You need to have `gcloud` CLI installed and authenticated. Run `gcloud auth application-default login` to authenticate for local development.
3.  **Python Dependencies**: Install the required packages. It's recommended to create a `requirements.txt` file in the `spike` directory with the following content:
    ```
    google-cloud-bigquery
    python-dotenv
    ```
    Then install them using:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The script relies on a few configuration files.

### 1. Environment Variables (`.env`)

Create a `.env` file in the `spike` directory to store your Google Cloud Project ID.

```
# .env
GCP_PROJECT_ID="your-gcp-project-id"
```

### 2. Main Configuration (`config.json`)

Create a `config.json` file in the `spike` directory. This file defines the BigQuery target, write behavior, and one or more schemas for different data types.

```json
{
  "bigquery_target": {
    "dataset_id": "retail_pulse_dev"
  },
  "write_disposition": "WRITE_TRUNCATE",
  "schemas": {
    "users": {
      "table_id": "users",
      "data_file": "data/users.jsonl",
      "definition": [
        { "name": "user_id", "type": "STRING", "mode": "REQUIRED" },
        { "name": "name", "type": "STRING" },
        { "name": "email", "type": "STRING" },
        { "name": "created_at", "type": "TIMESTAMP" }
      ]
    },
    "products": {
      "table_id": "products",
      "data_file": "data/products.jsonl",
      "definition": [
        { "name": "product_id", "type": "STRING", "mode": "REQUIRED" },
        { "name": "name", "type": "STRING" },
        { "name": "price", "type": "FLOAT" }
      ]
    }
  }
}
```

**Configuration Details:**
*   `bigquery_target`:
    *   `project_id`: (Optional) Your GCP project ID. Can also be set via the `GCP_PROJECT_ID` environment variable.
    *   `dataset_id`: The name of the BigQuery dataset to use.
*   `write_disposition`: (Optional) How to write data. Defaults to `WRITE_APPEND`. Other options include `WRITE_TRUNCATE` (overwrite) and `WRITE_EMPTY`.
*   `schemas`: A dictionary where each key is a unique `schema_name`.
    *   `table_id`: The name of the target table in BigQuery.
    *   `data_file`: The relative path to the source data file (must be newline-delimited JSON).
    *   `definition`: The BigQuery table schema. Each field needs a `name` and `type`. `mode` is optional and defaults to `NULLABLE`.

### 3. Data Files

Create the data files as specified in `config.json`. The files should be in **Newline Delimited JSON (NDJSON)** format. Each line must be a valid JSON object.

Example `data/users.jsonl`:
```json
{"user_id": "u001", "name": "Alice", "email": "alice@example.com", "created_at": "2023-01-15T10:00:00Z"}
{"user_id": "u002", "name": "Bob", "email": "bob@example.com", "created_at": "2023-01-16T11:30:00Z"}
```

## Usage

Run the script from your terminal, providing the `schema_name` from your `config.json` that you wish to load.

```bash
# Ensure you are in the 'spike' directory

# To load users data
python bigquery_data_loader.py users

# To load products data
python bigquery_data_loader.py products
```

The script will:
1.  Read the configuration for the specified schema (`users` or `products`).
2.  Check if the dataset and table exist in BigQuery, creating them if necessary.
3.  Start a BigQuery load job to stream the data from the local `.jsonl` file into the target table.
4.  Log the progress and final status of the load job.