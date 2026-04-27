# Applied AI System Pet Scheduler: PawPal+ 

## Summary

PawPal+ is an pet care scheduling assistant built with Python and Streamlit. It helps pet owners plan and manage daily care tasks for their pets by generating conflict-free, priority-aware schedules based on the owner's availability and the pet's needs.

The app combines a constraint-based task scheduler with a RAG (Retrieval-Augmented Generation) chatbot that answers simple pet care questions in real time. The chatbot fetches relevant information directly from Wikipedia, embeds it into a local vector database (chromeDb), and uses a local language model (google/flan-t5-base) to generate focused, context-grounded answers — no cloud API key to worry about. 

Base project url: https://github.com/yadel23/ai110-module2show-pawpal-starter

### How It Works

**Scheduler**
The owner enters their name, pet details (name, species, age), and one or more availability windows for the day. They then add care tasks with a title, duration, and priority level. PawPal+ scores each task using a weighted formula (priority × 0.5 + urgency × 0.3 + preference match × 0.2) and packs them sequentially into available time windows — respecting rest blocks, quiet hours, and a configurable daily activity limit. The resulting schedule is displayed in a table with the time, task name, duration, priority, and reasoning for each placement.

**RAG Chatbot feature (extension feature)**
1. **Keyword extraction** — The user's question is parsed for pet type (dog, cat, rabbit, etc.) and care topic (nutrition, grooming, health, behavior, etc.) to identify the most relevant Wikipedia articles to fetch
2. **Wikipedia scraping** — Targeted articles are scraped and stored locally
3. **Sentence-aware chunking** — Articles are split into clean, paragraph-level chunks prefixed with their Wikipedia section header (e.g. `[Diet]`, `[Health]`) so each chunk carries its own context
4. **Embedding** — Chunks are embedded using `all-MiniLM-L6-v2` (SentenceTransformers) and stored in ChromaDB
5. **Query expansion** — The user's question is rewritten into 4 search-friendly variants to improve retrieval coverage
6. **Retrieval + scoring** — All 4 query embeddings are used to search ChromaDB; results are deduplicated and ranked by similarity score; a score threshold filters out loosely related chunks
7. **Answer generation** — The top-ranked chunks are passed to `google/flan-t5-base` with a structured prompt that instructs the model to give a specific, practical 2–3 sentence answer based only on the provided context
8. **Fallback** — If no relevant chunks are found, the chatbot honestly responds: "I don't have enough information on that topic."

## Architecture Overview (`assets\system_diagram.md`)
1. Build Index (once per topic) — extracts keywords, scrapes Wikipedia, chunks the text, then embeds and stores it in ChromaDB.
2. Retrieve & Rank (every question) — expands the query into 4 variants, searches ChromaDB, filters low-scoring results, and re-ranks the top 3 chunks.
3. Generate Answer — if relevant chunks were found, builds a prompt and runs it through google/flan-t5-base; if not, returns a "not enough information" fallback. The answer goes back to the UI.

![chat diagram](assets\Chat_diagram.png)


## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### App Demo (`app.py`)
```bash
streamlit run app.py
```
1. open the left sidebar for PawPal+chat 
2. ask a simple question and get a back a short answer on data pulled from Wikipedia 
3. ex How much do dogs sleep on average?, how much water do cats need?, how often should i wash my dog? 
![chat screenshot](assets\pawpalchat_Screenshot.png)

# Testing PawPal+
```bash
python3 -m pytest
```

## DEMO
![PawPal App](assets\Demo_Screenshot.png)









## Original Features

### Pet & Owner Setup
- Enter owner name, pet name, species (dog, cat, rabbit, bird, reptile, other), and age
- Add multiple availability windows with custom start/end times
- Remove individual windows with a per-window delete button
- Set a daily max activity limit (30–480 minutes)
- Input validation: start must be before end; at least one window required before scheduling

### Task Management
- Add pet care tasks with a title, duration (1–240 min), and priority (low / medium / high)
- Tasks are displayed in a table as they are added
- High-priority tasks are automatically marked mandatory

### Smart Scheduling
- Generates a conflict-free daily schedule based on owner availability, pet rest blocks, and quiet hours set by owner
- Tasks are scored and ordered by a weighted formula (priority × 0.5 + urgency × 0.3 + preference match × 0.2)
- Higher-priority and overdue tasks are placed first
- Tasks are packed sequentially within windows — no gaps or double-booking
- Supports multiple availability windows across the day
- Tasks too long to fit in any window are reported with a "Could not place" note

### Schedule Display
- Scheduled tasks shown in a chronological table (time, task, duration, priority, reason)
- Notes section explains scheduling decisions and warnings
- Warning shown when total scheduled time exceeds the max activity limit

### Task Completion
- Checklist below the schedule table to mark tasks complete one at a time
- Checking a task immediately regenerates the schedule, removing it from the table
- Completed tasks are excluded from future schedule runs
- Green success banner appears when all scheduled tasks are done

### Summary
- Total minutes scheduled for the day
- Mandatory tasks listed by name with count
- Optional tasks listed by name with count

### Terminal Demo (`main.py`)
- Creates an owner with three pets (dog, cat, rabbit), each with three tasks
- Prints a formatted "Today's Schedule" to the terminal per pet
- Shows task times, names, and mandatory/optional labels



<!-- ## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built. -->
