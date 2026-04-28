from fastapi import APIRouter, Query
from typing import Literal
from app.schemas.system import SystemMode
from app.schemas.overview import SystemOverview
from app.services.system_service import (
    get_system_mode,
    get_system_overview,
    set_system_mode,
)

router = APIRouter()


@router.get("/api/system/mode", response_model=SystemMode)
def system_mode():
    return get_system_mode()


@router.post("/api/system/mode", response_model=SystemMode)
def update_system_mode(mode: Literal["Manual", "Static", "AI"] = Query(...)):
    return set_system_mode(mode)


@router.get("/api/system/overview", response_model=SystemOverview)
def system_overview():
    return get_system_overview()