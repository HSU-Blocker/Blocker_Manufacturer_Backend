
Key Management Strategy
    저장 방식 = AES-256으로 암호화된 상태로 저장
    저장 위치 = .env파일(깃허브 업로드 금지)
    사용 방법 = 코드에서 로딩 후 AES 복호화 후 사용


*안전한 키 저장소 활용
    AWS KMS(클라우드 환경)
    HashiCorp Valut(온프레미스 환경)
    Keyring(로컬 개발용)

*깃허브 보안 설정
    깃허브 시크릿 - API Key 및 개인키 보관
