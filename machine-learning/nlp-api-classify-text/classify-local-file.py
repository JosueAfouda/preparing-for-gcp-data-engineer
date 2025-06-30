import argparse
import os
from google.cloud import language_v1

def classify_local_text(file_path):
    """
    Classifies the text in a local file using the Natural Language API.

    Args:
      file_path (str): The path to the local file to analyze.
    """
    # This script uses Application Default Credentials (ADC).
    # Before running, ensure you have set the GOOGLE_APPLICATION_CREDENTIALS
    # environment variable to point to your service account key file.
    # Example:
    # export GOOGLE_APPLICATION_CREDENTIALS="key.json"

    try:
        # Instantiates a client
        client = language_v1.LanguageServiceClient()

        # Reads the file's content
        with open(file_path, 'r', encoding='utf-8') as text_file:
            content = text_file.read()

        # Prepare the document for the API
        document = language_v1.Document(
            content=content, type_=language_v1.Document.Type.PLAIN_TEXT
        )

        # Call the Natural Language API to classify the text
        print(f"Sending content of '{file_path}' to the Natural Language API...")
        response = client.classify_text(request={'document': document})

        # Process and print the results
        if response.categories:
            print("\n--- Classification Results ---")
            for category in response.categories:
                print(f"  Category: {category.name}")
                print(f"  Confidence: {category.confidence:.2%}")
            print("--------------------------")
        else:
            print("\nCould not classify the text. The content may be too short or ambiguous.")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file_path', help='The path to the local text file to classify.')
    args = parser.parse_args()
    classify_local_text(args.file_path)

