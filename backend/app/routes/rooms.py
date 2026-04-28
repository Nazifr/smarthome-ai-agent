from fastapi import APIRouter, HTTPException, Query
from typing import List, Literal
from app.schemas.room import Room
from app.schemas.history import HistoryPoint
import time
from app.services.room_service import (
    get_all_rooms,
    get_room_by_id,
    get_room_history,
    set_actuator
)

router = APIRouter()


@router.get("/api/rooms", response_model=List[Room])
def get_rooms():
    return get_all_rooms()


@router.get("/api/rooms/{room_id}", response_model=Room)
def get_room(room_id: str):
    room = get_room_by_id(room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.get("/api/rooms/{room_id}/history", response_model=List[HistoryPoint])
def get_history(
    room_id: str,
    sensor_type: str = Query(..., description="temperature, humidity, motion, smoke"),
    minutes: int = Query(60, ge=1, le=1440)
):
    history = get_room_history(room_id, sensor_type, minutes)

    if history is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return history


@router.post("/api/rooms/{room_id}/actuators/{device}")
def control_actuator(
    room_id: str,
    device: str,
    state: Literal["ON", "OFF"] = Query(...)
):
    print("API_RECEIVED", room_id, device, state, time.time())
    return set_actuator(room_id, device, state)