import os
import chromadb
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"
SCORE_THRESHOLD = 0.05


def get_retriever():
    model = SentenceTransformer(EMBED_MODEL)
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="pet_care")
    return model, collection


def expand_query(question):
    """Rewrite the question into 4 search-friendly variants."""
    q = question.strip().rstrip("?").strip()
    return [
        question,                             # original
        f"what is {q}",                       # definition form
        f"{q} for pets",                      # pet-care context
        f"how to care for pet {q}",           # care advice form
    ]


def retrieve(query, model, collection, top_k=3):
    """
    Query expansion → embed all variants → search ChromaDB →
    score threshold filter → deduplicate → re-rank → return top_k.
    """
    queries = expand_query(query)
    embeddings = model.encode(queries).tolist()

    # Search with each query variant, collect all candidates
    candidates = {}
    for embedding in embeddings:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k * 2,  # fetch extra to have room after filtering
            include=["documents", "metadatas", "distances"]
        )
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = round(1 - dist, 3)
            chunk_id = meta.get("chunk_id") or doc[:80]  # dedup key

            # Keep the highest score seen for each unique chunk
            if chunk_id not in candidates or score > candidates[chunk_id]["score"]:
                candidates[chunk_id] = {
                    "text": doc,
                    "source": meta["source"],
                    "url": meta["url"],
                    "score": score,
                }

    # Debug: show all candidate scores so threshold can be tuned
    all_ranked = sorted(candidates.values(), key=lambda c: c["score"], reverse=True)
    print(f"\n[Retriever] Top candidate scores for: '{query}'")
    for c in all_ranked[:6]:
        print(f"  {c['score']:.3f}  {c['source']}  {c['text'][:80]!r}")

    # Filter out weak matches and re-rank by score
    filtered = [c for c in candidates.values() if c["score"] >= SCORE_THRESHOLD]
    ranked = sorted(filtered, key=lambda c: c["score"], reverse=True)

    if not ranked:
        print(f"[Retriever] No chunks passed threshold {SCORE_THRESHOLD}. Top score was "
              f"{all_ranked[0]['score']:.3f}" if all_ranked else "[Retriever] Index is empty.")

    return ranked[:top_k]
