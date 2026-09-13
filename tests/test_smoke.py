import unittest

class SmokeTest(unittest.TestCase):
    def test_imports(self):
        """Smoke test to ensure all core project files syntax and structure are valid."""
        import bot.config
        import bot.utils.logging
        import bot.utils.formatting
        import bot.fetchers.filler_list
        import webapp.backend.auth
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()

