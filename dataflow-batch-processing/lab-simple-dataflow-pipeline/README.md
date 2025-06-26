# Lab: A Simple Dataflow Pipeline (Python)

## Overview

Dataflow is ...

In this lab, you will open a Dataflow project, use pipeline filtering, and execute the pipeline locally and on the cloud.

The goal of this lab is to become familiar with the structure of a Dataflow project and learn how to execute a Dataflow pipeline.

---

## 🎯 Objectives

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

export BUCKET=$PROJECT_ID

gcloud storage buckets create $BUCKET --location=US --uniform-bucket-level-access
```

---

### 8. Set a Compute Engine region for your resources

```bash
export REGION=us-central1
```

---

## Running an Apache Beam Pipeline Locally

This section demonstrates how to create and run a simple Apache Beam pipeline in **local mode** to filter rows from a CSV file.

### Step 1: Install Apache Beam

Before writing any code, install the Apache Beam SDK for Python:

```bash
pip install apache-beam
```

### Step 2: Create the Script

Create a new Python script called `grep.py`:

```bash
touch grep.py
```

The purpose of this script is to filter specific lines in a CSV file based on a search term (in this case, `"Paris"`). Below is an explanation of how it works.

---

### Script Explanation (`grep.py`)

1. **Library Import**
   The script uses the `apache_beam` library to define and run a data processing pipeline.

2. **`my_grep(line, term)` Function**
   This function takes a line of text and a search term as input.

   * If the line contains the term, it `yield`s the line.
   * Otherwise, it returns nothing — effectively filtering out that line.

3. **Pipeline Initialization**
   The pipeline is initialized with `beam.Pipeline(argv=sys.argv)`, which allows you to pass command-line arguments if needed. By default, it runs the pipeline locally.

4. **Pipeline Steps**

   * **Read**:

     ```python
     beam.io.ReadFromText(input_file, skip_header_lines=1)
     ```

     Reads the CSV file line by line, skipping the header row.

   * **Filter**:

     ```python
     beam.FlatMap(lambda line: my_grep(line, search_term))
     ```

     Applies the `my_grep` function to each line and retains only those that contain the word `"Paris"`.

   * **Write**:

     ```python
     beam.io.WriteToText(output_prefix)
     ```

     Writes the filtered lines to output text files prefixed with `output_csv`.

5. **Run**
   The pipeline is executed with:

   ```python
   p.run().wait_until_finish()
   ```

---

### Step 3: Execute the Pipeline

Run the script with:

```bash
python3 grep.py
```

---

### Output File: `output_csv-00000-of-00001`

* Apache Beam writes output using **sharding**, which means results are split across multiple files if needed. In this simple case, only one shard is created, hence the name `output_csv-00000-of-00001`.

* This file contains all lines (excluding the header) from the CSV input that include the word `"Paris"`.

Example content:

```
Alice,30,Paris
Charlie,35,Paris
```

* The output is a plain text file, with one CSV-formatted line per matching row.

---

Here’s the next section of your README in English, clearly explaining the purpose and changes needed to run the pipeline on **Google Cloud Dataflow**:

---

## Running the Same Apache Beam Pipeline on Google Cloud Dataflow

This section explains how to adapt the local Beam pipeline to run on **Google Cloud Dataflow**, Google’s fully managed service for executing Apache Beam pipelines.

### Step 1: Create the Script

Create a new file called `grepc.py`:

```bash
touch grepc.py
```

This version of the script modifies the original local pipeline to run in the cloud on **Dataflow**.

---

### What’s Different for Dataflow Execution?

Below are the key changes made to run the pipeline on Google Cloud:

---

### 1. **Pipeline Options for Dataflow**

A list of arguments (`argv`) is defined to specify how and where the job will run:

```python
argv = [
    f'--project={PROJECT_ID}',
    '--job_name=dataflow-grep-csv',
    '--save_main_session',
    f'--staging_location=gs://{BUCKET}/staging/',
    f'--temp_location=gs://{BUCKET}/temp/',
    f'--region={REGION}',
    '--worker_machine_type=e2-standard-2',
    '--runner=DataflowRunner',
]
```

* `--project`: GCP project ID.
* `--job_name`: Name of the Dataflow job.
* `--save_main_session`: Ensures global context is preserved when deploying the job.
* `--staging_location`: Location in Cloud Storage where temporary files needed to start the job will be staged.
* `--temp_location`: Location in Cloud Storage for temporary files during execution.
* `--region`: GCP region to run the job in.
* `--worker_machine_type`: Machine type for the Dataflow workers.
* `--runner=DataflowRunner`: Tells Apache Beam to use Dataflow as the runner.

The options are passed to the pipeline using:

```python
options = PipelineOptions(argv)
p = beam.Pipeline(options=options)
```

---

### 2. **Input and Output in Cloud Storage**

Instead of reading from and writing to local files, the pipeline uses **Cloud Storage buckets**:

```python
input_file = f'gs://{BUCKET}/input/sample.csv'
output_prefix = f'gs://{BUCKET}/output/filtered_lines'
```

* The input CSV file must be uploaded beforehand to `gs://your-bucket/input/sample.csv`.
* The filtered results will be written to files in `gs://your-bucket/output/`.

---

### 3. **Cloud-Friendly Transformations**

The Beam transforms used (`ReadFromText`, `Filter`, and `WriteToText`) remain the same but now operate in a cloud-distributed fashion:

```python
(p
 | 'ReadCSV' >> beam.io.ReadFromText(input_file, skip_header_lines=1)
 | 'FilterLines' >> beam.Filter(lambda line: search_term in line)
 | 'WriteOutput' >> beam.io.WriteToText(output_prefix, file_name_suffix='.txt')
)
```

* Reads the CSV from GCS, skipping the header.
* Filters only lines containing the term `"Paris"`.
* Writes output to sharded `.txt` files in GCS.

---

### 4. **Running the Pipeline**

To launch the job on Dataflow:

```bash
python3 grepc.py
```

Make sure you’ve:

* Activated your GCP credentials (`gcloud auth application-default login`)
* Uploaded your input file to `gs://<your-bucket>/input/sample.csv`
* Installed required packages:

  ```bash
  pip install apache-beam[gcp]
  ```

---

Voici la suite du README, toujours en anglais, pour la **section d'exécution du pipeline sur Dataflow**, avec toutes les étapes expliquées clairement :

---

## Running the Pipeline on Google Cloud Dataflow

This section explains how to **execute your Apache Beam pipeline on Dataflow**, Google Cloud’s managed distributed processing service.

---

### Step 1: Install Required Dependencies

Make sure you have the GCP support installed for Apache Beam:

```bash
pip install apache-beam[gcp]
```

---

### Step 2: Upload the Input File to Cloud Storage

Assuming your input file is called `sample.csv`, upload it to your GCS bucket:

```bash
gcloud storage cp sample.csv gs://${BUCKET}/input/sample.csv
```

Replace `${BUCKET}` with your actual bucket name (e.g., `preparing-for-gcp-de`).

---

### Step 3: Set Up Authentication with a Service Account Key

To allow your local environment to authenticate and launch the Dataflow job:

1. Go to **Google Cloud Console**
   → **IAM & Admin**
   → **Service Accounts**
   → Select the default or custom service account (e.g., `Compute Engine default service account`).

2. Click on **“Keys”** → **Add Key** → **Create new key (JSON)**.

3. Download the `.json` key and move it to your current working directory.

⚠️ **Important**: Never commit this file to Git or share it.

---

### Step 4: Set the Environment Variable for Authentication

In your terminal, set the environment variable to point to your service account key file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=YOUR_KEY_NAME.json
```

Replace `YOUR_KEY_NAME.json` with the actual filename.

---

### Step 5: Launch the Dataflow Job

Now you can execute the pipeline and submit the job to Google Cloud Dataflow:

```bash
python3 grepc.py
```

Once submitted, you can:

* Monitor job progress in the [Dataflow UI](https://console.cloud.google.com/dataflow)
* View logs and worker status
* Download output files from your GCS bucket in the `output/` directory

---

Voici la section `## Cleanup` en anglais pour compléter ton README :

---

## Cleanup

After completing the lab, it’s a good practice to clean up your resources to avoid unnecessary charges.

---

### 1. Delete the Dataflow Job

If the Dataflow job `dataflow-grep-csv` is still running or has completed, you can delete it using the following command:

```bash
gcloud dataflow jobs list --region=us-central1
```

Find the job ID of `dataflow-grep-csv`, then delete it with:

```bash
gcloud dataflow jobs cancel YOUR_JOB_ID --region=us-central1 --force
```

Replace `YOUR_JOB_ID` with the actual job ID from the list.

---

### 2. Delete the GCS Bucket

To delete the entire bucket (including all files inside), use:

```bash
gsutil rm -r gs://${BUCKET}
```

⚠️ Make sure `${BUCKET}` is correctly set and that you **really want to delete everything in that bucket**, as this operation is irreversible.

---











