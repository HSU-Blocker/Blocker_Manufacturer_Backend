from flask import Flask
from flask_cors import CORS
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    
    # routes.py에서 Blueprint 임포트 (순서 중요!)
    from .routes import bp  # ✅ 수정된 부분
    app.register_blueprint(bp)
    
    return app