# Lab: How to Execute a BigQuery query from within a Jupyter notebook in  VSCode?

## Overview

This lab demonstrates how to run BigQuery SQL queries from your local development environment using both Python scripts and Jupyter notebooks in VSCode.

Working locally gives you full control over your workflow while still leveraging the power of BigQuery — Google Cloud's fully managed and highly scalable data warehouse. You’ll learn how to authenticate securely, write efficient SQL queries, and retrieve results into Pandas DataFrames for further analysis or processing.

By the end of this lab, you'll be able to use BigQuery as part of your everyday data science or data engineering workflow, without relying on the Google Cloud Console UI.

---

## 🎯 Objectives

By completing this lab, you will be able to:

* ✅ Enable the BigQuery API in your GCP project.
* ✅ Install and configure the necessary Python libraries for BigQuery access.
* ✅ Authenticate using a service account key (`key.json`).
* ✅ Run a BigQuery query from a Python script using the BigQuery client library.
* ✅ Run a BigQuery query from a Jupyter notebook using the `%bigquery` magic command.
* ✅ Load query results into a Pandas DataFrame for analysis.

> This lab is ideal for data analysts, engineers, and scientists who want to integrate BigQuery into their local development workflow using VSCode.

---

## Setup and Requirements

Before starting the lab, make sure the following setup steps are completed on your local machine:

### 1. Create a new Google Cloud project

You can create a new project from the [Google Cloud Console](https://console.cloud.google.com/). This project will host your Cloud SQL instance and all related resources.

### 2. Install the gcloud CLI

Make sure the **Google Cloud SDK** (`gcloud`) is installed on your machine. Follow the official guide here:
👉 [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)

### 3. Initialize gcloud

Run the following command to authenticate and select the project and default configuration:

```bash
gcloud init
```

This will open a browser window for authentication and let you select or create a configuration.

---

### 4. Set the active project

```bash
gcloud config set project YOUR_PROJECT_ID
```

This sets the active project where all future `gcloud` commands will apply.

---

### 5. Verify your authenticated account

```bash
gcloud auth list
```

This shows which Google account is currently authenticated with the CLI.

---

### 6. Verify the current project

```bash
gcloud config list project
```

This confirms which project ID is currently active in your configuration.

---

Before running BigQuery queries in a Jupyter notebook inside VSCode, you need to prepare your environment with the right services and libraries.

### 7. Enable the BigQuery API

To use BigQuery in your project, you first need to enable the BigQuery API:

```bash
gcloud services enable bigquery.googleapis.com
```

This command tells Google Cloud to activate the BigQuery service for your current project, allowing your code and notebook to interact with it.

> 💡 Make sure you've already set the correct project with `gcloud config set project [PROJECT_ID]`.

---

### 8. Install the required Python libraries

Next, install the necessary Python packages:

```bash
pip install --upgrade google-cloud-bigquery pandas db-dtypes
```

Here's what each package does:

* **google-cloud-bigquery**: The official Python client library for BigQuery. It allows you to run SQL queries, upload/download data, and manage datasets.
* **pandas**: A popular data analysis library in Python. It helps you manipulate and visualize tabular data returned from BigQuery.
* **db-dtypes**: A helper library that ensures BigQuery data types (like `GEOGRAPHY`, `NUMERIC`, `TIMESTAMP`, etc.) are properly handled when converting data into pandas DataFrames.

> ✅ It's a good practice to run this command inside a virtual environment (e.g., using `venv` or `conda`) to avoid conflicts with other Python packages on your system.

---

## 👤 Create a Service Account

To allow your code to interact securely with Google Cloud services like BigQuery, you’ll create and configure a service account.

```bash
# Set your current project ID
export PROJECT=$(gcloud info --format='value(config.project)')
```

This sets the environment variable `PROJECT` to your active project ID.

```bash
# Create a new service account with a display name
gcloud iam service-accounts create my-account --display-name my-account
```

This creates a service account named `my-account`.

```bash
# Grant the service account BigQuery Admin permissions
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:my-account@$PROJECT.iam.gserviceaccount.com \
  --role=roles/bigquery.admin
```

This grants the service account the `BigQuery Admin` role, allowing it to create datasets, tables, and run queries.

```bash
# Grant the service account permission to use Google Cloud APIs
gcloud projects add-iam-policy-binding $PROJECT \
  --member=serviceAccount:my-account@$PROJECT.iam.gserviceaccount.com \
  --role=roles/serviceusage.serviceUsageConsumer
```

This allows the service account to consume Google Cloud APIs.

```bash
# Generate and download a key for the service account
gcloud iam service-accounts keys create key.json \
  --iam-account=my-account@$PROJECT.iam.gserviceaccount.com
```

This creates a private key in JSON format (`key.json`) that you'll use to authenticate your code with Google Cloud.

```bash
# Set the environment variable to use the downloaded key for authentication
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

This tells your environment to use the service account key for all Google Cloud SDK and client library operations.

---

## Option 1: Run a BigQuery Query from a Python Script Using the BigQuery Client Library

Instead of using Jupyter notebooks, you can also execute BigQuery queries directly from a Python script using the official BigQuery Python client.

### 1. Create a Python script

```bash
touch bq_python_client.py
```

### 2. Add the following code to `bq_python_client.py`

```python
# 1. Import the required libraries
from google.cloud import bigquery
import pandas as pd

# 2. Initialize a BigQuery client
# This uses your default credentials and active project from gcloud
client = bigquery.Client()

# 3. Define your SQL query
sql_query = f"""
    SELECT
        depdelay as departure_delay,
        COUNT(1) AS num_flights,
        APPROX_QUANTILES(arrdelay, 10) AS arrival_delay_deciles
    FROM
        `cloud-training-demos.airline_ontime_data.flights`
    WHERE
        depdelay is not null
    GROUP BY
        depdelay
    HAVING
        num_flights > 100
    ORDER BY
        depdelay ASC;
"""

# 4. Execute the query and load the results into a Pandas DataFrame
query_job = client.query(sql_query)     # Sends the query to BigQuery
df = query_job.to_dataframe()           # Waits for the result and converts to DataFrame

# 5. Display the DataFrame
print("Query executed successfully!")
print(df)
```

### 3. Run the script

```bash
python3 bq_python_client.py
```

This script connects to BigQuery using your local credentials (set via `gcloud auth application-default login` or via `GOOGLE_APPLICATION_CREDENTIALS`), sends a SQL query, and loads the results into a Pandas DataFrame.

> ✅ Ideal for integrating BigQuery with data pipelines or running ad hoc analysis outside of notebooks.

---


## Option 2: Run a BigQuery Query from a Jupyter Notebook Using the BigQuery Magic Command

You can also run BigQuery queries directly inside a Jupyter notebook using the `%bigquery` magic command. This approach is ideal for data exploration and analysis workflows.

### 1. Create a new notebook

```bash
touch bq_in_jupyternotebook.ipynb
```

Then open it in VSCode or JupyterLab.

---

### 💻 Notebook Cells Explained

#### 🔹 **Cell 1 — Load the BigQuery magic command extension**

```python
%load_ext google.cloud.bigquery
```

This loads the BigQuery Jupyter magic extension, allowing you to use `%%bigquery` to run SQL queries directly and store the result into a Pandas DataFrame.

---

#### 🔹 **Cell 2 — Set the environment variable for authentication**

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"
```

This sets the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account key file (`key.json`), so the notebook can authenticate with Google Cloud.

---

#### 🔹 **Cell 3 — Run a BigQuery SQL query and save the result**

```python
%%bigquery df --use_rest_api
SELECT
  depdelay as departure_delay,
  COUNT(1) AS num_flights,
  APPROX_QUANTILES(arrdelay, 10) AS arrival_delay_deciles
FROM
  `cloud-training-demos.airline_ontime_data.flights`
WHERE
  depdelay is not null
GROUP BY
  depdelay
HAVING
  num_flights > 100
ORDER BY
  depdelay ASC
```

This runs a SQL query on BigQuery and stores the result into a DataFrame named `df`. The `--use_rest_api` flag ensures compatibility with the REST API even outside of Colab.

---

#### 🔹 **Cell 4 — Display the first few rows of the result**

```python
df.head()
```

Shows the top 5 rows of the DataFrame for a quick preview of the query result.

---

#### 🔹 **Cell 5 — Display summary info about the DataFrame**

```python
df.info()
```

Gives an overview of the DataFrame: column names, data types, and non-null counts. Useful for understanding the structure of your data.

---

> ✅ This notebook-based approach is ideal for interactive data exploration, rapid prototyping, and visual analysis using Pandas and Plotly/Seaborn.

---


## Conclusion

In this lab, you learned two practical ways to run BigQuery SQL queries locally from your development environment:

* **Option 1** showed how to execute queries using the BigQuery Python client inside a `.py` script — ideal for automation, pipelines, or integrating BigQuery into larger Python applications.
* **Option 2** demonstrated how to use the `%bigquery` magic command in a Jupyter notebook — perfect for interactive data analysis and rapid prototyping with Pandas.

You also learned how to:

* Enable the BigQuery API in your GCP project.
* Install the required Python libraries (`google-cloud-bigquery`, `pandas`, `db-dtypes`).
* Authenticate with Google Cloud using a service account key (`key.json`).
* Retrieve query results into a Pandas DataFrame and inspect them.

> ✅ Whether you're building data pipelines or doing exploratory data analysis, integrating BigQuery with your local tools like VSCode and Jupyter empowers you to work faster and smarter — without needing to leave your familiar development environment.

Next, you can go further by visualizing the results with Matplotlib or Plotly, saving data to CSV, or integrating with machine learning libraries like Scikit-learn or TensorFlow.









