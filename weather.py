import requests
import json
url = "https://v.api.aa1.cn/api/tianqi-zs/index.php?id=101010100"
response = requests.get(url)
result = json.loads(response.text)

print("城市:", result["city"])
print("更新时间:", result["update"])
print("天气指数:")
for key, value in result["data"].items():
    print(value["name"], ":", value["type"])