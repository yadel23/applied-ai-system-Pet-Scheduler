import json
import os
import shutil

from scraper.wiki_scraper import TOPICS, scrape_articles
from pipeline.chunker import chunk_articles
from pipeline.embedder import embed_and_store

project_root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(project_root, "data")
raw_articles_path = os.path.join(data_dir, "raw_articles.json")
raw_chunks_path = os.path.join(data_dir, "raw_chunks.json")
chroma_db_path = os.path.join(project_root, "chroma_db")

if os.path.exists(chroma_db_path):
    print("Removing existing ChromaDB directory for a clean rebuild...")
    shutil.rmtree(chroma_db_path)

print("=== Step 1: Scraping Wikipedia ===")
articles = scrape_articles(TOPICS)
with open(raw_articles_path, "w") as f:
    json.dump(articles, f, indent=2)

print("\n=== Step 2: Chunking ===")
chunk_articles(raw_articles_path, raw_chunks_path)

print("\n=== Step 3: Embedding + Storing ===")
embed_and_store(raw_chunks_path)

print("\n=== All done. Run chatbot/chat.py to start chatting ===")