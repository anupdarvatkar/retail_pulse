# Spike: [Descriptive Title of the Spike]

This directory contains experimental code for [briefly describe the purpose of the spike, e.g., "evaluating a new data processing library"].

## 🎯 Objective

The primary goal of this spike is to:
*   [List the main objective, e.g., Evaluate the performance of Google Cloud Vision API for product detection.]
*   [Another objective, e.g., Determine the feasibility of using Pub/Sub for real-time event processing.]

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
*   Python 3.8+
*   `pip`
*   Google Cloud SDK

## ⚙️ Setup

1.  **Authenticate with Google Cloud:**
    If you are running this locally and need to authenticate to Google Cloud services, run the following command and follow the prompts:
    ```bash
    gcloud auth application-default login
    ```

2.  **Set Up Environment Variables:**
    Copy the example environment file and fill in your specific Google Cloud details.
    ```bash
    cp .env.example .env
    # Now, edit the .env file with your configuration
    ```

3.  **Create and activate a virtual environment:**
    It's highly recommended to use a virtual environment to keep dependencies isolated.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install dependencies:**
    Install the required Python packages from `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ Running the Spike

To run the main script for this spike, execute the following command:

```sh
# To add the sample data to the BigQuery table:
python add_raw_review_to_bigquery.py --action add

# To delete all data from the BigQuery table:
python add_raw_review_to_bigquery.py --action delete
```