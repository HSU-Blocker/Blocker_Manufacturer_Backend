from charm.toolbox.pairinggroup import PairingGroup, GT
from charm.core.engine.util import objectToBytes, bytesToObject
from charm.schemes.abenc.abenc_bsw07 import CPabe_BSW07
import os
import json
import logging
import pickle
from base64 import b64encode, b64decode
from hashlib import sha256
import base64

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class CPABETools:
    def __init__(self):
        self.group = PairingGroup("SS512")
        self.cpabe = CPabe_BSW07(self.group)
        self.charm_installed = True
        logger.info("Charm-crypto 라이브러리 로드 성공. CP-ABE 기능 활성화됨.")

    def setup(self, public_key_file, master_key_file):
        try:
            (pk, mk) = self.cpabe.setup()
            serialized_pk = {k: self.group.serialize(v).decode("latin1") for k, v in pk.items()}
            serialized_mk = {k: self.group.serialize(v).decode("latin1") for k, v in mk.items()}

            with open(public_key_file, "w") as f:
                json.dump(serialized_pk, f)
            with open(master_key_file, "w") as f:
                json.dump(serialized_mk, f)

            logger.info(f"CP-ABE 키 생성 및 저장 완료")
            return True
                
        except Exception as e:
            logger.error(f"CP-ABE 시스템 초기화 실패: {e}")
            return False

    def encrypt(self, message, policy, public_key_file):
        try:
            with open(public_key_file, "r") as f:
                serialized_pk = json.load(f)
            pk = {k: self.group.deserialize(v.encode("latin1")) for k, v in serialized_pk.items()}

            if isinstance(message, bytes):
                message_value = int.from_bytes(message, "big")
                message = self.group.init(GT, message_value)

            encrypted_result = self.cpabe.encrypt(pk, message, policy)

            def serialize_element(obj):
                if hasattr(obj, "initPP"):
                    return b64encode(self.group.serialize(obj)).decode("utf-8")
                elif isinstance(obj, bytes):
                    return b64encode(obj).decode("utf-8")
                elif isinstance(obj, list):
                    return [serialize_element(e) for e in obj]
                elif isinstance(obj, dict):
                    return {k: serialize_element(v) for k, v in obj.items()}
                else:
                    return obj

            encrypted_key_json = json.dumps(serialize_element(encrypted_result))
            return encrypted_key_json
        except Exception as e:
            logger.error(f"CP-ABE 암호화 실패: {e}")
            raise

    def generate_device_secret_key(self, public_key_file, master_key_file, attributes, device_secret_key_file):
        try:
            with open(public_key_file, "r") as f:
                serialized_pk = json.load(f)
            with open(master_key_file, "r") as f:
                serialized_mk = json.load(f)

            pk = {k: self.group.deserialize(v.encode("latin1")) for k, v in serialized_pk.items()}
            mk = {k: self.group.deserialize(v.encode("latin1")) for k, v in serialized_mk.items()}

            device_secret_key = self.cpabe.keygen(pk, mk, attributes)

            def serialize_element(obj):
                if hasattr(obj, "initPP"):
                    return self.group.serialize(obj)
                elif isinstance(obj, list):
                    return [serialize_element(e) for e in obj]
                elif isinstance(obj, dict):
                    return {k: serialize_element(v) for k, v in obj.items()}
                else:
                    return obj

            serialized_key = serialize_element(device_secret_key)

            os.makedirs(os.path.dirname(device_secret_key_file), exist_ok=True)
            with open(device_secret_key_file, "wb") as f:
                pickle.dump(serialized_key, f)

            return device_secret_key
        except Exception as e:
            logger.error(f"개인 키 생성 실패: {e}")
            return None

    def load_public_key(self, public_key_file):
        with open(public_key_file, "r") as f:
            serialized_pk = json.load(f)
        pk = {k: self.group.deserialize(v.encode("latin1")) for k, v in serialized_pk.items()}
        return pk

    def load_device_secret_key(self, device_secret_key_file):
        with open(device_secret_key_file, "rb") as f:
            serialized_key = pickle.load(f)

        def deserialize_element(obj):
            if isinstance(obj, bytes):
                return self.group.deserialize(obj)
            elif isinstance(obj, list):
                return [deserialize_element(e) for e in obj]
            elif isinstance(obj, dict):
                return {k: deserialize_element(v) for k, v in obj.items()}
            else:
                return obj

        return deserialize_element(serialized_key)

    def get_group(self):
        return self.group