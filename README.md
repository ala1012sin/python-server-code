# 🚨 실내 위치 측위 기반 재난 대피 경로 안내 (캡스톤 디자인)

> 수집된 Wi-Fi AP 데이터를 기반으로 사용자의 현재 실내 위치를 파악하고, 재난 발생 시 최적의 대피 경로를 안내하는 백엔드 API 서버입니다.
<br>

### 1. 앱 상태별 UI (SAFE / DANGER / CHECKING)
<p align="center">
  <img src="[ 여기에 'SAFE/DANGER' 3분할 이미지를 드래그 앤 드롭 ]" width="700"/>
</p>

### 2. 핵심 기능: 실내 대피 경로 안내
<p align="center">
  <img src="[ 여기에 '대피 경로 지도' 이미지를 드래그 앤 드롭 ]" width="350"/>
</p>
<br>

## 📜 프로젝트 개요
본 프로젝트는 GPS가 작동하지 않는 실내 환경에서, **Python과 FastAPI**를 기반으로 한 백엔드 서버를 구축하여 사용자의 위치를 측위하고 최적의 대피 경로를 제공하는 캡스톤 디자인 프로젝트입니다.

---

## 🧑‍💻 **My Role: Backend API Server**
저는 이 프로젝트에서 **백엔드 API 서버** 개발을 **전담**했습니다.

* **FastAPI**를 이용한 REST API 설계 및 `POST /locate` 엔드포인트 구현
* 클라이언트(Android)의 Wi-Fi AP 스캔 데이터를 받아 처리
* **RSSI 가중 평균(Weighted Average)** 알고리즘을 Python으로 구현하여 사용자 (x, y, z) 좌표 추정
* 추정된 위치에서 비상구까지의 최단 경로를 탐색하는 **A\* (A-star) 알고리즘** 적용
* 계산된 위치 좌표 및 대피 경로를 클라이언트에 JSON 형태로 반환
* **GCP(Google Cloud Platform)**를 이용한 서버 배포 및 운영

---

## 🛠️ 전체 프로젝트 기술 스택
<p>
  <strong>Backend (My Part)</strong><br>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white">
</p>
<p>
  <strong>Database (Team Part)</strong><br>
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
</p>
<p>
  <strong>Client (Team Part)</strong><br>
  <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white">
</p>

## ✨ 프로젝트 주요 기능 (전체)
* **실시간 상태 확인:** (SAFE, DANGER, CHECKING) 서버로부터 재난 상태 및 위치 정보를 받아와 UI에 반영합니다.
* **실내 위치 측위:** 클라이언트가 측정한 Wi-Fi AP 신호 세기(RSSI)를 API 서버로 전송합니다.
* **알고리즘 연산:** 서버는 **RSSI 가중 평균** 알고리즘을 통해 사용자의 실내 위치 좌표를 계산합니다.
* **경로 안내:** 계산된 위치를 그래프의 가장 가까운 노드에 매핑 후, **A\* 알고리즘**으로 비상구까지의 최단 대피 경로를 탐색하여 반환합니다.

## 🚀 배운 점 및 트러블슈팅 (My Part)
### 1. 안드로이드 스캔 주기로 인한 실시간성 저하
* **문제:** 안드로이드 OS 자체의 Wi-Fi 스캔 주기가 30초에 2-3회로 제한되어, 2층에서 1층으로 이동해도 앱의 지도 상에서 위치가 즉시 갱신되지 않는 치명적인 문제 발생.
* **해결:** 클라이언트 팀과 협의하여 **안드로이드 개발자 모드**를 활성화하고, 스캔 주기를 7-8초로 단축하도록 설정을 변경함. 이를 통해 서버가 더 자주 데이터를 수신하여, 사용자의 움직임을 거의 실시간으로 추적하고 경로를 재탐색할 수 있도록 **'실시간성'을 확보**함.

### 2. 해외 리전 서버로 인한 높은 Latency
* **문제:** 초기 테스트 배포에 사용한 Railway의 싱가포르 리전 서버와 국내 사용자(클라이언트) 간의 물리적 거리로 인해 네트워크 지연(high latency)이 발생.
* **해결:** 서버를 **Google Cloud Platform(GCP)**의 서울 리전(`asia-northeast3`)으로 이전 배포하여, 국내 클라이언트와의 API 통신 속도를 크게 개선하고 안정적인 서비스를 제공함.

## 👥 팀원 기여 (Contributors)
* **Backend (ME)**: **[ala1012sin](https://github.com/ala1012sin)**
* **Client (Android)**: **[Dohyeongx3](https://github.com/Dohyeongx3/Capstone_Frontend)**
* **Database / Login**: **[LeeYoungw](https://github.com/LeeYoungw/CapstoneLogin)**
