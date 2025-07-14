# This script embeds Bible verses using OpenAI's API and uploads the embeddings to a Neo4j database.
# It reads verses from a JSON file, generates embeddings, and stores them in the database.

import openai
import os
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def upload_to_neo4j(session, verses):
    for verse in verses:
        session.run("""
            MATCH (v:Verse {verseId: $id})
            SET v.embedding = $embedding
        """, id=verse["id"], embedding=verse["embedding"])

with open("bible_parsed.json", "r", encoding="utf-8") as f:
    bible_data = json.load(f)

all_verses = []
for book in bible_data["books"]:
    bookName = book["name"]
    for chapter in book["chapters"]:
        chapterNum = chapter["chapter"]
        for verse in chapter["verses"]:
            verseId = f"{bookName} {chapterNum}:{verse['verse']}"
            all_verses.append({
                "id": verseId,
                "text": verse["text"]
            })

BATCH_SIZE = 50
embedded = {}

print(f"Embedding and uploading {len(all_verses)} verses...")

with driver.session() as session:
    for i in tqdm(range(0, len(all_verses), BATCH_SIZE)):
        batch = all_verses[i:i + BATCH_SIZE]
        texts = [v["text"] for v in batch]
        ids = [v["id"] for v in batch]

        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            processed = []
            for j, item in enumerate(response.data):
                processed.append({
                    "id": ids[j],
                    "text": texts[j],
                    "embedding": item.embedding
                })
                embedded[ids[j]] = {
                    "text": texts[j],
                    "embedding": item.embedding
                }

            # Upload immediately
            upload_to_neo4j(session, processed)
            time.sleep(0.3)

        except Exception as e:
            print(f"ERROR: Batch {i//BATCH_SIZE + 1} failed: {e}")
            continue

# Optional: Backup embeddings locally
with open("verse_embeddings.json", "w", encoding="utf-8") as f:
    json.dump(embedded, f, indent=2)

driver.close()
print("Success")
