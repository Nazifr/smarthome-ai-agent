from fastapi import APIRouter
from app.services.weather_service import get_weather

router = APIRouter()


@router.get("/api/weather")
def weather():
    return get_weather()
