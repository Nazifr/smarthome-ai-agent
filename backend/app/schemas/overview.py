from pydantic import BaseModel
from typing import List
from app.schemas.room import Room


class SystemOverview(BaseModel):
    mode: str
    total_rooms: int
    active_alerts: int
    rooms: List[Room]