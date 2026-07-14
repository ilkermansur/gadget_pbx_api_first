# Chapter 6: Sistemi Genişletme, Daraltma ve Hata Ayıklama Rehberi

Bu bölümde, projenin modüler yapısını bozmadan nasıl yeni özellikler ekleyebileceğiniz (genişletme), sistemi nasıl daha hafif hale getirebileceğiniz (daraltma) ve olası hataları nasıl teşhis edebileceğiniz (troubleshooting) anlatılmaktadır.

---

## 1. Sistemi Genişletme (Expanding the System)

GadgetPBX mimarisi, yeni standartlar ve özellikler eklemeyi kolaylaştırmak üzere tasarlanmıştır.

### 1.1. WebRTC Desteği Ekleme (Web Üzerinden Arama)
Kullanıcıların web tarayıcıları üzerinden (WebRTC / SIP.js kullanarak) ek bir yazılım yüklemeden arama yapabilmesi için:
1.  **Transport Eklenmesi:** `asterisk/pjsip.conf` dosyasında bir WebSocket transport'u tanımlanmalıdır:
    ```ini
    [transport-wss]
    type=transport
    protocol=wss
    bind=0.0.0.0:8089
    ```
2.  **Güvenli RTP (SRTP) ve DTLS Aktifleştirme:** Veritabanındaki `ps_endpoints` tablosunda ilgili endpoint için:
    *   `dtls_enable = 'yes'`
    *   `dtls_cert_file = '/etc/asterisk/keys/asterisk.pem'`
    *   `ice_support = 'yes'`
    *   `use_avpf = 'yes'`
    *   `rtp_symmetric = 'yes'`
    *   `force_rport = 'yes'`
    *   `rewrite_contact = 'yes'`
    değerleri set edilmelidir. API katmanındaki `ExtensionCreate` şemasına bu alanlar eklenerek otomatize edilebilir.

### 1.2. Ses Kaydı (Call Recording) Entegrasyonu
Tüm iç ve dış görüşmelerin kaydedilmesi isteniyorsa:
*   Dialplan kurallarına arama (`Dial`) işleminden hemen önce `MixMonitor` uygulaması yerleştirilmelidir.
*   **Veritabanı Dialplan Adımı Örneği:**
    *   `app`: `MixMonitor`
    *   `appdata`: `/var/spool/asterisk/monitor/${UNIQUEID}.wav,b`
*   Bu sayede Asterisk, ses kanalını cevaplandığı andan itibaren arka planda kaydedecek ve ses dosyasını benzersiz çağrı kimliği (`uniqueid`) adıyla diske yazacaktır.

### 1.3. ARI / AMI ile Gerçek Zamanlı Dashboard Aktifleştirme
Dashboard API'sinde anlık aktif çağrı sayısını ve trunk kayıt durumlarını görmek için:
1.  Asterisk üzerinde **ARI (Asterisk REST Interface)** aktif edilmelidir (`ari.conf`).
2.  FastAPI tarafına `ari` Python kütüphanesi (örn: `ari-py`) eklenmeli veya HTTP client ile Asterisk ARI portuna (`8088/ari/channels`) istek atılmalıdır.
3.  `GET /dashboard/summary` endpoint'i ARI'den dönen anlık kanal listesi sayısını okuyarak `active_calls` değerini dinamik olarak doldurabilir.

---

## 2. Sistemi Daraltma (Minimizing the System)

Sistem sadece basit bir dahili kayıt motoru (SIP Registrar) olarak kullanılacaksa ve kuyruk veya telesekreter gibi çağrı merkezi özelliklerine ihtiyaç duyulmuyorsa, kaynak tüketimini azaltmak için sistem daraltılabilir:

1.  **Modülleri Devre Dışı Bırakma:** `asterisk/modules.conf` içinde çağrı merkezi ve voicemail modülleri yüklenmemelidir:
    ```ini
    noload => app_queue.so
    noload => app_voicemail.so
    ```
2.  **Veritabanı Yükünü Azaltma:** `extconfig.conf` içinden queues, queue_members ve voicemail satırları kaldırılabilir. Böylece Asterisk açılışta ve çalışma sırasında bu tablolar için SQL sorgusu atmaz.
3.  **Hafif API:** FastAPI tarafında kullanılmayan `voicemail.py`, `queues.py` ve `hunt_groups.py` router'ları `api/main.py` içinden çıkarılabilir.

---

## 3. Hata Ayıklama ve Sorun Giderme (Troubleshooting)

Sistemde oluşabilecek sinyalleşme, veritabanı bağlantısı veya kodek sorunlarını çözmek için aşağıdaki CLI komutları ve araçlar kullanılmalıdır:

### 3.1. ODBC Bağlantı Sorunları (Database Connectivity)
Asterisk'in veritabanına bağlı olup olmadığını kontrol edin:
```bash
docker exec -it pbx-asterisk asterisk -rx "odbc show"
```
*   **Hata Belirtisi:** `Active connections: 0` veya bağlantı adı listelenmiyor.
*   **Çözüm:** `odbc.ini` içindeki kullanıcı adı/şifre ile `.env` dosyasındaki verilerin eşleştiğinden emin olun. Asterisk loglarında unixODBC sürücü yükleme hatası olup olmadığını kontrol edin (`docker logs pbx-asterisk | grep odbc`).

### 3.2. Realtime Tablo Sorgularını Test Etme
Asterisk'in veritabanındaki dahilileri veya dialplan'ı okuyup okumadığını test edin:
```bash
docker exec -it pbx-asterisk asterisk -rx "realtime load extensions exten 1000"
docker exec -it pbx-asterisk asterisk -rx "realtime load ps_endpoints id 1001"
```
*   Bu komutlar, veritabanından ilgili kaydı çekerek Asterisk'in gördüğü kolon-değer çiftlerini ekrana basar. Eğer veri dönmüyorsa Asterisk Realtime bağlantısı kurulamamıştır.

### 3.3. SIP Paketlerini ve Sinyalleşmeyi İzleme
Çağrıların neden kurulmadığını, kayıt (register) paketlerinin ulaşıp ulaşmadığını görmek için en güçlü araç **sngrep** aracıdır:
```bash
docker exec -it pbx-asterisk sngrep
```
*   **sngrep**, akan tüm SIP paketlerini yakalar, arama akış diyagramını çıkarır ve hata kodlarını (örn: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`) görselleştirerek hatanın nerede olduğunu gösterir.
*   Alternatif olarak Asterisk CLI içinden log açılabilir:
    ```bash
    docker exec -it pbx-asterisk asterisk -r
    pbx-asterisk*CLI> pjsip set logger on
    ```

### 3.4. Transcoding (Kodek Çevirici) Durumunu Doğrulama
G.729 veya Opus kodeklerinin aktif olup olmadığını ve birbirlerine dönüşüm gecikmelerini görmek için:
```bash
docker exec -it pbx-asterisk asterisk -rx "core show translation"
```
*   **Beklenen Durum:** Çıkan matriste `g729` ve `opus` satır/sütunlarının kesiştiği yerlerde sayısal milisaniye değerleri yer almalıdır. Eğer `-` işareti varsa, kodek modülü yüklenememiştir (derleme hatası veya modül eksikliği).

### 3.5. Dış Hat Kaydı (Trunk Registration) Sorunu Çözümü
Eğer dış hat tanımı yaptığınız halde arama gelmiyor veya gitmiyorsa:
1.  `asterisk/modules.conf` dosyasını açın.
2.  `noload => res_pjsip_outbound_registration.so` satırını silin veya `load => res_pjsip_outbound_registration.so` olarak değiştirin.
3.  Asterisk container'ını yeniden başlatın:
    ```bash
    docker-compose restart asterisk
    ```
4.  Kayıt durumunu kontrol edin:
    ```bash
    docker exec -it pbx-asterisk asterisk -rx "pjsip show registrations"
    ```
