from pydantic import BaseModel
from typing import Dict


class Room(BaseModel):
    room_id: str
    temperature: float
    humidity: int
    motion: int
    smoke: int
    actuators: Dict[str, str]