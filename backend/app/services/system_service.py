from app.schemas.system import SystemMode
from app.schemas.overview import SystemOverview
from app.services.room_service import get_all_rooms
from app.services.mqtt_service import publish

CURRENT_MODE = "Manual"


def get_system_mode() -> SystemMode:
    return SystemMode(mode=CURRENT_MODE)


def set_system_mode(mode: str) -> SystemMode:
    global CURRENT_MODE
    CURRENT_MODE = mode
    publish("home/system/mode", {"mode": mode})
    return SystemMode(mode=CURRENT_MODE)


def get_system_overview() -> SystemOverview:
    rooms = get_all_rooms()

    return SystemOverview(
        mode=CURRENT_MODE,
        total_rooms=len(rooms),
        active_alerts=0,
        rooms=rooms
    )