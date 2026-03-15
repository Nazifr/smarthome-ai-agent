"""
Telegram Bot

MQTT'den gelen alert mesajlarını kullanıcının telefonuna iletir.
Ayrıca kullanıcı bottan komut da gönderebilir.

Kurulum:
1. Telegram'da @BotFather'a yaz → /newbot → token al
2. docker-compose.yml içinde TELEGRAM_TOKEN'ı güncelle
3. Bota bir mesaj at → /start → Chat ID otomatik kaydedilir
"""

import os
import json
import asyncio
import threading

import paho.mqtt.client as mqtt
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

MQTT_BROKER    = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT      = int(os.getenv("MQTT_PORT", 1883))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Bildirim gönderilecek chat ID'leri (bot ile /start yapan herkes eklenir)
registered_chats: set = set()
telegram_app = None


# ── MQTT Callbacks ─────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[TelegramBot] MQTT'ye bağlandı ✓")
        client.subscribe("home/alerts")   # sadece uyarıları dinle
    else:
        print(f"[TelegramBot] MQTT bağlantı hatası: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    topic = msg.topic

    # Sadece kritik uyarılar telefona gelir
    # Rutin agent kararları Telegram'a gönderilmez
    if topic == "home/alerts":
        message = payload.get("message", "")
        severity = payload.get("severity", "normal")
        room = payload.get("room", "")
        emoji = "🚨" if severity == "high" else "⚠️"
        text = f"{emoji} *UYARI*\n{message}\n📍 Oda: {room}"
        asyncio.run_coroutine_threadsafe(
            broadcast(text), loop
        )


async def broadcast(text: str):
    """Kayıtlı tüm chat'lere mesaj gönder."""
    if not registered_chats or not telegram_app:
        return
    for chat_id in registered_chats:
        try:
            await telegram_app.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[TelegramBot] Mesaj gönderilemedi {chat_id}: {e}")


# ── Telegram Komutları ──────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.add(chat_id)
    await update.message.reply_text(
        "✅ Kayıt olundu! Akıllı ev bildirimleri bu sohbete gelecek.\n\n"
        "Komutlar:\n"
        "/start — kayıt ol\n"
        "/status — sistem durumu\n"
        "/stop — bildirimleri durdur"
    )
    print(f"[TelegramBot] Yeni kullanıcı kaydedildi: {chat_id}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 Sistem çalışıyor\n"
        f"👥 Kayıtlı kullanıcı sayısı: {len(registered_chats)}"
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.discard(chat_id)
    await update.message.reply_text("🔕 Bildirimler durduruldu.")


# ── Ana Döngü ───────────────────────────────────────────────────────────

loop = asyncio.new_event_loop()


def run_mqtt():
    client = mqtt.Client(client_id="smarthome-telegram-bot")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


def main():
    global telegram_app

    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[TelegramBot] ⚠️  TELEGRAM_TOKEN ayarlanmamış — bot devre dışı")
        # Token yoksa sadece MQTT'yi dinle ama Telegram gönderme
        mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
        mqtt_thread.start()
        import time
        while True:
            time.sleep(60)
        return

    # MQTT'yi ayrı thread'de başlat
    mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
    mqtt_thread.start()

    # Telegram botunu başlat
    asyncio.set_event_loop(loop)
    telegram_app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )
    telegram_app.add_handler(CommandHandler("start",  cmd_start))
    telegram_app.add_handler(CommandHandler("status", cmd_status))
    telegram_app.add_handler(CommandHandler("stop",   cmd_stop))

    print("[TelegramBot] Bot başlatıldı, /start komutu bekleniyor...")
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
