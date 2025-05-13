import requests
import json

with open("test_wifi_request.json", "r") as f:
    data = json.load(f)

url = "https://python-server-code-production.up.railway.app/locate"  # 배포된 도메인
res = requests.post(url, json=data)

print("응답 코드:", res.status_code)
print("결과:", res.json())
