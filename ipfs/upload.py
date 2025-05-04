import ipfshttpclient
import hashlib
import os
import subprocess
import logging
import time
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IPFSUploader:
    """IPFS에 실제 파일을 업로드하고 DHT 등록 및 핀 처리를 수행하는 클래스"""

    def __init__(self, ipfs_api=None):
        """IPFS 클라이언트 초기화 (실제 노드 연결)"""
        if ipfs_api is None:
            ipfs_api = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
        try:
            self.client = ipfshttpclient.connect(ipfs_api)
            logger.info(f"✅ IPFS 클라이언트 연결 성공: {ipfs_api}")
            self.ipfs_available = True
        except Exception as e:
            logger.error(f"🚨 IPFS 클라이언트 연결 실패: {e}")
            self.ipfs_available = False

    def upload_file(self, file_path):
        """파일을 IPFS에 업로드하고 DHT 등록 및 핀(Pin) 처리"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")

        try:
            if self.ipfs_available:
                logger.info(f"⏳ IPFS에 파일 업로드 시작: {file_path}")

                # 🔹 파일을 읽고 SHA-3 해시 계산
                with open(file_path, "rb") as f:
                    file_data = f.read()

                sha3_hash = hashlib.sha3_256(file_data).hexdigest()
                logger.info(f"🔑 SHA-3 해시 계산 완료: {sha3_hash}")

                # 🔹 IPFS에 파일 업로드
                result = self.client.add(file_path)
                cid = result["Hash"]
                logger.info(f"✅ 파일 업로드 완료! CID: {cid}")

                # 🔹 DHT 등록 (CLI 실행)
                logger.info("📢 DHT에 CID 등록 중...")
                subprocess.run(
                    ["ipfs", "dht", "provide", cid], capture_output=True, text=True
                )
                time.sleep(5)  # DHT 등록이 퍼질 시간을 줌
                logger.info("✅ DHT 등록 완료!")

                # 🔹 핀 추가 (파일을 노드에 유지)
                logger.info("📌 핀 설정 중...")
                self.client.pin.add(cid)
                logger.info("✅ 핀 설정 완료!")

                return cid  # CID 반환

            else:
                raise ConnectionError("🚨 IPFS 노드에 연결할 수 없습니다.")

        except Exception as e:
            logger.error(f"🚨 IPFS 업로드 중 오류 발생: {e}")
            return None
