import hashlib
import json


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Splits text into chunks by word count with overlap.
    Overlap helps preserve context across chunk boundaries.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # slide window with overlap

    return chunks


def make_chunk_id(article, index):
    source = article.get("url") or article.get("title", "unknown")
    unique_key = f"{source}|{index}"
    return hashlib.sha256(unique_key.encode("utf-8")).hexdigest()


def chunk_articles(input_path, output_path):
    with open(input_path, "r") as f:
        articles = json.load(f)

    # Deduplicate articles by URL or title to prevent repeated IDs.
    seen_sources = set()
    unique_articles = []
    for article in articles:
        source = article.get("url") or article.get("title")
        if source not in seen_sources:
            seen_sources.add(source)
            unique_articles.append(article)

    all_chunks = []

    for article in unique_articles:
        chunks = chunk_text(article["content"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": make_chunk_id(article, i),
                "source_title": article["title"],
                "source_url": article["url"],
                "text": chunk
            })

    with open(output_path, "w") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"Done. {len(all_chunks)} chunks created from {len(unique_articles)} unique articles.")


if __name__ == "__main__":
    chunk_articles("../data/raw_articles.json", "../data/raw_chunks.json")