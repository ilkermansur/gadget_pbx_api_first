# Chapter 1: Sistem Mimarisi ve Docker Orkestrasyonu

Bu bölümde, GadgetPBX stack'inin genel mimarisi, servislerin birbirleriyle olan ilişkileri, Docker Compose orkestrasyonu ve ağ (network) mimarisi detaylandırılmaktadır.

---

## 1. Genel Mimari (3'lü Yapı)

GadgetPBX; gerçek zamanlı ses/video işleme yeteneklerine sahip bir PBX (Santral), bu santrali yöneten modern bir RESTful API ve tüm konfigürasyonu barındıran ilişkisel bir veritabanından oluşan **3'lü bir mimari (3-Tier Architecture)** üzerine kurulmuştur.

```mermaid
graph TD
    subgraph Client Layer
        SIP[SIP Softphone / IP Phone]
        Web[Web / API Client]
    end

    subgraph Container Stack (Host Network / Docker Bridge)
        API[FastAPI Management API]
        DB[(PostgreSQL Database)]
        AST[Asterisk 20 PBX]
    end

    %% Client Interactions
    SIP <-->|SIP/RTP: Port 5060 & 10000-10100| AST
    Web <-->|HTTP: Port 8000| API

    %% Internal Stack Connections
    API <-->|psycopg2 Connection Pool| DB
    AST <-->|UnixODBC Realtime Connection| DB
```

### 1.1. Bileşenlerin Rolleri
1.  **Asterisk 20 (PBX & Transcoding Engine):**
    *   Sistem mimarisinin kalbidir. SIP sinyalleşmesini (PJSIP kanalı) ve RTP (Real-time Transport Protocol) ses/video akışlarını yönetir.
    *   Konfigürasyonları disk üzerindeki statik dosyalardan okumak yerine **Realtime (Gerçek Zamanlı)** motoru aracılığıyla doğrudan veritabanından sorgular.
    *   **G.729** ve **Opus** ses kodekleri entegre edilmiştir. Bu sayede düşük bant genişliğine sahip ağlarda bile transcodings (kodek dönüştürme) işlemlerini donanım seviyesinde optimize eder.
2.  **PostgreSQL 15 (Single Source of Truth):**
    *   Asterisk'in tüm çalışma zamanı (runtime) parametrelerini (Dahililer, Dış Hatlar, Dialplan kuralları, Çağrı Kuyrukları) saklar.
    *   Asterisk tarafından üretilen CDR (Call Detail Record), CEL (Call Event Logging) ve çağrı merkezi kuyruk loglarını (`queue_log`) depolar.
    *   API katmanının yaptığı tüm ekleme/güncelleme işlemleri doğrudan buraya yansır ve Asterisk bu değişiklikleri reload gerektirmeden anında okur.
3.  **FastAPI (Management API / API-First Layer):**
    *   Sistem üzerinde programatik kontrol sağlar. Santral yöneticilerinin Asterisk CLI veya veritabanı sorgularıyla uğraşmadan dahilileri, kuyrukları, dialplan rotalarını yönetmesini sağlayan modern bir arayüzdür.
    *   **API-First** prensibiyle tasarlanmıştır. Bu sayede üzerine kolayca bir web arayüzü (React, Next.js vb.) veya mobil uygulama inşa edilebilir.

---

## 2. Docker Compose Orkestrasyonu

Sistem, `./docker-compose.yml` dosyası aracılığıyla yönetilen üç bağımsız servisten oluşur.

### 2.1. docker-compose.yml İncelemesi
Servislerin tanımları ve kullanılan kaynak limitleri şu şekildedir:

*   **db (PostgreSQL 15):**
    *   Görsel imaj: `postgres:15-alpine` (hafif ve kararlı).
    *   Veri kalıcılığı için `db_data` adında bir Docker volume'u kullanır.
    *   Başlangıçta veritabanı şemasını otomatik oluşturmak için `./db/init.sql` dosyasını `/docker-entrypoint-initdb.d/init.sql` dizinine mount eder.
    *   Kaynak Sınırları: Max 1 CPU ve 1GB Bellek (Reserve: 512MB).
*   **asterisk (Asterisk 20):**
    *   Yerel `./asterisk` dizinindeki Dockerfile ile derlenir.
    *   Database hazır olmadan başlamaması için `db` servisinin `service_healthy` durumuna bağımlıdır (`depends_on`).
    *   Asterisk'in konfigürasyon dosyaları, ODBC sürücü tanımları (`odbc.ini`, `odbcinst.ini`) ana bilgisayardan (host) container içine mount edilir.
    *   Kaynak Sınırları: Max 2 CPU ve 2GB Bellek (Reserve: 1GB). Ses işleme gecikmeye hassas olduğundan kaynakları cömert tutulmuştur.
*   **api (FastAPI):**
    *   Yerel `./api` dizinindeki Dockerfile ile Python 3.11 tabanlı imajdan derlenir.
    *   Aynı şekilde veritabanının sağlıklı çalışıyor olmasına bağımlıdır.
    *   Dış dünyaya `8000` portunu açar.
    *   Kaynak Sınırları: Max 0.5 CPU ve 512MB Bellek (Reserve: 256MB).

---

## 3. Ağ (Network) Yapısı ve Host Mode Tercihi

Ağ tasarımı, bu stack'in en kritik bölümüdür. `docker-compose.yml` içinde `asterisk` servisi için `network_mode: "host"` tanımı yapılmıştır.

### 3.1. Neden Host Network Modu?
Docker'ın varsayılan köprü (bridge) ağ modu, HTTP gibi tek port üzerinden çift yönlü TCP trafiği yürüten servisler için uygundur. Ancak VoIP (Voice over IP) dünyasında durum farklıdır:
1.  **Sinyalleşme ve Medya Ayrımı:** SIP protokolü sinyalleşme için varsayılan olarak `5060` portunu (UDP/TCP) kullanırken, ses paketleri (RTP) dinamik olarak belirlenen geniş bir port aralığından (`10000 - 20000` veya projedeki ayara göre `10000 - 10100`) akar.
2.  **Docker NAT ve SDP Problemleri:** Docker bridge modunda, container içindeki Asterisk dış dünyadaki istemcinin IP adresini ve kendi dış IP adresini tam olarak bilemez. SIP paketlerinin gövdesinde bulunan SDP (Session Description Protocol) bilgisine yanlış IP'ler yazılır. Bu durum **"Tek Yönlü Ses (One-Way Audio)"** veya çağrı kurulur kurulmaz **"Sessizlik / Çağrının Düşmesi"** sorunlarına yol açar.
3.  **Port Eşleştirme Yükü:** Binlerce UDP portunu bridge modda host üzerine map etmek (`-p 10000-10100:10000-10100/udp`) Docker proxy süreçlerinin aşırı RAM tüketmesine ve performans kaybına neden olur.

**Çözüm:** `network_mode: "host"` kullanılarak Asterisk container'ı doğrudan ana makinenin (host) ağ arayüzünü (interface) kullanır. Bu sayede Docker NAT katmanı tamamen devre dışı kalır; paket kayıpları önlenir ve SDP içinde doğru IP adresleri taşınır.

### 3.2. Servisler Arası İletişim Akışı
*   **Asterisk -> Database İletişimi:** Asterisk host modda çalıştığından ve veritabanı portu host üzerine map edildiğinden (`5432:5432`), Asterisk veritabanına localhost üzerinden erişir. Bu nedenle `asterisk/odbc.ini` dosyasında `Servername = 127.0.0.1` olarak tanımlanmıştır.
*   **FastAPI -> Database İletişimi:** API servisi varsayılan Docker bridge ağında çalışır. Bu nedenle veritabanına erişirken `db` servis adını kullanır (örn. `postgresql://asterisk:asterisk@db:5432/asterisk`).
*   **İstemci -> FastAPI İletişimi:** Geliştirici veya arayüz API'ye `http://localhost:8000` üzerinden standart Docker port yönlendirmesiyle erişir.

---

## 4. Ortam Değişkenleri (.env) Yapısı

Stack'in esnekliği `.env` dosyası üzerinden sağlanır. Şablon dosya `.env.example` şu şekildedir:

```env
# PostgreSQL Configuration (Database Container Parametreleri)
POSTGRES_DB=asterisk
POSTGRES_USER=asterisk
POSTGRES_PASSWORD=asterisk_strong_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# API Configuration (FastAPI Bağlantı Stringi)
DATABASE_URL=postgresql://asterisk:asterisk_strong_password@db:5432/asterisk

# Asterisk Configuration (Asterisk ODBC Bağlantısı)
ASTERISK_DB_USER=asterisk
ASTERISK_DB_PASS=asterisk_strong_password
```

> [!IMPORTANT]
> Güvenlik nedeniyle, canlı ortama geçiş yaparken `.env` dosyasındaki default şifreleri (`asterisk_strong_password`) mutlaka karmaşık şifrelerle değiştirmeniz gerekir. `.env` üzerindeki şifre değiştiğinde hem DB container'ı, hem API, hem de Asterisk container'ları bu bilgiyi Docker Compose üzerinden otomatik olarak devralır.
