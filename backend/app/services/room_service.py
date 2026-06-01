from app.schemas.room import Room
from app.services.influx_service import query_latest_sensor, query_sensor_history, write_actuator_state
from app.services.mqtt_service import publish, get_actuator_state, normalize_device, remember_actuator_state
from datetime import datetime

ROOM_IDS = [
    "living_room",
    "bedroom",
    "kitchen",
    "bathroom",
    "hallway",
    "office",
]

ROOM_ACTUATORS = {
    "living_room": ["light", "ac", "fan"],
    "bedroom": ["light", "ac", "fan"],
    "kitchen": ["light", "exhaust_fan"],
    "bathroom": ["light", "ventilation_fan"],
    "hallway": ["light"],
    "office": ["light", "ac", "fan"],
}

DEMO_AUTOMATIONS = {
    "kitchen_smoke": [
        ("kitchen", "exhaust_fan", "ON"),
        ("kitchen", "light", "ON"),
    ],
    "bathroom_humidity": [
        ("bathroom", "ventilation_fan", "ON"),
        ("bathroom", "light", "ON"),
    ],
    "night_routine": [
        ("bedroom", "light", "DIM"),
        ("bedroom", "ac", "COOL_LOW"),
        ("bedroom", "fan", "OFF"),
        ("living_room", "light", "OFF"),
        ("living_room", "ac", "OFF"),
        ("living_room", "fan", "OFF"),
        ("kitchen", "light", "OFF"),
        ("kitchen", "exhaust_fan", "OFF"),
        ("hallway", "light", "DIM"),
        ("office", "light", "OFF"),
        ("office", "ac", "OFF"),
        ("office", "fan", "OFF"),
    ],
    "empty_home": [
        (room_id, device, "OFF")
        for room_id, devices in ROOM_ACTUATORS.items()
        for device in devices
    ],
    # Arriving home: everything off except hallway light (someone just walked in)
    "fair_arriving": [
        *[
            (room_id, device, "OFF")
            for room_id, devices in ROOM_ACTUATORS.items()
            for device in devices
            if not (room_id == "hallway" and device == "light")
        ],
        ("hallway", "light", "ON"),
    ],
}

DEMO_OVERRIDES = {}
CURRENT_DEMO = "live"

DEMO_SCENARIOS = {
    "live": {
        "label": "Live Data",
        "description": "Return to simulator and sensor data.",
        "rooms": {},
    },
    "kitchen_smoke": {
        "label": "Kitchen Smoke",
        "description": "Safety critical smoke event in the kitchen.",
        "rooms": {
            "kitchen": {"temperature": 34.5, "humidity": 62, "motion": 1, "smoke": 1},
            "hallway": {"motion": 1},
        },
    },
    "night_routine": {
        "label": "Night Routine",
        "description": "Late evening comfort and low-light automation.",
        "rooms": {
            "bedroom": {"temperature": 23.5, "humidity": 45, "motion": 1, "smoke": 0},
            "living_room": {"temperature": 22.1, "motion": 0, "smoke": 0},
            "hallway": {"motion": 1},
        },
    },
    "bathroom_humidity": {
        "label": "Bathroom Humidity",
        "description": "High humidity after shower, ventilation expected.",
        "rooms": {
            "bathroom": {"temperature": 25.2, "humidity": 86, "motion": 1, "smoke": 0},
        },
    },
    "empty_home": {
        "label": "Empty Home",
        "description": "No occupancy; energy saving decisions expected.",
        "rooms": {
            "living_room": {"motion": 0, "smoke": 0},
            "bedroom": {"motion": 0, "smoke": 0},
            "kitchen": {"motion": 0, "smoke": 0},
            "bathroom": {"motion": 0, "smoke": 0},
            "hallway": {"motion": 0, "smoke": 0},
            "office": {"motion": 0, "smoke": 0},
        },
    },
    "fair_arriving": {
        "label": "Arriving Home",
        "description": "User arrives home — choose your mood on Telegram to personalize the house.",
        "rooms": {
            "hallway":      {"temperature": 22.0, "humidity": 48, "motion": 1, "smoke": 0},
            "living_room":  {"temperature": 22.0, "humidity": 50, "motion": 0, "smoke": 0},
            "bedroom":      {"temperature": 21.5, "humidity": 47, "motion": 0, "smoke": 0},
            "kitchen":      {"temperature": 22.0, "humidity": 48, "motion": 0, "smoke": 0},
            "bathroom":     {"temperature": 22.0, "humidity": 50, "motion": 0, "smoke": 0},
            "office":       {"temperature": 22.0, "humidity": 48, "motion": 0, "smoke": 0},
        },
    },
}


def build_room(room_id: str) -> Room:
    temperature = query_latest_sensor(room_id, "temperature")
    humidity = query_latest_sensor(room_id, "humidity")
    motion = query_latest_sensor(room_id, "motion")
    smoke = query_latest_sensor(room_id, "smoke")
    light = query_latest_sensor(room_id, "light")
    override = DEMO_OVERRIDES.get(room_id, {})

    return Room(
        room_id=room_id,
        temperature=float(override.get("temperature", temperature if temperature is not None else 0.0)),
        humidity=int(override.get("humidity", humidity if humidity is not None else 0)),
        motion=int(override.get("motion", motion if motion is not None else 0)),
        smoke=int(override.get("smoke", smoke if smoke is not None else 0)),
        light=float(override.get("light", light if light is not None else 0.0)),
        actuators={
            device: get_actuator_state(room_id, device)
            for device in ROOM_ACTUATORS.get(room_id, ["light"])
        }
    )


def get_all_rooms() -> list[Room]:
    return [build_room(room_id) for room_id in ROOM_IDS]


def get_room_by_id(room_id: str) -> Room | None:
    if room_id not in ROOM_IDS:
        return None

    return build_room(room_id)


def get_room_history(room_id: str, sensor_type: str, minutes: int = 60):
    if room_id not in ROOM_IDS:
        return None

    return query_sensor_history(room_id, sensor_type, minutes)


def set_actuator(room_id: str, device: str, state: str):
    if room_id not in ROOM_IDS:
        return None

    normalized_device = normalize_device(room_id, device)
    if normalized_device not in ROOM_ACTUATORS.get(room_id, []):
        return None

    remember_actuator_state(room_id, device, state)
    topic = f"home/{room_id}/actuator/{device}/set"
    publish(topic, {"state": state})

    # Echo back to state topic immediately (test mode)
    state_topic = f"home/{room_id}/actuator/{device}/state"
    publish(state_topic, {"state": state})

    # Log to InfluxDB for energy tracking
    try:
        write_actuator_state(room_id, device, state)
    except Exception:
        pass

    return {
        "room": room_id,
        "device": normalized_device,
        "state": state
    }


def send_user_feedback(room_id: str, device: str, command: str, sensor_data: dict | None = None):
    if room_id not in ROOM_IDS:
        return None

    normalized_device = normalize_device(room_id, device)
    if normalized_device not in ROOM_ACTUATORS.get(room_id, []):
        return None

    if not sensor_data:
        room = build_room(room_id)
        sensor_data = {
            "temperature": room.temperature,
            "humidity": room.humidity,
            "motion": room.motion,
            "smoke": room.smoke,
            "light": room.light,
            "timestamp": datetime.now().isoformat(),
            "room": room_id,
        }

    feedback_payload = {
        "room": room_id,
        "device": normalized_device,
        "command": command,
        "sensor_data": sensor_data,
        "timestamp": datetime.now().isoformat(),
        "source": "dashboard_manual_toggle",
    }
    publish(f"home/{room_id}/feedback", feedback_payload)
    return feedback_payload


def get_demo_status():
    return {
        "active": CURRENT_DEMO,
        "scenarios": [
            {
                "id": scenario_id,
                "label": scenario["label"],
                "description": scenario["description"],
            }
            for scenario_id, scenario in DEMO_SCENARIOS.items()
        ],
    }


def set_demo_scenario(scenario_id: str):
    global CURRENT_DEMO, DEMO_OVERRIDES

    if scenario_id not in DEMO_SCENARIOS:
        return None

    CURRENT_DEMO = scenario_id
    scenario_rooms = DEMO_SCENARIOS[scenario_id]["rooms"]
    publish("home/system/demo", {
        "active": scenario_id,
        "label": DEMO_SCENARIOS[scenario_id]["label"],
        "timestamp": datetime.now().isoformat(),
    })

    if scenario_id == "live":
        # Live mode: clear everything, return to pure sensor data
        DEMO_OVERRIDES = {}
    else:
        # Start with smoke=0 for ALL rooms so stale alerts from a
        # previous scenario (e.g. kitchen_smoke) don't persist.
        base = {rid: {"smoke": 0} for rid in ROOM_IDS}
        for rid, overrides in scenario_rooms.items():
            base.setdefault(rid, {}).update(overrides)
        DEMO_OVERRIDES = base
        for room_id, sensor_payload in scenario_rooms.items():
            publish_demo_sensor(room_id, sensor_payload)
        for room_id, device, state in DEMO_AUTOMATIONS.get(scenario_id, []):
            set_actuator(room_id, device, state)

    return get_demo_status()


def publish_demo_sensor(room_id: str, payload: dict):
    sensor_payload = {
        "temperature": payload.get("temperature", query_latest_sensor(room_id, "temperature") or 22.0),
        "humidity": payload.get("humidity", query_latest_sensor(room_id, "humidity") or 50),
        "motion": payload.get("motion", query_latest_sensor(room_id, "motion") or 0),
        "smoke": payload.get("smoke", 0),
        "light": payload.get("light", query_latest_sensor(room_id, "light") or 120),
        "timestamp": datetime.now().isoformat(),
        "room": room_id,
        "demo": True,
    }
    publish(f"home/{room_id}/sensor/all", sensor_payload)
