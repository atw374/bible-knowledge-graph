# This script uploads the Bible data to a Neo4j graph database.
# It creates nodes for books, chapters, and verses, and establishes relationships between them.

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

load_dotenv
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

with open("bible_parsed.json", "r", encoding="utf-8") as f:
    bible_data = json.load(f)

def create_book(tx, book_entry):
    book = book_entry["name"]
    tx.run("MERGE (b:Book {name: $book})", book=book)

    for chapter_entry in book_entry["chapters"]:
        chapterNum = int(chapter_entry["chapter"])
                
        tx.run("""
        MERGE (b:Book {name: $book})
        MERGE (c:Chapter {number: $chapterNum, book: $book})
        MERGE (b)-[:HAS_CHAPTER]->(c)
        """, book=book, chapterNum=chapterNum)

        prev_verseId = None

        for verse_entry in chapter_entry["verses"]:
            verseNum = int(verse_entry["verse"])
            text = verse_entry["text"]
            verseId = f"{book} {chapterNum}:{verseNum}"
        
            tx.run("""
            MERGE (v:Verse {verseId: $verseId})
              ON CREATE SET v.number = $verseNum, v.text = $text

            MERGE (c:Chapter {number: $chapterNum, book: $book})
            MERGE (c)-[:HAS_VERSE]->(v)
            """, book=book, chapterNum=chapterNum,
                 verseNum=verseNum, text=text, verseId=verseId)
            
            if prev_verseId:
                tx.run("""
                MATCH (v1:Verse {verseId: $prevId})
                MATCH (v2:Verse {verseId: $currId})
                MERGE (v1)-[:NEXT_VERSE]->(v2)
                """, prevId=prev_verseId, currId=verseId)

            prev_verseId = verseId

with driver.session() as session:
    for book_entry in bible_data["books"]:
        session.execute_write(create_book, book_entry)
        print(f"📘 Uploaded book: {book_entry['name']}")

driver.close()
print("Successfully uploaded Bible data to Neo4j database.")