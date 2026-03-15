# Akıllı Ev AI Agent Sistemi

## Klasör Yapısı

```
smarthome/
├── docker-compose.yml          ← Tüm sistemi başlatır
├── mosquitto/
│   └── config/mosquitto.conf   ← MQTT broker ayarları
├── agent/
│   ├── main.py                 ← Ana agent (bağlam → karar → komut)
│   ├── context_analyzer.py     ← Sensör verisinden bağlam çıkarır
│   ├── decision_engine.py      ← ML modeli ile karar verir
│   ├── policy_manager.py       ← Kullanıcı kuralları uygular
│   └── requirements.txt
├── simulator/
│   └── simulator.py            ← Sahte sensör verisi üretir
└── telegram_bot/
    └── bot.py                  ← Telefona bildirim gönderir
```

## Kurulum

### 1. Docker Desktop kur
https://www.docker.com/products/docker-desktop

### 2. Telegram Bot Token al (isteğe bağlı)
- Telegram'da @BotFather'a yaz
- /newbot → isim ver → token kopyala
- docker-compose.yml içinde `YOUR_BOT_TOKEN_HERE` yerine yapıştır

### 3. Sistemi başlat
```bash
cd smarthome
docker compose up --build
```

### 4. Arayüzlere eriş
| Servis       | Adres                      |
|--------------|---------------------------|
| Node-RED     | http://localhost:1880      |
| InfluxDB     | http://localhost:8086      |
| MQTT Broker  | localhost:1883             |

InfluxDB giriş bilgileri:
- Kullanıcı: admin
- Şifre: smarthome123

### 5. Telegram'da bildirimleri aç
- Oluşturduğun bota Telegram'dan /start yaz
- Artık agent kararları ve uyarılar telefonuna gelir

## Sistemi Durdur
```bash
docker compose down
```

## MQTT Topic Yapısı

| Topic | Açıklama |
|-------|----------|
| `home/{oda}/sensor/all` | Sensör verisi (simülatörden) |
| `home/{oda}/{cihaz}/command` | Agent komutları |
| `home/alerts` | Uyarılar |
| `home/preferences` | Kullanıcı tercihleri |
| `home/{oda}/feedback` | Manuel override bildirimi |
