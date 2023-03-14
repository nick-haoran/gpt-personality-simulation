import requests
import sys

url = "https://api.wer.plus/api/dub?t=" + sys.argv[1]
response = requests.get(url).json()
print(response['data']['text'])