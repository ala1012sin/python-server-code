# 🧭 FastAPI 기반 실내 WiFi 위치 예측 및 탈출 경로 서버

건물 내 WiFi 신호 세기(RSSI)를 기반으로 사용자의 실내 위치(x, y, z)를 추정하고,  
가장 가까운 출입구까지의 경로를 A* 알고리즘으로 계산하는 Python FastAPI 서버입니다.

---

## 🚀 실행 방법

```bash
uvicorn server:app --reload
```

> 서버는 기본적으로 `http://127.0.0.1:8000`에서 실행됩니다.

---

## 🧪 테스트 방법

1. 테스트 데이터 다운로드:
   - [`test_wifi_request_4th_floor.json`](./test_wifi_request_4th_floor.json)
   - [`building_data_4floor_only_exit_on_1F.json`](./building_data_4floor_only_exit_on_1F.json)

2. 클라이언트 실행:

```bash
python test_client.py
```

응답 예시:
```json
{
  "estimated_location": {"x": ..., "y": ..., "z": ...},
  "floor": 4,
  "closest_node": "4F_N3",
  "escape_path": ["4F_N3", "4F_STAIR", ..., "1F_EXIT1"]
}
```

---

## 📂 파일 구조

```
project/
├── server.py
├── test_client.py
├── test_wifi_request_4th_floor.json
├── building_data_4floor_only_exit_on_1F.json
├── requirements.txt
└── README.md
```

---

## 🛠 의존성 설치

```bash
pip install -r requirements.txt
```

> 주요 라이브러리: `fastapi`, `uvicorn`, `scipy`, `requests`, `pydantic`

---

## 🗺 주요 기능

- WiFi AP RSSI 기반 3D 위치 예측 (x, y, z)
- 다수결 기반 층 추정 (z → floor)
- 건물 그래프 기반 A* 최단경로 탐색
- 여러 출입구 중 최단 거리 자동 선택

---

## 📬 문의 및 기여

이 프로젝트는 실내 재난 대응, 실시간 위치 추적 등 다양한 상황에 확장 가능합니다.  
기여 및 피드백은 언제든 환영합니다!
