import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fault_decode", ROOT / "tools" / "fault_decode.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class FaultDecodeTests(unittest.TestCase):
    def test_persistent_ts1p_bit(self):
        self.assertEqual(mod.set_bits(0x1000), [12])

    def test_current_ts0p_ts1p_bits(self):
        self.assertEqual(mod.set_bits(0x1800), [11, 12])

    def test_raw_hex_order_matches_live_smc_output(self):
        self.assertEqual(mod.raw_hex_bytes_to_numeric("00001000"), 0x1000)
        self.assertEqual(mod.raw_hex_bytes_to_numeric("00001800"), 0x1800)


if __name__ == "__main__":
    unittest.main()
