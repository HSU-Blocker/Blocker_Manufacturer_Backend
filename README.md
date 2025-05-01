# Blocker Manufacturer Backend

## 폴더/파일/함수별 상세 설명

### backend/
- **api.py** : 백엔드 메인 API 서버. 소프트웨어 업데이트 업로드, 권한 부여, 업데이트 목록 조회 등 API 제공.
  - `upload_software_update()` : 소프트웨어 업데이트 파일 업로드 및 암호화, IPFS 업로드, 블록체인 등록, 캐시 갱신 등 전체 프로세스 처리
  - `authorize_owner()` : 특정 소유자에게 업데이트 권한 부여(블록체인 트랜잭션)
  - `list_updates()` : 등록된 업데이트 목록 조회(캐시/블록체인)
  - `allowed_file(filename)` : 허용된 확장자 검사
  - `build_attribute_policy(policy_dict)` : CP-ABE 속성 정책 문자열 생성
  - `parse_attribute_policy(policy_str)` : 속성 정책 문자열 파싱
  - 기타: 정적 파일 제공 라우트, 서버 실행 진입점
- **update_cache.json** : 업로드된 소프트웨어 업데이트의 캐시 데이터(JSON 배열)
- **keys/** : 암호화/서명에 사용되는 키 파일 저장 폴더
  - `ecdsa_private_key.pem` : ECDSA 개인키(제조사 서명용)
  - `ecdsa_public_key.pem` : ECDSA 공개키(서명 검증용)
  - `master_key.bin` : CP-ABE 마스터키
  - `public_key.bin` : CP-ABE 공개키

### crypto/
암호화 관련 모듈 집합

- **cpabe/cpabe.py** : 속성 기반 암호화(CP-ABE) 도구
  - `CPABETools` 클래스
    - `__init__()` : CP-ABE 인스턴스 초기화
    - `setup(public_key_file, master_key_file)` : CP-ABE 키 생성 및 파일 저장
    - `encrypt(message, policy, public_key_file)` : 메시지(대칭키 등)를 정책 기반으로 암호화
    - `decrypt(encrypted_key_json, public_key, device_secret_key)` : 암호화된 키 복호화
    - `generate_device_secret_key(public_key_file, master_key_file, attributes, device_secret_key_file)` : 속성 기반 디바이스 비밀키 생성
    - `load_public_key(public_key_file)` : 공개키 로드
    - `load_device_secret_key(device_secret_key_file)` : 디바이스 비밀키 로드
    - `get_group()` : PairingGroup 객체 반환

- **ecdsa/ecdsa.py** : ECDSA 서명/검증 도구
  - `ECDSATools` 클래스
    - `generate_key_pair(private_key_path, public_key_path)` : ECDSA 키 쌍 생성 및 저장
    - `load_private_key(private_key_path)` : 개인키 로드
    - `load_public_key(public_key_path)` : 공개키 로드
    - `save_key(key, key_path)` : 키 파일 저장
    - `serialize_message(message)` : 메시지 직렬화
    - `deserialize_message(message_json)` : 메시지 역직렬화
    - `sign_message(message, private_key_path)` : 메시지 ECDSA 서명(이더리움 표준)
    - `verify_signature(message, signature, public_key)` : 서명 검증

- **hash/hash.py** : 해시 함수 도구
  - `HashTools` 클래스
    - `calculate_file_hash(file_path, algorithm="sha256")` : 파일 해시값 계산
    - `sha3_hash_file(file_path)` : SHA3-256 해시값 계산

- **symmetric/symmetric.py** : 대칭키 암호화 도구
  - `SymmetricCrypto` 클래스
    - `generate_key(group)` : GT 그룹 기반 대칭키 및 AES 키 생성
    - `encrypt_file(file_path, key)` : 파일을 AES CBC로 암호화
    - `decrypt_file(encrypted_file_path, key)` : 파일을 AES CBC로 복호화

---

각 함수별로 실제 구현 및 예외처리, 파일 입출력, 암호화/복호화, 서명/검증, 블록체인 연동 등 세부 로직이 포함되어 있습니다. 추가 설명이 필요한 함수나 파일이 있으면 말씀해 주세요.
