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
    "success": fields.Boolean(description="업로드 성공 여부"),
    "uid": fields.String(description="업데이트 ID (ex: filename_v1.0.0)"),
    "ipfs_hash": fields.String(description="IPFS에 업로드된 파일 해시"),
    "file_hash": fields.String(description="SHA3 해시값"),
    "tx_hash": fields.String(description="블록체인 트랜잭션 해시"),
    "version": fields.String(description="버전 정보"),
    "signature": fields.String(description="업데이트 데이터에 대한 ECDSA 서명"),
    "kbj": fields.String(description="원본 대칭 키, CP-ABE로 암호화되어 속성 기반 접근 제어에 사용"),
    "aes_key": fields.String(description="파일 암호화&복호화에 사용되는 AES 대칭키. kbj를 바이트로 직렬화한 후, SHA-256 해시를 통해 생성한 32바이트 AES-256 키"),
    "encrypted_key": fields.String(description="CP-ABE 알고리즘에 의해 정책 기반으로 암호화된 kbj. 이 암호문을 통해 정책에 부합하는 사용자만 kbj를 복호화 가능"),
    "device_secret_key": fields.String(description="사용자의 속성에 기반해 생성된 개인 키 & CP-ABE로 암호화된 kbj를 복호화 하는 키. 해당 속성들이 암호화 시 정의된 접근 정책을 만족할 경우에만 복호화가 가능"),
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