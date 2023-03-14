import json
import sys

import requests

url = f"https://www.googleapis.com/customsearch/v1?key=AIzaSyCjzhRGOwdo_b3bdrW0t8-fMCPh8GbE4Aw&q={sys.argv[1]}&cx=c2e9aa4a7fd614ecc&num=5&hl=zh-CN"
response = requests.get(url)
result = json.loads(response.text.replace('\xa0', ' ').replace('\u2022', ' '))

for item in result["items"]:
    print(item["snippet"])