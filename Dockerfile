# Blocker Manufacturer Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip \
    && pip install flask ipfshttpclient charm-crypto ecdsa python-dotenv

EXPOSE 5001

CMD ["python", "main.py"]
