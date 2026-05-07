from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.rooms import router as rooms_router
from app.routes.system import router as system_router
from app.services.mqtt_service import start_mqtt_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mqtt_listener()
    yield


app = FastAPI(lifespan=lifespan)

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
