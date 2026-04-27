import wikipedia
import json

# Default pet care topics (fallback)
DEFAULT_TOPICS = [
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

# Maintain TOPICS for backward compatibility
TOPICS = DEFAULT_TOPICS


def extract_topics_from_question(question, max_topics=5):
    """
    Extract only keywords explicitly mentioned in the question.
    Maps only directly mentioned terms to their Wikipedia topics.

    Args:
        question: User's question string
        max_topics: Maximum number of topics to extract

    Returns:
        List of topic strings to search for (only those mentioned in question)
    """
    question_lower = question.lower()
    extracted_topics = []

    # Pet type keywords mapped to their Wikipedia display name
    # Use care-specific articles (e.g. "Domestic rabbit" instead of "Rabbit"
    # so results focus on pet care rather than rabbit-as-food/wildlife)
    pet_mappings = {
        "dog":           "Dog",
        "puppy":         "Dog",
        "cat":           "Cat",
        "kitten":        "Cat",
        "rabbit":        "Domestic rabbit",
        "hamster":       "Hamster",
        "guinea pig":    "Guinea pig",
        "bearded dragon":"Bearded dragon",
        "budgie":        "Budgerigar",
        "parakeet":      "Budgerigar",
    }

    # Care keywords mapped to a short label used for topic combination
    care_mappings = {
        "nutrition": "nutrition",
        "feed":      "nutrition",
        "eat":       "nutrition",
        "food":      "nutrition",
        "groom":     "grooming",
        "grooming":  "grooming",
        "train":     "training",
        "training":  "training",
        "behavior":  "behavior",
        "behaviour": "behavior",
        "health":    "health",
        "sick":      "health",
        "illness":   "health",
        "disease":   "health",
        "vet":        "Veterinary medicine",
        "veterinary": "Veterinary medicine",
        "medicine":   "Veterinary medicine",
        # "sleep" and "exercise" are intentionally excluded — their Wikipedia
        # articles ("Sleep in animals", "Exercise") are too generic and score
        # poorly against pet-specific queries. The base pet + behavior article
        # added below covers these topics adequately.
    }

    # Keywords that signal lifestyle/activity questions — route to the
    # pet-specific behavior article instead of a generic topic article.
    behavior_keywords = {"sleep", "exercise", "play", "active", "rest", "energy"}
    needs_behavior = any(kw in question_lower for kw in behavior_keywords)

    # Short name used when building combined topics (e.g. "Dog nutrition")
    pet_short_name = {
        "Dog": "Dog", "Cat": "Cat", "Domestic rabbit": "Rabbit",
        "Hamster": "Hamster", "Guinea pig": "Guinea pig",
        "Bearded dragon": "Bearded dragon", "Budgerigar": "Budgerigar",
    }

    # Collect matched pet topics and care labels
    found_pets = []
    for keyword, topic in pet_mappings.items():
        if keyword in question_lower and topic not in found_pets:
            found_pets.append(topic)

    found_care = []
    for keyword, label in care_mappings.items():
        if keyword in question_lower and label not in found_care:
            found_care.append(label)

    # Build combined topics first (e.g. "Rabbit nutrition", "Dog grooming")
    # These are more targeted than the individual pet or care article alone.
    for pet in found_pets:
        short = pet_short_name.get(pet, pet)
        for care in found_care:
            if care == "Veterinary medicine":
                combined = "Veterinary medicine"
            else:
                combined = f"{short} {care}"
            if combined not in extracted_topics:
                extracted_topics.append(combined)

    # Always include the base pet article as a fallback.
    for pet in found_pets:
        if pet not in extracted_topics:
            extracted_topics.append(pet)

    # For sleep/exercise/activity questions, add the pet behavior article
    # which covers daily habits, rest, and activity levels.
    if needs_behavior:
        for pet in found_pets:
            short = pet_short_name.get(pet, pet)
            behavior_topic = f"{short} behavior"
            if behavior_topic not in extracted_topics:
                extracted_topics.append(behavior_topic)

    # If no pet was mentioned, fall back to generic care topics
    if not found_pets:
        for care in found_care:
            topic = care if care == "Veterinary medicine" else f"Pet {care}"
            if topic not in extracted_topics:
                extracted_topics.append(topic)

    return extracted_topics[:max_topics] if extracted_topics else []


def scrape_articles(topics=None):
    """
    Scrape Wikipedia articles for given topics.
    
    Args:
        topics: List of topic strings to scrape. If None, uses DEFAULT_TOPICS.
    
    Returns:
        List of article dictionaries with title, url, and content.
    """
    if topics is None:
        topics = DEFAULT_TOPICS
    
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
    import sys
    
    # Check if a question was provided as an argument
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        print(f"Extracting topics from question: {question}\n")
        topics_to_scrape = extract_topics_from_question(question)
        print(f"Topics to scrape: {topics_to_scrape}\n")
    else:
        print("Using default topics...\n")
        topics_to_scrape = DEFAULT_TOPICS
    
    articles = scrape_articles(topics_to_scrape)
    with open("../data/raw_articles.json", "w") as f:
        json.dump(articles, f, indent=2)
    # print(f"\nDone. {len(articles)} articles saved.")