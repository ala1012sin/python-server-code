import requests
import json

API_URL = "http://127.0.0.1:8000/find_path"

test_data = {
    "wifi_list": [
        {"bssid": "00:11:22:33:44:55", "level": -50},
        {"bssid": "66:77:88:99:AA:BB", "level": -65},
        {"bssid": "CC:DD:EE:FF:00:11", "level": -60}
    ]
}

response = requests.post(API_URL, json=test_data)

if response.status_code == 200:
    print("📍 결과:", json.dumps(response.json(), indent=4, ensure_ascii=False))
else:
    print("❌ 오류 발생:", response.status_code, response.text)
