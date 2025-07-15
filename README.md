# 📖 Bible Knowledge Graph

A Python + Neo4j project to extract people, places, and themes from the Bible using OpenAI. This graph-based pipeline explores how structured knowledge can be derived from unstructured text to support Biblical understanding through semantic analysis, thematic clustering, and future AI-assisted exploration.

---

## 🚀 Features

* ✅ Extracts canonical **people** and **place** entities from each verse (with aliases)
* ✅ Enriches the graph with **themes** via semantic clustering of OpenAI embeddings
* ✅ Builds a fully queryable **Neo4j knowledge graph** with relationships like:

  * `(:Verse)-[:MENTIONS]->(:Person)`
  * `(:verse)-[:IN_CHAPTER]->(:Chapter)`
  * `(:Verse)-[:HAS_THEME]->(:Theme)`
  * `(:Person)-[:IN_BOOK]->(:Book)`
* ✅ Designed for future extensions like question answering, dashboards, or semantic search

---

## 🧠 Why It Matters

> "How can we find patterns in text data?"

This project began as a personal experiment in building something ambitious: a semantic, searchable Bible powered by modern LLMs and graph databases.

The work demonstrates:

* LLM-assisted entity extraction in real-world noisy text
* Clustering based on dense embeddings (themes)
* Canonical mapping and disambiguation design
* Graph schema planning and Neo4j integrations

And perhaps most importantly: it shows how to turn ambiguity into learning.

Even without full extraction, this project supports:

* 🔍 Who/what/where co-occurrence analysis
* 🧭 Traversal and proximity of characters or themes
* 📚 Thematic overlap between chapters or stories

---

## 📁 Project Structure

```
.
├── data/                     # Bible input JSON (not uploaded)
├── outputs/                  # Extracted JSON files (excluded from repo)
├── neo4j/                    # Schema helpers (e.g., constraints)
│   ├── explore_graph.txt
│   └── indexes_constraints.txt
├── scripts/                  # Core processing scripts (alphabetic, not in order of execution)
│   ├── cluster.py            # Clusters Verse embeddings for theme extraction
│   ├── driver.py             # Connects and creates initial Neo4j graph
│   ├── jsonParse.py          # [Optional - only if using JSON over .txt] Parses Bible JSON text 
│   ├── people_extract.py     # Extracts people nodes from text (JSON)
│   ├── peopleplace_upload.py # Uploads people and place nodes to Neo4j
│   ├── places_extract.py     # Extracts place nodes from text (JSON)
│   └── theme.py              # Automates the process of clustering Bible verse embeddings, generates thematic labels for each cluster using GPT-4, and uploads the results to Neo4j
├── .env.example              # Config template
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🛠️ How to Use

1. Clone the repo:

```bash
git clone https://github.com/atw374/bible-knowledge-graph.git
cd bible-knowledge-graph
```

2. Set up your environment:

```bash
cp .env.example .env
# Fill in your OpenAI + Neo4j credentials
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create indexes and constraints:

```Cypher
(in Neo4j) neo4j/indexes_constraints.txt
```

5. Run extraction and upload (verify success after each file - bear in mind API cost): 

```bash
python Scripts/driver.py
python scripts/extract_people.py
python scripts/extract_places.py
python scripts/upload_entities.py
python scripts/theme.py
```

6. Explore the graph:

* Run sample queries in Neo4j from explore_graph.txt
* Connect to your Neo4j Aura instance and try out thematic or relational queries

---

## 🧪 Example Queries

* **Chapters that mention both Moses and Egypt**
* **People co-mentioned with Jesus**
* **Themes shared by verses that mention David**
* **Verses associated with the theme 'Prophecy'**
* **Cross-Testament figures** (mentioned in both Old + New Testaments)

See `notebooks/explore_graph.ipynb` for runnable examples.

---

## 🔒 Notes

* `.env` is excluded — copy `.env.example` to configure your keys
* `outputs/` and full data files are excluded for size and reproducibility
* You can regenerate all results with the included scripts

---

## 📝 License

MIT — free to use, modify, and build upon.

---

## 🙋‍♂️ Author

**Andrew W.**
Built with curiosity, scripture, and the desire to explore and connect God's word
