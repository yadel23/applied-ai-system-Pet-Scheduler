import json
import os
import shutil
import subprocess
import sys
from pipeline.retriever import get_retriever, retrieve
from scraper.wiki_scraper import extract_topics_from_question, DEFAULT_TOPICS

# Lazy-load retriever so stale collections are rebuilt correctly.
model = None
collection = None

FLAN_MODEL = "google/flan-t5-base"

# Lazy-load flan-t5 tokenizer and model
_tokenizer = None
_flan_model = None


def get_flan_model():
    global _tokenizer, _flan_model
    if _tokenizer is None or _flan_model is None:
        import transformers
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        transformers.logging.set_verbosity_error()
        print("Loading flan-t5-base model...")
        _tokenizer = AutoTokenizer.from_pretrained(FLAN_MODEL)
        _flan_model = AutoModelForSeq2SeqLM.from_pretrained(FLAN_MODEL)
        print("Model loaded.")
    return _tokenizer, _flan_model


def get_chroma_db_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def _topics_file():
    return os.path.join(get_chroma_db_path(), "indexed_topics.json")


def _save_indexed_topics(topics):
    os.makedirs(get_chroma_db_path(), exist_ok=True)
    with open(_topics_file(), "w") as f:
        json.dump(sorted(topics), f)


def _load_indexed_topics():
    path = _topics_file()
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def clean_chroma_db():
    db_path = get_chroma_db_path()
    if os.path.exists(db_path):
        shutil.rmtree(db_path)


def build_rag_db(question=None):
    clean_chroma_db()
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main_rag.py"))
    print(f"Building RAG index from: {script_path}")
    cmd = [sys.executable, script_path]
    if question:
        cmd.append(question)
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build RAG DB (exit code {result.returncode})")
    topics = extract_topics_from_question(question) if question else DEFAULT_TOPICS
    _save_indexed_topics(topics)


def ensure_indexed(question=None):
    global model, collection

    current_topics = sorted(extract_topics_from_question(question) if question else DEFAULT_TOPICS)
    indexed_topics = sorted(_load_indexed_topics())
    topics_changed = current_topics != indexed_topics

    if model is None or collection is None:
        model, collection = get_retriever()

    try:
        is_empty = len(collection.get()["ids"]) == 0
    except Exception:
        is_empty = True

    if is_empty or topics_changed:
        build_rag_db(question)
        model, collection = get_retriever()


def _to_complete_sentences(text, max_chars=400):
    """Trim text to the last complete sentence within max_chars."""
    import re
    text = text.strip().replace("\n", " ")
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars]
    # Find the last sentence boundary (. ! ?) within the trimmed text
    match = re.search(r"^(.*[.!?])\s", trimmed, re.DOTALL)
    if match:
        return match.group(1).strip()
    # No sentence boundary found — fall back to last word boundary
    return trimmed.rsplit(" ", 1)[0] + "..."


def answer_from_chunks(question, chunks):
    if not chunks:
        return "I don't have enough information on that topic.", []

    # Build sentence-aware context from top chunks
    context_parts = []
    total_chars = 0
    for c in chunks:
        excerpt = _to_complete_sentences(c["text"], max_chars=400 - total_chars)
        if not excerpt:
            break
        context_parts.append(excerpt)
        total_chars += len(excerpt)
        if total_chars >= 400:
            break

    context = " ".join(context_parts)

    prompt = (
        f"Use only the provided context to answer the pet care question. "
        f"Give a specific, practical answer in 2-3 sentences. "
        f"If the context does not contain the answer, say "
        f"\"I don't have enough information on that topic.\"\n\n"
        f"Context: {context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )

    tokenizer, flan = get_flan_model()
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    outputs = flan.generate(
        **inputs,
        max_new_tokens=120,
        num_beams=4,
        no_repeat_ngram_size=3,
        early_stopping=True,
    )
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # Fallback: vague or malformed output → honest not-found message
    if len(answer) < 10 or answer.lower().startswith(("a)", "b)", "1.", "2.")):
        answer = "I don't have enough information on that topic."

    sources = list({c["source"] for c in chunks})
    return answer, sources


def ask(question):
    ensure_indexed(question)

    try:
        chunks = retrieve(question, model, collection, top_k=3)
    except Exception:
        clean_chroma_db()
        build_rag_db(question)
        model, collection = get_retriever()
        chunks = retrieve(question, model, collection, top_k=3)

    answer, sources = answer_from_chunks(question, chunks)

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
