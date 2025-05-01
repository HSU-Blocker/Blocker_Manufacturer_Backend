import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from charm.toolbox.pairinggroup import GT  # GT 직접 가져오기
import logging
from hashlib import sha256
from charm.core.engine.util import objectToBytes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SymmetricCrypto:
    """대칭키 암호화/복호화를 위한 클래스"""

    @staticmethod
    def generate_key(group):
        """AES 키 생성 + GT 변환"""
        kbj = group.random(GT)  # GT 그룹 요소로 키 생성
        logger.info(f"GT 그룹에서 생성된 AES 키(kbj): {kbj}")

        kbj_bytes = group.serialize(kbj)
        # aes_key = kbj_bytes[:32]  # AES 256-bit (32바이트) 키 생성
        aes_key = sha256(objectToBytes(kbj, group)).digest()[:32]

        return kbj, aes_key

    @staticmethod
    def encrypt_file(file_path, key):
        """파일을 대칭키로 AES CBC 모드로 암호화"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "rb") as file:
            file_data = file.read()

        # 무작위 IV 생성 및 저장
        iv = os.urandom(16)  # AES 블록 크기 (16바이트 IV)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(pad(file_data, AES.block_size))

        encrypted_file_path = f"{file_path}.enc"
        with open(encrypted_file_path, "wb") as file:
            file.write(iv + encrypted_data)  # IV + 암호문 저장

        return encrypted_file_path

    @staticmethod
    def decrypt_file(encrypted_file_path, key):
        """파일을 대칭키로 AES CBC 모드로 복호화"""
        if not os.path.exists(encrypted_file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {encrypted_file_path}")

        with open(encrypted_file_path, "rb") as file:
            encrypted_data = file.read()

        if len(encrypted_data) < 16:
            raise ValueError("올바르지 않은 암호화 데이터입니다. (IV 없음)")

        iv = encrypted_data[:16]  # IV 추출
        encrypted_data = encrypted_data[16:]  # 암호문 분리

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted_data)

        try:
            decrypted_data = unpad(decrypted_data, AES.block_size)  # 패딩 제거
        except ValueError:
            raise ValueError("패딩 오류: 데이터가 올바르지 않음 (복호화 실패)")

        # 복호화된 파일 저장
        decrypted_file_path = encrypted_file_path.replace(".enc", "")
        with open(decrypted_file_path, "wb") as file:
            file.write(decrypted_data)

        return decrypted_file_path
