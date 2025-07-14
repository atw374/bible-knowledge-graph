# This script repairs the structure of the Bible data in a Neo4j database.
# It ensures that each verse is correctly linked to its book and chapter, and updates the verse

import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

with open("bible_parsed.json", "r", encoding="utf-8") as f:
    bible_data = json.load(f)

def repair_structure(tx, book, chapter_num, verseId):
    tx.run("""
    MERGE (b:Book {name: $book})
    MERGE (c:Chapter {number: $chapter_num, book: $book})
    MERGE (c)-[:IN_BOOK]->(b)
    WITH c
    MATCH (v:Verse {verseId: $verseId})
    MERGE (v)-[:IN_CHAPTER]->(c)
    """, book=book, chapter_num=chapter_num, verseId=verseId)

with driver.session() as session:
    for book in tqdm(bible_data["books"], desc="Books"):
        book_name = book["name"]
        for chapter in book["chapters"]:
            chapter_num = chapter["chapter"]
            for verse in chapter["verses"]:
                verseId = f"{book_name} {chapter_num}:{verse['verse']}"
                try:
                    session.execute_write(repair_structure, book_name, chapter_num, verseId)
                except Exception as e:
                    print(f"⚠️ Failed at {verseId}: {e}")

driver.close()
print("Success")