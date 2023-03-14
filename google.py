import json
import sys

import requests

url = f"https://www.googleapis.com/customsearch/v1?key=*******************************&q={sys.argv[1]}&cx=*********************&num=5&hl=zh-CN"
response = requests.get(url)
result = json.loads(response.text.replace('\xa0', ' ').replace('\u2022', ' '))

for item in result["items"]:
    print(item["snippet"])
