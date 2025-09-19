# Blocker Manufacturer Backend

### 1. 서비스 개요

Blocker Manufacturer Backend는 제조사가 배포하는 소프트웨어 업데이트를 안전하게 암호화·배포하고, 업데이트 메타데이터를 블록체인에 등록하여 무결성과 접근 제어를 보장하는 백엔드 서비스입니다. 주요 기능은 다음과 같습니다:

- 파일 암호화(AES-256) 및 정책 기반 키 암호화(CP-ABE)
- IPFS에 암호화된 업데이트 파일 업로드 및 CID(해시) 관리
- ECDSA 서명으로 업데이트 무결성 보증
- 스마트컨트랙트에 업데이트 메타데이터(버전, 설명, 가격, CID 등) 등록
- 서비스 계층 분리로 라우트에서 비즈니스 로직 분리

### 2. 개발 환경

- 운영체제: macOS (개발/테스트 권장)
- 셸: zsh
- Python: 3.10 이상 권장
- 의존성: `requirements.txt`에 정의
- 실행 진입점: `main.py`

자세한 설치 및 실행 방법은 `install.md`를 참고하세요.

### 3. 사용 기술

- 웹 프레임워크: Flask (Blueprint 기반 라우팅)
- 블록체인 연동: web3.py 또는 유사한 Ethereum 클라이언트 연동 (스마트컨트랙트 ABI 사용)
- 분산저장: IPFS (파일 업로드 및 핀)
- 암호화/키 관리:
  - CP-ABE (Ciphertext-Policy Attribute-Based Encryption) - `crypto/cpabe`
  - ECDSA 서명/검증 - `crypto/ecdsa`
  - 대칭암호(AES-256) - `crypto/symmetric`
  - 해시(SHA-3 등) - `crypto/hash`
- 로깅/유틸: 프로젝트 내 `utils/logger.py`
- 컨테이너화(선택): Docker, Docker Compose

### 4. 폴더 구조

프로젝트 최상위 폴더 구조 및 각 폴더의 역할은 다음과 같습니다:

```
Blocker_Manufacturer_Backend/
│
├── main.py                # 앱 실행 진입점
├── README.md              # 프로젝트 설명 (현재 파일)
├── install.md             # 설치 및 실행 가이드
├── requirements.txt       # Python 의존성
│
├── api/                   # API 엔드포인트(Flask Blueprint)
│   └── routes.py
│
├── blockchain/            # 블록체인 연동 모듈
│   ├── contract.py        # 스마트컨트랙트 연동 클래스
│   ├── utils.py
│   └── registry_address.json
│
├── crypto/                # 암호화 및 해시 관련 모듈
│   ├── cpabe/             # CP-ABE 관련 구현
│   │   └── cpabe.py
│   ├── ecdsa/             # ECDSA 서명/검증
│   │   └── ecdsa.py
│   ├── hash/              # 해시 함수
│   │   └── hash.py
│   ├── symmetric/         # 대칭키 암호화/복호화
│   │   └── symmetric.py
│   └── keys/              # 키 파일 (PEM, master key 등)
│       ├── device_secret_key_file.bin
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

- 설계 원칙:
  - 라우트는 요청/응답 처리만 담당하고 내부 비즈니스 로직은 `services/`에 위임합니다.
  - 암호화 관련 코드는 `crypto/` 아래에 모아 단일 책임 원칙을 유지합니다.
  - 민감 키 파일은 `crypto/keys/`에 보관하며 접근 권한을 제한해야 합니다.

---

추가로, 설치 및 실행 관련 상세 절차는 프로젝트 루트의 `install.md` 파일을 확인하세요.
