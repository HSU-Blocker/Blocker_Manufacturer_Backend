# config.py
import os  # 상단에 os 모듈 추가

class Config:
    CORS_ORIGINS = [
        'http://localhost:3000',  
        'http://52.78.52.216:3000',  
        'http://172.30.1.54:3000'
    ]

    RATE_LIMIT = "100 per hour"
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET')  # 이제 오류 사라짐