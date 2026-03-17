"""
Telegram Bot

MQTT'den gelen alert mesajlarını kullanıcının telefonuna iletir.
Kullanıcı /mood komutuyla günlük duygu durumunu bildirir.
"""

import os
import json
import asyncio
import threading

import paho.mqtt.client as mqtt
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

MQTT_BROKER    = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT      = int(os.getenv("MQTT_PORT", 1883))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

registered_chats: set = set()
telegram_app = None
mqtt_client_global = None


# ── MQTT Callbacks ─────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[TelegramBot] MQTT'ye bağlandı ✓")
        client.subscribe("home/alerts")
    else:
        print(f"[TelegramBot] MQTT bağlantı hatası: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    if msg.topic == "home/alerts":
        message  = payload.get("message", "")
        severity = payload.get("severity", "normal")
        room     = payload.get("room", "")
        emoji    = "🚨" if severity == "high" else "⚠️"
        text     = f"{emoji} *UYARI*\n{message}\n📍 Oda: {room}"
        asyncio.run_coroutine_threadsafe(broadcast(text), loop)


async def broadcast(text: str):
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
        "/mood  — günlük duygu durumunu bildir\n"
        "/status — sistem durumu\n"
        "/stop  — bildirimleri durdur"
    )
    print(f"[TelegramBot] Yeni kullanıcı kaydedildi: {chat_id}")


async def cmd_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcıya duygu durumu butonları göster."""
    keyboard = [
        [
            InlineKeyboardButton("😊 İyiyim",   callback_data="mood_nötr"),
            InlineKeyboardButton("😴 Yorgunum", callback_data="mood_yorgun"),
        ],
        [
            InlineKeyboardButton("🏃 Aktifim",  callback_data="mood_aktif"),
            InlineKeyboardButton("😤 Stresli",  callback_data="mood_stresli"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌅 Bugün nasıl hissediyorsun?\nSeçimine göre ev ayarlarını optimize edeceğim.",
        reply_markup=reply_markup
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 Sistem çalışıyor\n"
        f"👥 Kayıtlı kullanıcı sayısı: {len(registered_chats)}"
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    registered_chats.discard(chat_id)
    await update.message.reply_text("🔕 Bildirimler durduruldu.")


async def handle_mood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı duygu durumu butonuna bastığında çalışır."""
    query    = update.callback_query
    await query.answer()

    data      = query.data  # "mood_yorgun" gibi
    sentiment = data.replace("mood_", "")

    emoji_map = {
        "nötr":    "😊",
        "yorgun":  "😴",
        "aktif":   "🏃",
        "stresli": "😤",
    }
    emoji = emoji_map.get(sentiment, "😊")

    # MQTT üzerinden agent'a gönder
    if mqtt_client_global:
        payload = json.dumps({
            "sentiment": sentiment,
            "chat_id":   query.from_user.id
        })
        mqtt_client_global.publish("home/user/sentiment", payload)
        print(f"[TelegramBot] Duygu durumu gönderildi: {sentiment}")

    await query.edit_message_text(
        f"{emoji} Anlaşıldı! Duygu durumun *{sentiment}* olarak kaydedildi.\n"
        f"Ev ayarları buna göre optimize edilecek.",
        parse_mode="Markdown"
    )


# ── Ana Döngü ───────────────────────────────────────────────────────────

loop = asyncio.new_event_loop()


def run_mqtt():
    global mqtt_client_global
    client = mqtt.Client(client_id="smarthome-telegram-bot")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client_global = client
    client.loop_forever()


def main():
    global telegram_app

    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[TelegramBot] ⚠️  TELEGRAM_TOKEN ayarlanmamış — bot devre dışı")
        mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
        mqtt_thread.start()
        import time
        while True:
            time.sleep(60)
        return

    mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
    mqtt_thread.start()

    asyncio.set_event_loop(loop)
    telegram_app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )
    telegram_app.add_handler(CommandHandler("start",  cmd_start))
    telegram_app.add_handler(CommandHandler("mood",   cmd_mood))
    telegram_app.add_handler(CommandHandler("status", cmd_status))
    telegram_app.add_handler(CommandHandler("stop",   cmd_stop))
    telegram_app.add_handler(CallbackQueryHandler(handle_mood_callback, pattern="^mood_"))

    print("[TelegramBot] Bot başlatıldı, /start komutu bekleniyor...")
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
