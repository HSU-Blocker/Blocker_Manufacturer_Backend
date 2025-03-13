class BlockchainService:
    def __init__(self):
        self.temp_storage = {}
        self.counter = 0  # 간단한 테스트용 카운터

    def upload_to_blockchain(self, text: str) -> str:
        # 유효성 검사 강화
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
            
        if len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
            
        if len(text) > 500:
            raise ValueError("Text exceeds 500 characters limit")
            
        # 정상 처리 로직
        tx_hash = f"TX_{self.counter:04d}"
        self.temp_storage[tx_hash] = text
        self.counter += 1
        return tx_hash