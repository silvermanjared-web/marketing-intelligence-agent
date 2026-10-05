import unittest

from src.core.capabilities import invoke


class SecurityTests(unittest.TestCase):
    def test_undeclared_operation_is_refused(self):
        result = invoke("system.unbounded", confirm=True)
        self.assertEqual(result["status"], "refused")

    def test_write_capability_fails_closed_without_confirmation(self):
        result = invoke("files.organize.apply", confirm=False)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["effect"], "write")


if __name__ == "__main__":
    unittest.main()
