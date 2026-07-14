# Chapter 4: FastAPI Yönetim Arayüzü ve API Mimarisi

Bu bölümde, API katmanının teknik mimarisi, veritabanı bağlantı havuzu (connection pool) yönetimi, veri modelleri (Pydantic schemas) ve API endpoint'lerinin detaylı çalışma mantığı incelenmektedir.

---

## 1. API Katmanının Genel Tasarımı ve Bağlantı Havuzu

FastAPI, PBX stack'ine programatik bir kontrol katmanı ekleyerek yapıyı **API-First** hale getirir. Tüm iş mantığı (business logic) Python tabanlı FastAPI backend'inde yürütülür ve ilişkisel veritabanı üzerinden Asterisk'e yansıtılır.

### 1.1. Veritabanı Bağlantı Havuzu: [database.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/database.py)
API, yüksek eş zamanlı istek yüklerini kaldırabilmek için doğrudan veritabanı bağlantısı açıp kapatmak yerine `psycopg2.pool.SimpleConnectionPool` bağlantı havuzu modelini kullanır:
*   Havuz boyutu minimum `1`, maksimum `10` adet aktif bağlantı olacak şekilde sınırlandırılmıştır.
*   **Hata Toleransı (Retry Logic):** Havuz başlatılırken ve veritabanına bağlanırken geçici ağ kopmalarına karşı 10 denemeli (2'şer saniye aralıklı) bir otomatik yeniden bağlanma mekanizması kurgulanmıştır.
*   **Bağlantı Yönetimi:** Her HTTP isteği başladığında `get_db_conn()` ile havuzdan bir bağlantı çekilir ve işlem bittiğinde `release_db_conn(conn)` ile bağlantı havuza güvenli bir şekilde iade edilir.

---

## 2. API Veri Modelleri (Pydantic Schemas)

Sistemdeki tüm veri doğrulama (validation) kuralları `api/schemas.py` içinde tanımlanmıştır.

### 2.1. Extension Şemaları (`ExtensionCreate` & `ExtensionUpdate`)
Dahili oluştururken gönderilen veriler:
```python
class ExtensionCreate(BaseModel):
    ext_id: str = "1001"
    password: str = "pass123"
    context: str = "from-internal"
    moh_suggest: Optional[str] = "default"
    allow_transfer: bool = True
    mailboxes: Optional[str] = None
    named_call_group: Optional[str] = None
    named_pickup_group: Optional[str] = None
    dnd_enabled: bool = False
    allow: Optional[str] = "opus,ulaw,alaw,h264,vp8"
    disallow: Optional[str] = "all"
    # Kodek Boolean Bayrakları
    codec_ulaw: bool = True
    codec_alaw: bool = True
    codec_g729: bool = False
    codec_h264: bool = True
    codec_opus: bool = False
    codec_vp8: bool = False
    codec_priority: Optional[str] = "h264,ulaw,alaw"
```

---

## 3. API Routers ve İş Mantığı (Business Logic)

### 3.1. Dahili Yönetimi ([extensions.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/extensions.py))
Bir dahili oluşturulduğunda (`POST /extensions/`), API tek bir veritabanı transaction'ı içinde 3 farklı tabloya kayıt yazar:
1.  `ps_aors`: Maksimum cihaz bağlantı limitini 5 olarak belirleyen AOR kaydı.
2.  `ps_auths`: Dahili numarası ve SIP şifresini barındıran doğrulama kaydı.
3.  `ps_endpoints`: Bağlam, müzik sınıfı ve çağrı transfer izinlerini barındıran temel profil kaydı.

#### Kodek Derleme Mantığı (`compile_allow_string`):
Asterisk'in anladığı kodek formatı virgülle ayrılmış bir string'dir (Örn: `g729,alaw,ulaw`). API, boolean alanlar ve öncelik sıralamasına göre bu string'i otomatik olarak derler:
*   Arayüzden aktif edilen kodekler listelenir (Örn: ulaw, alaw, g729).
*   `codec_priority` içindeki öncelik sıralamasına (örn: `g729,alaw`) göre kodekler sıralanır. Sıralamada belirtilmeyen kodekler en sona itilir.
*   Ortaya çıkan string `allow` kolonuna yazılır.

### 3.2. Dış Hat Yönetimi ([trunks.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/trunks.py))
Dış hat tanımları `ps_registrations` tablosuna yazılır:
*   `server_uri`: Karşı operatörün SIP host adresi (`sip:sip.provider.com`).
*   `client_uri`: Dış hatta kaydolacak kullanıcı adı ve sunucu bilgisi (`sip:username@sip.provider.com`).
*   > [!IMPORTANT]
> Hatırlatma: Asterisk tarafında `res_pjsip_outbound_registration.so` modülü `noload` yapıldığı için dış hat kaydı oluşturulsa dahi Asterisk karşı operatöre REGISTER isteği göndermez. Dış hatları kullanmak için bu modülün `modules.conf` üzerinden aktif edilmesi gerekir.

### 3.3. Dialplan Yönetimi ([dialplan.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/dialplan.py))
`extensions` tablosuna doğrudan CRUD işlemlerini gerçekleştirir:
*   Arama rotaları ve bu rotaların öncelikleri (`priority`), çalıştıracağı uygulamalar (`app`: Dial, Playback, Hangup vb.) ve parametreleri (`appdata`) veritabanına eklenir.

### 3.4. Çağrı Merkezleri ve Kuyruklar ([queues.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/queues.py))
Kuyruk (`queues`) oluşturulmasını ve bu kuyruklara ajan (`queue_members`) eklenmesini yönetir:
*   Ajan eklenirken otomatik olarak `kuyruk_adi_ajan_arayuzu` biçiminde (örn: `support_PJSIP_1001`) tekil bir `uniqueid` oluşturulur. Bu kimlik, çağrı analitiklerinde ajanın performansını izlemek için kullanılır.

### 3.5. İzleme ve Dashboard Hizmetleri ([dashboard.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/dashboard.py) & [monitoring.py](file:///Users/ilkermansur/Desktop/gadget_pbx/api/routers/monitoring.py))
Santral durumunu izlemek için kullanılan iki temel endpoint bulunur:

#### 1. Hizmet Sağlık Durumları (`GET /dashboard/services`):
Veritabanı bağlantı hızını test eder. Asterisk'in çalışıp çalışmadığını ise şu portlara TCP socket bağlantısı deneyerek kontrol eder:
*   `5060` (SIP Portu)
*   `8088` (ARI Portu)
*   `5038` (AMI Portu)

#### 2. Dahili Durum İzleme (`GET /monitoring/peers`):
Bir dahili cihazın online olup olmadığını anlamak için veritabanında PJSIP endpoint tablosu ile aktif kontak tablosunu (`ps_contacts`) LEFT JOIN ile birleştirir:
```sql
SELECT 
    e.id as extension,
    e.context,
    CASE WHEN c.id IS NOT NULL THEN 'online' ELSE 'offline' END as status,
    c.user_agent,
    c.uri as ip_address
FROM ps_endpoints e
LEFT JOIN ps_contacts c ON c.id LIKE e.id || '%'
```
Cihaz REGISTER isteği gönderdiğinde `ps_contacts` tablosuna veri yazılacağı için, join sonucunda kontak kaydı olanlar **online**, olmayanlar **offline** olarak işaretlenir.
