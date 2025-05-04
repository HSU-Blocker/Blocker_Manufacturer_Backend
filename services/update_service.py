import os
import json
import uuid
import base64
from werkzeug.utils import secure_filename
from crypto.symmetric.symmetric import SymmetricCrypto
from crypto.hash.hash import HashTools
from crypto.cpabe.cpabe import CPABETools
from ipfs.upload import IPFSUploader
from blockchain.contract import BlockchainNotifier
from crypto.ecdsa.ecdsa import ECDSATools


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
        cpabe = CPABETools()
        cpabe_group = cpabe.get_group()
        kbj, aes_key = SymmetricCrypto.generate_key(cpabe_group)
        encrypted_file_path = SymmetricCrypto.encrypt_file(file_path, aes_key)
        file_hash = HashTools.sha3_hash_file(encrypted_file_path)
        ipfs_uploader = IPFSUploader()
        ipfs_hash = ipfs_uploader.upload_file(encrypted_file_path)
        if not ipfs_hash:
            raise Exception("IPFS 업로드 실패: ipfs_hash가 None입니다.")
        key_dir = os.path.join(os.path.dirname(__file__), "../crypto/keys")
        public_key_file = os.path.join(key_dir, "public_key.bin")
        master_key_file = os.path.join(key_dir, "master_key.bin")
        cpabe.setup(public_key_file, master_key_file)
        encrypted_key = cpabe.encrypt(kbj, attribute_policy, public_key_file)
        if not encrypted_key:
            raise Exception("CP-ABE 암호화 실패: encrypted_key가 None입니다.")
        update_uid = f"{original_filename.split('.')[0]}_v{version}"
        ecdsa_private_key_path = os.path.join(key_dir, "ecdsa_private_key.pem")
        ecdsa_public_key_path = os.path.join(key_dir, "ecdsa_public_key.pem")
        
        # 키가 있으면 로드하고, 없으면 생성 (매번 새로 생성하지 않음)
        if os.path.exists(ecdsa_private_key_path) and os.path.exists(ecdsa_public_key_path):
            ecdsa_private_key = ECDSATools.load_private_key(ecdsa_private_key_path)
            ecdsa_public_key = ECDSATools.load_public_key(ecdsa_public_key_path)
            print("기존 ECDSA 키 로드 완료")
        else:
            ecdsa_private_key, ecdsa_public_key = ECDSATools.generate_key_pair(
                ecdsa_private_key_path, ecdsa_public_key_path
            )
            print("새 ECDSA 키 생성 완료")
        
        signature_message = (
            update_uid,
            ipfs_hash,
            encrypted_key,
            file_hash,
            description,
            price,
            version,
        )
        signature = ECDSATools.sign_message(signature_message, ecdsa_private_key_path)
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
