# 🚨 실내 위치 측위 기반 재난 대피 경로 안내 서비스 (캡스톤 디자인)

> 수집된 Wi-Fi AP 데이터를 기반으로 사용자의 현재 실내 위치를 파악하고, 재난 발생 시 최적의 대피 경로를 안내하는 백엔드 API 서버입니다.
<br>

<p align="center">
  <img src="[ 여기에 앱 실행 화면 GIF 또는 시스템 아키텍처 이미지 ]" width="700"/>
</p>
<br>

## 📜 프로젝트 개요
본 프로젝트는 20XX년도 캡스톤 디자인의 일환으로 진행되었습니다. GPS가 작동하지 않는 복잡한 실내 환경(쇼핑몰, 지하철역 등)에서 재난이 발생했을 때, 사용자의 위치를 빠르고 정확하게 파악하여 '골든 타임' 내에 안전하게 대피할 수 있도록 돕는 것을 목표로 했습니다.

## ✨ 주요 기능
* **실내 위치 측위 (측위 서버):**
    * 클라이언트(앱)로부터 실시간 Wi-Fi AP 신호 세기(RSSI) 데이터를 수신합니다.
    * 기 저장된 AP 위치 정보(BSSID, 좌표)와 수신된 데이터를 비교 분석합니다.
    * **삼각측량(Trilateration) 알고리즘**을 Python으로 구현하여 사용자의 현재 실내 위치 좌표를 계산하고 반환합니다.
* **최단 대피 경로 안내:**
    * 계산된 사용자 위치를 기반으로, 미리 설정된 비상구까지의 최단 대피 경로를 탐색합니다. (예: 다익스트라 알고리즘 활용)
    * 클라이언트에 경로 좌표 데이터를 JSON 형태로 제공합니다.
* **데이터 관리:**
    * 실내 지도 및 Wi-Fi AP의 위치 정보(BSSID, MAC 주소, 설치 좌표)를 DB에 저장하고 관리합니다.

## 🛠️ 사용 기술 (Tech Stack)
<p>
  <strong>Backend</strong><br>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
</p>
<p>
  <strong>Database</strong><br>
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
</p>
<p>
  <strong>(기타 - 만약 사용했다면)</strong><br>
  <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white">
</p>


## 🚀 배운 점 및 트러블슈팅
### 1. Wi-Fi 신호 불안정성으로 인한 위치 오차
* **문제:** 벽, 장애물, 신호 간섭 등으로 인해 Wi-Fi 신호 세기(RSSI) 값이 불안정하여 삼각측량 계산 시 위치 오차가 크게 발생했습니다.
* **해결:**
    1.  (예시) 단순 삼각측량 대신, `칼만 필터(Kalman Filter)`를 적용하여 노이즈를 보정하고 위치 값을 평활화했습니다.
    2.  (예시) 또는, 가장 신호가 강한 AP 3개뿐만 아니라 5~6개의 AP 정보를 `가중 평균(Weighted Average)`하여 오차 범위를 줄였습니다.

### 2. (만약 FastAPI를 썼다면) 실시간 데이터 처리
* **문제:** 다수의 클라이언트가 동시에 위치 정보를 요청할 때, FastAPI의 비동기 처리를 효과적으로 활용해야 했습니다.
* **해결:** 무거운 계산(삼각측량) 로직을 `async def` 함수 내에서 별도의 스레드 풀(`run_in_threadpool`)에서 실행하도록 분리하여, 다른 API 요청 처리가 블로킹(차단)되지 않도록 성능을 개선했습니다.
