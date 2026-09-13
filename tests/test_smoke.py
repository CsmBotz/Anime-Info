import unittest

class SmokeTest(unittest.TestCase):
    def test_core_imports(self):
        """Smoke test to ensure all core project utilities and templates work without errors."""
        import bot.config
        import bot.utils.logging
        import bot.utils.formatting
        import webapp.backend.auth
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
