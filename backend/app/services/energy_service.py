"""
Energy tracking service.

Calculates energy usage from actuator ON/OFF state changes logged to InfluxDB.
Each device has an estimated wattage; ON-hours × watts = energy consumed.
"""

from datetime import datetime, timezone, timedelta
from app.services.influx_service import query_actuator_states
from app.services.mqtt_service import ACTUATOR_STATES

# Estimated wattage per device type (watts)
DEVICE_WATTS = {
    "light":           10,
    "fan":             45,
    "ac":            1200,
    "exhaust_fan":     30,
    "ventilation_fan": 35,
}

DEFAULT_WATTS = 20  # for unknown devices


def _calculate_on_hours(records, period_end):
    """Walk a sorted list of {time, state} records and sum ON-duration."""
    on_since = None
    total_seconds = 0.0

    for rec in records:
        if rec["state"] == 1 and on_since is None:
            on_since = rec["time"]
        elif rec["state"] == 0 and on_since is not None:
            total_seconds += (rec["time"] - on_since).total_seconds()
            on_since = None

    # If still ON at end of period, count up to period_end
    if on_since is not None:
        total_seconds += (period_end - on_since).total_seconds()

    return max(0.0, total_seconds / 3600.0)


def _watts_for(device_name: str) -> int:
    """Look up wattage for a device name."""
    name = device_name.lower()
    for pattern, watts in DEVICE_WATTS.items():
        if pattern in name:
            return watts
    return DEFAULT_WATTS


def _active_device_estimate():
    """Fallback estimate from currently-ON devices (no InfluxDB data needed)."""
    total_watts = 0
    for room_id, devices in ACTUATOR_STATES.items():
        for device, state in devices.items():
            if state == "ON":
                total_watts += _watts_for(device)
    # Assume average 4 hours of use today as rough baseline
    return round(total_watts * 4 / 1000, 2)


def get_energy_summary():
    """Return energy summary for today + 7-day history."""
    now = datetime.now(timezone.utc)

    # Query last 7 days of actuator state data
    device_records = query_actuator_states("-7d")

    # Bucket records by day and device
    daily_kwh = {}
    for day_offset in range(7):
        day_start = (now.replace(hour=0, minute=0, second=0, microsecond=0)
                     - timedelta(days=6 - day_offset))
        day_end = day_start + timedelta(days=1)
        if day_end > now:
            day_end = now

        day_label = day_start.strftime("%a")
        day_date  = day_start.strftime("%Y-%m-%d")
        day_total_wh = 0.0
        day_breakdown = []

        for (room, device), all_records in device_records.items():
            day_records = []
            last_before = None
            for rec in all_records:
                if rec["time"] < day_start:
                    last_before = rec
                elif rec["time"] <= day_end:
                    day_records.append(rec)

            if last_before is not None:
                day_records.insert(0, {"time": day_start, "state": last_before["state"]})

            if not day_records:
                continue

            on_hours = _calculate_on_hours(day_records, day_end)
            watts = _watts_for(device)
            day_total_wh += on_hours * watts

            if on_hours > 0:
                day_breakdown.append({
                    "room":     room,
                    "device":   device,
                    "on_hours": round(on_hours, 2),
                    "kwh":      round(on_hours * watts / 1000, 3),
                    "watts":    watts,
                })

        day_breakdown.sort(key=lambda x: x["kwh"], reverse=True)
        daily_kwh[day_offset] = {
            "day":       day_label,
            "date":      day_date,
            "kwh":       round(day_total_wh / 1000, 2),
            "breakdown": day_breakdown,
        }

    daily = [daily_kwh[i] for i in range(7)]
    today_kwh = daily[-1]["kwh"] if daily else 0
    prev_days = [d["kwh"] for d in daily[:-1] if d["kwh"] > 0]
    avg_kwh = round(sum(prev_days) / len(prev_days), 2) if prev_days else 0

    if today_kwh == 0 and all(d["kwh"] == 0 for d in daily):
        fallback = _active_device_estimate()
        today_kwh = fallback
        daily[-1]["kwh"] = fallback

    delta_pct = round(
        (today_kwh - avg_kwh) / avg_kwh * 100, 1
    ) if avg_kwh > 0 else 0

    return {
        "today_kwh":   today_kwh,
        "avg_7d_kwh":  avg_kwh,
        "delta_pct":   delta_pct,
        "daily":       daily,
        "breakdown":   daily[-1]["breakdown"],  # today's breakdown for backward compat
    }
