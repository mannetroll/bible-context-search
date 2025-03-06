#
# pip install sentence-transformers elasticsearch requests
#
import os
import json
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers.errors import BulkIndexError
from tqdm import tqdm


# ----- Configuration -----
DATA_DIR = "downloaded_jsons"  # folder containing 1.json to 66.json
INDEX_NAME = "bible"
EMBEDDING_DIM = 768  # using all-mpnet-base-v2 which returns 768-dim vectors

# ----- Elasticsearch Setup -----
es_base = Elasticsearch("http://localhost:9200")
es = es_base.options(request_timeout=120)

# Define the index mapping including a dense_vector field for embeddings
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
            "text": {"type": "text"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIM
            }
        }
    }
}

# Delete the index if it exists, then create a new one
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
es.indices.create(index=INDEX_NAME, body=mapping)
print(f"Created Elasticsearch index: {INDEX_NAME}")

# ----- Initialize the Embedding Model -----
model = SentenceTransformer('all-mpnet-base-v2')

# ----- Process JSON Files and Prepare Documents -----
documents = []  # will store metadata and text for each verse
verse_texts = []  # list of verse texts for batch embedding generation

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
                "text": verse.get("text")
            }
            documents.append(doc)
            verse_texts.append(verse.get("text"))

print(f"Collected {len(documents)} verses for indexing.")

# ----- Generate Embeddings for Each Verse -----
print("Generating embeddings for verses...")
embeddings = model.encode(verse_texts, convert_to_numpy=True)

# Add the embedding to each document
for i, doc in enumerate(documents):
    # Convert numpy array to list for Elasticsearch JSON compatibility
    doc["embedding"] = embeddings[i].tolist()

# ----- Bulk Index Documents into Elasticsearch -----
actions = [
    {
        "_index": INDEX_NAME,
        "_source": doc
    }
    for doc in documents
]

#print("Indexing documents into Elasticsearch...")
#try:
#    helpers.bulk(es, actions)
#    print("Indexing complete!")
#except BulkIndexError as bulk_error:
#    print("Bulk indexing error:")
#    # bulk_error.errors is a list of errors for each failed document
#    for error in bulk_error.errors:
#        print(error)

print("Indexing documents into Elasticsearch...")
try:
    success_count = 0
    error_list = []
    # Assuming 'actions' is a list or generator of documents to index
    for ok, result in tqdm(helpers.streaming_bulk(es, actions), total=len(actions)):
        if ok:
            success_count += 1
        else:
            error_list.append(result)

    print("Indexing complete!")
    print(f"Successfully indexed {success_count} documents.")
    if error_list:
        print("Bulk indexing errors:")
        for error in error_list:
            print(error)
except BulkIndexError as bulk_error:
    print("Bulk indexing error:")
    for error in bulk_error.errors:
        print(error)