import base64
import os
import json
import hashlib
from ecdsa import SigningKey, VerifyingKey, NIST256p, BadSignatureError
from charm.toolbox.pairinggroup import PairingGroup
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from ecdsa.util import number_to_string, sigdecode_string, sigencode_string

# 전역적으로 PairingGroup 객체 생성
GLOBAL_GROUP = PairingGroup('SS512')

class ECDSATools:

    @staticmethod
    def generate_key_pair(private_key_path, public_key_path):
        """제조사 개인 키(SKm)와 공개 키(PKm) 생성 및 저장"""
        private_key = SigningKey.generate(curve=NIST256p)
        public_key = private_key.get_verifying_key()

        # 키 파일 저장
        ECDSATools.save_key(private_key, private_key_path)
        ECDSATools.save_key(public_key, public_key_path)

        return private_key, public_key

    @staticmethod
    def load_private_key(private_key_path):
        """제조사 개인 키(SKm) 로드 (PEM 형식)"""
        with open(private_key_path, "rb") as f:
            return SigningKey.from_pem(f.read())

    @staticmethod
    def load_public_key(public_key_path):
        """제조사 공개 키(PKm) 로드 (PEM 형식)"""
        with open(public_key_path, "rb") as f:
            return VerifyingKey.from_pem(f.read())

    @staticmethod
    def save_key(key, key_path):
        """ 키를 PEM 형식으로 저장 """
        with open(key_path, "wb") as f:
            if isinstance(key, SigningKey):
                f.write(key.to_pem())  # 개인 키 저장
            elif isinstance(key, VerifyingKey):
                f.write(key.to_pem())  # 공개 키 저장
            else:
                raise ValueError("Invalid key type. Must be SigningKey or VerifyingKey.")

    @staticmethod
    def serialize_message(message):
        """메시지 직렬화: JSON 변환 가능하도록 변환"""
        def encode_custom(obj):
            if isinstance(obj, bytes):
                return {"__bytes__": base64.b64encode(obj).decode()}
            elif isinstance(obj, type(GLOBAL_GROUP.random())):  # PairingGroup 요소 변환
                return {"__element__": base64.b64encode(GLOBAL_GROUP.serialize(obj)).decode()}
            elif isinstance(obj, set):  # set을 list로 변환
                return list(obj)
            return obj

        return json.dumps(message, sort_keys=True, default=encode_custom).encode()

    @staticmethod
    def deserialize_message(message_json):
        """메시지 역직렬화: Base64 → bytes 및 PairingGroup 요소 변환"""
        def decode_custom(d):
            if "__bytes__" in d:
                return base64.b64decode(d["__bytes__"])
            elif "__element__" in d:
                return GLOBAL_GROUP.deserialize(base64.b64decode(d["__element__"]))
            return d

        return json.loads(message_json, object_hook=decode_custom)

    # @staticmethod
    # def sign_message(message, private_key_path):
    #     """메시지를 제조사 개인 키(SKm)로 서명하여 65바이트 서명 값 반환 (R + S + V)"""
    #     signing_key = ECDSATools.load_private_key(private_key_path)
    #     message_json = ECDSATools.serialize_message(message)

    #     # 64바이트 서명 생성 (R + S)
    #     signature_raw = signing_key.sign(message_json)

    #     # 서명 길이 확인 (64바이트)
    #     if len(signature_raw) != 64:
    #         raise ValueError(f"서명 값이 잘못되었습니다. 예상: 64바이트, 실제: {len(signature_raw)}바이트")

    #     # Ethereum에서 요구하는 65바이트 서명: r, s, v 추가
    #     v = 27  # 복구 ID 값 (기본값 27 사용, 필요시 28로 설정 가능)
    #     signature = signature_raw + bytes([v])

    #     return signature

    # @staticmethod
    # def sign_message(message, private_key_path):
    #     """Ethereum 표준 형식(R 32B + S 32B + V 1B)으로 서명"""
    #     # ✅ SigningKey 로드 (curve 인자 제거)
    #     with open(private_key_path, "rb") as key_file:
    #         signing_key = SigningKey.from_pem(key_file.read())

    #     # ✅ Ethereum 메시지 프리픽스 적용
    #     eth_prefix = f"\x19Ethereum Signed Message:\n{len(message)}".encode() + message.encode()
    #     message_hash = hashlib.sha3_256(eth_prefix).digest()

    #     # ✅ 서명 생성 (R, S를 직접 추출)
    #     signature = signing_key.sign_digest_deterministic(message_hash, sigencode=sigencode_string)
    #     r, s = signature[:32], signature[32:64]  # r, s 값을 분리

    #     # ✅ RFC 6979: S 값이 오더의 절반을 넘으면 조정
    #     curve_order = signing_key.curve.order
    #     s_int = int.from_bytes(s, byteorder="big")
    #     if s_int > curve_order // 2:
    #         s_int = curve_order - s_int
    #         s = s_int.to_bytes(32, byteorder="big")

    #     # ✅ Ethereum에서는 V 값 추가 필요 (27 또는 28)
    #     v = 27 + (r[31] % 2)  # R의 마지막 바이트의 홀짝성으로 V 결정
    #     v_bytes = bytes([v])

    #     # ✅ 최종 서명 (65 바이트: R + S + V)
    #     signature_fixed = r + s + v_bytes

    #     if len(signature_fixed) != 65:
    #         raise ValueError(f"서명 길이가 올바르지 않습니다: {len(signature_fixed)}바이트 (예상: 65바이트)")

    #     return signature_fixed  # Solidity에서 바로 사용 가능

    @staticmethod
    def sign_message(message, private_key_path):
        """Ethereum 표준 형식(R 32B + S 32B + V 1B)으로 서명"""
        with open(private_key_path, "rb") as key_file:
            signing_key = SigningKey.from_pem(key_file.read())

        # Ethereum 메시지 프리픽스 적용
        eth_prefix = f"\x19Ethereum Signed Message:\n{len(message)}".encode() + message.encode()
        message_hash = hashlib.sha3_256(eth_prefix).digest()

        # 서명 생성 (sigencode_string 사용, order 전달)
        signature = signing_key.sign_digest_deterministic(
            message_hash, 
            sigencode=lambda r, s, order: sigencode_string(r, s, order=signing_key.curve.order)
        )
        r, s = signature[:32], signature[32:64]

        # RFC 6979: S 값이 오더의 절반을 넘으면 조정
        curve_order = signing_key.curve.order
        s_int = int.from_bytes(s, byteorder="big")
        if s_int > curve_order // 2:
            s_int = curve_order - s_int
            s = s_int.to_bytes(32, byteorder="big")

        # Ethereum에서는 V 값 추가 필요 (27 또는 28)
        v = 27 + (r[31] % 2)  # R의 마지막 바이트의 홀짝성으로 V 결정
        v_bytes = bytes([v])

        # 최종 서명 (65 바이트: R + S + V)
        signature_fixed = r + s + v_bytes

        if len(signature_fixed) != 65:
            raise ValueError(f"서명 길이가 올바르지 않습니다: {len(signature_fixed)}바이트 (예상: 65바이트)")

        return signature_fixed  # Solidity에서 바로 사용 가능

    @staticmethod
    def verify_signature(message, signature, public_key):
        """Ethereum 표준 형식(R 32B + S 32B + V 1B) 서명 검증"""
        # public_key가 VerifyingKey 객체가 아니라면 파일에서 로드
        if isinstance(public_key, str):
            public_key = ECDSATools.load_public_key(public_key)

        # Ethereum 메시지 프리픽스 적용
        eth_prefix = f"\x19Ethereum Signed Message:\n{len(message)}".encode() + message.encode()
        message_hash = hashlib.sha3_256(eth_prefix).digest()

        # 서명을 65바이트(R, S, V)로 분할
        if len(signature) != 65:
            raise ValueError(f"서명 길이가 올바르지 않습니다: {len(signature)}바이트 (예상: 65바이트)")

        r = int.from_bytes(signature[:32], byteorder="big")
        s = int.from_bytes(signature[32:64], byteorder="big")
        v = signature[64]

        # Ethereum에서 사용하는 서명 검증을 위한 V 값 확인
        if v not in [27, 28]:
            raise ValueError(f"유효하지 않은 V 값입니다. v는 27 또는 28이어야 합니다. 실제 값: {v}")

        # 서명 검증 수행
        try:
            return public_key.verify_digest(
                sigencode_string(r, s, public_key.curve.order),
                message_hash
            )
        except BadSignatureError:
            return False

        # message_json = ECDSATools.serialize_message(message)
        
        # # Base64 디코딩 제거 (이미 바이너리 형태인 경우)
        # signature_bytes = signature if isinstance(signature, bytes) else base64.b64decode(signature)
        
        # # 서명이 65바이트여야 하므로, r, s, v 값으로 분리
        # if len(signature_bytes) != 65:
        #     raise ValueError(f"서명 값이 잘못되었습니다. 예상: 65바이트, 실제: {len(signature_bytes)}바이트")

        # r = signature_bytes[:32]  # r은 서명의 첫 32바이트
        # s = signature_bytes[32:64]  # s는 서명의 32~64바이트
        # v = signature_bytes[64]  # v는 서명의 마지막 1바이트

        # # Ethereum에서 사용하는 서명 검증을 위한 recover_id 설정
        # # Ethereum에서는 v 값이 27 또는 28이어야 합니다.
        # if v not in [27, 28]:
        #     raise ValueError(f"유효하지 않은 v 값입니다. v는 27 또는 28이어야 합니다. 실제 값: {v}")

        # # r, s, v로 서명 검증
        # signature_for_verification = r + s
        # try:
        #     return verifying_key.verify(signature_for_verification, message_json)
        # except Exception:
        #     return False

    # @staticmethod
    # def verify_signature(message, signature, verifying_key):
    #     """서명을 제조사 공개 키(PKm)로 검증"""
    #     if isinstance(verifying_key, str):  # 경로인 경우 로드
    #         verifying_key = ECDSATools.load_public_key(verifying_key)

    #     message_json = ECDSATools.serialize_message(message)
        
    #     # Base64 디코딩 제거 (이미 바이너리 형태인 경우)
    #     signature_bytes = signature if isinstance(signature, bytes) else base64.b64decode(signature)
        
    #     try:
    #         return verifying_key.verify(signature_bytes, message_json)
    #     except Exception:
    #         return False

