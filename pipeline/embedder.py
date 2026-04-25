import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# Free, local embedding model — no API key needed
EMBED_MODEL = "all-MiniLM-L6-v2"


def embed_and_store(chunks_path):
    # Load chunks
    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    # Load embedding model
    model = SentenceTransformer(EMBED_MODEL)

    # Set up ChromaDB (local, persistent)
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="pet_care")

    # Embed and insert in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [{"source": c["source_title"], "url": c["source_url"]} 
                     for c in batch]

        embeddings = model.encode(texts).tolist()

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"Stored batch {i // batch_size + 1}")

    print(f"\nDone. {len(chunks)} chunks embedded and stored.")

if __name__ == "__main__":
    embed_and_store("../data/raw_chunks.json")