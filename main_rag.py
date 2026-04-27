import json
import os
import shutil
import sys

from scraper.wiki_scraper import DEFAULT_TOPICS, extract_topics_from_question, scrape_articles
from pipeline.chunker import chunk_articles
from pipeline.embedder import embed_and_store

project_root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(project_root, "data")
raw_articles_path = os.path.join(data_dir, "raw_articles.json")
raw_chunks_path = os.path.join(data_dir, "raw_chunks.json")
chroma_db_path = os.path.join(project_root, "chroma_db")
print("===== Start of Chat ====")
# Determine topics to use
if len(sys.argv) > 1:
    # If a question is provided as argument, extract topics from it
    question = " ".join(sys.argv[1:])
    print(f"=== Analyzing Question: {question} ===\n")
    topics = extract_topics_from_question(question)
    if not topics:
        print("⚠️  Warning: No recognized keywords found in your question.")
        print("Supported keywords include: dog, cat, rabbit, hamster, guinea pig, nutrition, grooming, training, behavior, health, etc.\n")
        print("Using DEFAULT_TOPICS instead...\n")
        topics = DEFAULT_TOPICS
    print(f"Extracted Topics: {topics}\n")
else:
    # Otherwise, use default topics
    print("No question provided. Using DEFAULT_TOPICS...\n")
    topics = DEFAULT_TOPICS

if os.path.exists(chroma_db_path):
    print("Removing existing ChromaDB directory for a clean rebuild...")
    shutil.rmtree(chroma_db_path)

print("=== Step 1: Scraping Wikipedia ===")
articles = scrape_articles(topics)

if not articles:
    print("\n❌ Error: No articles were scraped!")
    print("Make sure your question contains recognized keywords:")
    print("   Pet types: dog, cat, rabbit, hamster, guinea pig, bearded dragon, budgie, parakeet")
    print("   Care topics: nutrition, feed, eat, groom, train, behavior, health, sleep, exercise, vet, etc.")
    print("\nExample: python3 main_rag.py 'how much do rabbits sleep?'")
    sys.exit(1)

with open(raw_articles_path, "w") as f:
    json.dump(articles, f, indent=2)

print(f"\n✓ Successfully scraped {len(articles)} articles")

print("\n=== Step 2: Chunking ===")
chunk_articles(raw_articles_path, raw_chunks_path)

print("\n=== Step 3: Embedding + Storing ===")
embed_and_store(raw_chunks_path)

print("\n=== All done. Run chatbot/chat.py to start chatting ===")