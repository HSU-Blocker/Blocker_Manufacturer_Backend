from flask import Blueprint, request, jsonify
import os
import json
import uuid
import base64
from werkzeug.utils import secure_filename
import logging

from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier
from services.update_service import UpdateService

api_bp = Blueprint("api", __name__)

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
            None,  # device_secret_key_folder는 더이상 사용하지 않음
            None,  # user_attributes도 사용하지 않음
            key_dir,
            cache_file,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/manufacturer/updates", methods=["GET"])
def list_updates():
    try:
        notifier = BlockchainNotifier()
        updates = (
            notifier.get_all_updates()
        ) 
        return jsonify({"updates": updates})
    except Exception as e:
        return jsonify({"error": str(e), "updates": []}), 500
