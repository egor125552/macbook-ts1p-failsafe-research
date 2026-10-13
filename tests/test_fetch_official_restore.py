import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'fetch_official_restore', ROOT / 'tools' / 'fetch_official_restore.py'
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class OfficialRestoreTests(unittest.TestCase):
    def test_manifest_is_pinned_to_expected_build(self):
        m = mod.MANIFEST
        self.assertEqual(m['device'], 'Mac16,12')
        self.assertEqual(m['board'], 'J713AP')
        self.assertEqual(m['build'], '26A428')
        self.assertEqual(m['filename'], 'UniversalMac_27.0_26A428_Restore.ipsw')
        self.assertEqual(
            m['sha256'],
            '2a5d3c695d501022b7fad9adaffcf2627bcb867d993fb5662dcd41bac99a2836',
        )
        self.assertEqual(m['size'], 26626436228)

    def test_only_https_apple_cdn_is_accepted(self):
        mod.validate_url(mod.MANIFEST['url'])
        for bad in [
            'http://updates.cdn-apple.com/file.ipsw',
            'https://example.com/file.ipsw',
            'https://updates.cdn-apple.com.example.org/file.ipsw',
        ]:
            with self.assertRaises(ValueError):
                mod.validate_url(bad)

    def test_sha256_file(self):
        p = ROOT / 'tests' / '.sha-fixture'
        try:
            p.write_bytes(b'abc')
            self.assertEqual(
                mod.sha256_file(p),
                'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
            )
        finally:
            p.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
