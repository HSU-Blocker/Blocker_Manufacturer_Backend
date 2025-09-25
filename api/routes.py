from flask import Blueprint, request
import os
import json
import re
from flask_restx import Api, Resource, Namespace, fields, reqparse

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

# 페이지네이션 정보 모델
pagination_model = manufacturer_ns.model(
    "Pagination",
    {
        "current_page": fields.Integer(description="현재 페이지 번호"),
        "per_page": fields.Integer(description="페이지당 항목 수"),
        "total_count": fields.Integer(description="전체 항목 수"),
        "total_pages": fields.Integer(description="전체 페이지 수"),
        "has_next": fields.Boolean(description="다음 페이지 존재 여부"),
        "has_prev": fields.Boolean(description="이전 페이지 존재 여부"),
        "start_index": fields.Integer(description="현재 페이지 시작 인덱스"),
        "end_index": fields.Integer(description="현재 페이지 끝 인덱스"),
    },
)

# 업데이트 정보 모델
update_info_model = manufacturer_ns.model(
    "UpdateInfo",
    {
        "uid": fields.String(description="업데이트 고유 ID"),
        "ipfs_hash": fields.String(description="IPFS 해시"),
        "encrypted_key": fields.String(description="암호화된 키"),
        "hash_of_update": fields.String(description="업데이트 해시"),
        "description": fields.String(description="업데이트 설명"),
        "price": fields.Float(description="가격 (ETH)"),
        "version": fields.String(description="버전"),
        "isValid": fields.Boolean(description="유효성 여부"),
    },
)

# 페이지네이션 업데이트 목록 응답 모델
paginated_updates_model = manufacturer_ns.model(
    "PaginatedUpdates",
    {
        "updates": fields.List(fields.Nested(update_info_model), description="업데이트 목록"),
        "pagination": fields.Nested(pagination_model, description="페이지네이션 정보"),
    },
)

# 업데이트 목록 쿼리 파라미터 파서
updates_parser = reqparse.RequestParser()
updates_parser.add_argument(
    "page", type=int, required=False, default=None, help="페이지 번호 (1부터 시작, 생략시 전체 조회)"
)
updates_parser.add_argument(
    "limit", type=int, required=False, default=20, help="페이지당 항목 수 (기본 20, 최대 100)"
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


# ✅ 소프트웨어 업데이트 목록 조회 API (페이지네이션 지원)
@manufacturer_ns.route("/updates")
class SoftwareList(Resource):
    @manufacturer_ns.expect(updates_parser)
    @manufacturer_ns.response(200, "업데이트 목록 조회 성공", paginated_updates_model)
    @manufacturer_ns.doc(
        description="""
        소프트웨어 업데이트 목록 조회 API (유효한 업데이트만)
        
        쿼리 파라미터:
        - page: 페이지 번호 (1부터 시작, 생략시 전체 조회)
        - limit: 페이지당 항목 수 (기본 20, 최대 100)
        
        예시:
        - /updates (전체 조회, 기존 방식과 호환)
        - /updates?page=1&limit=20 (1페이지, 20개씩)
        - /updates?page=2&limit=10 (2페이지, 10개씩)
        """
    )
    def get(self):
        try:
            args = updates_parser.parse_args()
            page = args.get('page')
            limit = args.get('limit', 20)
            
            notifier = BlockchainNotifier()
            
            # 페이지 파라미터가 없으면 기존 방식으로 전체 조회 (하위 호환성)
            if page is None:
                updates = notifier.get_updates(include_invalid=False)
                return {"updates": updates}
            
            # 페이지네이션 조회
            result = notifier.get_updates_paginated(
                page=page, 
                limit=limit, 
                include_invalid=False
            )
            return result
            
        except Exception as e:
            return {"error": str(e), "updates": []}, 500


# ✅ 전체 소프트웨어 업데이트 목록 조회 API (페이지네이션 지원)
@manufacturer_ns.route("/updates/all")
class SoftwareListAll(Resource):
    @manufacturer_ns.expect(updates_parser)
    @manufacturer_ns.response(200, "전체 업데이트 목록 조회 성공", paginated_updates_model)
    @manufacturer_ns.doc(
        description="""
        전체 소프트웨어 업데이트 목록 조회 API (취소된 업데이트 포함)
        
        쿼리 파라미터:
        - page: 페이지 번호 (1부터 시작, 생략시 전체 조회)
        - limit: 페이지당 항목 수 (기본 20, 최대 100)
        
        각 업데이트에 isValid 필드 포함
        """
    )
    def get(self):
        try:
            args = updates_parser.parse_args()
            page = args.get('page')
            limit = args.get('limit', 20)
            
            notifier = BlockchainNotifier()
            
            # 페이지 파라미터가 없으면 기존 방식으로 전체 조회 (하위 호환성)
            if page is None:
                updates = notifier.get_updates(include_invalid=True)
                return {"updates": updates}
            
            # 페이지네이션 조회
            result = notifier.get_updates_paginated(
                page=page, 
                limit=limit, 
                include_invalid=True
            )
            return result
            
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
