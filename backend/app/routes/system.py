from fastapi import APIRouter, Query, Depends, Request
from typing import Literal
from app.schemas.system import SystemMode
from app.schemas.overview import SystemOverview
from app.services.system_service import (
    get_system_mode,
    get_system_overview,
    set_system_mode,
)
from app.services.integration_service import get_ai_status, get_service_health, get_spotify_status
from app.services.room_service import get_demo_status, set_demo_scenario
from app.security import require_api_key, limiter

router = APIRouter()


@router.get("/api/system/mode", response_model=SystemMode)
def system_mode():
    return get_system_mode()


@router.post("/api/system/mode", response_model=SystemMode)
@limiter.limit("10/minute")
async def update_system_mode(
    request: Request,
    mode: Literal["Manual", "Static", "AI"] = Query(...),
    _: None = Depends(require_api_key),
):
    return set_system_mode(mode)


@router.get("/api/system/overview", response_model=SystemOverview)
def system_overview():
    return get_system_overview()


@router.get("/api/system/diagnostics")
def system_diagnostics():
    current_mode = get_system_mode().mode
    return {
        "ai": get_ai_status(current_mode),
        "spotify": get_spotify_status(),
        "demo": get_demo_status(),
        "services": get_service_health(current_mode),
    }


@router.post("/api/system/demo")
@limiter.limit("10/minute")
async def update_demo_scenario(
    request: Request,
    scenario: str = Query(...),
    _: None = Depends(require_api_key),
):
    result = set_demo_scenario(scenario)
    if result is None:
        return {"error": "Unknown demo scenario", "demo": get_demo_status()}
    return result
