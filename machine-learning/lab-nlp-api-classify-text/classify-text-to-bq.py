from google.cloud import storage, language_v1, bigquery
import os

# Set up our GCS, NL, and BigQuery clients
storage_client = storage.Client()
nl_client = language_v1.LanguageServiceClient()
# TODO: replace YOUR_PROJECT with your project id below
bq_client = bigquery.Client(project='ml-for-data-eng')

dataset_ref = bq_client.dataset('news_classification_dataset')
dataset = bigquery.Dataset(dataset_ref)
table_ref = dataset.table('article_data') # Update this if you used a different table name
table = bq_client.get_table(table_ref)

# Send article text to the NL API's classifyText method
# def classify_text(article):
#         response = nl_client.classify_text(
#                 document=language_v1.types.Document(
#                         content=article,
#                         type_='PLAIN_TEXT'
#                 )
#         )
#         return response
def classify_text(text_bytes):
    document = language_v1.Document(content=text_bytes.decode("utf-8"), type_=language_v1.Document.Type.PLAIN_TEXT)
    return nl_client.classify_text(request={'document': document})

rows_for_bq = []
folder_path = "bbc-fulltext"
#files = storage_client.bucket('cloud-training-demos-text').list_blobs()
files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
print("Got article files from a local folder, sending them to the NL API (this will take ~2 minutes)...")

# Send files to the NL API and save the result to send to BigQuery
# for file in files:
#         if file.name.endswith('txt'):
#                 article_text = file.download_as_bytes()
#                 nl_response = classify_text(article_text)
#                 if len(nl_response.categories) > 0:
#                         rows_for_bq.append((str(article_text), str(nl_response.categories[0].name), nl_response.categories[0].confidence))

for file_path in files:
    with open(file_path, "rb") as f:
        article_text = f.read()

    try:
        nl_response = classify_text(article_text)
        if nl_response.categories:
            rows_for_bq.append((
                article_text.decode("utf-8"),
                nl_response.categories[0].name,
                nl_response.categories[0].confidence
            ))
    except Exception as e:
        print(f"Erreur pour le fichier {file_path}: {e}")

print("Writing NL API article data to BigQuery...")
# Write article text + category data to BQ
errors = bq_client.insert_rows(table, rows_for_bq)
assert errors == []