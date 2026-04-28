import os
import json
import time
import threading
from datetime import datetime
from context_enricher import ContextEnricher

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from context_analyzer import ContextAnalyzer
from decision_engine import DecisionEngine
from policy_manager import PolicyManager

MQTT_BROKER  = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER    = os.getenv("MQTT_USER", "")
MQTT_PASSWORD= os.getenv("MQTT_PASSWORD", "")
INFLUX_URL   = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "smarthome-super-secret-token")
INFLUX_ORG   = os.getenv("INFLUX_ORG", "smarthome")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET", "sensor_data")

TOPIC_SENSOR_ALL = "home/+/sensor/+"
TOPIC_CMD_PREFIX = "home"
TOPIC_FEEDBACK   = "home/+/feedback"
TOPIC_PREFERENCES= "home/preferences"
TOPIC_ALERT      = "home/alerts"
TOPIC_SENTIMENT  = "home/user/sentiment"
TOPIC_SYSTEM_MODE= "home/system/mode"

SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() == "true"


class SmartHomeAgent:
    def __init__(self):
        self._last_context = {}
        self._system_mode  = "AI"   # "AI" | "Static" | "Manual"
        self.analyzer = ContextAnalyzer()
        self.engine   = DecisionEngine()
        self.policy   = PolicyManager()
        self.enricher = ContextEnricher()

        self.influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

        self.mqtt_client = mqtt.Client(client_id="smarthome-agent")
        if MQTT_USER and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.mqtt_client.on_connect    = self._on_connect
        self.mqtt_client.on_message    = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[Agent] MQTT broker'a bağlandı ✓")
            client.subscribe(TOPIC_SENSOR_ALL)
            client.subscribe(TOPIC_FEEDBACK)
            client.subscribe(TOPIC_PREFERENCES)
            client.subscribe(TOPIC_SENTIMENT)
            client.subscribe(TOPIC_SYSTEM_MODE)
            print(f"[Agent] Dinleniyor: {TOPIC_SENSOR_ALL}")
        else:
            print(f"[Agent] Bağlantı hatası, kod: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[Agent] Bağlantı kesildi (rc={rc}), yeniden bağlanılıyor...")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print(f"[Agent] Geçersiz JSON — topic: {topic}")
            return

        if "/sensor/" in topic:
            self._handle_sensor(topic, payload)
        elif "/feedback" in topic:
            self._handle_feedback(topic, payload)
        elif topic == TOPIC_PREFERENCES:
            self.policy.update_preferences(payload)
            print(f"[Agent] Tercihler güncellendi: {payload}")
        elif topic == TOPIC_SENTIMENT:
            self._handle_sentiment(payload)
        elif topic == TOPIC_SYSTEM_MODE:
            self._handle_system_mode(payload)

    def _handle_sentiment(self, payload: dict):
        sentiment = payload.get("sentiment", "nötr")
        self.enricher.update_sentiment(sentiment)
        print(f"[Agent] Kullanıcı duygu durumu güncellendi: {sentiment}")
        self._last_context = {}

    def _handle_system_mode(self, payload: dict):
        mode = payload.get("mode", "AI")
        self._system_mode = mode
        print(f"[Agent] Sistem modu değiştirildi: {mode}")
        self._last_context = {}  # force re-evaluation on next sensor tick

    def _handle_sensor(self, topic, payload):
        parts = topic.split("/")
        room = parts[1] if len(parts) > 1 else "unknown"
        payload["timestamp"] = payload.get("timestamp", datetime.now().isoformat())
        payload["room"] = room
        self._write_to_influx(payload)
        context = self.analyzer.analyze(payload)
        context = self.enricher.enrich(context)
        features = self.analyzer.to_feature_vector(context)

        print(f"[Agent] Bağlam: {context['context_label']} | "
              f"Sıcaklık: {context['temperature']}°C | "
              f"Hareket: {context['occupancy']}")

        self._check_alerts(context, room)

        # Respect system mode — only make autonomous decisions in AI mode
        if self._system_mode != "AI":
            return

        current_label  = context.get("context_label")
        last_label     = self._last_context.get("context_label")
        temp_diff      = abs(context.get("temperature", 0) - self._last_context.get("temperature", 0))
        motion_changed = context.get("occupancy") != self._last_context.get("occupancy")

        if current_label == last_label and temp_diff < 2.0 and not motion_changed:
            return

        self._last_context = context
        actions = self.engine.decide(context, features)

        for action in actions:
            action["room"] = room
            result = self.policy.apply(action, context)
            if result["approved"]:
                self._execute_action(action, context)
            else:
                print(f"[Agent] Karar reddedildi: {result['reason']}")

    def _execute_action(self, action: dict, context: dict):
        device         = action["device"]
        room           = action["room"]
        command        = action["command"]
        reason         = action["reason"]
        confidence     = action.get("confidence", None)
        method         = action.get("method", "heuristic")
        context_label  = context.get("context_label", "bilinmiyor")
        confidence_str = f"{confidence:.0%}" if confidence else "—"

        if SIMULATION_MODE:
            print(f"[Agent][SİMÜLASYON] Komut → {room}/{device}: {command}")
            print(f"         Gerekçe: {reason} | Yöntem: {method} | Güven: {confidence_str} | Bağlam: {context_label}")
        else:
            topic = f"{TOPIC_CMD_PREFIX}/{room}/{device}/command"
            self.mqtt_client.publish(topic, json.dumps({
                "command": command, "reason": reason, "method": method,
                "confidence": confidence_str, "context_label": context_label,
                "timestamp": datetime.now().isoformat(),
            }))
            print(f"[Agent] ✓ Komut → {topic}: {command}")
            print(f"         Gerekçe: {reason} | Yöntem: {method} | Güven: {confidence_str} | Bağlam: {context_label}")

        self._log_action(device, room, command, reason, context)

    def _handle_feedback(self, topic, payload):
        device  = payload.get("device")
        command = payload.get("command")
        sensor  = payload.get("sensor_data", {})
        if device and command and sensor:
            context  = self.analyzer.analyze(sensor)
            features = self.analyzer.to_feature_vector(context)
            self.engine.record_feedback(features, device, command)
            room = payload.get("room", "general")
            self.policy.set_manual_override(f"{room}_{device}", command)
            print(f"[Agent] Feedback alındı: {device} → {command} (öğrenme kaydedildi)")

    def _check_alerts(self, context: dict, room: str):
        alerts = []
        if context["temperature"] > 35:
            alerts.append(f"⚠️ {room} odasında sıcaklık kritik: {context['temperature']}°C")
        if context["temperature"] < 10:
            alerts.append(f"⚠️ {room} odasında düşük sıcaklık: {context['temperature']}°C")
        for alert in alerts:
            self.mqtt_client.publish(TOPIC_ALERT, json.dumps({
                "message": alert, "room": room,
                "timestamp": datetime.now().isoformat(), "severity": "high",
            }))
            print(f"[Agent] ALERT: {alert}")

    def _write_to_influx(self, data: dict):
        room = data.get("room", "unknown")
        try:
            point = (Point("sensor_reading")
                .tag("room", room)
                .field("temperature", float(data.get("temperature", 0)))
                .field("humidity",    float(data.get("humidity", 0)))
                .field("motion",      int(data.get("motion", 0)))
                .field("light",       float(data.get("light", 0))))
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"[Agent] InfluxDB yazma hatası: room={room} → {e}")

    def _log_action(self, device, room, command, reason, context):
        try:
            point = (Point("action_log")
                .tag("device", device).tag("room", room)
                .tag("command", command).tag("context", context.get("context_label", "unknown"))
                .field("reason", reason)
                .field("temperature", float(context.get("temperature", 0))))
            self.write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"[Agent] Action log hatası: {e}")

    def run(self):
        print("[Agent] Akıllı ev agent'ı başlatılıyor...")
        while True:
            try:
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                self.mqtt_client.loop_forever()
            except Exception as e:
                print(f"[Agent] Bağlantı hatası: {e} — 5 saniye sonra tekrar denenecek")
                time.sleep(5)


if __name__ == "__main__":
    agent = SmartHomeAgent()
    agent.run()
