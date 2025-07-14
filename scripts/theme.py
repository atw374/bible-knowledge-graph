# This script clusters Bible verse embeddings, generates themes using GPT-4, and uploads the results to a Neo4j database.
# It reads verse embeddings from a JSON file, performs clustering, labels themes, and establishes relationships

import json
import numpy as np
import hdbscan
import random
from collections import Counter
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import openai
from tqdm import tqdm

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")

with open("verse_embeddings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

verseIds = list(data.keys())
texts = [data[vid]["text"] for vid in verseIds]
vectors = np.array([data[vid]["embedding"] for vid in verseIds])

# Shuffle for clustering fairness
combined = list(zip(verseIds, texts, vectors))
random.shuffle(combined)
verseIds, texts, vectors = zip(*combined)
vectors = np.array(vectors)

print("🔍 Clustering verse embeddings using HDBSCAN...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=10, metric='euclidean', core_dist_n_jobs=-1)
clusters = clusterer.fit_predict(vectors)

cluster_labels = {}
cluster_to_ids = {}
for i, cluster_id in enumerate(clusters):
    if cluster_id == -1:
        continue
    cluster_to_ids.setdefault(cluster_id, []).append(i)

print(f"Generating theme labels for {len(cluster_to_ids)} clusters using GPT-4...")
for cluster_id, indices in tqdm(cluster_to_ids.items(), desc="Labeling"):
    centroid = vectors[indices].mean(axis=0)
    central_verses = sorted(indices, key=lambda i: np.dot(vectors[i], centroid))[-10:]
    sample_texts = [texts[i] for i in central_verses]
    
    book_counts = Counter([verseIds[i].split()[0] for i in indices])
    print(f"📘 Cluster {cluster_id} book distribution: {dict(book_counts)}")

    prompt = (
        "You are labeling clusters of Bible verses to identify recurring themes. Each cluster contains verses that share a common theme or message. Verses may have multiple themes apply to them "
        "Return a single, meaningful word or phrase that summarizes the central message of the cluster "
        "(e.g. 'Redemption', 'Law', 'Prophecy', 'Faith', 'Rejection', 'Guardian Redeemer', 'Temple Worship', 'Love', 'War', 'Exile', 'Covenant', 'Angels', 'Heaven', 'Promise').\n\n"
    )
    prompt += "\n".join(f"- {t}" for t in sample_texts)
    prompt += "\n\nTheme:"

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        theme = response.choices[0].message.content.strip()
    except Exception as e:
        theme = f"Cluster_{cluster_id}"
        print(f"⚠️ Error labeling cluster {cluster_id}: {e}")

    cluster_labels[cluster_id] = theme

centroids = {cid: vectors[cluster_to_ids[cid]].mean(axis=0) for cid in cluster_labels.keys()}

print("Computing similarity links...")
SIMILARITY_THRESHOLD = 0.80
verse_theme_links = []

for i, verseId in tqdm(list(enumerate(verseIds)), desc="Computing"):
    if clusters[i] == -1:
        continue
    vec = vectors[i]

    sims = {
        cluster_labels[cid]: np.dot(vec, centroid) / (np.linalg.norm(vec) * np.linalg.norm(centroid))
        for cid, centroid in centroids.items()
    }

    for theme, score in sims.items():
        if score >= SIMILARITY_THRESHOLD:
            verse_theme_links.append((verseId, theme))

print(f"Prepared {len(verse_theme_links)} verse-theme links for upload.")

def upload_links(session, links_batch):
    session.write_transaction(_upload_batch, links_batch)

def _upload_batch(tx, links):
    for verseId, theme in links:
        tx.run("""
        MATCH (v:Verse {verseId: $verseId})
        MATCH (t:Theme {name: $theme})
        MERGE (v)-[:HAS_THEME]->(t)
        """, verseId=verseId, theme=theme)

print("Uploading to Neo4j in batches...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
BATCH_SIZE = 100

with driver.session() as session:
    for theme in cluster_labels.values():
        session.run("MERGE (:Theme {name: $name})", name=theme)

    for i in tqdm(range(0, len(verse_theme_links), BATCH_SIZE), desc="Uploading"):
        batch = verse_theme_links[i:i + BATCH_SIZE]
        try:
            upload_links(session, batch)
        except Exception as e:
            print(f"⚠️ Upload failed for batch {i // BATCH_SIZE}: {e}")

driver.close()
print("Success")
