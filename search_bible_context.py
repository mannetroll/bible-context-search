#
# python search_bible_context.py "more power to the people"
#
import argparse

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


def main():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="CLI for searching Bible verses using all-mpnet-base-v2 embeddings"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default="more power to the people",
        help="Query text (all terms must match) [default: 'more power to the people']"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)"
    )
    parser.add_argument(
        "--index",
        type=str,
        default="bible",
        help="Elasticsearch index name (default: bible)"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Number of top results to return (default: 5)"
    )
    args = parser.parse_args()

    # Connect to Elasticsearch.
    es = Elasticsearch(args.host)

    # Load the SentenceTransformer model.
    model = SentenceTransformer('all-mpnet-base-v2')

    # Generate the query embedding.
    query_embedding = model.encode(args.query, convert_to_numpy=True)

    # Build the Elasticsearch query.
    # We use a script_score query to compute cosine similarity between the query embedding
    # and each document's "embedding" field. The cosineSimilarity function returns a value in
    # [-1, 1] so we add 1.0 to make the score positive.
    query_body = {
        "size": args.top_k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding.tolist()}
                }
            }
        }
    }

    # Execute the search query.
    response = es.search(index=args.index, body=query_body)
    hits = response["hits"]["hits"]

    # Display the results.
    print(f"Top {args.top_k} results for query: '{args.query}'")
    for hit in hits:
        source = hit["_source"]
        score = hit["_score"]
        book = source.get("book", "Unknown")
        chapter = source.get("chapter", "?")
        verse = source.get("verse", "?")
        text = source.get("text", "")
        print(f"\nScore: {score:.4f} - {book} {chapter}:{verse}")
        print(f"Text: {text[:150]}{'...' if len(text) > 150 else ''}")


if __name__ == "__main__":
    main()
