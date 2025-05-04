# 플랫폼 지정 및 Python 3.9-slim 이미지 사용
FROM --platform=linux/amd64 python:3.9-slim

# 기본 패키지 설치 (libgmp-dev 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgmp-dev \
    libssl-dev \
    wget \
    cmake \
    flex \
    bison \
    autoconf \
    libtool \
    python3-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# PBC 라이브러리 설치 (기본 제공 GMP 사용)
RUN wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz && \
    tar -xvf pbc-0.5.14.tar.gz && \
    cd pbc-0.5.14 && \
    ./configure --disable-gmp-tests && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf pbc-0.5.14 pbc-0.5.14.tar.gz

# PyParsing 2.1.5 및 Hypothesis 설치
RUN pip install --no-cache-dir pyparsing==2.1.5 hypothesis

# charm-crypto 설치
RUN git clone https://github.com/JHUISI/charm.git && \
    cd charm && \
    ./configure.sh && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf charm

# 요구사항 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install regex>=2022.3.15 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install pycryptodome>=3.14.1 cryptography>=36.0.0

RUN pip install --no-cache-dir -r requirements.txt

# solc 설치
RUN pip install py-solc-x
RUN python -c "import solcx; solcx.install_solc('0.8.17'); solcx.set_solc_version('0.8.17')"

# 프로젝트 파일 복사
COPY . .

# 기본 명령어
CMD ["python", "main.py"]
