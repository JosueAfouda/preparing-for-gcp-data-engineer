# Lab: How to Load and Analyze Data in Google Cloud SQL?

## Overview

Cloud SQL is a fully managed database service that makes it easy to set up and administer your relational databases in the cloud. It supports MySQL, PostgreSQL, and Microsoft SQL Server.

In this lab, you will learn how to import data from CSV text files into Cloud SQL and then carry out some basic data analysis using simple queries.

## Objectives

- Create Cloud SQL instance

- Create a Cloud SQL database

- Import text data into Cloud SQL

- Check the data for integrity

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

## Create a Cloud SQL Instance

### 1. Create the SQL instance

```bash
gcloud sql instances create taxi --tier=db-n1-standard-1 --activation-policy=ALWAYS
```

This command creates a new **Cloud SQL instance** named `taxi`, using the machine type `db-n1-standard-1`.
The `--activation-policy=ALWAYS` flag ensures that the instance is always running.

> ✅ When prompted, type `Y` to **enable the required API**.

---

### 2. Set the root user password

```bash
gcloud sql users set-password root --host % --instance taxi --password YOUR_PASSWORD_FOR_THE_SQL_INSTANCE
```

This sets the password for the `root` user of your Cloud SQL instance.
The `--host %` option allows connections from any host (by default, access is restricted).

---

### 3. Authorize your IP address

By default, Cloud SQL blocks all **external connections** for security reasons. You need to **whitelist your public IP address**.

```bash
export ADDRESS=$(curl -4 ifconfig.me)/32
echo $ADDRESS
```

* This retrieves your **public IPv4 address** and formats it in CIDR notation (`/32` means “this exact IP”).

```bash
gcloud sql instances patch taxi --authorized-networks $ADDRESS
```

* This updates the Cloud SQL instance to allow incoming connections from your machine’s IP address.

> ✅ When prompted, type `Y` to confirm the patch.

---

### 🛠 Optional: Automate IP whitelisting

You can create a small script called `whitelist_my_ip.sh` to automate the IP detection and authorization:

```bash
#!/bin/bash

# Name of your Cloud SQL instance
INSTANCE_NAME="taxi"

# Gets the public IPv4 address and adds /32 for CIDR
MY_IP=$(curl -4 -s ifconfig.me)/32

echo "Detected IP address: $MY_IP"
echo "Adding to the authorized networks of Cloud SQL instance: $INSTANCE_NAME..."

# Apply the patch with the IP address
gcloud sql instances patch "$INSTANCE_NAME" --authorized-networks="$MY_IP"

# Check result
if [ $? -eq 0 ]; then
  echo "IP $MY_IP successfully authorized for instance $INSTANCE_NAME."
else
  echo "An error occurred while updating the whitelist."
fi
```

Make it executable:

```bash
chmod +x whitelist_my_ip.sh
./whitelist_my_ip.sh
```

---

### 4. Get the public IP address of your instance

```bash
MYSQLIP=$(gcloud sql instances describe taxi --format="value(ipAddresses.ipAddress)")
echo $MYSQLIP
```

This command extracts and displays the **public IP address** of the Cloud SQL instance, which you'll use to connect via a MySQL client.

> 💡 You should see the **same IP** as the one that was displayed when you created the instance.

---

## Connect to Cloud SQL and Create the Database and Table

### 1. Connect to the Cloud SQL instance using the MySQL client

```bash
mysql --host=$MYSQLIP --user=root --password --verbose
```

This connects you to your Cloud SQL instance using the MySQL command-line client, with the root user.
You’ll be prompted to enter the password you previously set with `gcloud sql users set-password`.

---

### 2. Install the MySQL client (if not already installed)

If you see an error like `mysql: command not found`, you need to install the MySQL client.

Open a **new terminal window** and run the following commands (for Linux/Ubuntu):

```bash
sudo apt update
sudo apt install mysql-client-core-8.0
```

Then re-run the connection command:

```bash
mysql --host=$MYSQLIP --user=root --password --verbose
```

---

### 3. Create the database and the `trips` table

Once inside the MySQL prompt (`mysql>`), execute the following SQL commands:

```sql
CREATE DATABASE IF NOT EXISTS bts;
USE bts;

DROP TABLE IF EXISTS trips;

CREATE TABLE trips (
  vendor_id VARCHAR(16),		
  pickup_datetime DATETIME,
  dropoff_datetime DATETIME,
  passenger_count INT,
  trip_distance FLOAT,
  rate_code VARCHAR(16),
  store_and_fwd_flag VARCHAR(16),
  payment_type VARCHAR(16),
  fare_amount FLOAT,
  extra FLOAT,
  mta_tax FLOAT,
  tip_amount FLOAT,
  tolls_amount FLOAT,
  imp_surcharge FLOAT,
  total_amount FLOAT,
  pickup_location_id VARCHAR(16),
  dropoff_location_id VARCHAR(16)
);
```

---

### 4. Check the structure of the table

```sql
DESCRIBE trips;
```

This displays the structure of the `trips` table and verifies that it was created correctly.

---

### 5. Test a sample query

```sql
SELECT DISTINCT(pickup_location_id) FROM trips;
```

This query confirms the table is accessible and will later return results after data is imported.

---

### 6. Exit the MySQL shell

```sql
EXIT;
```

---

## Import Data into the Cloud SQL Instance

### 1. Download the CSV data files from Google Cloud Storage

Use the following `gcloud storage cp` commands to copy two public datasets into your current working directory:

```bash
gcloud storage cp gs://cloud-training/OCBL013/nyc_tlc_yellow_trips_2018_subset_1.csv trips.csv-1

gcloud storage cp gs://cloud-training/OCBL013/nyc_tlc_yellow_trips_2018_subset_2.csv trips.csv-2
```

These files will be saved locally in the current terminal folder.

---

### 2. Connect to your Cloud SQL instance with local file import enabled

Use the `--local-infile` option to allow loading data from local files:

```bash
mysql --host=$MYSQLIP --user=root --password --local-infile
```

Enter the password for your Cloud SQL instance when prompted.

---

### 3. Select the database you created earlier

In the MySQL interactive console, run:

```sql
USE bts;
```

This sets the working database to `bts`.

---

### 4. Import the CSV data into the `trips` table

Use the `LOAD DATA LOCAL INFILE` command to load each file into the `trips` table:

```sql
LOAD DATA LOCAL INFILE 'trips.csv-1' INTO TABLE trips
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(vendor_id, pickup_datetime, dropoff_datetime, passenger_count, trip_distance, rate_code, store_and_fwd_flag, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, imp_surcharge, total_amount, pickup_location_id, dropoff_location_id);

LOAD DATA LOCAL INFILE 'trips.csv-2' INTO TABLE trips
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(vendor_id, pickup_datetime, dropoff_datetime, passenger_count, trip_distance, rate_code, store_and_fwd_flag, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, imp_surcharge, total_amount, pickup_location_id, dropoff_location_id);
```

Each command loads the contents of a CSV file into the `trips` table, skipping the first row (column headers).

---

### 5. Verify the data import

Check the total number of rows imported:

```sql
SELECT COUNT(*) FROM trips;
```

You should see the result:

```
20024
```

This matches the total number of rows from the two CSV files:

* `trips.csv-1` has **10018** rows
* `trips.csv-2` has **10006** rows
* `10018 + 10006 = 20024`

You can open the CSV files in VSCode or a text editor to manually confirm the row counts if desired.

---

## Basic Data Analysis with SQL Queries

Once the data has been loaded successfully into the `trips` table, you can perform some simple exploratory analysis using SQL queries:

---

### 1. Explore unique pickup location IDs

```sql
SELECT DISTINCT(pickup_location_id) FROM trips;
```

This query returns the different pickup locations found in the dataset. It helps identify how many unique pickup zones are present.

---

### 2. Check the range of trip distances

```sql
SELECT
  MAX(trip_distance),
  MIN(trip_distance)
FROM
  trips;
```

This provides the maximum and minimum trip distances recorded. Very large or small values may indicate data quality issues.

---

### 3. Count the number of trips with zero distance

```sql
SELECT COUNT(*) FROM trips WHERE trip_distance = 0;
```

This shows how many trips have a recorded distance of zero, which could suggest errors or extremely short rides.

---

### 4. Identify trips with negative fare amounts

```sql
SELECT COUNT(*) FROM trips WHERE fare_amount < 0;
```

Negative fares are typically invalid and may point to issues in the source data.

---

### 5. Analyze the distribution of payment types

```sql
SELECT
  payment_type,
  COUNT(*)
FROM
  trips
GROUP BY
  payment_type;
```

This query gives you the number of trips by payment method (e.g., cash, credit card, etc.), helping understand customer preferences.

---

### 6. Exit MySQL console

```sql
exit
```

Use `exit` to leave the interactive MySQL session once your analysis is done.

---

## Cleanup

Once you've completed the lab, you can clean up your resources to avoid unnecessary charges.

You have two options:

### Option 1: Delete the entire project

If you created a dedicated project for this lab, you can delete it completely:

```bash
gcloud projects delete PROJECT_ID
```

Replace `PROJECT_ID` with the actual ID of your project.
This will remove **all** resources associated with that project.

---

### Option 2: Delete only the Cloud SQL instance

If you want to keep your project but just remove the SQL instance:

```bash
gcloud sql instances delete taxi --quiet
```

This command deletes the Cloud SQL instance named `taxi` without prompting for confirmation (due to `--quiet`).

---

## Conclusion

In this lab, you learned how to:

* Create and configure a Cloud SQL instance on Google Cloud
* Authorize your IP address for secure external access
* Use the MySQL client to connect and interact with a Cloud SQL database
* Create a new database and define a table schema
* Import structured CSV data from Google Cloud Storage into Cloud SQL
* Perform basic data analysis using SQL queries to validate and explore the dataset

These steps form the foundation for real-world data engineering tasks on Google Cloud. You’ve now gained practical experience with:

* Managing relational databases in a cloud environment
* Importing and analyzing structured data
* Using `gcloud` CLI for provisioning and automation

You’re one step closer to becoming a Google Cloud Professional Data Engineer!

---
