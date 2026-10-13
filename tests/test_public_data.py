import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicDataTests(unittest.TestCase):
    def test_sensor_history_is_full_and_contains_both_good_and_failed_samples(self):
        with (ROOT / "data" / "ts0p-ts1p-history.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 900)
        ts1 = [float(r["Ts1P_c"]) for r in rows if r["Ts1P_c"] not in ("", "None")]
        self.assertTrue(any(v > 15 for v in ts1))
        self.assertTrue(any(v == 0 for v in ts1))

    def test_budget_history_contains_normal_and_failsafe_package_values(self):
        with (ROOT / "data" / "xppt-xupt-history.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 879)
        values = [float(r["xPPT_watts"]) for r in rows if r["xPPT_watts"] not in ("", "None")]
        self.assertTrue(any(abs(v - 65.0) < 1e-6 for v in values))
        self.assertTrue(any(abs(v - 2.0) < 1e-6 for v in values))

    def test_isolated_replay_result_matches_documented_causal_experiment(self):
        obj = json.loads((ROOT / "data" / "smc-failsafe-replay.json").read_text())
        faulted = obj["fault_present"]
        cleared = obj["input_12_cleared"]
        self.assertEqual(faulted["package_watts"], 2.0)
        self.assertEqual(faulted["utility_watts"], 2.5)
        self.assertEqual(cleared["package_watts"], 65.0)
        self.assertEqual(cleared["utility_watts"], 30.0)


if __name__ == "__main__":
    unittest.main()
