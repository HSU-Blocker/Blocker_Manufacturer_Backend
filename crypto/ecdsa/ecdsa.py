import base64
import json
from charm.toolbox.pairinggroup import PairingGroup
from web3 import Web3
from eth_abi.packed import encode_packed
from eth_account import Account
from eth_account.messages import encode_defunct

# 전역적으로 PairingGroup 객체 생성
GLOBAL_GROUP = PairingGroup("SS512")


class ECDSATools:

    @staticmethod
    def generate_key_pair():
        """제조사 개인 키(SKm)와 공개 키(PKm) 생성 및 저장
        - 기존 PEM 저장 대신 Ethereum secp256k1 키 쌍을 생성
        """
        acct = Account.create()
        private_key_hex = acct.key.hex()
        address = acct.address
        print("Generated Ethereum Account:", address)
        return private_key_hex, address

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

    @staticmethod
    def sign_message(message_tuple, private_key_hex):
        uid, ipfs_hash, encrypted_key, hash_of_update, description, price, version = message_tuple

        # 반드시 encrypted_key는 bytes 그대로 encodePacked에 넣기
        if isinstance(encrypted_key, str):
            encrypted_key = encrypted_key.encode()

        message_bytes = encode_packed(
            ["string", "string", "bytes", "string", "string", "uint256", "string"],
            [uid, ipfs_hash, encrypted_key, hash_of_update, description, int(price), version],
        )
        message_hash = Web3.keccak(message_bytes)

        # Ethereum Signed Message prefix 적용
        signable_message = encode_defunct(primitive=message_hash)

        signed = Account.sign_message(signable_message, private_key_hex)
        return signed.signature  # 65바이트 (r, s, v)

    @staticmethod
    def verify_signature(message_tuple, signature, expected_address):
        """Ethereum 표준 형식(R 32B + S 32B + V 1B) 서명 검증"""
        uid, ipfs_hash, encrypted_key, hash_of_update, description, price, version = message_tuple

        # Ethereum 메시지 해시 생성
        message_bytes = encode_packed(
            ["string", "string", "string", "string", "string", "uint256", "string"],
            [uid, ipfs_hash, encrypted_key, hash_of_update, description, int(price), version],
        )
        message_hash = Web3.keccak(message_bytes)
        signable_message = encode_defunct(primitive=message_hash)

        # recover된 주소와 비교
        recovered = Account.recover_message(signable_message, signature=signature)
        print("Recovered address:", recovered)
        return recovered.lower() == expected_address.lower()
