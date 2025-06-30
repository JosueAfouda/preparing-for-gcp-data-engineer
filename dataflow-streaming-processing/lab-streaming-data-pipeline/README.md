# Lab: How to Build a Real-Time Data Pipeline with Pub/Sub, Dataflow and BigQuery on Google Cloud?

## Overview

Google Cloud **Pub/Sub** is a fully-managed real-time messaging service that allows you to send and receive messages between independent applications. Use Cloud Pub/Sub to publish and subscribe to data from multiple sources, then use Google Cloud Dataflow to understand your data, all in real time.

Google Cloud **Dataflow** is Google Cloud’s fully managed service for executing Apache Beam pipelines. It enables scalable and efficient batch and stream data processing.

In this lab, you will use Dataflow to collect traffic events from simulated traffic sensor data made available through Google Cloud PubSub, process them into an actionable average, and store the raw data in BigQuery for later analysis. You will learn how to start a Dataflow pipeline, monitor it, and, lastly, optimize it.

---

## 🎯 Objectives

By the end of this lab, you will be able to:

* ✅ Create a **Cloud Pub/Sub topic and subscription** to ingest streaming data.
* ✅ Simulate **real-time sensor data** publishing using a Python script.
* ✅ Deploy an **Apache Beam pipeline** on **Cloud Dataflow** to process the streaming data.
* ✅ Write processed output to a **BigQuery** table for further analysis.
* ✅ Verify that data flows correctly from ingestion to final storage.
* ✅ Understand the key components of a **serverless streaming data pipeline** on Google Cloud.

This lab gives you hands-on experience with the core services used in real-time data processing and prepares you for production-grade use cases involving telemetry, IoT, and traffic analysis.

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

### 7. Create a Cloud Storage bucket

```bash
export PROJECT_ID=$(gcloud info --format='value(config.project)')

export REGION=us-central1

export export GCS_BUCKET="gs://${PROJECT_ID}-dataflow-bucket"

gcloud storage buckets create $GCS_BUCKET --location=$REGION --uniform-bucket-level-access
```

---

### 8. Create a BigQuery dataset

```bash
bq mk --location=$REGION $PROJECT_ID:demos
```

---

## Create a Pub/Sub Topic and Subscription

First, create a **Pub/Sub topic** named `sandiego`. This topic will be used to stream simulated traffic data.

```bash
gcloud pubsub topics create sandiego
```

Create a new Python file to simulate real-time publishing:

```bash
touch send_sensor_data.py
```

Then download the historical traffic data file:

```bash
gsutil cp gs://cloud-training-demos/sandiego/sensor_obs2008.csv.gz .
```

Confirm that the default compute Service Account {project-number}-compute@developer.gserviceaccount.com is present and has the editor role assigned. 

Generate a **JSON key** for the default service account (  {project-number}-compute@developer.gserviceaccount.com) and export it as an environment variable for authentication:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

You can now simulate streaming traffic sensor data with:

```bash
python3 send_sensor_data.py --speedFactor=60 --project $PROJECT_ID
```

The `--speedFactor=60` option means the simulation runs 60× faster than real time (i.e., 1 hour of data is sent in 1 minute).

---

### What the Script Does (`send_sensor_data.py`)

This script simulates streaming traffic events from a CSV file and publishes them to a Pub/Sub topic in real time.

Here's a breakdown of its components:

* **Pub/Sub Setup**:
  It initializes a `PublisherClient`, checks if the topic exists, and creates it if not.

* **Reading and Simulating Events**:
  The gzipped CSV file contains timestamped sensor data. The script reads it line by line, extracts the observation timestamp, and:

  * Calculates how much time to "sleep" to simulate real-time pacing (`simulate()` function).
  * Groups events into small batches and publishes them with `publish()`.

* **Time Acceleration**:
  The `--speedFactor` controls how much faster than real time the simulation runs. A higher value means faster publishing.

* **Efficient Publishing**:
  Data is buffered and published in batches for efficiency. The timestamp of each event determines the timing of publication.

In short, this script brings historical traffic data to life by streaming it through Pub/Sub as if it were coming from real-time sensors.

---

## Verify That Messages Are Being Received

Open a **new terminal window**, then re-export the environment variables to ensure your project and region settings are available:

```bash
export PROJECT_ID=$(gcloud info --format='value(config.project)')
export REGION=us-central1
export GCS_BUCKET="gs://${PROJECT_ID}-dataflow-bucket"
```

Now, create a **Pub/Sub subscription** to the `sandiego` topic. This allows you to consume and verify the incoming messages:

```bash
gcloud pubsub subscriptions create --topic sandiego mySub2
```

Then pull messages from the subscription to confirm that data is being published:

```bash
gcloud pubsub subscriptions pull --auto-ack mySub2
```

You should see traffic sensor events printed to the terminal, which confirms that the simulated data is successfully being streamed into Pub/Sub.

---

Voici la version enrichie de la section **README** pour inclure une **explication claire et concise du code `average_speeds.py`** :

---

## Launch the Dataflow Pipeline

Before running the pipeline, make sure the necessary APIs are enabled and dependencies are installed:

```bash
gcloud services disable dataflow.googleapis.com --force
gcloud services enable dataflow.googleapis.com

pip install apache-beam[gcp]
```

Create the pipeline script:

```bash
touch average_speeds.py
```

Then authenticate with your service account:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

Finally, launch the pipeline with:

```bash
python3 average_speeds.py \
  --project=$PROJECT_ID \
  --region=$REGION \
  --runner=DataflowRunner \
  --staging_location=$GCS_BUCKET/staging/ \
  --temp_location=$GCS_BUCKET/temp/ \
  --input_topic=projects/$PROJECT_ID/topics/sandiego \
  --output_table=${PROJECT_ID}:demos.average_speeds
```

---

### What the `average_speeds.py` Pipeline Does

This script defines an **Apache Beam streaming pipeline** that processes real-time traffic sensor data from **Pub/Sub** and writes aggregated average speed data into **BigQuery**.

#### Key Steps Explained:

1. **Reading Messages from Pub/Sub**

   ```python
   ReadFromPubSub(topic=args.input_topic)
   ```

   * The pipeline continuously reads raw byte messages from the specified Pub/Sub topic.

2. **Decoding & Parsing Messages**

   ```python
   beam.Map(lambda x: x.decode('utf-8'))
   beam.Map(parse_message)
   ```

   * Messages are UTF-8 decoded and parsed from JSON format.
   * `parse_message()` extracts the `sensorId` as a key and the `speed` as a float.

3. **Applying Sliding Windows**

   ```python
   beam.WindowInto(SlidingWindows(averaging_interval, frequency))
   ```

   * Data is grouped into **sliding windows** to compute average speeds over time.
   * This allows overlapping time windows for finer temporal resolution.

4. **Computing Averages**

   ```python
   beam.CombinePerKey(beam.combiners.MeanCombineFn())
   ```

   * Computes the **mean speed per sensor** (keyed by sensorId and location info).

5. **Formatting for BigQuery**

   ```python
   beam.Map(to_bq_row)
   ```

   * Converts each `(key, avg_speed)` tuple into a BigQuery-compatible dictionary.
   * Parses the key to extract fields like latitude, longitude, highway, direction, and lane.

6. **Writing to BigQuery**

   ```python
   WriteToBigQuery(...)
   ```

   * Appends the processed data to the `demos.average_speeds` table in BigQuery.
   * Automatically creates the table if it doesn't exist.

#### Schema of the Output Table

The data is written to BigQuery using this schema:

| Field     | Type      |
| --------- | --------- |
| timestamp | TIMESTAMP |
| latitude  | FLOAT     |
| longitude | FLOAT     |
| highway   | STRING    |
| direction | STRING    |
| lane      | INTEGER   |
| speed     | FLOAT     |
| sensorId  | STRING    |

---

This pipeline provides a scalable way to monitor traffic speed trends in near real-time using Google Cloud's Pub/Sub, Dataflow, and BigQuery.

---

## Cleanup

Once you have completed the lab and no longer need the resources, it is **strongly recommended** to delete the project to avoid incurring unnecessary charges.

> ⚠️ **Warning**: This action is irreversible. Deleting the project will permanently remove all resources: Pub/Sub topics, Dataflow jobs, BigQuery datasets, Cloud Storage buckets, service accounts, etc.

To delete the project, run:

```bash
gcloud projects delete $PROJECT_ID
```

You can verify that the project has been marked for deletion by listing your active projects:

```bash
gcloud projects list
```

If your project no longer appears, the deletion process has been successfully initiated.

This final step ensures that your Google Cloud account remains clean and cost-free after completing the streaming data processing pipeline lab.

---

## Conclusion

In this lab, you built a complete real-time data processing pipeline on Google Cloud using the following components:

* **Cloud Pub/Sub** to publish and ingest simulated traffic sensor data.
* **Apache Beam with Dataflow** to process streaming data and compute average speeds.
* **BigQuery** to store and analyze the processed results.

You also learned how to:

* Simulate real-time data ingestion using a Python script.
* Deploy a streaming pipeline using DataflowRunner.
* Verify data flow through Pub/Sub subscriptions.
* Write pipeline outputs to a BigQuery table for further analysis.

This hands-on workflow demonstrates how to build scalable and serverless data streaming architectures with minimal operational overhead. It lays the foundation for more advanced pipelines involving windowing, aggregations, and anomaly detection in real-time.

> ✅ You are now ready to explore more complex streaming use cases on GCP!

---

