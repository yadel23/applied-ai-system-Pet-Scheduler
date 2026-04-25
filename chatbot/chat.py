import os
import shutil
import subprocess
import sys
from pipeline.retriever import get_retriever, retrieve

# Lazy-load retriever so stale collections are rebuilt correctly.
model = None
collection = None


def get_chroma_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def clean_chroma_db():
    db_path = get_chroma_db_path()
    if os.path.exists(db_path):
        shutil.rmtree(db_path)


def build_rag_db():
    clean_chroma_db()
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main_rag.py"))
    print(f"Building RAG index from: {script_path}")
    result = subprocess.run([sys.executable, script_path], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build RAG DB (exit code {result.returncode})")


def ensure_indexed():
    global model, collection
    if model is None or collection is None:
        model, collection = get_retriever()

    try:
        if len(collection.get()["ids"]) == 0:
            clean_chroma_db()
            build_rag_db()
            model, collection = get_retriever()
    except Exception:
        clean_chroma_db()
        build_rag_db()
        model, collection = get_retriever()


def answer_from_chunks(chunks):
    if not chunks:
        return "I couldn't find any relevant Wikipedia content for that question.", []

    answer_parts = []
    for c in chunks:
        excerpt = c["text"].strip().replace("\n", " ")
        if len(excerpt) > 450:
            excerpt = excerpt[:450].rsplit(" ", 1)[0] + "..."
        answer_parts.append(f"Source: {c['source']}\n{excerpt}")

    answer = (
        "I found the most relevant pet care information from Wikipedia below. "
        "Use these notes to answer your question.\n\n" + "\n\n".join(answer_parts)
    )
    sources = list({c["source"] for c in chunks})
    return answer, sources


def ask(question):
    # Ensure the RAG DB is populated before retrieval.
    ensure_indexed()

    try:
        # Step 1: Retrieve relevant chunks
        chunks = retrieve(question, model, collection, top_k=3)
    except Exception:
        clean_chroma_db()
        build_rag_db()
        model, collection = get_retriever()
        chunks = retrieve(question, model, collection, top_k=3)

    # Step 2: Build answer from retrieved chunks
    answer, sources = answer_from_chunks(chunks)

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    print("Pet Care Chatbot — type 'quit' to exit\n")
    while True:
        question = input("You: ").strip()
        if question.lower() == "quit":
            break
        result = ask(question)
        print(f"\nBot: {result['answer']}")
        print(f"Sources: {', '.join(result['sources'])}\n")