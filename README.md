# Blocker Manufacturer Backend

## 폴더/파일 구조 및 역할 (2025.05.02 기준 최신)

```
Blocker_Manufacturer_Backend/
│
├── main.py                # 앱 실행 진입점
├── README.md              # 프로젝트 설명
├── update_cache.json      # 소프트웨어 업데이트 캐시 데이터
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
│   └── symmetric/symmetric.py # 대칭키 암호화/복호화
│
├── db/                    # 데이터베이스 모델 및 CRUD
│   ├── crud.py
│   └── models.py
│
├── ipfs/                  # IPFS 업로드 기능
│   └── upload.py
│
├── keys/                  # 암호화/서명에 사용되는 키 파일
│   ├── ecdsa_private_key.pem
│   ├── ecdsa_public_key.pem
│   ├── master_key.bin
│   └── public_key.bin
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
- **backend 폴더 제거**: 키 파일과 캐시 파일은 각각 keys/, 루트로 이동하여 폴더 구조를 명확하게 정리
- **crypto/**: 암호화, 해시, 서명 등 모든 보안 관련 기능을 하위 폴더로 세분화
- **utils/logger.py**: 공통 로깅 함수 제공
- **main.py**: Flask 앱 실행 및 Blueprint 등록

## 개발/확장 가이드
- 라우트 함수 내부에 비즈니스 로직을 직접 작성하지 않고, 반드시 services/ 계층에 위임할 것
- 암호화/블록체인/DB 등 각 기능별로 폴더를 분리하여 단일 책임 원칙을 지킬 것
- 키 파일, 캐시 파일 등은 별도 폴더에 보관하여 관리 용이성 및 보안성 확보

---

이 구조는 유지보수, 확장성, 보안성, 협업에 최적화되어 있습니다. 각 폴더/파일별 상세 설명이나 예시가 필요하면 README에 추가해 주세요.
