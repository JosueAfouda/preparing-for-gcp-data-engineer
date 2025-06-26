# %%
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# %%
# 1. Initialize the SparkSession
spark = SparkSession.builder \
    .appName('Local ETL - Taxi Parquet') \
    .getOrCreate()

# %%
# 2. Read the local Parquet file (Extract)
df = spark.read.parquet("yellow_tripdata_2023-01.parquet")
df.show(5)

# %%
# 3. Apply some simple transformations (Transform)
df_cleaned = df.select(
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "fare_amount"
).filter(col("trip_distance") > 0)

df_cleaned.show(10)

# 4. Write results locally in Parquet format (Load)
df_cleaned.write.mode("overwrite").parquet("cleaned_trips")

# 6. End Spark Session
spark.stop()
