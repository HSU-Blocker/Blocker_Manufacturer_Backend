import json
import os
from web3 import Web3

# 블록체인 스마트컨트랙트 연동 모듈 (예시)

class BlockchainNotifier:
    def __init__(self, provider_url=None, registry_info_path=None, update_abi_path=None, account_address=None, private_key=None):
        # provider_url 기본값
        if provider_url is None:
            provider_url = os.environ.get("BLOCKCHAIN_PROVIDER", "http://localhost:8545")
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        # AddressRegistry 정보 경로
        if registry_info_path is None:
            registry_info_path = os.path.join(os.path.dirname(__file__), "registry_address.json")
        # SoftwareUpdateContract ABI 경로
        if update_abi_path is None:
            update_abi_path = os.path.join(os.path.dirname(__file__), "contract_address.json")
        # AddressRegistry 주소/ABI 로드
        with open(registry_info_path, "r") as f:
            reg_info = json.load(f)
        registry_address = reg_info["address"]
        registry_abi = reg_info["abi"]
        registry_contract = self.web3.eth.contract(address=registry_address, abi=registry_abi)
        # SoftwareUpdateContract 주소 동적 조회
        update_address = registry_contract.functions.getContractAddress("SoftwareUpdateContract").call()
        # SoftwareUpdateContract ABI 로드
        with open(update_abi_path, "r") as f:
            update_abi_json = json.load(f)
        update_abi = update_abi_json["abi"]
        self.contract = self.web3.eth.contract(address=update_address, abi=update_abi)
        self.account_address = account_address or os.environ.get("BLOCKCHAIN_ACCOUNT")
        self.private_key = private_key or os.environ.get("BLOCKCHAIN_PRIVATE_KEY")

    def register_update(self, uid, ipfs_hash, encrypted_key, hash_of_update, description, price, version, signature):
        # 트랜잭션 데이터 준비
        tx = self.contract.functions.registerUpdate(
            uid,
            ipfs_hash,
            encrypted_key,
            hash_of_update,
            description,
            int(price),
            version,
            signature
        ).build_transaction({
            'from': self.account_address,
            'nonce': self.web3.eth.get_transaction_count(self.account_address),
            'gas': 2000000,  # 가스 한도 증가: 500,000 -> 2,000,000
            'gasPrice': self.web3.to_wei('20', 'gwei')  # 가스 가격도 증가: 10 -> 20 gwei
        })
        # 서명 및 전송
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash

    def get_all_updates(self):
        """
        블록체인 SoftwareUpdateContract에서 전체 업데이트 목록을 조회하여 반환합니다.
        - getUpdateCount()로 전체 개수 조회
        - getUpdateIdByIndex(index)로 각 uid 조회
        - getUpdateInfo(uid)로 상세 정보 조회
        """
        updates = []
        try:
            update_count = self.contract.functions.getUpdateCount().call()
            for idx in range(update_count):
                uid = self.contract.functions.getUpdateIdByIndex(idx).call()
                info = self.contract.functions.getUpdateInfo(uid).call()
                # info 구조는 실제 컨트랙트 반환값에 맞게 파싱 필요
                updates.append(
                    {
                        "uid": uid,
                        "version": info.get("version", ""),
                        "description": info.get("description", ""),
                        "ipfs_hash": info.get("ipfsHash", ""),
                        "price": info.get("price", 0) / 1e18,
                    }
                )
        except Exception as e:
            # 필요시 로깅
            pass
        return updates
