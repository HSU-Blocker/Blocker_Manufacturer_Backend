# Installation and Run Guide

This document provides step-by-step instructions to set up and run the project in a local development environment or inside containers.

## 1. System Requirements

- Operating system: macOS, Linux, Windows (WSL recommended)
- Python 3.10 or newer
- Docker & Docker Compose (for containerized runs)
- Internet connection (for package installation and IPFS/blockchain access)

## 2. Local Development Setup

1. Clone the repository and change into the project directory

```bash
git clone <repo-url>
cd Blocker_Manufacturer_Backend
```

2. Configure environment variables

To set environment variables locally, create a `.env` file and add keys like:

```env
BLOCKCHAIN_PROVIDER={YOUR_BLOCKCHAIN_PROVIDER}
BLOCKCHAIN_ACCOUNT={YOUR_BLOCKCHAIN_ACCOUNT}
BLOCKCHAIN_PRIVATE_KEY={YOUR_BLOCKCHAIN_PRIVATE_KEY}
IPFS_API_URL=/dns/ipfs/tcp/5001/http
```

## 3. Run with Docker

1. Build the Docker image

```bash
docker build -t blocker-manufacturer-backend .
```

2. Run with Docker Compose

```bash
docker compose up --build
```

You can configure blockchain nodes, IPFS nodes, and other services in `docker-compose.yml` to connect to a test network if needed.



## 4. Testing(optional)

- Test API endpoints with `curl`, Postman, or similar tools.
- Example endpoints:
  - POST /api/manufacturer/upload: Upload and register an update file
  - GET /api/manufacturer/updates: List registered updates
- Alternatively, you can access Swagger for testing at http://127.0.0.1:5002/api/docs.

## 5. Security Recommendations(optional)

- In production, store sensitive secrets (e.g., PRIVATE_KEY, master keys) in a secure secret manager (Vault, KMS, etc.).
- Restrict filesystem permissions for the `crypto/keys/` folder.
- Use HTTPS, configure CORS properly, and validate all inputs.

---

If you encounter issues, check the README and source code first, then open an issue in the repository.
