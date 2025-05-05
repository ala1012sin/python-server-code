import requests
import json

# 파일 경로
WIFI_FILE = "test_wifi_request_4th_floor.json"
BUILDING_FILE = "building_data_4floor_only_exit_on_1F.json"
SERVER_URL = "http://127.0.0.1:8000/locate"

# Wi-Fi 측정 데이터 로드
with open(WIFI_FILE, "r", encoding="utf-8") as f:
    wifi_data = json.load(f)

# 건물 데이터 로드
with open(BUILDING_FILE, "r", encoding="utf-8") as f:
    building_data = json.load(f)

# 요청 데이터 구성
payload = {
    "building_id": "example_building",
    "building_data": building_data,
    "wifi_list": wifi_data["wifi_list"]
}

# POST 요청
res = requests.post(SERVER_URL, json=payload)

# 결과 출력
print("응답 코드:", res.status_code)
try:
    print("결과:", json.dumps(res.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("응답 파싱 오류:", e)
    print("원시 응답:", res.text)
