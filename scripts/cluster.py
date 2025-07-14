# This script performs clustering on verse embeddings using HDBSCAN.
# It reads embeddings from a JSON file, runs clustering, and saves the results.

import json
import numpy as np
import hdbscan

with open("verse_embeddings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

verseIds = list(data.keys())
vectors = np.array([data[vid]["embedding"] for vid in verseIds])

print("🔍 Running HDBSCAN clustering...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=20, metric='euclidean', core_dist_n_jobs=-1)
clusters = clusterer.fit_predict(vectors)

cluster_map = {vid: int(cid) for vid, cid in zip(verseIds, clusters)}

with open("clusters.json", "w", encoding="utf-8") as f:
    json.dump(cluster_map, f, indent=2)

print(f"Success with {len(cluster_map)} entries.")
