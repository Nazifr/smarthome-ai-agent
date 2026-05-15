from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routes.rooms import router as rooms_router
from app.routes.system import router as system_router
from app.routes.energy import router as energy_router
from app.routes.weather import router as weather_router
from app.services.mqtt_service import start_mqtt_listener
from app.security import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mqtt_listener()
    yield


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Smart Home Backend Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(rooms_router)
app.include_router(system_router)
app.include_router(energy_router)
app.include_router(weather_router)
