# Akıllı Ev AI Agent Sistemi

Bu proje; sensör simülasyonu, MQTT haberleşmesi, yapay zekâ karar mekanizması, zaman serisi veritabanı, REST API, web arayüzü, Telegram bildirimleri ve Spotify entegrasyonunu birleştiren uçtan uca bir **AI destekli akıllı ev kontrol sistemi**dir.

Sistem temel olarak şu akışla çalışır:

```text
Simulator / Node-RED
        ↓
      MQTT
        ↓
AI Agent → InfluxDB
        ↓
FastAPI Backend
        ↓
React Mission Control Frontend
        ↓
Telegram / Spotify / Demo Dashboard
```

## Klasör Yapısı

```text
smarthome/
├── docker-compose.yml              ← Tüm servisleri başlatır
├── README.md                       ← Proje dokümantasyonu
├── mosquitto/
│   ├── config/mosquitto.conf       ← MQTT broker ayarları
│   ├── data/                       ← MQTT kalıcı veri
│   └── log/                        ← MQTT logları
├── nodered/                        ← Node-RED akışları ve dashboard altyapısı
├── influxdb/                       ← InfluxDB kalıcı verileri
├── backend/
│   ├── app/main.py                 ← FastAPI uygulaması
│   ├── app/routes/                 ← REST API endpointleri
│   ├── app/services/               ← MQTT, InfluxDB, oda ve entegrasyon servisleri
│   └── app/schemas/                ← Pydantic veri modelleri
├── frontend/
│   ├── src/App.jsx                 ← Ana React dashboard uygulaması
│   ├── src/services/api.js         ← Backend API bağlantıları
│   ├── src/components/             ← Dashboard bileşenleri
│   │   ├── Header.jsx              ← Mission Control hero + logo
│   │   ├── StatsBar.jsx            ← Mod, oda, alarm ve sağlık metrikleri
│   │   ├── DemoConsole.jsx         ← Demo senaryosu başlatıcı
│   │   ├── RoomGrid.jsx            ← Kart / floor plan oda görünümü
│   │   ├── FloorPlan.jsx           ← Görsel oda yerleşim planı
│   │   ├── RoomCard.jsx            ← Canlı oda kartları
│   │   ├── RoomPanel.jsx           ← Oda detay paneli ve actuator kontrolleri
│   │   ├── ActuatorToggle.jsx      ← ON/OFF cihaz kontrol bileşeni
│   │   ├── ActivityFeed.jsx        ← Son aksiyonlar ve canlı olaylar
│   │   ├── AiExplanation.jsx       ← AI karar açıklaması
│   │   ├── AiTimeline.jsx          ← Sensör → bağlam → karar → komut zaman çizelgesi
│   │   ├── EnergySavings.jsx       ← Tahmini enerji tasarrufu paneli
│   │   └── IntegrationDock.jsx     ← AI, Spotify ve Telegram entegrasyon durumu
│   └── src/index.css               ← Mission Control görsel tasarım sistemi
├── agent/
│   ├── main.py                     ← Ana agent (bağlam → karar → komut)
│   ├── context_analyzer.py         ← Sensör verisinden bağlam çıkarır
│   ├── context_enricher.py         ← Hava durumu / duygu durumu gibi ek bağlam ekler
│   ├── decision_engine.py          ← ML modeli ile karar verir
│   ├── policy_manager.py           ← Kullanıcı kuralları ve güvenlik politikaları uygular
│   ├── spotify_controller.py       ← Spotify çalma/durdurma ve playlist entegrasyonu
│   ├── spotify_auth.py             ← Spotify OAuth token üretimi
│   ├── models/                     ← Eğitilmiş karar modeli ve encoder dosyaları
│   └── requirements.txt
├── simulator/
│   └── simulator.py                ← Sahte sensör verisi üretir
└── telegram_bot/
    ├── bot.py                      ← Telefona bildirim gönderir, mood input alır
    └── requirements.txt
```

## Ana Özellikler

### 1. Mission Control Web Dashboard

React tabanlı frontend artık klasik bir dashboard yerine **Mission Control** tarzı bir kontrol paneli olarak tasarlandı.

Öne çıkanlar:

- Koyu tema, canlı grid arka planı ve animasyonlu kontrol yüzeyi
- Proje logosu / marka alanı: **NeuroNest - Adaptive Smart Home**
- Sistem sağlığı göstergesi
- Manual / Static / AI mod seçimi
- Canlı oda kartları
- Kart görünümü ve floor plan görünümü
- Oda detay paneli
- Actuator ON/OFF kontrolleri
- Son aksiyonlar geçmişi
- AI karar açıklaması
- AI karar zaman çizelgesi
- Enerji tasarrufu tahmini
- Spotify, Telegram ve AI entegrasyon durumu

Frontend adresi:

```text
http://localhost:5173
```

Telefon üzerinden aynı Wi-Fi ağında erişmek için:

```text
http://<bilgisayar-ip-adresi>:5173
```

Örnek:

```text
http://192.168.139.238:5173
```

Not: Telefon erişimi için backend CORS ayarları LAN demo kullanımına uygun hale getirildi. Frontend de API adresini otomatik olarak açıldığı host üzerinden çözer.

### 2. AI Agent

`agent/main.py`, MQTT üzerinden sensör verilerini dinler, gelen veriyi bağlama dönüştürür, ML karar motoruna gönderir ve uygun actuator komutlarını yayınlar.

Agent akışı:

```text
MQTT sensor payload
  → ContextAnalyzer
  → ContextEnricher
  → DecisionEngine
  → PolicyManager
  → MQTT command
  → InfluxDB action_log
```

AI modu seçildiğinde backend şu topic'e mod bilgisini yayınlar:

```text
home/system/mode
```

Önemli: AI moduna geçmek her zaman anında yeni aksiyon üretmez. Agent, anlamlı bir sensör veya bağlam değişikliği geldiğinde karar verir.

### 3. AI Explanation Panel

Frontend'de AI kararlarının daha anlaşılır olması için **Decision Trace** paneli eklendi.

Bu panel:

- AI açık mı kapalı mı gösterir
- Son AI kararını listeler
- Kararın nedenini gösterir
- O karar sırasında kullanılan sinyalleri özetler

Örnek:

```text
Latest decision:
Bathroom Fan -> OFF

Reason:
ML kararı: ev_bos

Signals used:
- Temperature 23.1 C
- Motion Clear
- Humidity 48%
```

Bu özellik, jüriye sistemin sadece veri göstermediğini, kararlarını açıklayabildiğini göstermek için eklendi.

### 4. AI Timeline

**Signal To Action** paneli, akıllı karar zincirini görsel olarak açıklar:

```text
Sensor input
  → Context layer
  → AI decision
  → Actuator output
```

Bu panel, sistem mimarisini sunum sırasında anlatmayı kolaylaştırır.

### 5. Demo Mode / Scenario Launcher

Sergi sırasında gerçek sensör verisi her zaman dramatik veya açıklayıcı olmayabilir. Bu yüzden backend'e demo senaryoları eklendi.

Endpoint:

```text
POST /api/system/demo?scenario=<scenario_id>
```

Mevcut senaryolar:

| Senaryo | Açıklama |
|---|---|
| `live` | Simülatör / gerçek veriye geri döner |
| `kitchen_smoke` | Mutfakta duman / güvenlik alarmı senaryosu |
| `night_routine` | Akşam / uyku hazırlığı bağlamı |
| `bathroom_humidity` | Banyoda yüksek nem ve havalandırma ihtiyacı |
| `empty_home` | Ev boş, enerji tasarrufu davranışı |

Frontend'deki **Scenario Launcher** panelinden bu senaryolar tek tıkla başlatılabilir.

### 6. Floor Plan View

Oda kartlarına ek olarak **floor plan** görünümü eklendi.

Bu görünümde:

- Odalar mekânsal bir yerleşim gibi gösterilir
- Hareket olan odalar vurgulanır
- Alarm durumundaki odalar kırmızı / kritik görünür
- Odaya tıklanınca detay paneli açılır

Bu özellik, hangi odanın hangi durumda olduğunu daha sezgisel göstermeyi amaçlar.

### 7. Energy Savings Panel

**AI Savings Estimate** paneli, AI aksiyonlarına ve aktif cihaz sayısına göre yaklaşık enerji etkisi gösterir.

Gösterilen metrikler:

- Tahmini kWh tasarrufu
- AI tarafından yapılan OFF kararları
- Konfor skoru
- Aktif cihaz sayısı

Bu panel, projenin sadece konfor değil, enerji verimliliği yönünü de anlatmak için eklendi.

### 8. Spotify Entegrasyonu

Agent tarafında Spotify kontrolü için:

```text
agent/spotify_controller.py
agent/spotify_auth.py
```

Backend tarafında Spotify durum bilgisi frontend'e taşınır.

Dashboard Spotify kartı:

- Spotify token cache var mı kontrol eder
- Şu anda çalan müzik varsa gösterir
- Sanatçı / albüm bilgisi gösterebilir
- Spotify linki varsa açma bağlantısı sunar

Spotify için `.spotify_cache` dosyasının oluşmuş olması gerekir.

### 9. Telegram Bot Entegrasyonu

Telegram bot:

```text
telegram_bot/bot.py
```

Özellikler:

- `/start` ile bildirimlere kayıt olur
- `/mood` ile kullanıcı duygu durumu alır
- `/status` ile bot durumunu gösterir
- `/stop` ile bildirimleri durdurur

Telegram bot MQTT üzerinden:

```text
home/alerts
home/user/sentiment
```

topic'leriyle sistemle haberleşir.

### 10. Backend REST API

Backend FastAPI ile çalışır.

Ana endpointler:

| Endpoint | Açıklama |
|---|---|
| `GET /health` | Backend sağlık kontrolü |
| `GET /api/system/overview` | Sistem modu, odalar, sensörler, actuator durumları |
| `GET /api/system/mode` | Mevcut sistem modu |
| `POST /api/system/mode?mode=AI` | Manual / Static / AI mod seçimi |
| `GET /api/system/diagnostics` | AI, Spotify ve demo durumu |
| `POST /api/system/demo?scenario=...` | Demo senaryosu başlatır |
| `POST /api/rooms/{room}/actuators/{device}?state=ON` | Actuator kontrolü |
| `GET /api/rooms/{room}/history` | Sensör geçmişi |

Backend adresi:

```text
http://localhost:8000
```

API dokümantasyonu:

```text
http://localhost:8000/docs
```

## Kurulum

### 1. Docker Desktop kur

```text
https://www.docker.com/products/docker-desktop
```

### 2. Ortam değişkenlerini ayarla

`.env` dosyasında gerekli değerler bulunur.

Önemli değişkenler:

```text
MQTT_USER
MQTT_PASSWORD
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
GEMINI_API_KEY
WEATHER_API_KEY
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
TELEGRAM_TOKEN
```

Telegram ve Spotify isteğe bağlıdır. Token yoksa sistemin çekirdek dashboard / AI / MQTT akışı çalışmaya devam eder.

### 3. Sistemi başlat

```bash
cd smarthome
docker compose up --build
```

Arka planda çalıştırmak için:

```bash
docker compose up --build -d
```

### 4. Arayüzlere eriş

| Servis | Adres |
|---|---|
| Mission Control Frontend | http://localhost:5173 |
| FastAPI Backend | http://localhost:8000 |
| FastAPI Docs | http://localhost:8000/docs |
| Node-RED | http://localhost:1880 |
| InfluxDB | http://localhost:8086 |
| MQTT Broker | localhost:1883 |

InfluxDB giriş bilgileri:

```text
Kullanıcı: admin
Şifre: smarthome123
```

### 5. Telefon üzerinden açma

Bilgisayarın IP adresini öğren:

```powershell
ipconfig
```

Telefon ve bilgisayar aynı Wi-Fi ağındaysa telefonda şu formatta aç:

```text
http://<bilgisayar-ip-adresi>:5173
```

Örnek:

```text
http://192.168.139.238:5173
```

Eğer açılmazsa:

- Telefon ve bilgisayar aynı ağda mı kontrol et
- Windows Firewall Docker / 5173 / 8000 portlarını engelliyor mu kontrol et
- Telefonda eski cache varsa gizli sekmede dene

## Demo Senaryosu Test Rehberi

### Kitchen Smoke

Dashboard'da `Kitchen Smoke` butonuna bas.

Kontrol et:

- Kitchen kartı kritik / alert görünmeli
- Smoke değeri `Alert` olmalı
- Alerts sayısı artmalı
- Floor plan'da Kitchen kırmızı/kritik görünmeli
- Action History'de demo aktivasyonu görünmeli

### Bathroom Humidity

`Bathroom Humidity` butonuna bas.

Kontrol et:

- Bathroom nem değeri yükselmeli
- Bathroom kartında humidity dikkat çekmeli
- AI Explanation sinyal listesinde humidity görülebilmeli
- Bu senaryo havalandırma fanı davranışını anlatmak için kullanılabilir

### Night Routine

`Night Routine` butonuna bas.

Kontrol et:

- Bedroom ve Hallway hareket bağlamı göstermeli
- Akşam / uyku rutini AI kararları için iyi bir sunum senaryosudur
- AI Timeline üzerinden sensör → bağlam → karar akışı anlatılabilir

### Empty Home

`Empty Home` butonuna bas.

Kontrol et:

- Odalarda motion clear olmalı
- Energy Savings paneli üzerinden enerji tasarrufu anlatılmalı
- AI'nin ev boşken cihazları kapatma yaklaşımı açıklanabilir

### Live Data

`Live Data` butonuna bas.

Kontrol et:

- Demo override kapanır
- Sistem tekrar simülatör / canlı sensör verisine döner

## MQTT Topic Yapısı

| Topic | Açıklama |
|---|---|
| `home/{oda}/sensor/+` | Sensör verileri |
| `home/{oda}/actuator/{cihaz}/set` | Frontend/backend actuator komutu |
| `home/{oda}/actuator/{cihaz}/state` | Actuator state bilgisi |
| `home/{oda}/{cihaz}/command` | Agent tarafından verilen komut |
| `home/system/mode` | Manual / Static / AI mod bilgisi |
| `home/alerts` | Kritik uyarılar |
| `home/preferences` | Kullanıcı tercihleri |
| `home/user/sentiment` | Telegram mood girdisi |
| `home/{oda}/feedback` | Manuel override / feedback bildirimi |

## Sistemi Durdur

```bash
docker compose down
```

Volume/veri temizlemek için dikkatli kullanılmalıdır:

```bash
docker compose down -v
```

## Sunum İçin Kısa Açıklama

Bu proje, sensörlerden gelen veriyi MQTT üzerinden toplayan, bu veriyi bağlama dönüştüren, ML tabanlı bir karar motoruyla uygun akıllı ev aksiyonları üreten ve sonuçları hem web dashboard hem de Telegram/Spotify gibi yan sistemlerle görünür hale getiren uçtan uca bir akıllı ev otomasyon platformudur.

Dashboard sadece verileri göstermekle kalmaz; AI kararlarını açıklar, karar zaman çizelgesini gösterir, demo senaryoları ile güvenilir sunum yapılmasını sağlar ve enerji tasarrufu tahmini sunar.
