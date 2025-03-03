import os
import json
from elasticsearch import Elasticsearch, helpers

# ----- Configuration -----
DATA_DIR = "downloaded_jsons"  # Folder containing 1.json to 66.json
INDEX_NAME = "bible_elser"

# ----- Elasticsearch Setup -----
es = Elasticsearch("http://localhost:9200")

# Create index mapping.
# Here we use an "object" field for the embedding.
# Replace or adjust mapping as needed for your sparse representation.
mapping = {
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
            "text": {"type": "text"},
            "embedding": {"type": "object", "enabled": True}
        }
    }
}

# Delete existing index if it exists
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
es.indices.create(index=INDEX_NAME, body=mapping)
print(f"Created Elasticsearch index: {INDEX_NAME}")

# ----- Placeholder for ELSER encoding -----
def get_elser_embedding(text):
    """
    Replace this function with your actual ELSER encoding logic.
    
    This function should take a text string as input and return a sparse 
    representation of the text (for example, a dictionary mapping token 
    indices or terms to float weights).
    
    For demonstration purposes, we return a dummy sparse vector.
    """
    # Example dummy sparse vector; replace with actual ELSER output.
    return {"1": 0.1, "42": 0.5, "100": 0.2}

# ----- Process JSON Files and Prepare Documents -----
documents = []

# Loop over files 1.json to 66.json
for i in range(1, 67):
    file_path = os.path.join(DATA_DIR, f"{i}.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Iterate over chapters and verses
    for chapter in data.get("chapters", []):
        for verse in chapter.get("verses", []):
            text = verse.get("text")
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
                "text": text,
                "embedding": get_elser_embedding(text)
            }
            documents.append(doc)

print(f"Prepared {len(documents)} documents for indexing.")

# ----- Bulk Index Documents into Elasticsearch -----
actions = [
    {
        "_index": INDEX_NAME,
        "_source": doc
    }
    for doc in documents
]

helpers.bulk(es, actions)
print("Indexing complete!")