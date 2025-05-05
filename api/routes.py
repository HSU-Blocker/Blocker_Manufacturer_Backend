from flask import Blueprint, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
from flask_restx import Api, Resource, Namespace, fields, reqparse

from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier
from services.update_service import UpdateService

# URL prefix 추가
api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp, doc="/docs", title="Manufacturer Backend API", description="Software update API")

# Manufacturer 관련 API를 위한 네임스페이스
manufacturer_ns = Namespace("Update", description="소프트웨어 업데이트 관련 API")
api.add_namespace(manufacturer_ns, path="/manufacturer")

# 파일 업로드 파서
upload_parser = reqparse.RequestParser()
upload_parser.add_argument("file", location="files", type='file', required=True, help="업로드할 소프트웨어 파일")

# 파일 + 폼 필드 파서 정의
upload_parser = reqparse.RequestParser()
upload_parser.add_argument("file", location="files", type='file', required=True, help="업로드할 소프트웨어 파일")
upload_parser.add_argument("version", location="form", type=str, required=False, help="업데이트 버전")
upload_parser.add_argument("description", location="form", type=str, required=False, help="업데이트 설명")
upload_parser.add_argument("price", location="form", type=str, required=False, help="가격(ETH)")
upload_parser.add_argument("policy", location="form", type=str, required=False, help='속성 정책 (예: {   "model": "K4 AND K5",   "serial": "123456 OR ATTR1",   "option": "A OR B AND C" })')

# 업로드 응답 모델 정의
upload_response_model = manufacturer_ns.model("UploadResponse", {
    "update_id": fields.String(),
    "ipfs_hash": fields.String(),
    "version": fields.String(),
})



# ✅ 소프트웨어 업로드 API
@manufacturer_ns.route("/upload")
class SoftwareUpload(Resource):
    @manufacturer_ns.expect(upload_parser)  # ✅ metadata model 제거
    @manufacturer_ns.response(200, "업로드 성공", upload_response_model)
    @manufacturer_ns.doc(description="소프트웨어 업데이트 업로드 API")
    def post(self):
        try:
            # 파일이 없으면 에러 반환
            if "file" not in request.files:
                return {"error": "파일이 제공되지 않았습니다."}, 400

            file = request.files["file"]
            version = request.form.get("version", "")
            description = request.form.get("description", "")
            price_eth = request.form.get("price", "0")
            policy_dict = json.loads(request.form.get("policy", "{}"))
            
            # 업로드 경로는 필요시 직접 지정, 디바이스 비밀키 경로/속성 예시는 제거
            upload_folder = os.path.join(os.path.dirname(__file__), "../uploads")
            key_dir = os.path.join(os.path.dirname(__file__), "../crypto/keys")
            cache_file = os.path.join(os.path.dirname(__file__), "../update_cache.json")

            result = UpdateService.process_update_upload(
                file,
                version,
                description,
                price_eth,
                policy_dict,
                upload_folder,
                key_dir,
                cache_file,
            )
            return result
        except Exception as e:
            return {"error": str(e)}, 500

# ✅ 소프트웨어 업데이트 목록 조회 API
@manufacturer_ns.route("/updates")
class SoftwareList(Resource):
    @manufacturer_ns.doc(description="업로드된 소프트웨어 업데이트 목록 조회 API")
    def get(self):
        try:
            notifier = BlockchainNotifier()
            updates = notifier.get_all_updates()
            return {"updates": updates}
        except Exception as e:
            return {"error": str(e), "updates": []}, 500