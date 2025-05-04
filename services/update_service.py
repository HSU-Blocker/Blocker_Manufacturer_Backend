import os
import json
import uuid
import base64
import logging
from flask import jsonify
from werkzeug.utils import secure_filename
from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier
from crypto.ecdsa.ecdsa import ECDSATools
from eth_account import Account
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

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
        try:
            price_float = float(price_eth)
            price = int(price_float * 10**18)
        except ValueError:
            price = 0
        uid = f"update_{uuid.uuid4().hex}"
        original_filename = secure_filename(file.filename)
        file_ext = (
            original_filename.rsplit(".", 1)[1].lower()
            if "." in original_filename
            else "bin"
        )
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
        logger.info(f"파일 경로 타입: {type(encrypted_file_path)}")
        
        # HA-3 해시 생성 hEbj
        file_hash = HashTools.sha3_hash_file(encrypted_file_path)
        
        # IPFS에 암호화된 바이너리 업로드
        try:
            ipfs_uploader = IPFSUploader()
            ipfs_hash = ipfs_uploader.upload_file(encrypted_file_path)
            logger.info(f"IPFS 업로드 완료: {ipfs_hash}")
        except ConnectionError as ce:
            logger.error(f"IPFS 연결 오류: {ce}")
            return jsonify({"error": f"IPFS 연결에 실패했습니다.: {e}"}), 500
        except Exception as e:
            logger.error(f"IPFS 업로드 중 예외 발생: {e}")
            return jsonify({"error": f"IPFS 업로드 실패: {e}"}), 500
            
        
        # CP-ABE 키 생성
        key_dir = os.path.join(os.path.dirname(__file__), "../crypto/keys")
        public_key_file = os.path.join(key_dir, "public_key.bin")
        master_key_file = os.path.join(key_dir, "master_key.bin")

        # policy_dict의 키를 기반으로 user_attributes 생성
        user_attributes = [v for k, v in policy_dict.items() if v]
        logger.info(f"추출된 user_attributes: {user_attributes}")
        
        cpabe.setup(public_key_file, master_key_file)
        serialized_device_secret_key = cpabe.generate_device_secret_key(
            public_key_file, master_key_file, user_attributes
        )
        logger.info(f"생성된 serialized_device_secret_key: {serialized_device_secret_key}")
        
        encrypted_key = cpabe.encrypt(kbj, attribute_policy, public_key_file)
        logger.info(f"CP-ABE로 대칭키 암호화 완료, encrypted_key: {encrypted_key}")

        update_uid = f"{original_filename.split('.')[0]}_v{version}" 
        logger.debug(f"업데이트 UID 생성: {update_uid}")    
        
        # ECDSA 서명(σ) 생성
        try:
            # PRIVATE_KEY 환경 변수에서 값 읽기
            eth_private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
            logger.info(f"eth_private_key 길이: {len(eth_private_key)}")  # 66

            # 개인키로 서명할 때 사용한 address
            signer_address = Account.from_key(eth_private_key).address
            logger.info(f"서명에 사용한 계정: {signer_address}")

            if not eth_private_key:
                raise ValueError("PRIVATE_KEY 값이 .env 파일에 정의되어 있지 않습니다.")
            
            # 확인용 제조사 공개키 출력 (블록체인 private key)
            logger.info(f"불러온 Ethereum Private Key: {eth_private_key[:10]}...(생략)")
            
            # 메시지에 ECDSA 서명 생성
            signature = ECDSATools.sign_message(
                update_uid, ipfs_hash, encrypted_key, file_hash, eth_private_key
            ) 
            logger.info(f"ECDSA 서명 생성 완료: {signature[:20]}...")
        except Exception as sign_err:
            logger.error(f"서명 생성 실패: {sign_err}")
            return jsonify({"error": f"서명 생성에 실패했습니다: {sign_err}"}), 500
        
        notifier = BlockchainNotifier()
        tx_hash = notifier.register_update(
            uid=update_uid,
            ipfs_hash=ipfs_hash,
            encrypted_key=encrypted_key,
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

    @staticmethod
    def build_attribute_policy(policy_dict):
        conditions = []
        if "model" in policy_dict and policy_dict["model"]:
            conditions.append(policy_dict["model"])
        if "serial" in policy_dict and policy_dict["serial"]:
            serial_value = policy_dict["serial"]
            conditions.append(f"({serial_value} or ATTR1)")
        return f"({' and '.join(conditions)})"
