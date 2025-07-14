# This script fetches the King James Version (KJV) Bible in JSON format from a URL and saves it to a local file.
# It uses the requests library to download the data and json to save it in a structured format

import requests
import json

url = "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/KJV.json"
response = requests.get(url)
bible_data = response.json()

with open("bible_parsed.json", "w", encoding="utf-8") as f:
    json.dump(bible_data, f, indent=2)

print(f"Loaded {len(bible_data)} verses.")