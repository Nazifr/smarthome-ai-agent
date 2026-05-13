from app.schemas.system import SystemMode
from app.schemas.overview import SystemOverview
from app.services.room_service import get_all_rooms
from app.services.mqtt_service import publish

CURRENT_MODE = "AI"


def get_system_mode() -> SystemMode:
    return SystemMode(mode=CURRENT_MODE)


def set_system_mode(mode: str) -> SystemMode:
    global CURRENT_MODE
    CURRENT_MODE = mode
    publish("home/system/mode", {"mode": mode})

    # Away (Static) mode: automatically turn off all devices for energy saving
    if mode == "Static":
        from app.services.room_service import ROOM_ACTUATORS, set_actuator
        for room_id, devices in ROOM_ACTUATORS.items():
            for device in devices:
                set_actuator(room_id, device, "OFF")

    return SystemMode(mode=CURRENT_MODE)


def get_system_overview() -> SystemOverview:
    rooms = get_all_rooms()

    return SystemOverview(
        mode=CURRENT_MODE,
        total_rooms=len(rooms),
        active_alerts=sum(1 for room in rooms if room.smoke > 0),
        rooms=rooms
    )
