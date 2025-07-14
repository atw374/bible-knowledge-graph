# This script uploads extracted people and places data to a Neo4j database.
# It reads data from JSON files and creates nodes and relationships in the database.

import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

with open("extracted_people.json", "r", encoding="utf-8") as f:
    people_data = json.load(f)
with open("extracted_places.json", "r", encoding="utf-8") as f:
    places_data = json.load(f)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def upload_batch(tx, entries):
    for entry in entries:
        verse_id = entry["id"]
        for person in entry.get("people", []):
            name = person["name"].strip()
            aliases = [a.strip() for a in person.get("aliases", [])]
            tx.run("""
            MERGE (p:Person {name: $name})
            SET p.aliases = $aliases
            WITH p
            MATCH (v:Verse {verseId: $verse_id})
            MATCH (v)-[:IN_CHAPTER]->(c:Chapter)
            MATCH (c)-[:IN_BOOK]->(b:Book)
            MERGE (v)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_VERSE]->(v)
            MERGE (c)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_CHAPTER]->(c)
            MERGE (b)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_BOOK]->(b)
            """, name=name, aliases=aliases, verse_id=verse_id)

        for place in entry.get("places", []):
            name = place["name"].strip()
            aliases = [a.strip() for a in place.get("aliases", [])]
            tx.run("""
            MERGE (p:Place {name: $name})
            SET p.aliases = $aliases
            WITH p
            MATCH (v:Verse {verseId: $verse_id})
            MATCH (v)-[:IN_CHAPTER]->(c:Chapter)
            MATCH (c)-[:IN_BOOK]->(b:Book)
            MERGE (v)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_VERSE]->(v)
            MERGE (v)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_VERSE]->(v)
            MERGE (c)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_CHAPTER]->(c)
            MERGE (b)-[:MENTIONS]->(p)
            MERGE (p)-[:IN_BOOK]->(b)
            """, name=name, aliases=aliases, verse_id=verse_id)

combined = {}
for entry in people_data:
    combined[entry["id"]] = {"id": entry["id"], "people": entry.get("people", []), "places": []}
for entry in places_data:
    if entry["id"] not in combined:
        combined[entry["id"]] = {"id": entry["id"], "people": [], "places": entry.get("places", [])}
    else:
        combined[entry["id"]]["places"] = entry.get("places", [])

batch_size = 50
with driver.session() as session:
    for i in tqdm(range(0, len(combined), batch_size), desc="Uploading to Neo4j"):
        batch = list(combined.values())[i:i+batch_size]
        session.execute_write(upload_batch, batch)

driver.close()
print("Success")
