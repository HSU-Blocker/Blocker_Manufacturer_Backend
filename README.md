# Blocker Manufacturer Backend

## Overview
This repository implements the manufacturer backend of a blockchain-based secure software update platform. The manufacturer prepares and encrypts software updates, publishes update metadata and purchase information to a blockchain smart contract, and stores encrypted update packages on IPFS. Devices then discover updates, purchase them, download the encrypted packages from IPFS, verify integrity, and decrypt them using CP-ABE-managed keys.

### Manufacturer Update Process
1. Prepare the update package and encrypt the file with a generated symmetric key (AES-256).
2. Encrypt the symmetric key under a CP-ABE policy (producing Ec) so only compliant devices can decrypt it.
3. Upload the encrypted update file to IPFS and obtain the CID (Es).
4. Compute hashes (e.g., SHA3-256) of the encrypted file for integrity reference.
5. Sign metadata (version, price, CID, file hash, description) with the manufacturer's ECDSA private key.
6. Register the update metadata and purchase conditions on the blockchain smart contract.
7. Optionally monitor purchase events and deliver post-purchase actions (e.g., revoke, update policies).

## Development Environment
- OS: macOS (development recommended)
- Shell: zsh
- Python: 3.10 or newer
- Dependencies: listed in `requirements.txt`
- Entry point: `main.py`
- Containerization: Docker & Docker Compose supported

## Technology Stack

- ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)  Web framework used for the backend API and admin endpoints (imports in `main.py` and `api/routes.py`).

- ![Flask-RESTX](https://img.shields.io/badge/Flask--RESTX-007ACC?style=flat&logo=python&logoColor=white)  API documentation and request parsing (used in `api/routes.py`).

- ![Web3.py](https://img.shields.io/badge/Web3.py-F16822?style=flat&logo=ethereum&logoColor=white)  Ethereum/compatible blockchain interactions (used in `blockchain/contract.py`).

- ![IPFS](https://img.shields.io/badge/IPFS-65C2CB?style=flat&logo=ipfs&logoColor=white)  IPFS client (`ipfshttpclient`) for uploading encrypted update files (`ipfs/upload.py`).

- ![Charm-Crypto](https://img.shields.io/badge/Charm--Crypto-6C3483?style=flat&logo=academia&logoColor=white)  CP-ABE implementation (used in `crypto/cpabe/cpabe.py`).

- ![PyCryptodome](https://img.shields.io/badge/PyCryptodome-006699?style=flat&logo=python&logoColor=white)  AES-256 symmetric encryption utilities (`crypto/symmetric/symmetric.py`).

- ![SHA3-256](https://img.shields.io/badge/SHA3--256-117A65?style=flat&logo=hashnode&logoColor=white)  File integrity hashing (uses `hashlib.sha3_256` in `crypto/hash/hash.py`).

- ![ECDSA](https://img.shields.io/badge/ECDSA-34495E?style=flat&logo=openssl&logoColor=white)  Signature creation/verification utilities (see `crypto/ecdsa/ecdsa.py`).

- ![Python](https://img.shields.io/badge/Python_3.10-3776AB?style=flat&logo=python&logoColor=white)  Project language and runtime environment.

- ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)  Containerization support (see `Dockerfile`).

## Installation
See `install.md` for installation and usage instructions.

## Directory Structure
```
Blocker_Manufacturer_Backend/
│
├── main.py                # Application entry point
├── README.md              # Project description (this file)
├── install.md             # Installation and run guide
├── requirements.txt       # Python dependencies
│
├── api/                   # API endpoints (Flask Blueprint)
│   └── routes.py
│
├── blockchain/            # Blockchain integration modules
│   ├── contract.py        # Smart contract interface class
│   ├── utils.py
│   └── registry_address.json
│
├── crypto/                # Crypto and hashing modules
│   ├── cpabe/             # CP-ABE implementation
│   │   └── cpabe.py
│   ├── ecdsa/             # ECDSA sign/verify
│   │   └── ecdsa.py
│   ├── hash/              # Hash utilities (SHA3, etc.)
│   │   └── hash.py
│   ├── symmetric/         # Symmetric encryption/decryption (AES-256)
│   │   └── symmetric.py
│   └── keys/              # Key files (PEM, master key, etc.)
│       ├── device_secret_key_file.bin
│       ├── ecdsa_private_key.pem
│       ├── ecdsa_public_key.pem
│       ├── master_key.bin
│       └── public_key.bin
│
├── ipfs/                  # IPFS upload utilities
│   └── upload.py
│
├── services/              # Business logic (service layer)
│   └── update_service.py
│
└── utils/                 # Common utilities
    └── logger.py
```

## License
This project is licensed under the MIT License. See `LICENSE` for details.

---

Contributions and questions are welcome via Issues and Pull Requests. For more information about the overall project, visit the organization repository or open an issue on this repository.
