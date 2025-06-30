from google.cloud import language_v1

# Instantiates a client
client = language_v1.LanguageServiceClient()

# Reads the file's content
file_path = "001.txt"
with open(file_path, 'r', encoding='utf-8') as text_file:
    content = text_file.read()

# Prepare the document for the API
document = language_v1.Document(
    content=content, type_=language_v1.Document.Type.PLAIN_TEXT
)
print(f"Document prepared for classification: {document}")

print("\n")

# Call the Natural Language API to classify the text
print(f"Sending content of '{file_path}' to the Natural Language API...")
response = client.classify_text(request={'document': document})
print(response)