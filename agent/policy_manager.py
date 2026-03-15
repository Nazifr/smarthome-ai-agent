from datetime import datetime


class PolicyManager:
    """
    ML modelinin kararlarını kullanıcı tercihlerine ve
    güvenlik kısıtlarına göre filtreler.
    Son karar buradan çıkar.
    """

    def __init__(self):
        # Varsayılan kullanıcı tercihleri
        # Bunlar ileride Node-RED dashboard'dan güncellenecek
        self.preferences = {
            "quiet_hours_start": 23,    # 23:00'dan sonra sessiz mod
            "quiet_hours_end": 7,       # 07:00'a kadar sessiz mod
            "temp_min": 16,             # güvenlik alt sınırı (°C)
            "temp_max": 30,             # güvenlik üst sınırı (°C)
            "energy_saving_mode": False,
        }

        # Manuel override'lar: {"living_room_ac": "OFF_MANUAL"} gibi
        self.manual_overrides = {}

    def update_preferences(self, new_prefs: dict):
        """Node-RED veya kullanıcıdan gelen tercih güncellemesi."""
        self.preferences.update(new_prefs)

    def set_manual_override(self, device: str, state: str):
        """Kullanıcı manuel müdahale etti — agent bu cihaza dokunmayacak."""
        self.manual_overrides[device] = state

    def clear_override(self, device: str):
        """Manuel override kaldırıldı — agent tekrar kontrol alabilir."""
        self.manual_overrides.pop(device, None)

    def apply(self, action: dict, context: dict) -> dict:
        """
        action: {"device": "ac", "room": "bedroom", "command": "ON", "reason": "..."}
        context: ContextAnalyzer'dan gelen bağlam

        Döndürür: {"approved": True/False, "action": action, "reason": "..."}
        """
        device_key = f"{action.get('room', 'general')}_{action.get('device', 'unknown')}"
        hour = context.get("hour", 12)
        command = action.get("command", "")

        # ── Kural 1: Manuel Override Kontrolü ────────────────────────
        if device_key in self.manual_overrides:
            return {
                "approved": False,
                "action": action,
                "reason": f"Manuel override aktif: kullanıcı {device_key} cihazını manuel kontrol ediyor.",
            }

        # ── Kural 2: Quiet Hours Kontrolü ────────────────────────────
        quiet_start = self.preferences["quiet_hours_start"]
        quiet_end = self.preferences["quiet_hours_end"]
        in_quiet_hours = hour >= quiet_start or hour < quiet_end

        if in_quiet_hours and command == "ON" and action.get("device") in ["fan", "vacuum"]:
            return {
                "approved": False,
                "action": action,
                "reason": f"Sessiz saatler aktif ({quiet_start}:00-{quiet_end}:00). Gürültülü cihazlar çalıştırılmıyor.",
            }

        # ── Kural 3: Sıcaklık Güvenlik Sınırları ─────────────────────
        if action.get("device") == "heater" and command == "ON":
            if context.get("temperature", 20) >= self.preferences["temp_max"]:
                return {
                    "approved": False,
                    "action": action,
                    "reason": f"Sıcaklık zaten {context['temperature']}°C — ısıtıcı açılmıyor (güvenlik sınırı: {self.preferences['temp_max']}°C).",
                }

        if action.get("device") == "ac" and command == "ON":
            if context.get("temperature", 20) <= self.preferences["temp_min"]:
                return {
                    "approved": False,
                    "action": action,
                    "reason": f"Sıcaklık zaten {context['temperature']}°C — klima açılmıyor (minimum: {self.preferences['temp_min']}°C).",
                }

        # ── Kural 4: Enerji Tasarrufu Modu ───────────────────────────
        if self.preferences["energy_saving_mode"] and command == "ON":
            non_essential = ["fan", "lights"]
            if action.get("device") in non_essential and context.get("occupancy") == "bos":
                return {
                    "approved": False,
                    "action": action,
                    "reason": "Enerji tasarrufu modu aktif ve ev boş — gereksiz cihazlar açılmıyor.",
                }

        # ── Tüm kontroller geçildi, onay ver ─────────────────────────
        return {
            "approved": True,
            "action": action,
            "reason": action.get("reason", "Politika kontrolleri geçildi."),
        }
