# Lab: How to Run a PySpark ETL Job on Google Cloud Dataproc?

## Overview

Cloud Dataproc is a fully managed and scalable service for running Apache Spark and Hadoop jobs on Google Cloud. It simplifies infrastructure management and allows you to focus on writing and deploying your data pipelines.

In this lab, you'll learn how to take an existing PySpark ETL script and run it in two stages:

* **Locally**, to validate the transformations.
* **On a Cloud Dataproc cluster**, using data stored in Cloud Storage and writing the output to BigQuery.

This approach reflects a real-world workflow where development starts locally and is then scaled to the cloud.

## Objectives

By the end of this lab, you will be able to:

* Create and configure a Dataproc cluster using the `gcloud` CLI.
* Write and run a PySpark ETL job locally on your machine.
* Upload input data and PySpark scripts to Google Cloud Storage.
* Deploy and execute your ETL pipeline on Dataproc.
* Load cleaned data into BigQuery.
* Validate your transformation by running SQL queries on the resulting table.

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

## 🚀 Configure and Start a Cloud Dataproc Cluster

To run PySpark jobs on Google Cloud, you first need to create a **Dataproc cluster**. The following command provisions a cluster named `sparktodp` in the **`us-central1` region**, using **Debian 11** with Spark and Jupyter components enabled:

```bash
gcloud dataproc clusters create sparktodp \
  --region=us-central1 \
  --zone=us-central1-a \
  --image-version=2.1-debian11 \
  --enable-component-gateway \
  --optional-components=JUPYTER \
  --master-machine-type=e2-standard-2 \
  --master-boot-disk-type=pd-standard \
  --master-boot-disk-size=30 \
  --worker-machine-type=e2-standard-2 \
  --worker-boot-disk-type=pd-standard \
  --worker-boot-disk-size=30 \
  --num-workers=2
```

> ✅ When prompted, type `Y` to **enable the required API** (Dataproc and Compute Engine, if not already enabled).

### 🎯 Get the Cloud Storage Bucket Used by Dataproc

Dataproc automatically creates a **default staging bucket** in Cloud Storage. To retrieve and store it in an environment variable (`DP_STORAGE`), run:

```bash
export DP_STORAGE="gs://$(gcloud dataproc clusters describe sparktodp --region=us-central1 --format='value(config.configBucket)')"
echo $DP_STORAGE
```

This `DP_STORAGE` variable will be useful later for:

* Uploading input files (e.g., Parquet or CSV)
* Setting a temporary bucket for BigQuery integration

---

## 🧪 Create and Test a Local ETL Pipeline with PySpark

Before submitting your job to the Dataproc cluster, it's a good idea to test your ETL logic locally.

### 📁 Step 1: Create the project folder

```bash
mkdir sparktobq
```

### 📝 Step 2: Create your local PySpark script

```bash
touch sparktobq/pyspark_local_to_local.py
```

In this script, you:

* Load the Parquet file `yellow_tripdata_2023-01.parquet` as a PySpark DataFrame.
* Apply basic transformations (column selection and filtering).
* Write the cleaned DataFrame to a local output folder `sparktobq/cleaned_trips`.

### ▶️ Step 3: Run the PySpark job locally

```bash
spark-submit sparktobq/pyspark_local_to_local.py
```

If everything runs smoothly, you should find the transformed data written in the `sparktobq/cleaned_trips/` directory as new Parquet files.

---

## 🚀 Deploy the Spark Job to Dataproc

Once your local pipeline is tested, you can deploy and run it on a Dataproc cluster using data stored in Cloud Storage and write the output to BigQuery.

### 📝 Step 1: Prepare your ETL script for deployment

Create the script `sparktobq/pyspark_gcs_to_bq.py`.
It is nearly identical to `pyspark_local_to_local.py`, but:

* The **input** Parquet file is read from a Cloud Storage bucket.
* The **output** is written directly to a BigQuery table.

### ☁️ Step 2: Upload input data and script to Cloud Storage

```bash
gcloud storage cp sparktobq/yellow_tripdata_2023-01.parquet $DP_STORAGE/formysparkjob/
gcloud storage cp sparktobq/pyspark_gcs_to_bq.py $DP_STORAGE/formysparkjob/
```

### 📦 Step 3: Create a BigQuery dataset

```bash
export PROJECT_ID=$(gcloud info --format='value(config.project)')

bq --location=us-central1 mk \
  --dataset \
  ${PROJECT_ID}:trips
```

This will create a dataset named `trips` in the `us-central1` region.

### 🔥 Step 4: Submit the Spark job to Dataproc

```bash
gcloud dataproc jobs submit pyspark \
  --cluster=sparktodp \
  --region=us-central1 \
  $DP_STORAGE/formysparkjob/pyspark_gcs_to_bq.py \
  --jars gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar
```

> This command submits the job to the cluster and uses the BigQuery connector via the `--jars` option.

### ✅ Step 5: Verify job execution and output

* In the **Cloud Console**, go to **Dataproc > Jobs**.
  You should see your job marked as **Succeeded** if everything went well.

* In **BigQuery**, navigate to the `trips.cleaned_trips` table:

  * Check the schema and preview the data.
  * Run a quick test query like:

```sql
SELECT * 
FROM `preparing-for-gcp-de.trips.cleaned_trips`
WHERE trip_distance <= 0;
```

Since your Spark job filters out rows where `trip_distance <= 0`, this query should return **zero rows**.

---

## 🧹 Cleanup

After completing the lab, you can clean up the resources to avoid unexpected charges.

### ✅ Delete the entire Dataproc cluster

```bash
gcloud dataproc clusters delete sparktodp --region=us-central1
```

This will delete the cluster and all associated VM instances.

### ✅ Delete specific resources manually

To delete the Cloud Storage staging bucket and the BigQuery dataset, you can run:

```bash
# Delete the temporary bucket used by Dataproc (be careful, this deletes all its contents)
gcloud storage rm --recursive $DP_STORAGE

# Delete the BigQuery dataset and its tables
bq rm -r -f ${PROJECT_ID}:trips
```

---

## ✅ Conclusion

In this lab, you learned how to build and deploy an end-to-end **ETL pipeline with PySpark on Google Cloud**.

### Key skills acquired:

* 🔧 Configure and start a **Cloud Dataproc** cluster using `gcloud`.
* 🧪 Build and test a **local Spark ETL job** using a Parquet file.
* ☁️ Upload data and scripts to **Cloud Storage**.
* 🛠 Deploy a **PySpark job to Dataproc** that reads from GCS and writes to **BigQuery**.
* 📊 Query and validate the output in **BigQuery** using SQL.

This approach mirrors a typical data engineering workflow: prototype locally, scale in the cloud.
You now have a solid foundation for running Spark jobs on GCP!


