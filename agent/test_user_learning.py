import tempfile
import unittest
from pathlib import Path

from user_learning import UserLearningStore


class UserLearningStoreTests(unittest.TestCase):
    def test_manual_feedback_becomes_matching_suggestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserLearningStore(Path(tmp) / "learning.json")
            context = {
                "room": "living_room",
                "time_period": "ogleden_sonra",
                "occupancy": "dolu",
                "light": 420,
            }

            store.record("living_room", "light", "OFF", context)
            suggestions = store.suggest(context)

            self.assertEqual(len(suggestions), 1)
            self.assertEqual(suggestions[0]["device"], "lights")
            self.assertEqual(suggestions[0]["command"], "OFF")
            self.assertEqual(suggestions[0]["method"], "learned")

    def test_suggestion_requires_matching_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = UserLearningStore(Path(tmp) / "learning.json")
            store.record("living_room", "light", "OFF", {
                "time_period": "ogleden_sonra",
                "occupancy": "dolu",
                "light": 420,
            })

            self.assertEqual(store.suggest({
                "room": "living_room",
                "time_period": "aksam",
                "occupancy": "dolu",
                "light": 40,
            }), [])


if __name__ == "__main__":
    unittest.main()
