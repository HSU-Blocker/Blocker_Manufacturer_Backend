from flask import Flask
from flask_cors import CORS
from api.routes import api_bp
from flask_restx import Api

app = Flask(__name__)
CORS(app)

# Swagger UI 설정을 위한 config 추가
app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
app.config['RESTX_VALIDATE'] = True
app.config['RESTX_MASK_SWAGGER'] = False

app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
