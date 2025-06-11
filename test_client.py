import requests
import json

url = "http://127.0.0.1:8000/locate"

# 수정된 JSON 데이터 로딩
with open("test_wifi_request.json", "r", encoding="utf-8") as f:
    wifi_list = json.load(f)

# 서버에 전송할 요청 형식으로 wrapping
data = {
    "apList": wifi_list["apList"]  # 기존 JSON 구조가 맞는지 확인하세요
}

# 요청 보내기
res = requests.post(url, json=data)

# 응답 확인
print("응답 코드:", res.status_code)
try:
    print("결과:", json.dumps(res.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("JSON 디코딩 오류:", e)
    print("응답 내용:", res.text)
