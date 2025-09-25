import json
import os
import base64
import binascii
from web3 import Web3
from eth_account import Account  # [추가]

# 블록체인 스마트컨트랙트 연동 모듈 (예시)
class BlockchainNotifier:
    def __init__(
        self,
        provider_url=None,
        registry_info_path=None,
        account_address=None,
        private_key=None,
    ):
        # provider_url 기본값
        if provider_url is None:
            provider_url = os.environ.get(
                "BLOCKCHAIN_PROVIDER", "http://localhost:8545"
            )
        self.web3 = Web3(Web3.HTTPProvider(provider_url))

        # AddressRegistry 정보 경로
        if registry_info_path is None:
            registry_info_path = os.path.join(
                os.path.dirname(__file__), "registry_address.json"
            )

        # AddressRegistry 주소/ABI 로드
        with open(registry_info_path, "r") as f:
            reg_info = json.load(f)
        registry_address = reg_info["address"]
        registry_abi = reg_info["abi"]
        registry_contract = self.web3.eth.contract(
            address=registry_address, abi=registry_abi
        )

        # SoftwareUpdateContract 주소와 ABI를 레지스트리에서 직접 조회
        update_address = registry_contract.functions.getContractAddress(
            "SoftwareUpdateContract"
        ).call()
        update_abi_json = registry_contract.functions.getAbi(
            "SoftwareUpdateContract"
        ).call()
        update_abi = json.loads(update_abi_json)

        # contract 핸들러 생성
        self.contract = self.web3.eth.contract(address=update_address, abi=update_abi)

        # 계정 정보: 환경 변수에서 가져오거나 전달받음
        self.private_key = private_key or os.environ.get("BLOCKCHAIN_PRIVATE_KEY")

        # [추가] private_key만 주어져도 주소를 도출
        if account_address:
            self.account_address = account_address
        elif self.private_key:
            self.account_address = Account.from_key(self.private_key).address
        else:
            self.account_address = os.environ.get("BLOCKCHAIN_ACCOUNT")

        if not self.account_address or not self.private_key:
            raise RuntimeError(
                "[BlockchainNotifier] account/private_key 누락. "
                "BLOCKCHAIN_PRIVATE_KEY를 설정하거나 __init__ 인자로 전달하세요."
            )

        # [추가] 사전 검증: manufacturer와 sender가 같은지 확인해 조기에 명확히 실패
        try:
            manufacturer = self.contract.functions.manufacturer().call()
            if self.account_address.lower() != manufacturer.lower():
                raise RuntimeError(
                    f"[registerUpdate 사전검증 실패] 트랜잭션 송신자({self.account_address})가 "
                    f"컨트랙트 manufacturer({manufacturer})와 다릅니다. "
                    "컨트랙트를 해당 주소로 배포했는지 확인하거나, "
                    "BLOCKCHAIN_PRIVATE_KEY를 manufacturer의 키로 설정하세요."
                )
        except Exception as e:
            # manufacturer 조회 실패는 네트워크/주소 문제일 수 있으므로 그대로 올림
            raise

    def register_update(
        self,
        uid,
        ipfs_hash,
        encrypted_key,
        hash_of_update,
        description,
        price,
        version,
        signature,
    ):
        """
        SoftwareUpdateContract의 registerUpdate() 함수 호출
        Solidity 함수 시그니처는 다음과 같음:

        function registerUpdate(
            string memory uid,
            string memory ipfsHash,
            bytes memory encryptedKey,
            string memory hashOfUpdate,
            string memory description,
            uint256 price,
            string memory version,
            bytes memory signature
        ) public
        """

        # encrypted_key가 문자열인 경우 bytes로 변환
        if isinstance(encrypted_key, str):
            try:
                # base64 인코딩된 경우 디코딩
                encrypted_key = base64.b64decode(encrypted_key)
            except Exception:
                encrypted_key = encrypted_key.encode()

        # signature가 hex string("0x...") 형태인 경우 raw bytes로 변환
        if isinstance(signature, str):
            if signature.startswith("0x"):
                signature = binascii.unhexlify(signature[2:])
            else:
                # base64 인코딩된 경우 처리
                try:
                    signature = base64.b64decode(signature)
                except Exception:
                    signature = signature.encode()

        # [추가] 체인ID/가스가격/가스 추정으로 안정화
        chain_id = self.web3.eth.chain_id
        gas_price = self.web3.to_wei("20", "gwei")
        # 먼저 call data 구성
        func = self.contract.functions.registerUpdate(
            uid,
            ipfs_hash,
            encrypted_key,   # ✅ raw bytes
            hash_of_update,
            description,
            int(price),
            version,
            signature,       # ✅ raw bytes
        )
        # 가스 추정 (sender 지정)
        try:
            estimated_gas = func.estimate_gas({"from": self.account_address})
        except Exception:
            estimated_gas = 2_000_000  # 추정 실패시 보수적 상한

        tx = func.build_transaction(
            {
                "from": self.account_address,
                "nonce": self.web3.eth.get_transaction_count(self.account_address),
                "gas": estimated_gas,
                "gasPrice": gas_price,
                "chainId": chain_id,  # [추가] EIP-155 안전
            }
        )

        # [추가] 잔액 체크 (가스비 부족 시 깔끔한 에러)
        try:
            balance = self.web3.eth.get_balance(self.account_address)
            max_cost = tx["gas"] * tx["gasPrice"]
            if balance < max_cost:
                raise RuntimeError(
                    f"Insufficient funds: balance={balance}, needed≈{max_cost}"
                )
        except Exception:
            pass  # 네트워크별 get_balance 실패 시 그냥 진행

        # 서명 및 전송
        signed_tx = self.web3.eth.account.sign_transaction(
            tx, private_key=self.private_key
        )
        try:
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return tx_hash
        except ValueError as e:
            # [추가] JSON-RPC 오류 메시지를 그대로 노출 (리버트 사유 등)
            raise RuntimeError(f"send_raw_transaction error: {e}")

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
            print(f"블록체인에서 조회된 업데이트 수: {update_count}")

            for idx in range(update_count):
                try:
                    uid = self.contract.functions.getUpdateIdByIndex(idx).call()
                    print(f"인덱스 {idx}의 UID: {uid}")

                    # 스마트 컨트랙트에서 반환하는 데이터 형식에 맞게 처리
                    info = self.contract.functions.getUpdateInfo(uid).call()
                    print(f"UID {uid}의 원본 정보: {info}")

                    # 리스트 형식으로 반환되는 경우 (배열 반환)
                    if isinstance(info, list):
                        update_info = {
                            "uid": uid,
                            "ipfs_hash": info[0] if len(info) > 0 else "",
                            "description": info[3] if len(info) > 3 else "",
                            "price": float(info[4]) / 1e18 if len(info) > 4 else 0,
                            "version": info[5] if len(info) > 5 else "",
                        }
                    # 스마트 컨트랙트 반환값이 튜플인 경우(일반적인 Solidity 반환 형태)
                    elif isinstance(info, tuple):
                        update_info = {
                            "uid": uid,
                            "ipfs_hash": info[0] if len(info) > 0 else "",
                            "description": info[3] if len(info) > 3 else "",
                            "price": float(info[4]) / 1e18 if len(info) > 4 else 0,
                            "version": info[5] if len(info) > 5 else "",
                        }
                    # 이미 딕셔너리 형태로 반환되는 경우
                    elif isinstance(info, dict):
                        update_info = {
                            "uid": uid,
                            "ipfs_hash": info.get("ipfsHash", ""),
                            "description": info.get("description", ""),
                            "price": float(info.get("price", 0)) / 1e18,
                            "version": info.get("version", ""),
                        }
                    else:
                        print(f"지원하지 않는 정보 형식: {type(info)}")
                        continue

                    updates.append(update_info)
                    print(f"처리된 업데이트 정보: {update_info}")

                except Exception as e:
                    print(f"UID {uid} 정보 조회 오류: {str(e)}")
                    continue

        except Exception as e:
            print(f"업데이트 목록 조회 중 오류 발생: {str(e)}")

        print(f"최종 반환할 업데이트 수: {len(updates)}")
        return updates

    def get_updates(self, include_invalid=False):
        """
        include_invalid=True: 전체(취소 포함)
        include_invalid=False: 유효한(isValid==True) 업데이트만
        각 업데이트에 isValid 필드 포함
        """
        updates = []
        try:
            update_count = self.contract.functions.getUpdateCount().call()
            for idx in range(update_count):
                try:
                    uid = self.contract.functions.getUpdateIdByIndex(idx).call()
                    info = self.contract.functions.getUpdateInfo(uid).call()
                    # info: [ipfsHash, encryptedKey, hashOfUpdate, description, price, version, isValid]
                    is_valid = info[6] if len(info) > 6 else True
                    update_info = {
                        "uid": uid,
                        "ipfs_hash": info[0] if len(info) > 0 else "",
                        "encrypted_key": (
                            base64.b64encode(info[1]).decode() if info[1] else ""
                        ),
                        "description": info[3] if len(info) > 3 else "",
                        "price": float(info[4]) / 1e18 if len(info) > 4 else 0,
                        "version": info[5] if len(info) > 5 else "",
                        "isValid": is_valid,
                    }
                    if include_invalid or is_valid:
                        updates.append(update_info)
                except Exception:
                    continue
        except Exception:
            pass
        return updates

    def cancel_update(self, uid):
        """
        블록체인 SoftwareUpdateContract의 cancelUpdate(uid) 함수 호출
        제조사(관리자)만 호출 가능
        """
        tx = self.contract.functions.cancelUpdate(uid).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.web3.eth.get_transaction_count(self.account_address),
                "gas": 200000,  # 적절한 가스 한도
                "gasPrice": self.web3.to_wei("20", "gwei"),
                "chainId": self.web3.eth.chain_id,  # [추가]
            }
        )
        signed_tx = self.web3.eth.account.sign_transaction(
            tx, private_key=self.private_key
        )
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash

    def get_updates_paginated(self, page=1, limit=20, include_invalid=False):
        """
        페이지네이션을 지원하는 업데이트 목록 조회

        Args:
            page (int): 페이지 번호 (1부터 시작)
            limit (int): 페이지당 항목 수 (기본 20, 최대 100)
            include_invalid (bool): 취소된 업데이트 포함 여부

        Returns:
            dict: 업데이트 목록과 페이지네이션 정보
        """
        # 입력값 검증
        if page < 1:
            page = 1
        if limit < 1:
            limit = 20
        if limit > 100:  # 최대 100개로 제한
            limit = 100

        updates = []
        try:
            # 전체 업데이트 개수 조회
            total_count = self.contract.functions.getUpdateCount().call()

            # 페이지네이션 계산
            start_index = (page - 1) * limit
            end_index = min(start_index + limit, total_count)

            # 전체 페이지 수 계산
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

            # 요청한 페이지가 범위를 벗어난 경우
            if start_index >= total_count and total_count > 0:
                return {
                    "updates": [],
                    "pagination": {
                        "current_page": page,
                        "per_page": limit,
                        "total_count": total_count,
                        "total_pages": total_pages,
                        "has_next": False,
                        "has_prev": page > 1,
                    },
                }

            print(
                f"페이지네이션 조회: 페이지 {page}, 범위 {start_index}~{end_index-1}, 전체 {total_count}개"
            )

            # 지정된 범위의 업데이트만 조회
            for idx in range(start_index, end_index):
                try:
                    uid = self.contract.functions.getUpdateIdByIndex(idx).call()
                    info = self.contract.functions.getUpdateInfo(uid).call()

                    # info: [ipfsHash, encryptedKey, hashOfUpdate, description, price, version, isValid]
                    is_valid = info[6] if len(info) > 6 else True

                    # include_invalid가 False면 유효한 업데이트만 포함
                    if not include_invalid and not is_valid:
                        continue

                    update_info = {
                        "uid": uid,
                        "ipfs_hash": info[0] if len(info) > 0 else "",
                        "encrypted_key": (
                            base64.b64encode(info[1]).decode() if info[1] else ""
                        ),
                        "hash_of_update": info[2] if len(info) > 2 else "",
                        "description": info[3] if len(info) > 3 else "",
                        "price": float(info[4]) / 1e18 if len(info) > 4 else 0,
                        "version": info[5] if len(info) > 5 else "",
                        "isValid": is_valid,
                    }
                    updates.append(update_info)

                except Exception as e:
                    print(f"인덱스 {idx}의 업데이트 조회 오류: {str(e)}")
                    continue

            # 페이지네이션 정보 구성
            pagination_info = {
                "current_page": page,
                "per_page": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "start_index": start_index + 1 if total_count > 0 else 0,
                "end_index": min(start_index + len(updates), total_count),
            }

            return {"updates": updates, "pagination": pagination_info}

        except Exception as e:
            print(f"페이지네이션 업데이트 목록 조회 중 오류 발생: {str(e)}")
            return {
                "updates": [],
                "pagination": {
                    "current_page": page,
                    "per_page": limit,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False,
                    "start_index": 0,
                    "end_index": 0,
                },
            }
