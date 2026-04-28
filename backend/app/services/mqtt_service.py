import json
import os
import threading
import paho.mqtt.client as mqtt
import time

MQTT_HOST     = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

ACTUATOR_STATES = {}


def _make_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    return client


def _on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("home/+/actuator/+/state")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        state = payload.get("state", "UNKNOWN")

        topic_parts = msg.topic.split("/")
        room_id = topic_parts[1]
        device = topic_parts[3]

        if room_id not in ACTUATOR_STATES:
            ACTUATOR_STATES[room_id] = {}

        ACTUATOR_STATES[room_id][device] = state
        print(f"[MQTT] State update: {room_id} {device} = {state}")
        print("MQTT_STATE_RECEIVED", msg.topic, msg.payload.decode(), time.time())

    except Exception as e:
        print(f"[MQTT] Error processing message: {e}")


def start_mqtt_listener():
    client = _make_client()
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()


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
    return ACTUATOR_STATES.get(room_id, {}).get(device, "UNKNOWN")
