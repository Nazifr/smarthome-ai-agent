from fastapi import APIRouter
from app.services.energy_service import get_energy_summary

router = APIRouter()


@router.get("/api/energy/summary")
def energy_summary():
    return get_energy_summary()
