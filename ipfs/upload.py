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
        """IPFS 클라이언트 초기화"""
        if ipfs_api is None:
            ipfs_api = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
        try:
            self.client = ipfshttpclient.connect(ipfs_api)
            logger.info(f"IPFS 클라이언트 연결 성공: {ipfs_api}")
            self.ipfs_available = True
        except Exception as e:
            logger.error(f"IPFS 클라이언트 연결 실패: {e}")
            self.ipfs_available = False

    def upload_file(self, file_path):
        """
        파일을 IPFS에 업로드하고 DHT 등록 및 핀(Pin) 처리
        :param file_path: 업로드할 로컬 파일 경로
        :return: {cid, file_name, sha3}
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            if self.ipfs_available:
                logger.info(f"IPFS에 파일 업로드 시작: {file_path}")

                # wrap-with-directory 옵션 → 파일명 보존
                result = self.client.add(file_path, wrap_with_directory=True)

                """
                result는 배열 형태로 반환됨 (디렉토리와 파일 CID 모두 포함)
                [
                    {'Name': '파일명.py.enc', 'Hash': 'QmFileCID', 'Size': '1234'},
                    {'Name': '', 'Hash': 'QmDirCID', 'Size': '2345'}
                ]
                """
                # 디렉토리 CID (블록체인에 저장할 값)
                dir_entry = next(r for r in result if r["Name"] == "")
                dir_cid = dir_entry["Hash"]

                # 파일명은 따로 기록용
                file_entry = next(r for r in result if r["Name"] != "")
                file_name = file_entry["Name"]

                # 블록체인에 저장할 해시값은 디렉토리 CID
                cid = dir_cid

                logger.info(f"파일 업로드 완료 CID: {cid}, 파일명: {file_name}")

                # DHT 등록
                logger.info("DHT에 CID 등록 중")
                subprocess.run(["ipfs", "dht", "provide", cid], capture_output=True, text=True)
                time.sleep(5)
                logger.info("DHT 등록 완료") # DHT 등록이 퍼질 시간을 줌

                # 핀 추가 (파일을 노드에 유지)
                logger.info("핀 설정 중")
                self.client.pin.add(cid)
                logger.info("핀 설정 완료")

                return {"cid": cid, "file_name": file_name,}

            else:
                raise ConnectionError("IPFS 노드에 연결할 수 없습니다.")

        except Exception as e:
            logger.error(f"IPFS 업로드 중 오류 발생: {e}")
            return None
