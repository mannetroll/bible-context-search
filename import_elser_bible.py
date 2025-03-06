import os
import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers.errors import BulkIndexError

# ----- Configuration -----
DATA_DIR = "downloaded_jsons"  # folder containing 1.json to 66.json
INDEX_NAME = "bible-elser"

# ----- Elasticsearch Setup -----
es_base = Elasticsearch("http://localhost:9200")
es = es_base.options(request_timeout=120)

# Define the index mapping with a semantic_text field that uses the inference endpoint.
mapping = {
    "settings": {
        "index": {
            "refresh_interval": "10s",
            "number_of_shards": "1",
            "number_of_replicas": "0"
        }
    },
    "mappings": {
        "properties": {
            "translation": {"type": "keyword"},
            "abbreviation": {"type": "keyword"},
            "lang": {"type": "keyword"},
            "language": {"type": "keyword"},
            "direction": {"type": "keyword"},
            "encoding": {"type": "keyword"},
            "nr": {"type": "integer"},
            "book": {"type": "keyword"},
            "chapter": {"type": "integer"},
            "verse": {"type": "integer"},
            "text": {
                "type": "semantic_text",
                "inference_id": ".elser-2-elasticsearch"
            }
        }
    }
}

# Delete the index if it exists, then create a new one.
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
es.indices.create(index=INDEX_NAME, body=mapping)
print(f"Created Elasticsearch index: {INDEX_NAME}")

# ----- Process JSON Files and Prepare Documents -----
documents = []  # List to store each verse as a document

# Loop over files 1.json through 66.json
for i in range(1, 67):
    file_path = os.path.join(DATA_DIR, f"{i}.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # For each chapter in the book
    for chapter in data.get("chapters", []):
        # Each chapter should have a list of verses
        for verse in chapter.get("verses", []):
            text = verse.get("text")
            # Optionally, filter out documents with empty text to avoid issues.
            if not text or not text.strip():
                continue
            doc = {
                "translation": data.get("translation"),
                "abbreviation": data.get("abbreviation"),
                "lang": data.get("lang"),
                "language": data.get("language"),
                "direction": data.get("direction"),
                "encoding": data.get("encoding"),
                "nr": data.get("nr"),
                "book": data.get("name"),
                "chapter": verse.get("chapter"),
                "verse": verse.get("verse"),
                "text": text
            }
            documents.append(doc)

print(f"Collected {len(documents)} verses for indexing.")

# ----- Bulk Index Documents into Elasticsearch -----
actions = [
    {
        "_index": INDEX_NAME,
        "_source": doc
    }
    for doc in documents
]

print("Indexing documents into Elasticsearch...")
try:
    #helpers.bulk(es, actions, pipeline="bible-inference-endpoint")
    helpers.bulk(es, actions)
    print("Indexing complete!")
except BulkIndexError as bulk_error:
    print("Bulk indexing error:")
    # bulk_error.errors is a list of errors for each failed document
    for error in bulk_error.errors:
        print(error)