# NeuroNest: Personalized AI Smart Home System

NeuroNest is an end-to-end AI-assisted smart home control system. It combines simulated live sensor data, MQTT messaging, a Python AI agent, InfluxDB time-series storage, a FastAPI backend, a React dashboard, Telegram mood input, and optional Spotify integration.

The project is designed for a jury/demo setting: it can run live from simulated room data, it can launch controlled demo scenarios, and it can explain what the AI decided and why.

## System Overview

```text
Room Sensor Simulator
        |
        v
      MQTT
        |
        v
AI Agent ---> InfluxDB
        |
        v
FastAPI Backend
        |
        v
React Dashboard
        |
        v
Telegram / Spotify / Demo Controls
```

## What Makes It AI And Personalized

NeuroNest uses a layered decision system:

1. Safety rules
   - Smoke and very high humidity take priority.
   - Example: kitchen smoke turns on the exhaust fan and lights.

2. Learned user preferences
   - When the user manually toggles a device, the dashboard sends feedback to the backend.
   - The backend publishes that feedback to MQTT.
   - The AI agent stores it in `agent/user_learning.json`.
   - Future decisions check these learned preferences before the generic model.

3. Pretrained ML model
   - The existing model trained from the larger dataset provides baseline smart-home behavior.

4. Gemini / LLM reasoning
   - Used for complex context when configured and available.

5. Heuristic fallback rules
   - Used when ML/LLM cannot decide or when simple rules are safer.

6. Policy and safety guards
   - Empty rooms should not randomly turn lights on.
   - Bright daytime conditions should keep lights off unless the user has explicitly taught otherwise.

This means user feedback is not just added as a few weak rows to a large CSV. Instead, user behavior becomes a high-priority personalization layer over the generic model. You do not need to retrain the large model for learned preferences to affect the demo.

## Live Data Source

Indoor live room data comes from:

```text
simulator/simulator.py
```

The simulator publishes room readings to MQTT topics such as:

```text
home/living_room/sensor/all
home/kitchen/sensor/all
home/bathroom/sensor/all
```

Each payload includes:

```text
temperature, humidity, motion, smoke, light, timestamp, room
```

Open-Meteo is not the indoor room data source. It is used only as outdoor weather context by the AI agent.

## Real-Time Clock And Lighting Logic

The system uses the real current time from the sensor timestamp / system clock.

Lighting logic now works like this:

- Daytime: if the room is bright, lights stay off even if motion is detected.
- Evening/night: lights may turn on when motion is detected, depending on context.
- Empty rooms: lights are forced off.
- Learned preference: if the user repeatedly chooses a different behavior, that preference can override the generic daylight rule for matching conditions.

This is why lights may not turn on during the day even when there is motion: the system knows it is daytime and sees enough light.

## Main Services

| Service | Purpose | URL |
|---|---|---|
| React Frontend | Main dashboard | `http://localhost:5173` |
| FastAPI Backend | REST API and dashboard data | `http://localhost:8000` |
| FastAPI Docs | API documentation | `http://localhost:8000/docs` |
| MQTT Broker | Message bus for sensors/actions | `localhost:1883`, TLS `8883` |
| Node-RED | Optional flow/dashboard tooling | `http://localhost:1880` |
| InfluxDB | Sensor/action history | internal Docker network |
| Telegram Bot | Mood input and alerts | Telegram |
| Spotify | Optional music integration | Spotify account/device |

## Repository Structure

```text
smarthome/
├── docker-compose.yml
├── README.md
├── AI_WORKFLOW_AND_LEARNING.md
├── backend/
│   ├── app/main.py
│   ├── app/routes/
│   ├── app/services/
│   ├── app/schemas/
│   └── tests/
├── frontend/
│   ├── src/App.jsx
│   ├── src/components/
│   ├── src/hooks/
│   ├── src/services/
│   └── src/mobile/
├── agent/
│   ├── main.py
│   ├── context_analyzer.py
│   ├── context_enricher.py
│   ├── decision_engine.py
│   ├── policy_manager.py
│   ├── user_learning.py
│   ├── spotify_controller.py
│   └── models/
├── simulator/
│   └── simulator.py
├── telegram_bot/
│   └── bot.py
├── mosquitto/
├── nodered/
└── influxdb/
```

## Key Frontend Features

- Live room dashboard
- Floor plan view
- Room detail panel
- Device toggles
- Auto / Manual / Away modes
- Demo scenario launcher
- AI Explanation panel
- AI Timeline panel
- Personal learning status
- Energy savings estimate
- Service health cards
- Spotify and Telegram integration cards
- Desktop and mobile UI

## System Modes

| UI Mode | Backend Mode | Meaning |
|---|---|---|
| Auto | `AI` | AI agent can make autonomous decisions |
| Manual | `Manual` | User controls devices; AI autonomy pauses |
| Away | `Static` | Reduced/autonomous-safe behavior |

Mode is published over MQTT:

```text
home/system/mode
```

## AI Decision Flow

```text
MQTT sensor payload
  -> ContextAnalyzer
  -> ContextEnricher
  -> User learned preference check
  -> ML model / Gemini / heuristics
  -> PolicyManager
  -> MQTT command
  -> InfluxDB action_log
  -> Backend diagnostics
  -> Dashboard AI Timeline
```

AI decisions can be seen in:

- Frontend: `Integrations -> AI Explanation`
- Frontend: `Integrations -> AI Timeline`
- Frontend: `Integrations -> Personal learning`
- API: `GET /api/system/diagnostics`
- InfluxDB measurement: `action_log`

## Manual Feedback Learning

When a user toggles a device in the dashboard:

```text
Frontend toggle
  -> POST /api/rooms/{room}/actuators/{device}
  -> POST /api/rooms/{room}/feedback
  -> MQTT home/{room}/feedback
  -> AI agent records preference
  -> Future matching contexts use learned preference first
```

The learned rule includes:

```text
room, device, command, time period, occupancy, light level
```

Example:

If the user turns the living room light off during bright daytime while someone is in the room, the AI learns:

```text
living_room + lights + afternoon + occupied + bright -> OFF
```

Next time the same context appears, the agent prefers that learned behavior over the generic model.

## Demo Scenarios

Demo scenarios are controlled injections for presentation reliability. They are intentionally deterministic.

Endpoint:

```text
POST /api/system/demo?scenario=<scenario_id>
```

Available scenarios:

| Scenario | Purpose |
|---|---|
| `live` | Return to live simulator data |
| `kitchen_smoke` | Smoke safety scenario |
| `bathroom_humidity` | High humidity / ventilation scenario |
| `night_routine` | Evening wind-down behavior |
| `empty_home` | Energy-saving empty home behavior |
| `fair_arriving` | Mood-based personalized arrival scenario |

While a demo scenario is active, the agent ignores normal simulator ticks unless the payload is marked as demo data. This keeps jury demonstrations stable.

## Suggested Jury Demo Flow

1. Start in `Auto` mode with `Live Data`.
2. Show service health: Backend, MQTT, InfluxDB, Simulator, AI Agent, Telegram.
3. Open the `Integrations` tab.
4. Show `AI Explanation`, `AI Timeline`, and `Personal learning`.
5. Run `Kitchen Smoke`.
   - Expected: kitchen smoke alert, exhaust fan ON, lights ON.
6. Run `Bathroom Humidity`.
   - Expected: bathroom humidity high, ventilation fan ON.
7. Run `Empty Home`.
   - Expected: motion clear, devices OFF.
8. Demonstrate learning:
   - During daytime/bright light, manually toggle a light.
   - Explain that this feedback is stored as a learned user preference.
9. Run `Arriving Home`.
   - Use Telegram `/mood`.
   - Explain mood-based personalization.
10. Return to `Live Data`.

## Spotify Integration

Spotify integration has two parts:

1. Dashboard status
   - Backend checks current Spotify playback and shows status in the UI.

2. Agent playback control
   - Controlled by:

```text
ENABLE_SPOTIFY_ACTIONS=true|false
```

If `ENABLE_SPOTIFY_ACTIONS=false`, the AI can decide music internally but will not actually press play/pause on Spotify. This avoids demo errors when there is no active Spotify device.

If `ENABLE_SPOTIFY_ACTIONS=true`, Spotify must be open and active on a laptop/phone. Otherwise Spotify may return "no active device" errors.

## Telegram Integration

The Telegram bot supports:

- `/start`
- `/mood`
- `/status`
- `/stop`

It publishes mood input through MQTT:

```text
home/user/sentiment
```

The `fair_arriving` scenario uses this mood input to personalize the home.

## REST API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Backend health check |
| `GET /api/system/overview` | Rooms, sensors, actuators, active mode |
| `GET /api/system/mode` | Current mode |
| `POST /api/system/mode?mode=AI` | Set mode |
| `GET /api/system/diagnostics` | AI, learning, Spotify, demo, service health |
| `POST /api/system/demo?scenario=...` | Launch demo scenario |
| `GET /api/rooms` | List all rooms |
| `GET /api/rooms/{room_id}` | Room details |
| `POST /api/rooms/{room_id}/actuators/{device}?state=ON` | Control actuator |
| `POST /api/rooms/{room_id}/feedback` | Record manual user preference |
| `GET /api/rooms/{room_id}/history` | Sensor history |
| `GET /api/energy/summary` | Energy estimate |
| `GET /api/weather` | Outdoor weather context |

Mutating endpoints require `X-API-Key` when `API_KEY` is configured.

## MQTT Topics

| Topic | Purpose |
|---|---|
| `home/{room}/sensor/all` | Full room sensor payload |
| `home/{room}/actuator/{device}/set` | Backend actuator command |
| `home/{room}/actuator/{device}/state` | Actuator state echo |
| `home/{room}/{device}/command` | AI agent actuator command |
| `home/{room}/feedback` | Manual user feedback for learning |
| `home/system/mode` | AI / Manual / Static mode |
| `home/system/demo` | Active demo scenario |
| `home/alerts` | Safety and notification messages |
| `home/preferences` | User preference updates |
| `home/user/sentiment` | Telegram mood input |

## Setup

1. Install Docker Desktop.

2. Configure `.env`.

Important variables:

```text
MQTT_USER
MQTT_PASSWORD
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
GEMINI_API_KEY
WEATHER_API_KEY
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
TELEGRAM_TOKEN
API_KEY
```

3. Start the system:

```bash
docker compose up --build -d
```

4. Open:

```text
http://localhost:5173
```

## Testing

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Backend tests:

```bash
set PYTHONPATH=backend
python -B -m unittest discover backend/tests
```

Agent learning tests:

```bash
python -B -m unittest discover agent -p "test_*.py"
```

Docker backend tests:

```bash
docker compose exec -T backend sh -lc "PYTHONPATH=/app python -m unittest discover /app/tests"
```

Quick live checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/system/diagnostics
Invoke-RestMethod http://localhost:8000/api/system/overview
```

## Stop The System

```bash
docker compose down
```

To remove volumes and stored runtime data:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes persisted database state.

## Short Presentation Description

NeuroNest is a personalized AI smart-home platform. It collects live room data through MQTT, enriches it with time, weather, occupancy, and mood context, then uses a layered AI decision engine to control home devices. The system combines safety rules, learned user preferences, a pretrained ML model, optional Gemini reasoning, and policy guards. The dashboard shows real-time state, AI explanations, decision timelines, service health, demo scenarios, energy estimates, and personalized learning progress.
