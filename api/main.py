"""
SmartHome FastAPI - Tablet Uygulaması için REST API + WebSocket

Endpoints:
  GET  /status          — anlık sistem durumu
  GET  /history         — son 20 agent kararı
  POST /command         — cihaza komut gönder
  POST /mood            — duygu durumu güncelle
  POST /preferences     — enerji modu / tercihler
  WS   /ws              — gerçek zamanlı sensör akışı
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MQTT_BROKER   = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

app = FastAPI(title="SmartHome API", version="1.0.0")

# CORS — tablet uygulaması farklı origin'den bağlanabilir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Durum Deposu ──────────────────────────────────────────────────────
state = {
    "sensors": {},          # oda → son sensör verisi
    "last_action": {},      # son agent kararı
    "action_history": [],   # son 20 karar
    "context": {},          # aktif bağlam
    "alerts": [],           # son 5 uyarı
}

# WebSocket bağlantıları
connected_clients: list[WebSocket] = []

# ── MQTT ──────────────────────────────────────────────────────────────
mqtt_client = mqtt.Client(client_id="smarthome-api")
if MQTT_USER and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[API] MQTT broker'a bağlandı ✓")
        client.subscribe("home/+/sensor/all")
        client.subscribe("home/+/+/command")
        client.subscribe("home/alerts")
    else:
        print(f"[API] MQTT bağlantı hatası: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic   = msg.topic
        parts   = topic.split("/")

        if "/sensor/" in topic:
            room = parts[1]
            state["sensors"][room] = {**payload, "room": room, "updated_at": datetime.now().isoformat()}

        elif "/command" in topic:
            room   = parts[1]
            device = parts[2]
            entry  = {
                "room": room, "device": device,
                "command":    payload.get("command"),
                "reason":     payload.get("reason"),
                "method":     payload.get("method"),
                "confidence": payload.get("confidence"),
                "scenario":   payload.get("context_label"),
                "timestamp":  datetime.now().isoformat(),
            }
            state["last_action"] = entry
            state["action_history"].insert(0, entry)
            state["action_history"] = state["action_history"][:20]

        elif topic == "home/alerts":
            alert = {**payload, "timestamp": datetime.now().isoformat()}
            state["alerts"].insert(0, alert)
            state["alerts"] = state["alerts"][:5]

        # WebSocket'e yayınla
        asyncio.run(broadcast_ws({"type": "update", "topic": topic, "data": payload}))

    except Exception as e:
        print(f"[API] MQTT mesaj hatası: {e}")

async def broadcast_ws(data: dict):
    disconnected = []
    for ws in connected_clients:
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected_clients.remove(ws)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

import threading
def start_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"[API] MQTT başlatma hatası: {e}")

threading.Thread(target=start_mqtt, daemon=True).start()

# ── Pydantic Modeller ─────────────────────────────────────────────────

class CommandRequest(BaseModel):
    room: str
    device: str
    command: str

class MoodRequest(BaseModel):
    sentiment: str  # notr, yorgun, aktif, stresli

class PreferencesRequest(BaseModel):
    energy_mode: Optional[str] = "normal"
    quiet_hours: Optional[bool] = False

# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "SmartHome API çalışıyor", "version": "1.0.0"}

@app.get("/status")
def get_status():
    """Anlık sistem durumu — sensörler, son karar, aktif senaryo"""
    return {
        "sensors":     state["sensors"],
        "last_action": state["last_action"],
        "alerts":      state["alerts"],
        "timestamp":   datetime.now().isoformat(),
    }

@app.get("/history")
def get_history():
    """Son 20 agent kararı"""
    return {"history": state["action_history"]}

@app.post("/command")
def send_command(req: CommandRequest):
    """Cihaza manuel komut gönder"""
    valid_devices  = ["ac", "lights", "fan", "heater"]
    valid_commands = ["ON", "OFF", "COOL_LOW", "COOL_HIGH", "HEAT", "DIM"]

    if req.device not in valid_devices:
        raise HTTPException(status_code=400, detail=f"Geçersiz cihaz: {req.device}")
    if req.command not in valid_commands:
        raise HTTPException(status_code=400, detail=f"Geçersiz komut: {req.command}")

    topic   = f"home/{req.room}/{req.device}/command"
    payload = json.dumps({
        "command": req.command,
        "reason":  "Tablet manuel kontrolü",
        "method":  "manual",
        "timestamp": datetime.now().isoformat(),
    })
    mqtt_client.publish(topic, payload)

    # Feedback olarak agent'a bildir
    feedback_topic = f"home/{req.room}/feedback"
    feedback = json.dumps({
        "device":  req.device,
        "command": req.command,
        "room":    req.room,
        "sensor_data": state["sensors"].get(req.room, {}),
    })
    mqtt_client.publish(feedback_topic, feedback)

    return {"status": "ok", "topic": topic, "command": req.command}

@app.post("/mood")
def update_mood(req: MoodRequest):
    """Kullanıcı duygu durumunu güncelle"""
    valid = ["notr", "yorgun", "aktif", "stresli"]
    if req.sentiment not in valid:
        raise HTTPException(status_code=400, detail=f"Geçersiz duygu: {req.sentiment}")

    mqtt_client.publish("home/user/sentiment", json.dumps({
        "sentiment": req.sentiment,
        "source": "tablet",
    }))
    return {"status": "ok", "sentiment": req.sentiment}

@app.post("/preferences")
def update_preferences(req: PreferencesRequest):
    """Enerji modu ve tercih güncelle"""
    mqtt_client.publish("home/preferences", json.dumps({
        "energy_mode":  req.energy_mode,
        "quiet_hours":  req.quiet_hours,
        "timestamp":    datetime.now().isoformat(),
    }))
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Gerçek zamanlı sensör ve karar akışı"""
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"[API] WebSocket bağlandı. Toplam: {len(connected_clients)}")

    # Bağlantı kurulunca anlık durumu gönder
    await websocket.send_json({"type": "initial", "data": state["sensors"]})

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"[API] WebSocket ayrıldı. Toplam: {len(connected_clients)}")
