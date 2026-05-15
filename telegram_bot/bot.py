import os
import json
import time
import asyncio
import threading
import paho.mqtt.client as mqtt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

MQTT_BROKER    = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT      = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER      = os.getenv("MQTT_USER", "")
MQTT_PASSWORD  = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS       = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_CA_CERT   = os.getenv("MQTT_CA_CERT", "/etc/smarthome/certs/ca.crt")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# ── Whitelist ─────────────────────────────────────────────────────────────────
# Set ALLOWED_CHAT_IDS=123456789,987654321 in env to restrict access.
# Leave empty to allow anyone who /start's the bot (open mode).
_raw_ids = os.getenv("ALLOWED_CHAT_IDS", "").strip()
ALLOWED_CHAT_IDS: set[int] = {
    int(x.strip()) for x in _raw_ids.split(",")
    if x.strip().lstrip("-").isdigit()
} if _raw_ids else set()

if ALLOWED_CHAT_IDS:
    print(f"[TelegramBot] Whitelist active — {len(ALLOWED_CHAT_IDS)} allowed chat ID(s)")
else:
    print("[TelegramBot] Whitelist not set — open mode (anyone can register)")

# ── Smoke dedup ────────────────────────────────────────────────────────────────
SMOKE_COOLDOWN = 600  # seconds — suppress repeat smoke alerts within this window
_last_smoke_alert: dict[str, float] = {}  # room -> unix timestamp of last sent alert

registered_chats: set = set()
telegram_app = None
mqtt_client_global = None


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

        # Smoke dedup: only fire once per SMOKE_COOLDOWN window per room
        if severity == "high":
            now  = time.time()
            last = _last_smoke_alert.get(room, 0.0)
            if now - last < SMOKE_COOLDOWN:
                mins_left = int((SMOKE_COOLDOWN - (now - last)) / 60) + 1
                print(f"[TelegramBot] Smoke alert suppressed for '{room}' "
                      f"({mins_left} min remaining in cooldown)")
                return
            _last_smoke_alert[room] = now

        emoji = "🚨" if severity == "high" else "⚠️"
        text  = f"{emoji} *UYARI*\n{message}\n📍 Oda: {room}"
        asyncio.run_coroutine_threadsafe(broadcast(text), loop)


async def broadcast(text: str):
    if not registered_chats or not telegram_app:
        return
    for chat_id in registered_chats:
        try:
            await telegram_app.bot.send_message(
                chat_id=chat_id, text=text, parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[TelegramBot] Mesaj gönderilemedi {chat_id}: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Whitelist gate
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text(
            "❌ Yetkisiz erişim. Sistem yöneticisiyle iletişime geçin.\n"
            f"(Your chat ID: `{chat_id}`)",
            parse_mode="Markdown"
        )
        print(f"[TelegramBot] Unauthorized /start from chat_id={chat_id}")
        return

    registered_chats.add(chat_id)
    await update.message.reply_text(
        "✅ Kayıt olundu! Akıllı ev bildirimleri bu sohbete gelecek.\n\n"
        "Komutlar:\n/start — kayıt ol\n/mood  — günlük duygu durumunu bildir\n"
        "/status — sistem durumu\n/stop  — bildirimleri durdur"
    )
    print(f"[TelegramBot] Yeni kullanıcı kaydedildi: {chat_id}")


async def cmd_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("😊 Iyiyim",   callback_data="mood_notr"),
         InlineKeyboardButton("😴 Yorgunum", callback_data="mood_yorgun")],
        [InlineKeyboardButton("🏃 Aktifim",  callback_data="mood_aktif"),
         InlineKeyboardButton("😤 Stresli",  callback_data="mood_stresli")],
    ]
    await update.message.reply_text(
        "🌅 Bugün nasıl hissediyorsun?\nSeçimine göre ev ayarlarını optimize edeceğim.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    whitelist_info = (
        f"🔒 Whitelist: {len(ALLOWED_CHAT_IDS)} ID(s)"
        if ALLOWED_CHAT_IDS else "🔓 Whitelist: open"
    )
    await update.message.reply_text(
        f"🟢 Sistem çalışıyor\n"
        f"👥 Kayıtlı kullanıcı: {len(registered_chats)}\n"
        f"{whitelist_info}"
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registered_chats.discard(update.effective_chat.id)
    await update.message.reply_text("🔕 Bildirimler durduruldu.")


async def handle_mood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sentiment = query.data.replace("mood_", "")
    emoji_map = {"notr": "😊", "yorgun": "😴", "aktif": "🏃", "stresli": "😤"}
    if mqtt_client_global:
        mqtt_client_global.publish(
            "home/user/sentiment",
            json.dumps({"sentiment": sentiment, "chat_id": query.from_user.id})
        )
        print(f"[TelegramBot] Duygu durumu gönderildi: {sentiment}")
    await query.edit_message_text(
        f"{emoji_map.get(sentiment, '😊')} Anlaşıldı! Duygu durumun *{sentiment}* olarak kaydedildi.\n"
        f"Ev ayarları buna göre optimize edilecek.", parse_mode="Markdown"
    )


loop = asyncio.new_event_loop()


def run_mqtt():
    global mqtt_client_global
    client = mqtt.Client(client_id="smarthome-telegram-bot")
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    if MQTT_TLS:
        client.tls_set(ca_certs=MQTT_CA_CERT)
        print(f"[TelegramBot] TLS enabled — CA: {MQTT_CA_CERT}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client_global = client
    client.loop_forever()


def main():
    global telegram_app
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[TelegramBot] ⚠️  TELEGRAM_TOKEN ayarlanmamış — bot devre dışı")
        threading.Thread(target=run_mqtt, daemon=True).start()
        import time as _time
        while True:
            _time.sleep(60)
        return

    threading.Thread(target=run_mqtt, daemon=True).start()
    asyncio.set_event_loop(loop)
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start",  cmd_start))
    telegram_app.add_handler(CommandHandler("mood",   cmd_mood))
    telegram_app.add_handler(CommandHandler("status", cmd_status))
    telegram_app.add_handler(CommandHandler("stop",   cmd_stop))
    telegram_app.add_handler(CallbackQueryHandler(handle_mood_callback))
    print("[TelegramBot] Bot başlatıldı, /start komutu bekleniyor...")
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
