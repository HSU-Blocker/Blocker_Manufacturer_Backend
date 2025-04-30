# 베이스 이미지로 Python 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스 코드 복사
COPY . .

# 포트 설정
EXPOSE 5000

# Flask 서버 실행
CMD ["python", "run.py"]