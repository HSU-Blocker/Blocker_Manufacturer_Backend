from flask import Blueprint, request, jsonify
import os
import json
import re
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
api = Api(
    api_bp,
    doc="/docs",
    title="Manufacturer Backend API",
    description="Software update API",
)

# Manufacturer 관련 API를 위한 네임스페이스
manufacturer_ns = Namespace("Update", description="소프트웨어 업데이트 관련 API")
api.add_namespace(manufacturer_ns, path="/manufacturer")

# 파일 업로드 파서
upload_parser = reqparse.RequestParser()
upload_parser.add_argument(
    "file",
    location="files",
    type="file",
    required=True,
    help="업로드할 소프트웨어 파일",
)

# 파일 + 폼 필드 파서 정의
upload_parser = reqparse.RequestParser()
upload_parser.add_argument(
    "file",
    location="files",
    type="file",
    required=True,
    help="업로드할 소프트웨어 파일",
)
upload_parser.add_argument(
    "version", location="form", type=str, required=False, help="업데이트 버전"
)
upload_parser.add_argument(
    "description", location="form", type=str, required=False, help="업데이트 설명"
)
upload_parser.add_argument(
    "price", location="form", type=str, required=False, help="가격(ETH)"
)
upload_parser.add_argument(
    "policy",
    location="form",
    type=str,
    required=False,
    help='속성 정책 (예:  { "model": "VS500", "serial": "KMHEM42APXA75****", "date": "2015", "option": "EXCLUSIVE OR PRESTIGE" })',
)

# 업로드 응답 모델 정의
upload_response_model = manufacturer_ns.model(
    "UploadResponse",
    {
        "success": fields.Boolean(description="업로드 성공 여부"),
        "uid": fields.String(description="업데이트 ID (ex: filename_v1.0.0)"),
        "ipfs_hash": fields.String(description="IPFS에 업로드된 파일 해시"),
        "file_hash": fields.String(description="SHA3 해시값"),
        "tx_hash": fields.String(description="블록체인 트랜잭션 해시"),
        "version": fields.String(description="버전 정보"),
        "signature": fields.String(description="업데이트 데이터에 대한 ECDSA 서명"),
    },
)

# 업데이트 취소 요청 파서
cancel_parser = reqparse.RequestParser()
cancel_parser.add_argument(
    "uid", location="json", type=str, required=True, help="취소할 업데이트 UID"
)

# 업데이트 취소 응답 모델
cancel_response_model = manufacturer_ns.model(
    "CancelResponse",
    {
        "success": fields.Boolean(description="취소 성공 여부"),
        "tx_hash": fields.String(description="블록체인 트랜잭션 해시"),
        "error": fields.String(description="에러 메시지", required=False),
    },
)


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


# ✅ 유효한 소프트웨어 업데이트 목록 조회 API
@manufacturer_ns.route("/updates")
class SoftwareList(Resource):
    @manufacturer_ns.doc(
        description="유효한(취소되지 않은) 소프트웨어 업데이트 목록 조회 API"
    )
    def get(self):
        try:
            notifier = BlockchainNotifier()
            updates = notifier.get_updates(include_invalid=False)
            return {"updates": updates}
        except Exception as e:
            return {"error": str(e), "updates": []}, 500


# ✅ 전체 소프트웨어 업데이트 목록 조회 API
@manufacturer_ns.route("/updates/all")
class SoftwareListAll(Resource):
    @manufacturer_ns.doc(
        description="전체(취소 포함) 소프트웨어 업데이트 목록 조회 API. isValid 필드 포함"
    )
    def get(self):
        try:
            notifier = BlockchainNotifier()
            updates = notifier.get_updates(include_invalid=True)
            return {"updates": updates}
        except Exception as e:
            return {"error": str(e), "updates": []}, 500


# ✅ 업데이트 취소 API
@manufacturer_ns.route("/cancel")
class CancelUpdate(Resource):
    @manufacturer_ns.expect(cancel_parser)
    @manufacturer_ns.response(200, "업데이트 취소 결과", cancel_response_model)
    @manufacturer_ns.doc(description="업데이트 취소(비활성화) API. 제조사만 호출 가능.")
    def post(self):
        try:
            data = request.get_json(force=True)
            uid = data.get("uid")
            if not uid:
                return {"success": False, "error": "uid는 필수입니다."}, 400
            notifier = BlockchainNotifier()
            try:
                tx_hash = notifier.cancel_update(uid)
                tx_hash_str = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
                return {"success": True, "tx_hash": tx_hash_str}
            except Exception as e:
                # revert reason만 추출해서 반환
                error_str = str(e)
                match = re.search(r"reason': '([^']+)'", error_str)
                if match:
                    revert_reason = match.group(1)
                else:
                    revert_reason = error_str
                return {"success": False, "error": revert_reason}, 400
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
