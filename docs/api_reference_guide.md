# GadgetPBX Management API - Reference Guide

Bu rehber, FastAPI tabanlı GadgetPBX Yönetim API'sinin tüm endpoint'lerini, parametrelerini, beklenen veri şemalarını ve dönüş formatlarını detaylandırmaktadır. 

API'ye yerel ortamda varsayılan olarak `http://localhost:8000` adresinden, etkileşimli Swagger dokümantasyonuna ise `http://localhost:8000/docs` adresinden erişebilirsiniz.

---

## 1. Genel / Sistem Durumu (System & Status)

### Root
*   **Endpoint:** `GET /`
*   **Amaç:** API'nin çevrimiçi olup olmadığını hızlıca kontrol etmek için kullanılır.
*   **Response (200 OK):**
    ```json
    {
      "message": "Welcome to GadgetPBX Management API",
      "status": "online"
    }
    ```

### Sistem Sağlık Durumu
*   **Endpoint:** `GET /status`
*   **Amaç:** API katmanının ve veritabanı (PostgreSQL) bağlantısının durumunu raporlar.
*   **Response (200 OK):**
    ```json
    {
      "database": "online", // "offline" veya "error: [detay]"
      "version": "1.0.0"
    }
    ```

---

## 2. Dahili Yönetimi (Extensions)

PJSIP Dahili profillerinin (AOR, Auth, Endpoint) tam yaşam döngüsünü yönetir.

### Dahilileri Listele
*   **Endpoint:** `GET /extensions/`
*   **Amaç:** Sistemdeki tüm kayıtlı PJSIP dahililerini listeler.
*   **Response (200 OK):**
    ```json
    [
      {
        "id": "1001",
        "context": "from-internal",
        "moh_suggest": "default",
        "allow_transfer": "yes",
        "mailboxes": "1001@default",
        "named_call_group": "sales",
        "named_pickup_group": "sales",
        "dnd_enabled": false,
        "codec_ulaw": true,
        "codec_alaw": true,
        "codec_g729": false,
        "codec_h264": true,
        "codec_opus": false,
        "codec_vp8": false,
        "codec_priority": "h264,ulaw,alaw"
      }
    ]
    ```

### Dahili Detayı
*   **Endpoint:** `GET /extensions/{ext_id}`
*   **Path Parametresi:** `ext_id` (string - Dahili numarası, örn: `1001`)
*   **Response (200 OK):** Seçilen dahiliye ait tekil detay objesini döner. Bulunamadıysa `404 Not Found` hatası verir.

### Dahili Oluştur
*   **Endpoint:** `POST /extensions/`
*   **Request Body (ExtensionCreate - JSON):**
    *   `ext_id` (string, zorunlu): Dahili numara (Örn: `"1001"`)
    *   `password` (string, zorunlu): SIP şifresi (Örn: `"pass123"`)
    *   `context` (string, default: `"from-internal"`): Aramaların çıkış yapacağı dialplan context'i.
    *   `moh_suggest` (string, optional, default: `"default"`): Dinletilecek bekleme müziği sınıfı.
    *   `allow_transfer` (boolean, default: `true`): Dahilinin çağrı aktarma yetkisi.
    *   `mailboxes` (string, optional): Telesekreter kutusu eşleşmesi (Örn: `"1001@default"`).
    *   `named_call_group` / `named_pickup_group` (string, optional): Çağrı yakalama grubu tanımları.
    *   `dnd_enabled` (boolean, default: `false`): Rahatsız Etmeyin modu.
    *   `allow` (string, optional): Doğrudan izin verilen kodek listesi. Boş bırakılırsa boolean bayraklardan derlenir.
    *   `codec_ulaw` / `codec_alaw` / `codec_h264` (boolean, default: `true`): Kodek izinleri.
    *   `codec_g729` / `codec_opus` / `codec_vp8` (boolean, default: `false`): Kodek izinleri.
    *   `codec_priority` (string, default: `"h264,ulaw,alaw"`): Kodeklerin öncelik sıralaması.
*   **Response (200 OK):**
    ```json
    {
      "message": "Extension 1001 created successfully"
    }
    ```

### Dahili Güncelle (PATCH)
*   **Endpoint:** `PATCH /extensions/{ext_id}`
*   **Path Parametresi:** `ext_id` (string)
*   **Request Body (ExtensionUpdate - JSON):** `ExtensionCreate` içindeki tüm alanlar isteğe bağlı (optional) olarak gönderilebilir. Sadece gönderilen alanlar veritabanında güncellenir.
*   **Response (200 OK):** `{"message": "Extension 1001 updated"}`

### Dahili Sil
*   **Endpoint:** `DELETE /extensions/{ext_id}`
*   **Path Parametresi:** `ext_id` (string)
*   **Amaç:** Dahiliyi veritabanından kalıcı olarak siler (`ps_endpoints`, `ps_auths` ve `ps_aors` tablolarındaki tüm ilişkili kayıtlar silinir).
*   **Response (200 OK):** `{"message": "Extension 1001 deleted"}`

---

## 3. Dış Hat Yönetimi (Trunks)

### Dış Hatları Listele
*   **Endpoint:** `GET /trunks/`
*   **Response (200 OK):**
    ```json
    [
      {
        "id": "provider_trunk",
        "server_uri": "sip:sip.provider.com",
        "client_uri": "sip:username@sip.provider.com"
      }
    ]
    ```

### Dış Hat Oluştur
*   **Endpoint:** `POST /trunks/`
*   **Request Body (TrunkCreate - JSON):**
    *   `trunk_id` (string, zorunlu): Dış hat benzersiz kimliği (Örn: `"my_provider"`)
    *   `host` (string, zorunlu): Karşı SIP sunucu adresi (Örn: `"sip.provider.com"`)
    *   `username` (string, optional): Dış hat kullanıcı adı.
    *   `password` (string, optional): Dış hat şifresi.
*   **Response (200 OK):** `{"message": "Trunk my_provider created"}`

### Dış Hat Güncelle
*   **Endpoint:** `PATCH /trunks/{trunk_id}`
*   **Request Body (TrunkUpdate - JSON):** `host`, `username`, `password` alanları isteğe bağlı olarak güncellenebilir.
*   **Response (200 OK):** `{"message": "Trunk my_provider updated"}`

### Dış Hat Sil
*   **Endpoint:** `DELETE /trunks/{trunk_id}`
*   **Response (200 OK):** `{"message": "Trunk my_provider deleted"}`

---

## 4. Dinamik Dialplan Yönetimi (Dialplan)

Arama kurallarını ve yönlendirmelerini (Asterisk `extensions` tablosu) yönetir.

### Rotaları Listele
*   **Endpoint:** `GET /dialplan/`
*   **Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "context": "from-internal",
        "exten": "1000",
        "priority": 1,
        "app": "Answer",
        "appdata": ""
      }
    ]
    ```

### Rota Detayı
*   **Endpoint:** `GET /dialplan/{route_id}`
*   **Path Parametresi:** `route_id` (integer - Tablodaki otomatik artan birincil anahtar ID)

### Rota Oluştur
*   **Endpoint:** `POST /dialplan/`
*   **Request Body (RouteCreate - JSON):**
    *   `context` (string, zorunlu): Yönlendirmenin geçerli olacağı grup (Örn: `"from-internal"`)
    *   `exten` (string, zorunlu): Aranan numara veya regex şablonu (Örn: `"100"`)
    *   `priority` (integer, default: `1`): Öncelik/adım sırası.
    *   `app` (string, zorunlu): Çalıştırılacak Asterisk uygulaması (Örn: `"Dial"`, `"Playback"`, `"Hangup"`)
    *   `appdata` (string, optional): Uygulama parametreleri (Örn: `"PJSIP/1001"`)
*   **Response (200 OK):** `{"message": "Route created"}`

### Rota Güncelle
*   **Endpoint:** `PATCH /dialplan/{route_id}`
*   **Request Body (RouteUpdate - JSON):** `context`, `exten`, `priority`, `app`, `appdata` alanları isteğe bağlı olarak gönderilerek güncellenebilir.
*   **Response (200 OK):** `{"message": "Route [id] updated"}`

### Rota Sil
*   **Endpoint:** `DELETE /dialplan/{route_id}`
*   **Response (200 OK):** `{"message": "Route [id] deleted"}`

---

## 5. Telesekreter Kutuları (Voicemail)

### Voicemail Kutularını Listele
*   **Endpoint:** `GET /voicemail/`
*   **Response (200 OK):**
    ```json
    [
      {
        "uniqueid": 1,
        "context": "default",
        "mailbox": "1001",
        "fullname": "Ahmet Yilmaz",
        "email": "ahmet@firma.com"
      }
    ]
    ```

### Voicemail Detayı
*   **Endpoint:** `GET /voicemail/{mailbox}`
*   **Query Parametresi:** `context` (string, default: `"default"`)
*   **Response (200 OK):** Telesekreter kutusunun tüm detay ayarlarını döner.

### Voicemail Oluştur
*   **Endpoint:** `POST /voicemail/`
*   **Request Body (VoicemailCreate - JSON):**
    *   `mailbox` (string, zorunlu): Telesekreter kutusu numarası (Örn: `"1001"`)
    *   `context` (string, zorunlu, default: `"default"`): Bağlam.
    *   `password` (string, zorunlu): Telesekreter kutusuna girerken girilecek PIN şifresi (Örn: `"1234"`)
    *   `fullname` (string, optional): Kullanıcı adı.
    *   `email` (string, optional): Bildirimlerin gönderileceği e-posta adresi.
*   **Response (200 OK):** `{"message": "Voicemail box 1001 created successfully"}`

### Voicemail Güncelle
*   **Endpoint:** `PATCH /voicemail/{mailbox}`
*   **Query Parametresi:** `context` (string, default: `"default"`)
*   **Request Body (VoicemailUpdate - JSON):** `password`, `fullname`, `email` alanları opsiyonel olarak güncellenebilir.
*   **Response (200 OK):** `{"message": "Voicemail box 1001 updated"}`

### Voicemail Sil
*   **Endpoint:** `DELETE /voicemail/{mailbox}`
*   **Query Parametresi:** `context` (string, default: `"default"`)
*   **Response (200 OK):** `{"message": "Voicemail box 1001 deleted"}`

---

## 6. Kuyruklar & Ajanlar (Queues)

Çağrı merkezi sıraları ve bu sıraları cevaplayacak ajan tanımlarını yönetir.

### Kuyrukları Listele
*   **Endpoint:** `GET /queues/`
*   **Response (200 OK):** Tüm kuyruk ayarlarını ve dağıtım stratejilerini içeren listeyi döner.

### Kuyruk Oluştur
*   **Endpoint:** `POST /queues/`
*   **Request Body (QueueCreate - JSON):**
    *   `name` (string, zorunlu): Kuyruk adı (Örn: `"destek_kuyrugu"`)
    *   `musiconhold` (string, default: `"default"`): Bekleme müziği.
    *   `strategy` (string, default: `"ringall"`): Dağıtım stratejisi (`ringall`, `leastrecent`, `fewesthits`, `random`, `rrmemory`).
    *   `timeout` (integer, default: `15`): Bir ajanın telefonu çalma süresi (saniye).
    *   `joinempty` (string, default: `"yes"`): Sırada ajan yoksa çağrı kabul edilsin mi? (`yes`/`no`).
*   **Response (200 OK):** `{"message": "Queue destek_kuyrugu created"}`

### Kuyruk Sil
*   **Endpoint:** `DELETE /queues/{name}`
*   **Amaç:** Kuyruğu ve o kuyruğa atanmış tüm ajanları (members) sistemden siler.
*   **Response (200 OK):** `{"message": "Queue destek_kuyrugu deleted"}`

### Ajanları Listele
*   **Endpoint:** `GET /queues/{name}/members`
*   **Amaç:** Seçilen kuyruğa bağlı tüm ajanları listeler.
*   **Response (200 OK):**
    ```json
    [
      {
        "queue_name": "destek_kuyrugu",
        "interface": "PJSIP/1001",
        "uniqueid": "destek_kuyrugu_PJSIP_1001",
        "membername": "Musteri Temsilcisi 1",
        "penalty": 0,
        "paused": 0
      }
    ]
    ```

### Ajan Ekle
*   **Endpoint:** `POST /queues/{name}/members`
*   **Request Body (QueueMemberAdd - JSON):**
    *   `interface` (string, zorunlu): Ajan kanalı (Örn: `"PJSIP/1001"`)
    *   `membername` (string, optional): Ajanın adı (Örn: `"Ahmet"`)
    *   `penalty` (integer, default: `0`): Ajan önceliği (Düşük penaltıya sahip olan ajanın telefonu öncelikli çalar).
*   **Response (200 OK):** `{"message": "Member PJSIP/1001 added to queue destek_kuyrugu"}`

---

## 7. Kara Liste (Blacklist)

İstenmeyen aramaları engellemek için kullanılan numaraları yönetir.

### Kara Listeyi Görüntüle
*   **Endpoint:** `GET /blacklist/`
*   **Response (200 OK):**
    ```json
    [
      {
        "number": "5551234567",
        "note": "Spam arama",
        "created_at": "2026-07-14 13:40:00"
      }
    ]
    ```

### Kara Listeye Numara Ekle
*   **Endpoint:** `POST /blacklist/`
*   **Request Body (BlacklistEntry - JSON):**
    *   `number` (string, zorunlu): Engellenecek numara (Örn: `"5551234567"`)
    *   `note` (string, optional): Engelleme nedeni (Örn: `"Spam Arayici"`)
*   **Response (200 OK):** `{"message": "Number 5551234567 blacklisted"}`

### Kara Listeden Numara Sil
*   **Endpoint:** `DELETE /blacklist/{number}`
*   **Response (200 OK):** `{"message": "Number 5551234567 removed from blacklist"}`

---

## 8. Zaman Koşulları / Mesai Saatleri (Time Conditions)

### Zaman Koşullarını Listele
*   **Endpoint:** `GET /time-conditions/`

### Zaman Koşulu Oluştur
*   **Endpoint:** `POST /time-conditions/`
*   **Request Body (TimeConditionCreate - JSON):**
    *   `name` (string, zorunlu): Kural adı (Örn: `"Mesai Saatleri"`)
    *   `start_time` (string, zorunlu): Başlangıç saati (Örn: `"09:00"`)
    *   `end_time` (string, zorunlu): Bitiş saati (Örn: `"18:00"`)
    *   `weekdays` (string, zorunlu): Gün aralığı (Örn: `"1-5"` - Pazartesi-Cuma)
    *   `match_context` (string, zorunlu): Koşul uyduğunda çağrının gideceği context (Örn: `"from-internal"`)
    *   `mismatch_context` (string, zorunlu): Koşul uymadığında (mesai dışı) gideceği context (Örn: `"after-hours"`)
*   **Response (200 OK):** `{"message": "Time condition 'Mesai Saatleri' created"}`

### Zaman Koşulu Sil
*   **Endpoint:** `DELETE /time-conditions/{tc_id}`
*   **Response (200 OK):** `{"message": "Time condition [id] deleted"}`

---

## 9. Hunt Grupları / Ring Grupları (Hunt Pilots)

Birden çok dahiliyi aynı anda veya sırayla çaldırmak için kullanılan gruplardır.

### Hunt Gruplarını Listele
*   **Endpoint:** `GET /hunt-groups/`

### Hunt Grubu Oluştur
*   **Endpoint:** `POST /hunt-groups/`
*   **Request Body (HuntGroupCreate - JSON):**
    *   `name` (string, zorunlu): Hunt grubu adı (Örn: `"satis_grubu"`)
    *   `strategy` (string, zorunlu): Çalma stratejisi (`"simultaneous"` - hepsi birden, `"linear"` - sırayla)
    *   `members` (string, zorunlu): Virgülle ayrılmış dahili listesi (Örn: `"1001,1002,1003"`)
*   **Response (200 OK):** `{"message": "Hunt group 'satis_grubu' created"}`

### Hunt Grubu Güncelle
*   **Endpoint:** `PATCH /hunt-groups/{hg_id}`
*   **Request Body (HuntGroupUpdate - JSON):** `strategy`, `members` alanları isteğe bağlı güncellenebilir.

### Hunt Grubu Sil
*   **Endpoint:** `DELETE /hunt-groups/{hg_id}`

---

## 10. Canlı İzleme ve Raporlama (Monitoring & Reports)

### Cihaz Kayıt Durumları (Peers Status)
*   **Endpoint:** `GET /monitoring/peers`
*   **Amaç:** Dahililerin anlık olarak online/offline durumlarını, IP adreslerini ve cihaz marka/modellerini listeler.
*   **Response (200 OK):**
    ```json
    [
      {
        "extension": "1001",
        "context": "from-internal",
        "status": "online", // "online" veya "offline"
        "user_agent": "Yealink SIP-T31G",
        "ip_address": "sip:1001@192.168.1.50:5060"
      }
    ]
    ```

### Dashboard Servis Durumları
*   **Endpoint:** `GET /dashboard/services`
*   **Amaç:** Sistemdeki ana servislerin (Veritabanı ve Asterisk) anlık çalışma ve bağlantı hız durumlarını sorgular.
*   **Response (200 OK):**
    ```json
    [
      {
        "name": "Database",
        "status": "online",
        "latency_ms": 2.5
      },
      {
        "name": "Asterisk",
        "status": "online",
        "latency_ms": null
      }
    ]
    ```

### Dashboard Özet Raporu
*   **Endpoint:** `GET /dashboard/summary`
*   **Amaç:** Dashboard arayüzünde gösterilecek istatistikleri ve donanım kullanım yükünü döner.
*   **Response (200 OK):**
    ```json
    {
      "extensions_total": 10,
      "extensions_online": 3,
      "extensions_offline": 7,
      "trunks_total": 1,
      "trunks_online": 0,
      "active_calls": 0,
      "physical_phones": 2, // Yealink, Cisco vb. içeren kayıtlar
      "softphones": 1,      // Diğerleri
      "system_load": 0.35   // CPU yükü
    }
    ```

### CDR Arama Geçmişi (Call Detail Records)
*   **Endpoint:** `GET /reports/cdr`
*   **Amaç:** Sonlanan son 50 çağrının geçmişini listeler.
*   **Response (200 OK):**
    ```json
    [
      {
        "src": "1001",
        "dst": "1002",
        "duration": 45,
        "disposition": "ANSWERED",
        "start": "2026-07-14 13:40:00"
      }
    ]
    ```

### Kuyruk Olay Raporları (Queue Logs)
*   **Endpoint:** `GET /reports/queuelog`
*   **Amaç:** Çağrı merkezi kuyruklarında gerçekleşen son 50 olayı listeler.
*   **Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "time": "2026-07-14 13:41:00",
        "callid": "147589230.12",
        "queuename": "destek_kuyrugu",
        "agent": "PJSIP/1001",
        "event": "CONNECT",
        "data1": "10", // Bekleme süresi
        "data2": "147589230.12",
        "data3": "1",
        "data4": "",
        "data5": ""
      }
    ]
    ```
