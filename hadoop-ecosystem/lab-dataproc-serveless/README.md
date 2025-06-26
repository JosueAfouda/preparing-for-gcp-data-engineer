# Lab: How to Run a PySpark ETL Job on Dataproc Serverless?

## Overview

Dataproc Serverless lets you run Spark workloads without requiring you to provision and manage your own Dataproc cluster

In this lab, you'll learn how to take an existing PySpark ETL script and run it in Dataproc Serverless.

---

## 🎯 Objectives

By the end of this lab, you will be able to:

* Understand how to use **Dataproc Serverless** to run Apache Spark jobs without managing cluster infrastructure.
* Prepare and upload input data and PySpark scripts to a **Google Cloud Storage** bucket.
* Write a PySpark ETL job that:

  * Reads Parquet data from GCS
  * Performs basic data transformations (column selection, filtering, etc.)
  * Writes the results directly into a **BigQuery** table

* Submit and monitor a **Dataproc Serverless batch job** using the `gcloud` command-line interface.
* Use the **Spark-BigQuery connector** to interact with BigQuery from Spark.
* Clean up cloud resources to avoid incurring additional costs.

This hands-on lab will give you a solid foundation for running scalable, serverless data processing pipelines on **Google Cloud Platform**.


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

### 7. Set a Compute Engine region for your resources

```bash
export REGION=us-central1
```

### 8. Enable Google Private Access on the default subnet in your selected region

Dataproc Serverless requires Google Private Access to be enabled in the regional subnet where you run your Spark workloads since Spark drivers and executors require private IP addresses.

```bash
gcloud compute networks subnets update default \
  --region=${REGION} \
  --enable-private-ip-google-access
```

Verify that Google Private Access is enabled. The output should be True:

```bash
gcloud compute networks subnets describe default \
  --region=${REGION} \
  --format="get(privateIpGoogleAccess)"
```

### 9. Specify or create a Cloud Storage bucket to store the assets that are created in this tutorial

```bash
export BUCKET=${PROJECT_ID}-gcs

gcloud storage buckets create gs://${BUCKET} --location=${REGION}
```

### 10. Create a BigQuery dataset

```bash
export DATASET=trips

bq  --location=${REGION} mk -d ${DATASET}

bq ls
```

This will create a dataset named `trips` in the `us-central1` region.

---

## Create a Persistent History Server (Optional but Recommended for Debugging)

Dataproc Serverless does **not expose the Spark UI by default**. If you want to **inspect execution details** of your Spark jobs — such as stages, tasks, shuffle operations, and memory usage — you can create a **single-node Persistent History Server (PHS)**.

This is **optional** for simple use cases or labs where you just want to verify job success/failure, but it's **recommended** when you need deeper debugging or performance insights.

To set it up:

```bash
PHS_CLUSTER_NAME=my_phs_cluster

gcloud dataproc clusters create ${PHS_CLUSTER_NAME} \
  --region=${REGION} \
  --single-node \
  --enable-component-gateway \
  --properties=spark:spark.history.fs.logDirectory=gs://${BUCKET}/phs/*/spark-job-history
```

Once created, the Spark UI will be available via the [Dataproc Clusters > Web Interfaces](https://console.cloud.google.com/dataproc/clusters) section in the Cloud Console.

**Note:** If you skip this step, you can still check basic logs using:

```bash
gcloud dataproc batches describe ${BATCH_NAME} --region=${REGION}
```

Then look for the `driverOutputResourceUri` field to find logs in your GCS bucket.

Set a name for your batch workload:

```bash
BATCH_NAME=spark-etl-pipeline
```

---

## 🚀 Dubmit the Spark batch workload to Dataproc Serverless

Once your local pipeline is tested, you can deploy and run it on Dataproc Serverless using data stored in Cloud Storage and write the output to BigQuery.

### 📝 Step 1: Prepare your ETL script for deployment

Create the script `serverless_dataproc_gcs_to_bq.py`.

### ☁️ Step 2: Upload input data and script to Cloud Storage

```bash
gcloud storage cp yellow_tripdata_2023-01.parquet gs://${BUCKET}/formysparkjob/
gcloud storage cp serverless_dataproc_gcs_to_bq.py gs://${BUCKET}/formysparkjob/
```

### 🔥 Step 3: Submit the Spark job to Dataproc Serverless

Set a name for your batch workload:

```bash
BATCH_NAME=spark-etl-pipeline
```

```bash
gcloud dataproc batches submit pyspark serveless_dataproc_gcs_to_bq.py \
  --batch=${BATCH_NAME} \
  --region=${REGION} \
  --deps-bucket=gs://${BUCKET} \
  --version=1.1 \
  --history-server-cluster=projects/${PROJECT_ID}/regions/${REGION}/clusters/${PHS_CLUSTER_NAME} \
  -- ${DATASET}
```

* `gcloud dataproc batches submit` calls the Dataproc Batches API.

* `pyspark` specifies that you are submitting a PySpark workload.

* `serveless_dataproc_gcs_to_bq.py`: PySpark script to run.

* `--batch` is the name of the batch workload. If not provided, a random generated UUID is used.

* `--region=${REGION}` is the Compute Engine geographical region where the workload is run.

* `--deps-bucket=gs://${BUCKET}` is the bucket where the local Python file is uploaded for access by the Dataproc Serverless environment.

* `--version=1.1`  is the Dataproc Serverless Spark runtime version.

* `--history-server-cluster=projects/${PROJECT_ID}/regions/${REGION}/clusters/${PHS_CLUSTER_NAME}` is the fully qualified name of the persistent history server. Spark event data (separate from console output) is stored and viewed from the Spark UI using the PHS cluster.

* `-- ${DATASET}`: The name of your BigQuery dataset is passed to the workload.

### ✅ Step 4: Verify job execution and output

* In the **Cloud Console**, go to **Dataproc > Batches**.
  You should see your batch workload marked as **Succeeded** if everything went well.

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

To avoid incurring additional costs, make sure to clean up the resources you created during this lab:

### 1. Delete the Dataproc cluster

If you created a **Persistent History Server (PHS) cluster**, delete it using:

```bash
gcloud dataproc clusters delete $PHS_CLUSTER_NAME --region=$REGION
```

### 2. Delete the Cloud Storage bucket

This removes all files (scripts, data) uploaded for the Dataproc job:

```bash
gsutil -m rm -r gs://$BUCKET
```

### 3. Delete the BigQuery dataset

To remove the output table stored in BigQuery:

```bash
bq rm -r -f ${PROJECT_ID}:${DATASET}
```

✅ Make sure you’ve saved any important data or scripts before running these commands, as they are **irreversible**.

---

## ✅ Conclusion

In this lab, you successfully ran a PySpark ETL job on **Dataproc Serverless**, a fully managed Spark environment on Google Cloud that eliminates the need to manage clusters manually.

You learned how to:

* Create a GCS bucket to host your input data and PySpark scripts.
* Write a PySpark job that reads Parquet data from GCS, transforms it, and loads it into a BigQuery table.
* Submit and monitor a **Dataproc Serverless batch job** using the `gcloud` CLI.
* Connect your job to BigQuery using the official Spark-BigQuery connector.
* Clean up cloud resources to avoid unnecessary costs.

Dataproc Serverless is an ideal option for teams looking to **run Spark workloads on-demand** without provisioning or scaling clusters. It offers **cost-efficiency**, **flexibility**, and **tight integration** with other GCP services like BigQuery and GCS.

You're now ready to use Dataproc Serverless in real-world ETL pipelines and automate scalable data workflows on Google Cloud. 🚀

---

