import os
from influxdb_client import InfluxDBClient

INFLUX_URL        = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN      = os.getenv("INFLUX_TOKEN", "smarthome-super-secret-token")
INFLUX_ORG        = os.getenv("INFLUX_ORG", "smarthome")
INFLUX_BUCKET     = os.getenv("INFLUX_BUCKET", "sensor_data")
INFLUX_MEASUREMENT = "sensor_reading"


def get_client():
    return InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )


def get_influx_status():
    client = get_client()
    try:
        ok = bool(client.ping())
        return {
            "ok": ok,
            "label": "InfluxDB",
            "detail": "reachable" if ok else "ping failed",
        }
    except Exception as e:
        return {
            "ok": False,
            "label": "InfluxDB",
            "detail": str(e),
        }
    finally:
        client.close()


def query_latest_sensor(room_id: str, sensor_type: str):
    client = get_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "{INFLUX_MEASUREMENT}")
      |> filter(fn: (r) => r._field == "{sensor_type}")
      |> filter(fn: (r) => r.room == "{room_id}")
      |> last()
    '''

    try:
        tables = query_api.query(query, org=INFLUX_ORG)

        for table in tables:
            for record in table.records:
                return record.get_value()

        return None

    finally:
        client.close()


def query_sensor_history(room_id: str, sensor_type: str, minutes: int = 60):
    client = get_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "{INFLUX_MEASUREMENT}")
      |> filter(fn: (r) => r._field == "{sensor_type}")
      |> filter(fn: (r) => r.room == "{room_id}")
      |> sort(columns: ["_time"])
    '''

    try:
        tables = query_api.query(query, org=INFLUX_ORG)
        points = []

        for table in tables:
            for record in table.records:
                points.append({
                    "time": record.get_time().isoformat(),
                    "value": float(record.get_value())
                })

        return points

    finally:
        client.close()


def write_actuator_state(room_id: str, device: str, state: str):
    """Write actuator state (ON/OFF) to InfluxDB for energy tracking."""
    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        client = get_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("actuator_state")
            .tag("room", room_id)
            .tag("device", device)
            .field("state", 1 if state == "ON" else 0)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        client.close()
    except Exception as e:
        print(f"[InfluxDB] Failed to write actuator state: {e}")


def query_actuator_states(start: str = "-24h"):
    """Query all actuator_state records for the given range.
    Returns dict of (room, device) -> [{time, state}] sorted by time."""
    client = get_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {start})
      |> filter(fn: (r) => r._measurement == "actuator_state")
      |> filter(fn: (r) => r._field == "state")
      |> sort(columns: ["_time"])
    '''

    try:
        tables = query_api.query(query, org=INFLUX_ORG)
        device_records = {}
        for table in tables:
            for record in table.records:
                key = (record.values.get("room", ""), record.values.get("device", ""))
                if key not in device_records:
                    device_records[key] = []
                device_records[key].append({
                    "time": record.get_time(),
                    "state": int(record.get_value()),
                })
        return device_records
    except Exception as e:
        print(f"[InfluxDB] Failed to query actuator states: {e}")
        return {}
    finally:
        client.close()


def query_recent_actions(minutes: int = 240, limit: int = 12):
    client = get_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "action_log")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: {limit})
    '''

    try:
        tables = query_api.query(query, org=INFLUX_ORG)
        actions = []

        for table in tables:
            for record in table.records:
                values = record.values
                actions.append({
                    "time": record.get_time().isoformat(),
                    "room": values.get("room", "unknown"),
                    "device": values.get("device", "device"),
                    "command": values.get("command", "UNKNOWN"),
                    "reason": values.get("reason", ""),
                    "context": values.get("context", "unknown"),
                })

        return sorted(actions, key=lambda item: item["time"], reverse=True)[:limit]

    finally:
        client.close()
