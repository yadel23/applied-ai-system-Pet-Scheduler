import hashlib
import json
import re


def chunk_text(text, max_words=300):
    """
    Splits Wikipedia text into paragraph-aware chunks that respect section
    boundaries. Each chunk is prefixed with its section header so the
    retriever and LLM always know what topic the text belongs to.

    Strategy:
      1. Walk line-by-line; detect == Section == headers.
      2. Accumulate paragraph text under the current header.
      3. When a paragraph boundary (blank line) is hit AND the buffer
         exceeds max_words, flush it as a chunk.
      4. Very short paragraphs (< 20 words) are merged into the next one
         to avoid useless stub chunks.
    """
    lines = text.split("\n")
    chunks = []
    current_section = ""
    buffer_paragraphs = []
    buffer_words = 0

    def flush(section, paragraphs):
        combined = " ".join(paragraphs).strip()
        if not combined:
            return
        prefix = f"[{section}] " if section else ""
        chunks.append(prefix + combined)

    for line in lines:
        stripped = line.strip()

        # Detect Wikipedia section headers: == Title == or === Title ===
        header_match = re.match(r"^={2,4}\s*(.+?)\s*={2,4}$", stripped)
        if header_match:
            # Flush current buffer before switching section
            if buffer_paragraphs:
                flush(current_section, buffer_paragraphs)
                buffer_paragraphs = []
                buffer_words = 0
            current_section = header_match.group(1)
            continue

        if stripped == "":
            # Blank line = paragraph boundary; flush if buffer is large enough
            if buffer_words >= max_words and buffer_paragraphs:
                flush(current_section, buffer_paragraphs)
                buffer_paragraphs = []
                buffer_words = 0
        else:
            word_count = len(stripped.split())
            # Skip stub lines (citations, single-word lines, etc.)
            if word_count < 5:
                continue
            buffer_paragraphs.append(stripped)
            buffer_words += word_count

    # Flush any remaining content
    if buffer_paragraphs:
        flush(current_section, buffer_paragraphs)

    # Split any chunk that still exceeds max_words (e.g. very long paragraphs)
    final_chunks = []
    for chunk in chunks:
        words = chunk.split()
        if len(words) <= max_words:
            final_chunks.append(chunk)
        else:
            for i in range(0, len(words), max_words):
                final_chunks.append(" ".join(words[i:i + max_words]))

    return final_chunks


def make_chunk_id(article, index):
    source = article.get("url") or article.get("title", "unknown")
    unique_key = f"{source}|{index}"
    return hashlib.sha256(unique_key.encode("utf-8")).hexdigest()


def chunk_articles(input_path, output_path):
    with open(input_path, "r") as f:
        articles = json.load(f)

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
