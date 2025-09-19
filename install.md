# 설치 및 실행 가이드

이 문서는 프로젝트를 로컬 개발 환경 또는 컨테이너에서 실행하기 위한 단계별 설치 및 실행 방법을 제공합니다.

## 1. 시스템 요구사항

- 운영체제: macOS, Linux, Windows(WSL 권장)
- Python 3.10 이상
- Docker & Docker Compose (컨테이너 실행 시)
- 인터넷 연결 (패키지 및 IPFS/블록체인 연결)

## 2. 로컬 개발 환경 설정

1. 저장소 클론 및 이동

```bash
git clone <repo-url>
cd Blocker_Manufacturer_Backend
```

2. Python 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. 의존성 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정

- 필요한 환경 변수 예시
  - INFURA_URL 또는 ETH_NODE_URL: 이더리움 노드 엔드포인트
  - PRIVATE_KEY: 트랜잭션 서명에 사용할 ECDSA 개인키(테스트용)
  - IPFS_API: IPFS API 엔드포인트

환경 변수를 로컬에서 설정하려면 `.env` 파일을 만들고 다음 키들을 추가하세요:

```env
ETH_NODE_URL=https://mainnet.infura.io/v3/<PROJECT_ID>
PRIVATE_KEY=0x...
IPFS_API=http://127.0.0.1:5001
```

5. 키 파일 준비

- `crypto/keys/` 폴더에 존재하는 키 파일들을 확인하세요. 필요 시 새 키를 생성하거나 테스트 키로 교체하세요.

6. 데이터베이스(옵션)

- 현재 예시는 간단한 파일/메모리 기반 저장을 가정합니다. 영구 저장소가 필요하면 데이터베이스 연결 및 마이그레이션을 추가하세요.

7. 애플리케이션 실행

```bash
# 가상환경이 활성화된 상태에서
python main.py
```

기본적으로 Flask가 바인딩한 포트(예: 5000)에서 서비스가 시작됩니다. `main.py`에서 포트나 디버그 설정을 변경할 수 있습니다.

## 3. Docker로 실행 (선택)

1. Docker 이미지 빌드

```bash
docker build -t blocker-manufacturer-backend .
```

2. Docker Compose로 실행

```bash
docker compose up --build
```

Docker Compose 파일에 블록체인 노드, IPFS 노드 등을 함께 구성할 수 있습니다. 필요 시 `docker-compose.yml` 파일을 수정해 테스트 네트워크와 연동하세요.

## 4. 테스트

- API 엔드포인트 테스트는 `curl` 또는 Postman을 사용하세요.
- 주요 엔드포인트 예시
  - POST /api/manufacturer/upload: 업데이트 파일 업로드 및 등록
  - GET /api/manufacturer/updates: 등록된 업데이트 목록 조회

## 5. 보안 권장사항

- 실제 운영 환경에서는 개인키(PRIAVTE_KEY)와 마스터키 같은 민감 정보를 안전한 키 관리 시스템(Vault 등)에 보관하세요.
- `crypto/keys/` 폴더에 대한 파일 시스템 권한을 제한하세요.
- HTTPS를 사용하고, CORS 설정과 입력값 검증을 적용하세요.

---

문제가 발생하면 README와 소스 코드를 확인한 뒤 이슈를 생성해 주세요.
