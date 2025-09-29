from charm.toolbox.pairinggroup import PairingGroup, GT
from charm.schemes.abenc.abenc_bsw07 import CPabe_BSW07
from charm.core.engine.util import objectToBytes, bytesToObject
import os
import json
import logging
import base64

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class CPABETools:
    def __init__(self):
        """
        CP-ABE(BSW07) 스킴 초기화 클래스.
        - PairingGroup("SS512")를 사용하여 안전한 암호연산 환경 생성
        - CPabe_BSW07 스킴을 로딩하여 정책 기반 암호화/복호화 기능 사용 가능
        """
        self.group = PairingGroup("SS512")
        self.cpabe = CPabe_BSW07(self.group)
        self.charm_installed = True
        logger.info("Charm-crypto 라이브러리 로드 성공. CP-ABE 기능 활성화됨.")

    def setup(self, public_key_file, master_key_file):
        """
        시스템 전체에서 공통으로 사용할 공개키(pk), 마스터키(mk)를 생성.
        - pk는 공개되어도 괜찮음
        - mk는 비밀로 보관해야 하며, keygen에서만 사용됨
        - objectToBytes → base64 인코딩하여 JSON 파일로 저장
        """
        try:
            (pk, mk) = self.cpabe.setup()

            # 그룹 원소를 직렬화 후 base64 인코딩
            serialized_pk = {k: base64.b64encode(objectToBytes(v, self.group)).decode() for k, v in pk.items()}
            serialized_mk = {k: base64.b64encode(objectToBytes(v, self.group)).decode() for k, v in mk.items()}

            # JSON 저장
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
        """
        입력된 메시지를 접근 제어 정책(policy)에 따라 암호화.
        - message: GT 요소여야 함 (바이트일 경우 GT 요소로 변환)
        - policy: 문자열 표현 (예: "ATTR1 and (ATTR2 or ATTR3)")
        - 반환값: 암호문을 JSON(base64 직렬화) 형태로 반환
        """
        try:
            # 공개키 로드
            with open(public_key_file, "r") as f:
                serialized_pk = json.load(f)
            pk = {k: bytesToObject(base64.b64decode(v), self.group) for k, v in serialized_pk.items()}

            # message가 bytes라면 int → GT 요소로 변환
            if isinstance(message, bytes):
                message_value = int.from_bytes(message, "big")
                message = self.group.init(GT, message_value)

            # BSW07 암호화 실행
            encrypted_result = self.cpabe.encrypt(pk, message, policy)

            # 재귀적으로 직렬화 (그룹 원소는 base64 문자열로 변환)
            def serialize_element(obj):
                if hasattr(obj, "initPP"):  # 그룹 원소(G1/G2/GT)
                    return base64.b64encode(objectToBytes(obj, self.group)).decode()
                elif isinstance(obj, list):
                    return [serialize_element(e) for e in obj]
                elif isinstance(obj, dict):
                    return {k: serialize_element(v) for k, v in obj.items()}
                else:  # 문자열 등은 그대로
                    return obj

            return json.dumps(serialize_element(encrypted_result))
        except Exception as e:
            logger.error(f"CP-ABE 암호화 실패: {e}")
            raise

    def generate_device_secret_key(self, public_key_file, master_key_file, attributes, device_secret_key_file):
        """
        속성(attribute) 집합을 기반으로 디바이스 비밀키 생성.
        - pk, mk를 로드 후 keygen 실행
        - 결과는 JSON(base64) 파일로 저장
        - attributes: ["ATTR1", "ATTR2", ...]
        """
        try:
            # 공개키, 마스터키 로드
            with open(public_key_file, "r") as f:
                serialized_pk = json.load(f)
            with open(master_key_file, "r") as f:
                serialized_mk = json.load(f)

            pk = {k: bytesToObject(base64.b64decode(v), self.group) for k, v in serialized_pk.items()}
            mk = {k: bytesToObject(base64.b64decode(v), self.group) for k, v in serialized_mk.items()}

            # 디바이스 비밀키 생성
            device_secret_key = self.cpabe.keygen(pk, mk, attributes)

            # 직렬화
            def serialize_element(obj):
                if hasattr(obj, "initPP"):  # 그룹 원소
                    return base64.b64encode(objectToBytes(obj, self.group)).decode()
                elif isinstance(obj, list):
                    return [serialize_element(e) for e in obj]
                elif isinstance(obj, dict):
                    return {k: serialize_element(v) for k, v in obj.items()}
                else:  # 문자열 등
                    return obj

            serialized_key = serialize_element(device_secret_key)

            # 파일 저장
            os.makedirs(os.path.dirname(device_secret_key_file), exist_ok=True)
            with open(device_secret_key_file, "w") as f:
                json.dump(serialized_key, f)

            return device_secret_key
        except Exception as e:
            logger.error(f"개인 키 생성 실패: {e}")
            return None

    def load_public_key(self, public_key_file):
        """
        저장된 공개키(JSON base64)를 로드하여 복원.
        """
        with open(public_key_file, "r") as f:
            serialized_pk = json.load(f)
        pk = {k: bytesToObject(base64.b64decode(v), self.group) for k, v in serialized_pk.items()}
        return pk

    def load_device_secret_key(self, device_secret_key_file):
        """
        저장된 디바이스 비밀키(JSON base64)를 로드하여 복원.
        - 주의: 비밀키 내부에는 'S'라는 속성 리스트가 포함되어 있음
        → 이는 단순 문자열 리스트이므로 base64 decode 하면 오류 발생
        → 따라서 key_name == "S"일 때는 그대로 반환
        """
        with open(device_secret_key_file, "r") as f:
            serialized_key = json.load(f)

        def deserialize_element(obj, key_name=None):
            # 'S' 키는 속성 리스트 → 그대로 문자열 반환
            if key_name == "S":
                return obj

            if isinstance(obj, str):
                try:
                    return bytesToObject(base64.b64decode(obj), self.group)
                except Exception:
                    return obj  # 순수 문자열은 그대로 유지
            elif isinstance(obj, list):
                return [deserialize_element(e, key_name) for e in obj]
            elif isinstance(obj, dict):
                return {k: deserialize_element(v, k) for k, v in obj.items()}
            else:
                return obj

        return deserialize_element(serialized_key)

    def get_group(self):
        """
        PairingGroup 객체 반환 (외부에서 GT 요소 생성 등 활용 가능).
        """
        return self.group
