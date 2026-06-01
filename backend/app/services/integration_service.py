import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from app.services.influx_service import query_recent_actions
from app.services.influx_service import get_influx_status, query_latest_sensor
from app.services.mqtt_service import get_mqtt_status

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_CACHE_PATH = os.getenv("SPOTIFY_CACHE_PATH", "/agent/.spotify_cache")
USER_LEARNING_PATH = os.getenv("USER_LEARNING_PATH", "/agent/user_learning.json")


def _read_spotify_cache():
    if not os.path.exists(SPOTIFY_CACHE_PATH):
        return None

    with open(SPOTIFY_CACHE_PATH, "r", encoding="utf-8") as cache_file:
        return json.load(cache_file)


def _refresh_spotify_token(cache):
    refresh_token = cache.get("refresh_token")
    if not refresh_token or not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None

    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode("utf-8")
    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("utf-8")
    request = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=payload,
        headers={
            "Authorization": f"Basic {base64.b64encode(credentials).decode('ascii')}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))

    cache.update(data)
    cache["expires_at"] = int(time.time()) + int(data.get("expires_in", 3600))
    with open(SPOTIFY_CACHE_PATH, "w", encoding="utf-8") as cache_file:
        json.dump(cache, cache_file)

    return cache.get("access_token")


def get_spotify_status():
    try:
        cache = _read_spotify_cache()
        if not cache:
            return {
                "available": False,
                "playing": False,
                "message": "Spotify token cache not found",
            }

        access_token = cache.get("access_token")
        if cache.get("expires_at", 0) <= int(time.time()) + 60:
            access_token = _refresh_spotify_token(cache)

        if not access_token:
            return {
                "available": False,
                "playing": False,
                "message": "Spotify needs re-authentication",
            }

        request = urllib.request.Request(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                if response.status == 204:
                    return {
                        "available": True,
                        "playing": False,
                        "message": "Nothing playing right now",
                    }
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 204:
                return {
                    "available": True,
                    "playing": False,
                    "message": "Nothing playing right now",
                }
            raise

        item = data.get("item") or {}
        artists = ", ".join(artist.get("name", "") for artist in item.get("artists", []))
        return {
            "available": True,
            "playing": bool(data.get("is_playing")),
            "track": item.get("name", "Unknown track"),
            "artist": artists or "Unknown artist",
            "album": (item.get("album") or {}).get("name", ""),
            "url": (item.get("external_urls") or {}).get("spotify", ""),
            "message": "Playing" if data.get("is_playing") else "Paused",
        }
    except Exception as exc:
        return {
            "available": False,
            "playing": False,
            "message": str(exc),
        }


def get_ai_status(current_mode: str):
    actions = query_recent_actions(minutes=240, limit=6)
    return {
        "mode": current_mode,
        "armed": current_mode == "AI",
        "recent_actions": actions,
        "learning": get_learning_status(),
        "message": (
            "AI is armed and will act on the next meaningful sensor/context change"
            if current_mode == "AI"
            else "AI autonomy is paused because the system is not in AI mode"
        ),
    }


def get_learning_status():
    if not os.path.exists(USER_LEARNING_PATH):
        return {
            "feedback_count": 0,
            "rule_count": 0,
            "last_feedback": None,
            "top_rules": [],
            "message": "No manual preferences learned yet",
        }
    try:
        with open(USER_LEARNING_PATH, "r", encoding="utf-8") as learning_file:
            data = json.load(learning_file)
        rules = sorted(
            data.get("rules", {}).values(),
            key=lambda rule: (rule.get("count", 0), rule.get("last_seen", 0)),
            reverse=True,
        )
        return {
            "feedback_count": int(data.get("feedback_count", 0)),
            "rule_count": len(rules),
            "last_feedback": data.get("last_feedback"),
            "top_rules": rules[:5],
            "message": (
                f"{data.get('feedback_count', 0)} manual preference(s) captured"
                if data.get("feedback_count", 0)
                else "No manual preferences learned yet"
            ),
        }
    except Exception as exc:
        return {
            "feedback_count": 0,
            "rule_count": 0,
            "last_feedback": None,
            "top_rules": [],
            "message": f"Learning status unavailable: {exc}",
        }


def get_service_health(current_mode: str):
    try:
        actions = query_recent_actions(minutes=240, limit=1)
    except Exception:
        actions = []
    try:
        simulator_has_data = query_latest_sensor("living_room", "temperature") is not None
    except Exception:
        simulator_has_data = False

    # Check Telegram token availability
    telegram_configured = bool(os.getenv("TELEGRAM_TOKEN", ""))

    return [
        {
            "id": "backend",
            "label": "Backend",
            "ok": True,
            "detail": "API responding",
        },
        get_mqtt_status(),
        get_influx_status(),
        {
            "id": "simulator",
            "label": "Simulator",
            "ok": simulator_has_data,
            "detail": "sensor stream active" if simulator_has_data else "waiting for sensor data",
        },
        {
            "id": "agent",
            "label": "AI Agent",
            "ok": current_mode == "AI",
            "detail": (
                f"{len(actions)} recent action(s), armed"
                if current_mode == "AI"
                else "paused by mode"
            ),
        },
        {
            "id": "telegram",
            "label": "Telegram Bot",
            "ok": telegram_configured,
            "detail": "alert notifications active" if telegram_configured else "not configured",
        },
    ]
