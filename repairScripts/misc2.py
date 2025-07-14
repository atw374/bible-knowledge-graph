# This script repairs and enriches existing Bible verse nodes in a Neo4j database.
# It ensures that each verse has the correct book and chapter relationships, and updates the verseId

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

verse_map = {}
for book in bible_data["books"]:
    bookNum = book["name"]
    for ch in book["chapters"]:
        chapterNum = ch["chapter"]
        chapterId = f"{bookNum} {chapterNum}"
        for v in ch["verses"]:
            verseNum = v["verse"]
            verseId = f"{bookNum} {chapterNum}:{verseNum}"
            verse_map[verseId] = {
                "book": bookNum,
                "chapter": chapterNum,
                "verse": verseNum,
                "text": v["text"],
                "chapterId": chapterId
            }


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

with driver.session() as session:
    result = session.run("""
        MATCH (v:Verse)
        RETURN v.verseId AS id
    """)
    existing_verse_ids = {record["id"] for record in result}


def repair_and_enrich(tx, payload):
    tx.run("""
    MERGE (b:Book {name: $book})
    MERGE (c:Chapter {number: $chapter, book: $book})
    SET c.name = $chapterId
    MERGE (c)-[:IN_BOOK]->(b)
    WITH c
    MATCH (v:Verse)
    WHERE v.text = $text
    SET v.verseId = $verseId
    MERGE (v)-[:IN_CHAPTER]->(c)
    """, payload)

with driver.session() as session:
    for verseId in tqdm(existing_verse_ids, desc="Repairing"):
        if verseId not in verse_map:
            continue  # skip if not in JSON

        payload = {
            "book": verse_map[verseId]["book"],
            "chapter": verse_map[verseId]["chapter"],
            "chapterId": verse_map[verseId]["chapterId"],
            "verseId": verseId
        }
        session.execute_write(repair_and_enrich, payload)

driver.close()