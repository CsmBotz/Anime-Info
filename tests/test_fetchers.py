import unittest
from bot.utils.formatting import escape_html, clean_synopsis

class FetcherAndFormatTest(unittest.TestCase):
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

    def test_episode_ranges(self):
        try:
            from bot.fetchers.filler_list import FillerFetcher
            res = FillerFetcher.format_episode_ranges([1, 2, 3, 5, 7, 8, 9])
            self.assertEqual(res, "1-3, 5, 7-9")
        except ImportError:
            pass

if __name__ == "__main__":
    unittest.main()
