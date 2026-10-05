import unittest

from src.core import capabilities


class CapabilityTests(unittest.TestCase):
    def test_discovery_declares_effects(self):
        registry = capabilities.discover()
        self.assertEqual(registry["intelligence.brief"]["effect"], "read")
        self.assertEqual(registry["files.organize.apply"]["effect"], "write")

    def test_unknown_capability_refuses(self):
        result = capabilities.invoke("unknown.operation", confirm=True)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], "unknown capability")

    def test_write_requires_confirmation(self):
        result = capabilities.invoke("files.organize.apply", confirm=False)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["effect"], "write")


if __name__ == "__main__":
    unittest.main()
