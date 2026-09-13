import unittest
from webapp.backend.auth import validate_telegram_init_data

class WebAppAuthTest(unittest.TestCase):
    def test_invalid_init_data(self):
        res = validate_telegram_init_data("invalid_data")
        self.assertIsNone(res)

if __name__ == "__main__":
    unittest.main()

