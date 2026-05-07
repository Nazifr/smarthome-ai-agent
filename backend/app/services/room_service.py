from app.schemas.room import Room
from app.services.influx_service import query_latest_sensor, query_sensor_history
from app.services.mqtt_service import publish, get_actuator_state

ROOM_IDS = [
    "living_room",
    "bedroom",
    "kitchen",
    "bathroom",
    "hallway",
]

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
        },
    },
}


def build_room(room_id: str) -> Room:
    temperature = query_latest_sensor(room_id, "temperature")
    humidity = query_latest_sensor(room_id, "humidity")
    motion = query_latest_sensor(room_id, "motion")
    smoke = query_latest_sensor(room_id, "smoke")
    override = DEMO_OVERRIDES.get(room_id, {})

    return Room(
        room_id=room_id,
        temperature=float(override.get("temperature", temperature if temperature is not None else 0.0)),
        humidity=int(override.get("humidity", humidity if humidity is not None else 0)),
        motion=int(override.get("motion", motion if motion is not None else 0)),
        smoke=int(override.get("smoke", smoke if smoke is not None else 0)),
        actuators={
            "light": get_actuator_state(room_id, "light"),
            "fan": get_actuator_state(room_id, "fan"),
            "ac": get_actuator_state(room_id, "ac"),
            "exhaust_fan": get_actuator_state(room_id, "exhaust_fan"),
            "ventilation_fan": get_actuator_state(room_id, "ventilation_fan"),
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
    topic = f"home/{room_id}/actuator/{device}/set"
    publish(topic, {"state": state})

    # Echo back to state topic immediately (test mode)
    state_topic = f"home/{room_id}/actuator/{device}/state"
    publish(state_topic, {"state": state})

    return {
        "room": room_id,
        "device": device,
        "state": state
    }


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
    DEMO_OVERRIDES = DEMO_SCENARIOS[scenario_id]["rooms"].copy()

    return get_demo_status()
