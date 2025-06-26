from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Créer une session Spark
spark = SparkSession.builder \
    .appName('Spark ETL from GCS to BigQuery') \
    .getOrCreate()

# Paramètres
BUCKET_NAME = "preparing-for-gcp-de-gcs"
SPARK_JOB_FOLDER = "formysparkjob"
GCS_PATH_INPUT = f"gs://{BUCKET_NAME}/{SPARK_JOB_FOLDER}/yellow_tripdata_2023-01.parquet"
BQ_TABLE = "trips.cleaned_trips"

# Lire le fichier Parquet depuis GCS
df = spark.read.parquet(GCS_PATH_INPUT)

# Sélectionner et nettoyer les données
df_cleaned = df.select(
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "fare_amount"
).filter(col("trip_distance") > 0)

# Écrire dans BigQuery
df_cleaned.write.format("bigquery") \
    .option("temporaryGcsBucket", BUCKET_NAME) \
    .option("table", BQ_TABLE) \
    .mode("overwrite") \
    .save()

# Terminer la session
spark.stop()
