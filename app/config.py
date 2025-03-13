# config.py
import os  # 상단에 os 모듈 추가

class Config:
    CORS_ORIGINS = [
        'http://localhost:3000',
        'https://your-production-domain.com'
    ]
    RATE_LIMIT = "100 per hour"
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET')  # 이제 오류 사라짐