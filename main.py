from flask import Flask
from flask_cors import CORS
from api.routes import api_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    # 디버그 모드 비활성화
    app.run(host="0.0.0.0", port=5002)
