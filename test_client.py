import requests
import json

url = "http://127.0.0.1:8000/locate"

with open("test_wifi_request.json", "r", encoding="utf-8") as f:
    data = json.load(f)

res = requests.post(url, json=data)
print("응답 코드:", res.status_code)
print("결과:", res.json())
