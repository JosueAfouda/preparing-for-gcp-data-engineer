# 1. Import the required libraries
from google.cloud import bigquery
import pandas as pd

# 2. Initialize a BigQuery client
# The client will automatically use your project ID and credentials from gcloud
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
query_job = client.query(sql_query)  # Make an API request.
df = query_job.to_dataframe()      # Wait for the job to complete and get the results.

# 5. Display the DataFrame
print("Query executed successfully!")
print(df)
