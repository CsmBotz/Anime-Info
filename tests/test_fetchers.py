import unittest
from bot.fetchers.filler_list import FillerFetcher
from bot.utils.formatting import escape_html, clean_synopsis

class FetcherTest(unittest.TestCase):
    def test_filler_fetcher(self):
        info = FillerFetcher.get_filler_info("naruto")
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "Naruto")
        self.assertEqual(info["total_episodes"], 220)

    def test_formatting_escaping(self):
        raw = "<script>alert('xss')</script>"
        escaped = escape_html(raw)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)

    def test_clean_synopsis(self):
        raw = "<b>Good anime</b> with lots of action."
        cleaned = clean_synopsis(raw)
        self.assertNotIn("<b>", cleaned)
        self.assertIn("Good anime", cleaned)

if __name__ == "__main__":
    unittest.main()

