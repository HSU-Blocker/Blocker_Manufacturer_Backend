# Blocker Manufacturer Backend

## 폴더/파일 구조 및 역할 (2025.05.02 기준 최신)

```
Blocker_Manufacturer_Backend/
│
├── main.py                # 앱 실행 진입점
├── README.md              # 프로젝트 설명
│
├── api/                   # API 엔드포인트(Flask Blueprint)
│   └── routes.py
│
├── blockchain/            # 블록체인 연동 모듈
│   ├── contract.py
│   └── utils.py
│
├── crypto/                # 암호화 및 해시 관련 모듈
│   ├── cpabe/cpabe.py     # CP-ABE 암호화/복호화
│   ├── ecdsa/ecdsa.py     # ECDSA 서명/검증
│   ├── hash/hash.py       # SHA-3 등 해시 함수
│   ├── symmetric/symmetric.py # 대칭키 암호화/복호화
│   └── keys/              # 암호화/서명에 사용되는 키 파일
│       ├── ecdsa_private_key.pem
│       ├── ecdsa_public_key.pem
│       ├── master_key.bin
│       └── public_key.bin
│
├── ipfs/                  # IPFS 업로드 기능
│   └── upload.py
│
├── services/              # 비즈니스 로직(서비스 계층)
│   └── update_service.py
│
└── utils/                 # 공통 유틸리티
    └── logger.py
```

## 주요 변경점 및 설계 원칙

- **api/routes.py**: 모든 API 엔드포인트는 Flask Blueprint로 분리, 라우트 함수에서는 요청 파싱/응답만 담당
- **services/update_service.py**: 파일 암호화, IPFS 업로드, 블록체인 등록 등 비즈니스 로직을 서비스 계층으로 분리
- **crypto/keys/**: 키 파일을 암호화 관련 폴더 하위로 이동하여 보안성과 구조 명확성 강화
- **backend 폴더 제거**: 키 파일은 crypto/keys/로 이동하여 폴더 구조를 명확하게 정리
- **crypto/**: 암호화, 해시, 서명 등 모든 보안 관련 기능을 하위 폴더로 세분화
- **utils/logger.py**: 공통 로깅 함수 제공
- **main.py**: Flask 앱 실행 및 Blueprint 등록

## 개발/확장 가이드
- 라우트 함수 내부에 비즈니스 로직을 직접 작성하지 않고, 반드시 services/ 계층에 위임할 것
- 암호화/블록체인 등 각 기능별로 폴더를 분리하여 단일 책임 원칙을 지킬 것
- 키 파일 등은 crypto/keys/ 폴더에 보관하여 관리 용이성 및 보안성 확보

---

이 구조는 유지보수, 확장성, 보안성, 협업에 최적화되어 있습니다. 각 폴더/파일별 상세 설명이나 예시가 필요하면 README에 추가해 주세요.

---

## 📚 주요 파일별 상세 클래스/함수 설명 (2025.05.04 기준)

### main.py
- Flask 앱 실행 및 Blueprint 등록.

### api/routes.py
- Flask Blueprint(`api_bp`)로 API 엔드포인트 제공.
- **upload_software_update()**: `/api/manufacturer/upload` POST, 소프트웨어 업데이트 업로드 전체 파이프라인 호출.
- **list_updates()**: `/api/manufacturer/updates` GET, 등록된 업데이트 목록 조회.
- **build_attribute_policy(policy_dict)**: 속성 정책 문자열 생성(내부 함수).

### blockchain/contract.py
- **BlockchainNotifier**: 블록체인 스마트컨트랙트 연동 클래스.
  - `__init__`: provider, ABI, 계정정보 등 초기화.
  - **register_update(uid, ipfs_hash, encrypted_key, hash_of_update, description, price, version, signature)**: 업데이트 등록 트랜잭션 생성/서명/전송.
  - **get_all_updates()**: 전체 업데이트 목록 조회.

### crypto/cpabe/cpabe.py
- **CPABETools**: CP-ABE(속성기반 암호화) 관련 기능 제공.
  - `__init__`: PairingGroup, CPabe_BSW07 초기화.
  - **setup(public_key_file, master_key_file)**: 공개키/마스터키 생성 및 파일 저장.
  - **encrypt(message, policy, public_key_file)**: 정책 기반 암호화.
  - **decrypt(encrypted_key_json, public_key, device_secret_key)**: 복호화.
  - **generate_device_secret_key(public_key_file, master_key_file, attributes, device_secret_key_file)**: 속성 기반 디바이스 비밀키 생성 및 저장.
  - **load_public_key(public_key_file)**: 공개키 파일 로드.
  - **load_device_secret_key(device_secret_key_file)**: 디바이스 비밀키 파일 로드.
  - **get_group()**: pairing group 객체 반환.

### crypto/ecdsa/ecdsa.py
- **ECDSATools**: ECDSA 서명/검증 및 키 관리.
  - **generate_key_pair(private_key_path, public_key_path)**: 개인/공개키 생성 및 PEM 저장.
  - **load_private_key(private_key_path)**, **load_public_key(public_key_path)**: 키 파일 로드.
  - **save_key(key, key_path)**: 키 파일 저장.
  - **sign_message(message, private_key_path)**: 메시지 서명(Ethereum 포맷, 65바이트).
  - **verify_signature(message, signature, public_key)**: 서명 검증.
  - **serialize_message(message)**, **deserialize_message(message_json)**: 메시지 직렬화/역직렬화.

### crypto/hash/hash.py
- **HashTools**: 파일 해시 계산 도구.
  - **calculate_file_hash(file_path, algorithm="sha256", chunk_size=8192)**: 다양한 알고리즘 지원 파일 해시.
  - **sha3_hash_file(file_path, chunk_size=8192)**: SHA3-256 해시.

### crypto/symmetric/symmetric.py
- **SymmetricCrypto**: 대칭키 암호화/복호화.
  - **generate_key(group)**: GT 그룹 기반 AES 키 생성, (GT element, 32byte AES key) 반환.
  - **encrypt_file(file_path, key)**: 파일을 AES CBC로 암호화, `.enc` 파일 생성.
  - **decrypt_file(encrypted_file_path, key)**: 암호화된 파일 복호화.

### ipfs/upload.py
- **IPFSUploader**: 파일을 IPFS에 업로드, DHT 등록, Pin 처리.
  - `__init__(ipfs_api)`: IPFS 클라이언트 연결.
  - **upload_file(file_path)**: 파일 업로드 및 CID 반환.

### services/update_service.py
- **UpdateService**: 소프트웨어 업데이트 업로드 전체 파이프라인 담당(비즈니스 로직).
  - **process_update_upload(file, version, description, price_eth, policy_dict, upload_folder, device_secret_key_folder, user_attributes, key_dir, cache_file=None)**: 파일 저장, 암호화, 해시, IPFS 업로드, CP-ABE 키 처리, ECDSA 서명, 블록체인 등록 등 전체 처리.
  - **build_attribute_policy(policy_dict)**: 속성 정책 문자열 생성.

---

### Swagger 접속
http://localhost:5001/api/docs 로 접속 후 API 요청 실행