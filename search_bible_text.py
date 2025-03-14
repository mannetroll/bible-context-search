#
# python search_bible_text.py "more power to the people"
# python search_bible_text.py --help
#
import argparse

from elasticsearch import Elasticsearch


def main():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="CLI for searching the Bible text field (all terms must match)"
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

    # Build the query to match terms in the 'text' field.
    query_body = {
        "size": args.top_k,
        "query": {
            "match": {
                "text": {
                    "query": args.query,
                    "operator": "or"
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
        score = hit["_score"]
        source = hit["_source"]
        book = source.get("book", "Unknown")
        chapter = source.get("chapter", "?")
        verse = source.get("verse", "?")
        text = source.get("text", "")
        print(f"\nScore: {score:.4f} - {book} {chapter}:{verse}")
        print(f"Text: {text[:150]}{'...' if len(text) > 150 else ''}")


if __name__ == "__main__":
    main()
