# Chapter 2: Asterisk 20 Derleme ve Sürücü Yapılandırması

Bu bölümde, Asterisk 20 PBX sisteminin Debian 12 (Slim) tabanında kaynak koddan derlenme aşamaları, ses kodeklerinin (Opus & G.729) entegrasyonu ve UnixODBC sürücü ayarları detaylandırılmıştır.

---

## 1. Kaynak Koddan Derleme Süreci

Santralin performansı, en az bağımlılıkla ve sadece ihtiyaç duyulan modüllerle optimize edilmiş bir şekilde çalışmasına bağlıdır. Bu amaçla sistem, Docker üzerinde Debian 12 (slim) imajı üzerine sıfırdan inşa edilir.

### 1.1. Bağımlılıkların Kurulumu
Dockerfile içindeki birinci adımda, derleme araçları (`build-essential`, `cmake`, `autoconf`) ile birlikte Asterisk ve odbc bağımlılıkları yüklenir:
*   `libopus-dev` (Opus kodek desteği için)
*   `libbcg729-dev` (G.729 kodek kütüphanesi için)
*   `unixodbc-dev` ve `odbc-postgresql` (PostgreSQL ODBC sürücüleri ve başlık dosyaları)
*   `libpq-dev` (Native PostgreSQL client kütüphanesi)
*   `sngrep`, `tcpdump`, `tshark` (VoIP paket analiz araçları - Hata ayıklama için imaja dahil edilmiştir)

### 1.2. Asterisk 20 ve PJProject İndirme
Asterisk, gömülü SIP yığını (SIP Stack) olarak **PJSIP**'i kullanır. Derleme sırasında ağ hatalarını ve indirme başarısızlıklarını önlemek için `pjproject` tarball dosyası önceden `/tmp` dizinine indirilir:
```dockerfile
RUN wget --no-check-certificate https://raw.githubusercontent.com/asterisk/third-party/master/pjproject/2.15.1/pjproject-2.15.1.tar.bz2 -P /tmp/
```

### 1.3. Konfigürasyon ve Menuselect
Asterisk derleme parametreleri şu şekildedir:
```bash
./configure --with-pjproject-bundled --with-ssl --with-crypto --with-odbc --with-postgres
```
*   `--with-pjproject-bundled`: PJProject'in Asterisk içindeki gömülü ve test edilmiş versiyonunun kullanılmasını zorunlu kılar.
*   `--with-odbc` & `--with-postgres`: Veritabanı realtime entegrasyonu için gerekli ODBC motorunu ve native Postgres sürücüsünü etkinleştirir.

Konfigürasyon sonrası `menuselect` aracılığıyla Opus ses kodeği derleme şablonuna eklenir:
```bash
make menuselect.makeopts
menuselect/menuselect --enable codec_opus menuselect.makeopts
make -j$(nproc) && make install
```

---

## 2. G.729 Kodek Entegrasyonu

**G.729**, VoIP dünyasında ses kalitesini korurken bant genişliğini 8 Kbps'e kadar düşüren (ulaw/alaw kodeklerine göre yaklaşık 8 kat daha az bant genişliği kullanan) endüstri standardı lisanslı bir ses kodeğidir.

### 2.1. asterisks-g72x Derlemesi
Asterisk çekirdeğinde g729 lisans kısıtlamaları nedeniyle derlenmiş olarak gelmez. Bu projede açık kaynaklı vebcg729 tabanlı transcoders modülü (`arkadijs/asterisk-g72x`) kullanılmıştır. Derleme adımları:
1.  Github'dan güncel kaynak kod indirilir.
2.  `bcg729` kütüphanesi referans verilerek konfigüre edilir:
    ```bash
    ./configure --with-bcg729 CPPFLAGS="-I/usr/src/asterisk/include"
    ```
3.  Derlenip Asterisk'in modül dizinine (`/usr/lib/asterisk/modules/codec_g729.so`) kurulur:
    ```bash
    make && make install
    ```
Bu işlem sonucunda Asterisk, ses paketlerini G.729 formatından Opus, alaw veya ulaw formatlarına gerçek zamanlı olarak dönüştürebilir hale gelir (Transcoding).

---

## 3. UnixODBC ve PostgreSQL Sürücü Entegrasyonu

Asterisk ile PostgreSQL arasındaki köprüyü **unixODBC** kurar. unixODBC, veritabanından bağımsız bir SQL API arayüzü sunar.

### 3.1. Çoklu Mimari (Multi-Arch) Desteği
Dockerfile derleme yapılan ana makinenin mimarisini (Apple Silicon/ARM64 veya Intel/x86_64) otomatik olarak algılar ve uygun kütüphane yolunu belirler:
```dockerfile
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then LIB_DIR="x86_64-linux-gnu"; \
    elif [ "$ARCH" = "aarch64" ]; then LIB_DIR="aarch64-linux-gnu"; fi && \
    apt-get update && apt-get install -y odbc-postgresql && \
    ln -s /usr/lib/$LIB_DIR/odbc/psqlodbcw.so /usr/lib/psqlodbcw.so
```
Bu sayede, PostgreSQL Unicode sürücüsü (`psqlodbcw.so`) `/usr/lib/psqlodbcw.so` yoluna sembolik linklenerek standartlaştırılır.

### 3.2. Sürücü ve DSN Yapılandırması
Sistem düzeyinde odbc bağlantıları iki dosyayla tanımlanır:

#### 1. [odbcinst.ini](file:///Users/ilkermansur/Desktop/gadget_pbx/asterisk/odbcinst.ini)
ODBC sürücüsünün (driver) sistemdeki yerini tanımlar:
```ini
[PostgreSQL Unicode]
Description=PostgreSQL ODBC driver (Unicode version)
Driver=/usr/lib/psqlodbcw.so
Setup=/usr/lib/psqlodbcw.so
UsageCount=1
```

#### 2. [odbc.ini](file:///Users/ilkermansur/Desktop/gadget_pbx/asterisk/odbc.ini)
Veritabanı bağlantı parametrelerini (DSN - Data Source Name) tanımlar:
```ini
[asterisk]
Description         = PostgreSQL connection to 'asterisk' database
Driver              = PostgreSQL Unicode
Database            = asterisk
Servername          = 127.0.0.1
UserName            = asterisk
Password            = asterisk
Port                = 5432
```
*   **Kritik Not:** Asterisk container'ı `network_mode: "host"` kullandığından, ana bilgisayarın port yayınındaki veritabanına erişmek için `Servername` parametresi `127.0.0.1` olarak set edilmiştir.

---

## 4. Asterisk ODBC Realtime Bağlantısı

Sistem katmanındaki ODBC ayarlarının Asterisk içine aktarılması `res_odbc.conf` ve `res_config_odbc.conf` dosyalarıyla sağlanır.

### 4.1. Bağlantı Havuzu Yapılandırması: [res_odbc.conf](file:///Users/ilkermansur/Desktop/gadget_pbx/asterisk/res_odbc.conf)
Asterisk'in veritabanı bağlantı havuzunu ve kimlik bilgilerini yönetir:
```ini
[asterisk]
enabled => yes
dsn => asterisk
username => ${ENV(ASTERISK_DB_USER)}
password => ${ENV(ASTERISK_DB_PASS)}
pre-connect => yes
```
*   `username` ve `password` parametreleri doğrudan container'a enjekte edilen ortam değişkenlerinden (`ASTERISK_DB_USER` ve `ASTERISK_DB_PASS`) dinamik olarak okunur.
*   `pre-connect => yes`: Asterisk başlar başlamaz veritabanına hazırda bekleyen bağlantılar açar, ilk çağrıda gecikme olmasını engeller.

### 4.2. Tablo Eşleştirmesi: [res_config_odbc.conf](file:///Users/ilkermansur/Desktop/gadget_pbx/asterisk/res_config_odbc.conf)
Veritabanındaki tabloların hangi ODBC DSN bağlantısı üzerinden sorgulanacağını belirler:
```ini
[asterisk]
dbstrategy => optimize

; PJSIP
ps_endpoints => asterisk,ps_endpoints
ps_auths => asterisk,ps_auths
ps_aors => asterisk,ps_aors
...
```
*   `dbstrategy => optimize`: Asterisk'in veritabanı sorgularını önbelleklemesini ve minimize edilmiş sorgular üretmesini sağlar.
*   `ps_endpoints => asterisk,ps_endpoints`: Sol taraftaki tablo ailesi adını, sağ taraftaki `[DSN_ADI],[VERITABANI_TABLO_ADI]` formatına eşler.
