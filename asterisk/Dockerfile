FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. Build Dependencies and Tools
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    cmake \
    autoconf \
    automake \
    libtool \
    libxml2-dev \
    libncurses5-dev \
    libsqlite3-dev \
    libssl-dev \
    uuid-dev \
    libjansson-dev \
    libedit-dev \
    libsrtp2-dev \
    libopus-dev \
    libbcg729-dev \
    libcurl4-openssl-dev \
    unixodbc-dev \
    libpq-dev \
    python3 \
    python3-dev \
    bsdextrautils \
    ca-certificates \
    libspandsp-dev \
    libspeex-dev \
    libspeexdsp-dev \
    libgsm1-dev \
    # --- Debugging Tools ---
    sngrep \
    tcpdump \
    tshark \
    procps \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 2. Asterisk Source and PJProject Pre-download
WORKDIR /usr/src
RUN wget --no-check-certificate https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz && \
    mkdir asterisk && \
    tar -zxvf asterisk-20-current.tar.gz -C asterisk --strip-components=1 && \
    rm asterisk-20-current.tar.gz

# Pre-download pjproject to /tmp to avoid build-time download failures
RUN wget --no-check-certificate https://raw.githubusercontent.com/asterisk/third-party/master/pjproject/2.15.1/pjproject-2.15.1.tar.bz2 -P /tmp/

# 3. Configure and Compile
WORKDIR /usr/src/asterisk
RUN ./configure --with-pjproject-bundled --with-ssl --with-crypto --with-odbc --with-postgres && \
    make menuselect.makeopts && \
    menuselect/menuselect --enable codec_opus menuselect.makeopts && \
    make -j$(nproc) && \
    make install && \
    make samples && \
    make config && \
    # 4. Build G.729 External Module (Verified arkadijs/asterisk-g72x)
    cd /usr/src && \
    curl -L https://github.com/arkadijs/asterisk-g72x/archive/refs/heads/master.tar.gz -o g72x.tar.gz && \
    mkdir asterisk-g72x && \
    tar -zxvf g72x.tar.gz -C asterisk-g72x --strip-components=1 && \
    cd asterisk-g72x && \
    ./autogen.sh && \
    ./configure --with-bcg729 CPPFLAGS="-I/usr/src/asterisk/include" && \
    make && \
    make install && \
    ldconfig

# 4. ODBC Driver and Multi-arch Polish
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then LIB_DIR="x86_64-linux-gnu"; \
    elif [ "$ARCH" = "aarch64" ]; then LIB_DIR="aarch64-linux-gnu"; fi && \
    apt-get update && apt-get install -y odbc-postgresql && \
    ln -s /usr/lib/$LIB_DIR/odbc/psqlodbcw.so /usr/lib/psqlodbcw.so && \
    rm -rf /var/lib/apt/lists/*

# 5. Logging and Final Setup
WORKDIR /etc/asterisk
RUN ln -sf /dev/stdout /var/log/asterisk/messages

# Asterisk'i Transcoding yeteneklerini gösterecek şekilde başlat
CMD ["asterisk", "-f", "-vvvvv", "-T"]
