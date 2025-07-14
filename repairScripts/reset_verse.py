# This script restores the verseId property for each verse in the Neo4j database.
# It reads the verseId and text from a JSON file and updates the corresponding nodes in the database.

import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

with open("bible_parsed.json", "r", encoding="utf-8") as f:
    bible_data = json.load(f)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

all_verses = []
for book in bible_data["books"]:
    book_name = book["name"]
    for ch in book["chapters"]:
        chapter_num = ch["chapter"]
        for v in ch["verses"]:
            verse_num = v["verse"]
            verseId = f"{book_name} {chapter_num}:{verse_num}"
            all_verses.append({
                "text": v["text"],
                "verseId": verseId
            })

def update_verseId(tx, text, verseId):
    tx.run("""
        MATCH (v:Verse)
        WHERE v.text = $text
        SET v.verseId = $verseId
    """, text=text, verseId=verseId)

with driver.session() as session:
    for verse in tqdm(all_verses, desc="Restoring verseId"):
        try:
            session.execute_write(update_verseId, verse["text"], verse["verseId"])
        except Exception as e:
            print(f"Failed to update: {verse['verseId']} | {e}")

driver.close()
print("Success")