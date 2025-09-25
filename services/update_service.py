import os
import uuid
import base64
import logging
import re
from flask import jsonify
from werkzeug.utils import secure_filename
from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier
from crypto.ecdsa.ecdsa import ECDSATools
from eth_account import Account  # [추가]

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UpdateService:
    @staticmethod
    def process_update_upload(
        file,
        version,
        description,
        price_eth,
        policy_dict,
        upload_folder,
        key_dir,
        cache_file=None,
    ):
        attribute_policy = UpdateService.build_attribute_policy(policy_dict)
        logger.info(f"CP-ABE attribute_policy 정책: {attribute_policy}")

        # 가격 처리
        try:
            price_float = float(price_eth)
            price = int(price_float * 10**18)
        except ValueError:
            price = 0

        # 파일 저장
        uid = f"update_{uuid.uuid4().hex}"
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "bin"
        temp_filename = f"{uid}.{file_ext}"
        file_path = os.path.join(upload_folder, temp_filename)
        os.makedirs(upload_folder, exist_ok=True)
        file.save(file_path)

        # CP-ABE 초기화 및 대칭키 kbj, aes_key 생성
        cpabe = CPABETools()
        cpabe_group = cpabe.get_group()
        kbj, aes_key = SymmetricCrypto.generate_key(cpabe_group)
        logger.info(f"대칭키 생성 완료 kbj: {kbj}, aes_key: {aes_key}")

        # 바이너리를 대칭키로 암호화 Es(bj,kbj)
        encrypted_file_path = SymmetricCrypto.encrypt_file(file_path, aes_key)
        logger.info(f"파일 암호화 완료: {encrypted_file_path}")

        # SHA-3 해시 생성 hEbj
        file_hash = HashTools.sha3_hash_file(encrypted_file_path)

        # IPFS에 암호화된 바이너리 업로드
        try:
            ipfs_uploader = IPFSUploader()
            upload_result = ipfs_uploader.upload_file(encrypted_file_path)
            if not upload_result:
                raise Exception("IPFS 업로드 결과가 없습니다.")
            ipfs_hash = upload_result["cid"]
            file_name = upload_result["file_name"]
            logger.info(f"IPFS 업로드 완료: CID={ipfs_hash}, 파일명={file_name}")
        except Exception as e:
            logger.error(f"IPFS 업로드 실패: {e}")
            return jsonify({"error": f"IPFS 업로드 실패: {e}"}), 500

        # CP-ABE 키 생성
        key_dir = os.path.join(os.path.dirname(__file__), "../crypto/keys")
        public_key_file = os.path.join(key_dir, "public_key.bin")
        master_key_file = os.path.join(key_dir, "master_key.bin")

        if not (os.path.exists(public_key_file) and os.path.exists(master_key_file)):
            cpabe.setup(public_key_file, master_key_file)

        # 속성 기반 키 생성
        user_attributes = UpdateService.extract_user_attributes(policy_dict)
        logger.info(f"추출된 user_attributes: {user_attributes}")
        cpabe.generate_device_secret_key(
            public_key_file, master_key_file, user_attributes, os.path.join(key_dir, "device_secret_key_file.bin")
        )

        # 대칭키 암호화
        encrypted_key = cpabe.encrypt(kbj, attribute_policy, public_key_file)
        encrypted_key_bytes = encrypted_key.encode() if encrypted_key else b""
        if not encrypted_key_bytes:
            raise Exception("CP-ABE 암호화 실패")

        update_uid = f"{original_filename.split('.')[0]}_v{version}"
        logger.debug(f"업데이트 UID 생성: {update_uid}")

        # ECDSA 서명 (Ethereum 기반)
        private_key_hex = os.environ.get("BLOCKCHAIN_PRIVATE_KEY")
        if not private_key_hex:
            private_key_hex, _ = ECDSATools.generate_key_pair()
            logger.warning("환경 변수에 키가 없어 새 Ethereum 계정 생성")

        # [추가] 트랜잭션도 반드시 같은 키로 보냄 (서명자 == msg.sender 보장)
        sender_address = Account.from_key(private_key_hex).address
        logger.info(f"[Signer/Sender] {sender_address}")

        # 서명 생성
        signature_message = (
            update_uid, ipfs_hash, encrypted_key_bytes,  # bytes로 일치
            file_hash, description, price, version
        )
        signature = ECDSATools.sign_message(signature_message, private_key_hex)

        # 블록체인 등록
        try:
            # [추가] Notifier에 같은 키/주소를 명시적으로 전달
            notifier = BlockchainNotifier(
                account_address=sender_address,
                private_key=private_key_hex
            )
            tx_hash = notifier.register_update(
                uid=update_uid,
                ipfs_hash=ipfs_hash,
                encrypted_key=encrypted_key_bytes,
                hash_of_update=file_hash,
                description=description,
                price=price,
                version=version,
                signature=signature,
            )
            tx_hash_str = tx_hash.hex() if isinstance(tx_hash, bytes) else tx_hash

            return {
                "success": True,
                "uid": update_uid,
                "ipfs_hash": ipfs_hash,
                "file_hash": file_hash,
                "tx_hash": tx_hash_str,
                "version": version,
                "signature": base64.b64encode(signature).decode(),
            }
        except Exception as e:
            # [추가] 리버트/가스/잔액 등 상세 사유를 그대로 전달
            logger.exception("블록체인 등록 실패")
            return jsonify({"error": f"Blockchain register_update failed: {str(e)}"}), 500

    @staticmethod
    def build_attribute_policy(policy_dict):
        # 필수 속성 검사
        required_keys = ["model", "serial"]
        for key in required_keys:
            if key not in policy_dict or not policy_dict[key].strip():
                raise ValueError(f"'{key}' 속성은 필수입니다.")

        def parse_expression(expr: str) -> str:
            expr = expr.strip().replace("AND", "and").replace("OR", "or")
            return re.sub(r"\s+", " ", expr)

        expressions = [f"({parse_expression(v)})" for v in policy_dict.values() if v.strip()]
        return " and ".join(expressions)

    @staticmethod
    def extract_user_attributes(policy_dict):
        """
        각 policy_dict의 값에서 AND/OR/괄호 등을 제거하고 속성 리스트 추출
        """
        attributes = []
        for value in policy_dict.values():
            if not isinstance(value, str) or not value.strip():
                continue
            expr = value.upper().replace("AND", " ").replace("OR", " ")
            expr = re.sub(r"[()]", " ", expr)
            tokens = [t.strip() for t in expr.split() if t.strip()]
            attributes.extend(tokens)
        return list(set(attributes))  # 중복 제거
