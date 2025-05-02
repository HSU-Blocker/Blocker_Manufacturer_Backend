from flask import Blueprint, request, jsonify
import os
import json
import uuid
import base64
from werkzeug.utils import secure_filename
import logging

# 필요한 모듈 import (경로는 실제 환경에 맞게 조정)
from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier  # contract.py에 맞게 이름 조정 필요

# from utils.logger import get_logger
from services.update_service import UpdateService

api_bp = Blueprint("api", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../backend/uploads")
DEVICE_SECRET_KEY_FOLDER = os.path.join(
    os.path.dirname(__file__), "../iot_device/client/keys"
)
USER_ATTRIBUTES = ["ABC123", "SN12345"]


# 유틸리티 함수 (간단히 유지)
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "bin",
        "hex",
        "zip",
        "tar",
        "gz",
    }


def build_attribute_policy(policy_dict):
    conditions = []
    if "model" in policy_dict and policy_dict["model"]:
        conditions.append(policy_dict["model"])
    if "serial" in policy_dict and policy_dict["serial"]:
        serial_value = policy_dict["serial"]
        conditions.append(f"({serial_value} or ATTR1)")
    return f"({' and '.join(conditions)})"


@api_bp.route("/api/manufacturer/upload", methods=["POST"])
def upload_software_update():
    try:
        if "file" not in request.files:
            return jsonify({"error": "파일이 제공되지 않았습니다."}), 400
        file = request.files["file"]
        version = request.form.get("version", "")
        description = request.form.get("description", "")
        price_eth = request.form.get("price", "0")
        policy_dict = json.loads(request.form.get("policy", "{}"))
        # 경로/상수 정의
        upload_folder = os.path.join(os.path.dirname(__file__), "../uploads")
        device_secret_key_folder = os.path.join(
            os.path.dirname(__file__), "../iot_device/client/keys"
        )
        user_attributes = ["ABC123", "SN12345"]
        key_dir = os.path.join(os.path.dirname(__file__), "../keys")
        cache_file = os.path.join(os.path.dirname(__file__), "../update_cache.json")
        result = UpdateService.process_update_upload(
            file,
            version,
            description,
            price_eth,
            policy_dict,
            upload_folder,
            device_secret_key_folder,
            user_attributes,
            key_dir,
            cache_file,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/manufacturer/authorize", methods=["POST"])
def authorize_owner():
    try:
        data = request.json
        if not all(["uid" in data, "owner_address" in data]):
            return jsonify({"error": "필수 필드가 누락되었습니다."}), 400
        uid = data["uid"]
        owner_address = data["owner_address"]
        notifier = BlockchainNotifier()
        tx_hash = notifier.authorize_owner(uid, owner_address)
        return jsonify(
            {
                "success": True,
                "tx_hash": tx_hash.hex() if hasattr(tx_hash, "hex") else tx_hash,
                "uid": uid,
                "owner_address": owner_address,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/manufacturer/updates", methods=["GET"])
def list_updates():
    try:
        # 캐시 파일 사용 제거, 블록체인에서 직접 조회
        notifier = BlockchainNotifier()
        updates = notifier.get_all_updates()  # contract.py에 get_all_updates 함수가 있다고 가정
        return jsonify({"updates": updates})
    except Exception as e:
        return jsonify({"error": str(e), "updates": []}), 500
