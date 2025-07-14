# This script extracts people mentioned in Bible verses using OpenAI's API.
# It reads verses from a JSON file, sends them to the API for processing, and saves the results.

import openai
import os
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
import backoff

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

with open("bible_parsed.json", "r", encoding="utf-8") as f:
    bible_data = json.load(f)

verses = []
for book in bible_data["books"]:
    book_name = book["name"]
    for chapter in book["chapters"]:
        chapter_num = chapter["chapter"]
        for verse in chapter["verses"]:
            verse_num = verse["verse"]
            verse_id = f"{book_name} {chapter_num}:{verse_num}"
            verses.append({"id": verse_id, "text": verse["text"]})

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def extract_people(batch):
    prompt = "Extract people mentioned in the following Bible verses using canonical names.\n"
    prompt += "Return JSON: [{\"id\": ..., \"people\": [{\"name\": ..., \"aliases\": [...]}, ...]}, ...]\n\n"
    prompt += "Verses:\n"
    for verse in batch:
        prompt += f"- ({verse['id']}): {verse['text']}\n"

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content.strip().strip("`")
    if not content.startswith("["):
        raise ValueError("Malformed response")
    return json.loads(content)

extracted = []
BATCH_SIZE = 10
num_batches = (len(verses) + BATCH_SIZE - 1) // BATCH_SIZE

for i in tqdm(range(num_batches), desc="Extracting People"):
    batch = verses[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
    try:
        result = extract_people(batch)
        extracted.extend(result)
    except Exception as e:
        print(f"Failed batch starting at {batch[0]['id']}: {e}")
    time.sleep(0.5)

with open("extracted_people.json", "w", encoding="utf-8") as f:
    json.dump(extracted, f, indent=2)

print("Success")