import unittest
from unittest.mock import patch

from app.services import room_service
from app.services.mqtt_service import ACTUATOR_STATES, get_actuator_state, remember_actuator_state
from app.services.system_service import set_system_mode


class DemoContractTests(unittest.TestCase):
    def setUp(self):
        ACTUATOR_STATES.clear()
        room_service.CURRENT_DEMO = "live"
        room_service.DEMO_OVERRIDES = {}

    def test_unknown_actuators_default_to_off(self):
        self.assertEqual(get_actuator_state("bathroom", "ventilation_fan"), "OFF")

    def test_generic_fan_maps_to_room_specific_device(self):
        remember_actuator_state("kitchen", "fan", "ON")
        remember_actuator_state("bathroom", "fan", "ON")

        self.assertEqual(get_actuator_state("kitchen", "exhaust_fan"), "ON")
        self.assertEqual(get_actuator_state("bathroom", "ventilation_fan"), "ON")

    @patch("app.services.room_service.write_actuator_state")
    @patch("app.services.room_service.query_latest_sensor", return_value=22)
    @patch("app.services.room_service.publish")
    def test_kitchen_smoke_sets_sensor_override_and_exhaust(self, publish, _query, _write):
        status = room_service.set_demo_scenario("kitchen_smoke")

        self.assertEqual(status["active"], "kitchen_smoke")
        self.assertEqual(room_service.DEMO_OVERRIDES["kitchen"]["smoke"], 1)
        self.assertEqual(get_actuator_state("kitchen", "exhaust_fan"), "ON")
        publish.assert_any_call("home/system/demo", unittest.mock.ANY)

    @patch("app.services.room_service.write_actuator_state")
    @patch("app.services.room_service.query_latest_sensor", return_value=22)
    @patch("app.services.room_service.publish")
    def test_empty_home_clears_motion_and_turns_devices_off(self, _publish, _query, _write):
        remember_actuator_state("office", "ac", "COOL_LOW")
        status = room_service.set_demo_scenario("empty_home")

        self.assertEqual(status["active"], "empty_home")
        self.assertTrue(all(room["motion"] == 0 for room in room_service.DEMO_OVERRIDES.values()))
        self.assertEqual(get_actuator_state("office", "ac"), "OFF")

    @patch("app.services.room_service.publish")
    def test_user_feedback_is_published_for_learning(self, publish):
        payload = room_service.send_user_feedback(
            "living_room",
            "light",
            "OFF",
            {"temperature": 22, "humidity": 50, "motion": 1, "smoke": 0, "light": 420},
        )

        self.assertEqual(payload["device"], "light")
        self.assertEqual(payload["command"], "OFF")
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[0], "home/living_room/feedback")

    @patch("app.services.system_service.publish")
    def test_system_modes_are_published(self, publish):
        result = set_system_mode("AI")

        self.assertEqual(result.mode, "AI")
        publish.assert_called_with("home/system/mode", {"mode": "AI"})


if __name__ == "__main__":
    unittest.main()
