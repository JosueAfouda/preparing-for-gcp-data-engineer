# Lab: How to classify unstructured text using the Natural Language API?

## Overview

The Cloud Natural Language API enables you to extract entities from text, perform sentiment and syntactic analysis, and classify text into categories. In this lab, we will focus on **text classification**. Leveraging a database of over 700 predefined categories, this API feature allows you to quickly and accurately classify large volumes of unstructured text data.

---

## 🎯 Objectives

By the end of this lab, you will be able to:

* Enable and authenticate access to the Cloud Natural Language API.
* Create and manage BigQuery datasets and tables for storing classification results.
* Write Python scripts to classify single and multiple text documents using the Natural Language API.
* Load classified data into BigQuery and perform basic analysis using SQL queries.
* Understand how to integrate Google Cloud services to build an end-to-end text classification pipeline.

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

## 🔐 Create an API Key for the Natural Language API

Before using the Natural Language API, you need to enable the API and generate an API key to authenticate your requests.

```bash
# Enable the Natural Language API
gcloud services enable language.googleapis.com
```

This command enables the Natural Language API for your current GCP project.

```bash
# Create an API key and store it in the environment variable API_KEY
export API_KEY=$(gcloud alpha services api-keys create \
  --display-name="Natural Language API Key" \
  --format="value(keyString)")
```

This command creates a new API key with the display name "Natural Language API Key" and stores the key value in the `API_KEY` environment variable. You’ll use this key to authenticate API requests.

```bash
# Display the API key (starts with AIz...)
echo $API_KEY
```

This command prints the API key to the terminal so you can verify it was created successfully. The key usually starts with `AIz...`.

---

## Create a BigQuery Dataset and Table

You’ll now set up a BigQuery dataset and table to store the results of text classification.

```bash
# Create a BigQuery dataset in the us-central1 region
bq --location=us-central1 mk --dataset news_classification_dataset
```

This command creates a new BigQuery dataset named `news_classification_dataset` in the `us-central1` region.

```bash
# Create a table to store the text classification results
bq mk \
  --table \
  --description "Table to store classified news articles" \
  'news_classification_dataset.article_data' \
  article_text:STRING,category:STRING,confidence:FLOAT
```

This command creates a new table named `article_data` within the dataset. The table includes the following fields:

* `article_text` (STRING): the original article text
* `category` (STRING): the predicted category label
* `confidence` (FLOAT): the confidence score of the prediction

```bash
# List available datasets to confirm creation
bq ls
```

This command lists all datasets in your current project so you can verify that the new dataset has been created.

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

## 🧪 Write a Script to Test Text Classification with the Natural Language API

Create a Python script to classify the content of a text file using the Natural Language API:

```bash
touch test-classify-test.py
```

### Explanation of the script:

* `language_v1.LanguageServiceClient()` creates a client to interact with the Natural Language API.
* The text file `001.txt` is opened and read into memory.
* The `Document` object wraps the text in a format required by the API.
* The `classify_text` method sends the content to the API, which returns a classification response (e.g., category and confidence).
* Results are printed directly to the terminal.

### Run the script:

```bash
python3 test-classify-test.py
```

If everything is configured correctly, the output will show one or more categories (e.g., `/Technology & Computing/Software`) along with a confidence score.

---

Here is the English version of the **"Classifying news data and storing the result in BigQuery"** section, including a clear explanation of the code:

---

## 🗂️ Classifying News Data and Storing the Results in BigQuery

Now that we know how to classify a single text, let's scale up!
Imagine you have a folder with multiple `.txt` news articles. This script will:

* Classify each article using the Natural Language API
* Store the article text, predicted category, and confidence in a BigQuery table

Create the script:

```bash
touch classify-text-to-bq.py
```

### Explanation of the script:

* It loads all `.txt` files from a local folder named `bbc-fulltext`.
* Each file is sent to the Natural Language API for category classification.
* The top category and its confidence are extracted (if available).
* All results (text, category, confidence) are stored in the BigQuery table `article_data`.

### Run the script

```bash
python3 classify-text-to-bq.py
```

You should see a message confirming that the rows have been written to BigQuery.
You can now explore the results directly from the BigQuery console or via SQL queries!

---

## 📊 Analyzing Categorized News Data in BigQuery

Now that your classified news articles are stored in BigQuery, you can start analyzing the results using SQL.

### 🧾 View All Classified Articles

This query displays every row in the `article_data` table, including the article text, predicted category, and confidence score.

```sql
SELECT * FROM `news_classification_dataset.article_data`;
```

> You can run this directly in the BigQuery console or using the `bq query` command in the terminal.

---

### 📈 Find the Most Common Categories

Use the following query to group the articles by category and count how many times each one appears:

```sql
SELECT
  category,
  COUNT(*) AS c
FROM
  `news_classification_dataset.article_data`
GROUP BY
  category
ORDER BY
  c DESC;
```

### 🧠 Interpretation:

* This helps you identify which types of news are most represented in your dataset.
* For example, you might see that `"Sports"` or `"Politics"` are the most frequent categories.

---

## Cleanup

Once you have completed the lab and no longer need the resources, it is **strongly recommended** to delete the project to avoid incurring unnecessary charges.

> ⚠️ **Warning**: This action is irreversible. Deleting the project will permanently remove all resources: Pub/Sub topics, Dataflow jobs, BigQuery datasets, Cloud Storage buckets, service accounts, etc.

To delete the project, run:

```bash
gcloud projects delete $PROJECT
```

You can verify that the project has been marked for deletion by listing your active projects:

```bash
gcloud projects list
```

If your project no longer appears, the deletion process has been successfully initiated.

This final step ensures that your Google Cloud account remains clean and cost-free after completing the streaming data processing pipeline lab.

---

## ✅ Conclusion

In this lab, you learned how to classify unstructured text using the **Google Cloud Natural Language API** and analyze the results in **BigQuery**. Step by step, you:

* Enabled the Natural Language API and created an API key.
* Created a BigQuery dataset and table to store classification results.
* Wrote and tested a Python script to classify individual text files.
* Scaled the solution to classify **multiple news articles** and store the predictions in BigQuery.
* Queried the results in BigQuery to identify the most frequent categories.

This workflow demonstrates how you can integrate **machine learning APIs** and **data warehouses** to extract insights from unstructured text data.

You are now ready to apply this pattern to other classification tasks or explore more advanced NLP features like **entity extraction** or **sentiment analysis**!


