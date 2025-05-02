# 블록체인 스마트컨트랙트 연동 모듈 (예시)


class BlockchainNotifier:
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
