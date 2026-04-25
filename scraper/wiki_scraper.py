import wikipedia
import json

# Define your target pet care topics
TOPICS = [
    # Dogs
    "Dog nutrition", "Dog grooming", "Dog breed", 
    "Dog training", "Puppy", "Dog health",
    # Cats
    "Cat nutrition", "Cat behavior", "Cat grooming",
    "Kitten", "Cat health",
    # Small pets
    "Rabbit care", "Hamster", "Guinea pig",
    "Bearded dragon", "Budgerigar",
    # General
    "Veterinary medicine", "Pet", "Animal nutrition"
]

def scrape_articles(topics):
    articles = []

    for topic in topics:
        try:
            page = wikipedia.page(topic, auto_suggest=False)
            articles.append({
                "title": page.title,
                "url": page.url,
                "content": page.content  # plain text, no HTML
            })
            print(f"✓ Scraped: {page.title}")
        except wikipedia.DisambiguationError as e:
            # If a topic is ambiguous, pick the first option
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                articles.append({
                    "title": page.title,
                    "url": page.url,
                    "content": page.content
                })
                print(f"✓ Scraped (disambiguation): {page.title}")
            except:
                print(f"✗ Skipped (disambiguation): {topic}")
        except Exception as ex:
            print(f"✗ Failed: {topic} — {ex}")

    return articles

if __name__ == "__main__":
    articles = scrape_articles(TOPICS)
    with open("../data/raw_articles.json", "w") as f:
        json.dump(articles, f, indent=2)
    print(f"\nDone. {len(articles)} articles saved.")