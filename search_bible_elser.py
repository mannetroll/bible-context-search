#
# python search_bible_elser.py "more power to the people"
# python search_bible_elser.py --help
#
import argparse
from elasticsearch import Elasticsearch

def main():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="CLI for searching the Bible ELSER (all terms must match)"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default="more power to the people",
        help="Query ELSER (semantic) [default: 'more power to the people']"
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
        default="bible-elser",
        help="Elasticsearch index name (default: bible-elser)"
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
            "semantic": {
                "field": "text",
                "query": args.query
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
        text_field = source.get("text", "")
        # Check if the text field is a dict (as in the response example)
        if isinstance(text_field, dict):
            text_content = text_field.get("text", "")
        else:
            text_content = text_field

        print(f"\nScore: {score:.4f} - {book} {chapter}:{verse}")
        print(f"Text: {text_content[:150]}{'...' if len(text_content) > 150 else ''}")

if __name__ == "__main__":
    main()