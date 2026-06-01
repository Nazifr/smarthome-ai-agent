import json
import os
import tempfile
import time
from pathlib import Path


LEARNING_PATH = Path(os.getenv(
    "USER_LEARNING_PATH",
    os.path.join(os.path.dirname(__file__), "user_learning.json"),
))


def _device_key(device: str) -> str:
    return "lights" if device == "light" else device


def _light_bucket(light: float) -> str:
    if light >= 300:
        return "bright"
    if light >= 80:
        return "dim"
    return "dark"


def _rule_key(room: str, device: str, context: dict) -> str:
    return "|".join([
        room,
        _device_key(device),
        str(context.get("time_period", "unknown")),
        str(context.get("occupancy", "unknown")),
        _light_bucket(float(context.get("light", 0))),
    ])


class UserLearningStore:
    def __init__(self, path: Path = LEARNING_PATH):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {
                "feedback_count": 0,
                "rules": {},
                "last_feedback": None,
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "feedback_count": 0,
                "rules": {},
                "last_feedback": None,
            }

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".user_learning.", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(self.data, tmp, indent=2, ensure_ascii=False)
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def record(self, room: str, device: str, command: str, context: dict) -> dict:
        normalized_device = _device_key(device)
        key = _rule_key(room, normalized_device, context)
        now = int(time.time())

        rule = self.data["rules"].get(key, {
            "room": room,
            "device": normalized_device,
            "time_period": context.get("time_period", "unknown"),
            "occupancy": context.get("occupancy", "unknown"),
            "light_bucket": _light_bucket(float(context.get("light", 0))),
            "commands": {},
            "count": 0,
            "created_at": now,
            "last_seen": now,
        })

        rule["commands"][command] = int(rule["commands"].get(command, 0)) + 1
        rule["count"] = int(rule.get("count", 0)) + 1
        rule["last_seen"] = now
        self.data["rules"][key] = rule
        self.data["feedback_count"] = int(self.data.get("feedback_count", 0)) + 1
        self.data["last_feedback"] = {
            "room": room,
            "device": normalized_device,
            "command": command,
            "time_period": rule["time_period"],
            "occupancy": rule["occupancy"],
            "light_bucket": rule["light_bucket"],
            "timestamp": now,
        }
        self._save()
        return rule

    def suggest(self, context: dict) -> list[dict]:
        room = context.get("room", "living_room")
        occupancy = context.get("occupancy", "unknown")
        time_period = context.get("time_period", "unknown")
        light_bucket = _light_bucket(float(context.get("light", 0)))
        suggestions = []

        for rule in self.data.get("rules", {}).values():
            if rule.get("room") != room:
                continue
            if rule.get("occupancy") != occupancy:
                continue
            if rule.get("time_period") != time_period:
                continue
            if rule.get("device") == "lights" and rule.get("light_bucket") != light_bucket:
                continue

            command_counts = rule.get("commands", {})
            if not command_counts:
                continue
            command, count = max(command_counts.items(), key=lambda item: item[1])
            total = max(1, int(rule.get("count", 1)))
            confidence = min(0.99, 0.70 + (count / total) * 0.20 + min(total, 5) * 0.02)
            suggestions.append({
                "device": rule.get("device", "lights"),
                "command": command,
                "reason": (
                    f"Learned preference from {total} manual choice(s): "
                    f"{room} {rule.get('device')} -> {command} during {time_period}/{light_bucket}"
                ),
                "confidence": confidence,
                "method": "learned",
                "learned": True,
            })

        return suggestions

    def summary(self) -> dict:
        rules = list(self.data.get("rules", {}).values())
        return {
            "feedback_count": int(self.data.get("feedback_count", 0)),
            "rule_count": len(rules),
            "last_feedback": self.data.get("last_feedback"),
            "top_rules": sorted(rules, key=lambda r: (r.get("count", 0), r.get("last_seen", 0)), reverse=True)[:5],
        }
