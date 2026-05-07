# NeuroNest Mobile — Removed Features Audit

This file lists every element from the `NeuroNest Mobile.html` design that was
**not implemented** in the mobile companion, and the exact backend reason for
each omission. Use it to prioritise backend additions.

---

## Removed: Presence / household members

**Design showed:** "Welcome home, Mira" with personalised name, plus Theo/Yuki
ETA chips (e.g. "Theo · 7 min").

**Why removed:** No `/api/users` endpoint, no presence model in `backend/app/schemas/`,
no MQTT presence topic. The `Room` schema has no `occupants` field.

**What's needed to restore:** User model + presence detector (BT/WiFi/phone
checkin); `/api/presence` endpoint returning `[{name, eta_minutes, home: bool}]`.

---

## Removed: Outside weather

**Design showed:** "14° · Light rain" in the summary card.

**Why removed:** No weather API in the backend. The `SystemOverview` schema has
no weather field.

**What's needed:** Integrate a weather service (Open-Meteo is free) and expose
`GET /api/weather/current → {temp_c, condition}`.

---

## Removed: Real energy data / "−12% vs avg"

**Design showed:** "8.4 kWh · −12% vs avg" and a real 7-day bar chart.

**Why removed:** No `/api/energy` endpoint. The backend has no historical
energy aggregation or metering.

**Current behaviour:** Values are estimated from active device count
(`8.4 + devicesOn × 0.3 kWh`). The 7-day bars are synthetic fractions.
A disclaimer is shown in the Energy screen.

**What's needed:** Persist device-on/off events with timestamps; expose
`GET /api/energy/summary → {today_kwh, avg_7d_kwh, daily: [{day, kwh}]}`.

---

## Removed: Office room card

**Design showed:** An "Office" room card in the rooms grid.

**Why removed:** Backend room IDs are `living_room`, `bedroom`, `kitchen`,
`bathroom`, `hallway`. There is no `office` room ID in the system overview.

**What's needed:** Add `office` to the room configuration and MQTT topic tree.

---

## Removed: Blinds actuator

**Design showed:** "Blinds 70%" in the Living Room device list.

**Why removed:** No blinds actuator present in any room's `actuators` dict
in the default backend configuration.

**What's needed:** Add `blinds` to the actuator schema with a percentage
value type (currently all actuators are `"ON" | "OFF"` only).

---

## Removed: Lux / CO₂ sensor readings

**Design showed:** Lux and CO₂ values next to temperature.

**Why removed:** `Room` schema has only `temperature`, `humidity`, `motion`
(int), `smoke` (int). No `lux` or `co2` fields exist.

**What's needed:** Add sensor fields to the Room Pydantic model and publish on
`home/{room}/sensor/light` and `home/{room}/sensor/co2` MQTT topics.

---

## Removed: AI decision trace timeline

**Design showed:** A 5-step timeline (Sensor trigger → Context → Decision →
Confidence → Action taken) on the "Why?" screen.

**Why removed:** `GET /api/system/diagnostics` exists but returns aggregate
diagnostics, not a per-decision trace with steps. There is no confidence field
in the diagnostics payload.

**Current behaviour:** The AI decision card ("NeuroNest decided") is rendered
only when a non-null last decision can be constructed from diagnostics. The "Why?"
button opens a modal (not yet wired to a real trace).

**What's needed:** Persist AI decisions with
`{id, timestamp, room, trigger, context, action, confidence, steps: []}`;
expose via `GET /api/decisions?limit=20`.

---

## Removed: Confidence percentage

**Design showed:** "94% confidence" badge on the AI decision card.

**Why removed:** The diagnostics endpoint does not include a confidence score
in its payload.

**What's needed:** Have the AI/rules engine emit a confidence value per
decision and include it in the decision schema.

---

## Removed: Dishwasher / off-peak scheduling suggestion

**Design showed:** "Run dishwasher at 23:00 — save £0.40" suggestion chip.

**Why removed:** No schedulable appliances, no electricity tariff data,
no `/api/suggestions` endpoint.

**What's needed:** A new suggestions service that scans heavy-load devices
(dishwasher, washing machine) and cross-references an electricity tariff
schedule.

---

## What IS working

| Feature | Status |
|---|---|
| Home glance (temp, humidity, device count, mode) | ✅ real data |
| Room cards grid with occupancy dot | ✅ real data |
| Room detail (temp, humidity dial, device list) | ✅ real data |
| Device toggle switches | ✅ calls `POST /api/rooms/{room}/actuators/{device}?state=ON\|OFF` |
| Optimistic toggle with revert on error | ✅ |
| Scene pills (Evening / Morning / Away) | ✅ calls `POST /api/system/demo?scenario=` |
| Mode switch (Auto / Manual / Away) | ✅ calls `POST /api/system/mode` |
| Energy screen (estimated kWh, synthetic bars) | ✅ with disclaimer |
| Tab navigation (Home / Rooms / Energy / Me) | ✅ |
| Back button from room detail | ✅ |
| "View on desktop" link | ✅ saves `localStorage.viewMode = 'desktop'` |
| Viewport-based auto-routing (≤820px → mobile) | ✅ |
| `?desktop=1` / `?mobile=1` override params | ✅ |
| Safe-area insets on tab bar | ✅ `env(safe-area-inset-bottom)` |
| Polling (3 s interval) | ✅ |
| Toast feedback on actions | ✅ |
