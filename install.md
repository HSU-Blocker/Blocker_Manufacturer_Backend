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

2. Create and activate a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Required example environment variables:
- INFURA_URL or ETH_NODE_URL: Ethereum node endpoint
- PRIVATE_KEY: ECDSA private key used for signing transactions (for testing)
- IPFS_API: IPFS API endpoint

To set environment variables locally, create a `.env` file and add keys like:

```env
ETH_NODE_URL=https://mainnet.infura.io/v3/<PROJECT_ID>
PRIVATE_KEY=0x...
IPFS_API=http://127.0.0.1:5001
```

5. Prepare key files

Check the `crypto/keys/` folder for the required key files. Generate new keys or replace them with test keys if needed.

6. Database (optional)

The current example assumes simple file- or in-memory-based storage. If persistent storage is required, add a database connection and migrations.

7. Run the application

```bash
# With the virtual environment activated
python main.py
```

By default, the Flask app will bind to a port (e.g., 5000). You can change the port or debug settings in `main.py`.

## 3. Run with Docker (optional)

1. Build the Docker image

```bash
docker build -t blocker-manufacturer-backend .
```

2. Run with Docker Compose

```bash
docker compose up --build
```

You can configure blockchain nodes, IPFS nodes, and other services in `docker-compose.yml` to connect to a test network if needed.

## 4. Testing

- Test API endpoints with `curl`, Postman, or similar tools.
- Example endpoints:
  - POST /api/manufacturer/upload: Upload and register an update file
  - GET /api/manufacturer/updates: List registered updates

## 5. Security Recommendations

- In production, store sensitive secrets (e.g., PRIVATE_KEY, master keys) in a secure secret manager (Vault, KMS, etc.).
- Restrict filesystem permissions for the `crypto/keys/` folder.
- Use HTTPS, configure CORS properly, and validate all inputs.

---

If you encounter issues, check the README and source code first, then open an issue in the repository.
