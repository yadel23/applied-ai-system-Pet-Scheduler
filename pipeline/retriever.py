import os
import chromadb
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"


def get_retriever():
    model = SentenceTransformer(EMBED_MODEL)
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="pet_care")
    return model, collection

def retrieve(query, model, collection, top_k=3):
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "source": meta["source"],
            "url": meta["url"],
            "score": round(1 - dist, 3)  # convert distance to similarity score
        })

    return chunks