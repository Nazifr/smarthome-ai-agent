import json
import os
import threading
import paho.mqtt.client as mqtt
import time

MQTT_HOST     = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS      = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_CA_CERT  = os.getenv("MQTT_CA_CERT", "/etc/smarthome/certs/ca.crt")

ACTUATOR_STATES = {}
MQTT_STATUS = {
    "connected": False,
    "last_connect": None,
    "last_message": None,
    "last_error": None,
}


def normalize_device(room_id: str, device: str) -> str:
    """Map generic device names to the room-specific names used by the UI."""
    if device == "lights":
        return "light"
    if device == "fan":
        if room_id == "kitchen":
            return "exhaust_fan"
        if room_id == "bathroom":
            return "ventilation_fan"
    return device


def remember_actuator_state(room_id: str, device: str, state: str):
    normalized_device = normalize_device(room_id, device)
    if room_id not in ACTUATOR_STATES:
        ACTUATOR_STATES[room_id] = {}
    ACTUATOR_STATES[room_id][normalized_device] = state
    return normalized_device


def _make_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    if MQTT_TLS:
        client.tls_set(ca_certs=MQTT_CA_CERT)
    return client


def _on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with result code {rc}")
    MQTT_STATUS["connected"] = rc == 0
    MQTT_STATUS["last_connect"] = time.time()
    MQTT_STATUS["last_error"] = None if rc == 0 else f"connect rc={rc}"
    client.subscribe("home/+/actuator/+/state")
    client.subscribe("home/+/+/command")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        MQTT_STATUS["last_message"] = time.time()
        state = payload.get("state", "UNKNOWN")

        topic_parts = msg.topic.split("/")
        room_id = topic_parts[1]
        if "/actuator/" in msg.topic:
            device = topic_parts[3]
            state = payload.get("state", "UNKNOWN")
        elif msg.topic.endswith("/command"):
            device = topic_parts[2]
            command = str(payload.get("command", "UNKNOWN")).upper()
            state = command
        else:
            return

        device = remember_actuator_state(room_id, device, state)
        print(f"[MQTT] State update: {room_id} {device} = {state}")
        print("MQTT_STATE_RECEIVED", msg.topic, msg.payload.decode(), time.time())

        # Log to InfluxDB for energy tracking
        try:
            from app.services.influx_service import write_actuator_state
            write_actuator_state(room_id, device, state)
        except Exception:
            pass  # don't crash the MQTT handler

    except Exception as e:
        MQTT_STATUS["last_error"] = str(e)
        print(f"[MQTT] Error processing message: {e}")


def start_mqtt_listener():
    client = _make_client()
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()


def get_mqtt_status():
    return {
        "ok": MQTT_STATUS["connected"],
        "label": "MQTT",
        "detail": "connected" if MQTT_STATUS["connected"] else (MQTT_STATUS["last_error"] or "not connected"),
        "last_message": MQTT_STATUS["last_message"],
    }


def publish(topic: str, payload: dict):
    client = _make_client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    print("MQTT_PUBLISH_SET", topic, payload, time.time())
    result = client.publish(topic, json.dumps(payload))
    result.wait_for_publish()

    client.loop_stop()
    client.disconnect()


def get_actuator_state(room_id: str, device: str) -> str:
    normalized_device = normalize_device(room_id, device)
    return ACTUATOR_STATES.get(room_id, {}).get(normalized_device, "OFF")
