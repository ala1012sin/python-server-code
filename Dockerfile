# 1. Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 2. 작업 디렉토리 생성
WORKDIR /app

# 3. 프로젝트 내 모든 파일 복사
COPY . .

# 4. pip 최신화 및 의존성 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. FastAPI 앱 실행
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
