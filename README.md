# Asterisk 20 + PostgreSQL + FastAPI Stack

A modular, containerized PBX stack featuring Asterisk 20 (source-built with G.729 support), PostgreSQL (Realtime configuration), and a FastAPI management API.

## 🏗 Architecture

- **Asterisk 20**: Compiled from source with `pjproject`, `opus`, and `g729` transcoder. Uses `res_odbc` for Realtime SIP/Dialplan configuration.
- **PostgreSQL 15**: Stores Asterisk configuration (Realtime) and CDR logs.
- **FastAPI API**: Provides a RESTful management layer for managing extensions, trunks, dialplan routes, and more.

## 🚀 Quick Start

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd container_asterisk_stack
    ```

2.  **Environment Setup**:
    Copy the example environment file and customize it:
    ```bash
    cp .env.example .env
    ```

3.  **Run the Stack**:
    ```bash
    docker-compose up -d --build
    ```

## ✅ Post-Health Check

Sistemin doğru kurulduğunu doğrulamak için şu komutları kullanabilirsiniz:

### 1. Konteynır Durumlarını Kontrol Et
Tüm servislerin `(healthy)` veya `Up` olduğundan emin olun:
```bash
docker ps
```

### 2. Veritabanı Bağlantısını (ODBC) Doğrula
Asterisk'in PostgreSQL'e bağlı olup olmadığını kontrol edin:
```bash
docker exec -it pbx-asterisk asterisk -rx "odbc show"
```
*Beklenen Çıktı: `Active connections: 1 (veya daha fazla)`*

### 3. API Durumunu Kontrol Et
API'nin çalışıp çalışmadığını test edin:
```bash
curl http://localhost:8000/
```
*Beklenen Çıktı: `{"message": "Welcome to GadgetPBX Management API", "status": "online"}`*

### 4. Asterisk Loglarını İzle
Hata olup olmadığını gerçek zamanlı görün:
```bash
docker logs -f pbx-asterisk
```

## 🔌 API Access

The management API is accessible at:
- **Base URL**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

## ⚙️ Configuration Notes

### Host Networking
The Asterisk container uses `network_mode: "host"`. This is intentional to ensure seamless SIP and RTP traffic handling without complex Docker NAT issues. If your host's port `5060` or `10000-20000` is already in use, you may need to adjust the configuration.

### ODBC & Realtime
Asterisk connects to the PostgreSQL database using ODBC (`unixODBC`). The database schema is initialized automatically from `./db/init.sql`.

## 🛠 Project Structure

```text
.
├── api/                # FastAPI application
├── asterisk/           # Asterisk config & Dockerfile
├── db/                 # SQL initialization scripts
├── .env.example        # Environment template
└── docker-compose.yml  # Docker orchestration
```

## 📜 License
*Note: Please specify your preferred license.*
