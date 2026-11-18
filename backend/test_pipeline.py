import unittest
from nlp_pipeline import make_chapters
from pdf_pipeline import clean_text


class PipelineTests(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(clean_text("Hello\r\n\r\n\nWorld"), "Hello\n\nWorld")

    def test_detects_chapter_headings(self):
        chapters = make_chapters("Chapter 1: Start\nFirst story.\n\nChapter 2: Next\nSecond story.", 1000)
        self.assertEqual(len(chapters), 2)
        self.assertIn("Chapter 1", chapters[0]["title"])
        self.assertIn("Second story", chapters[1]["text"])

    def test_splits_long_text(self):
        chapters = make_chapters(" ".join(["word"] * 500), 300)
        self.assertGreater(len(chapters), 1)
        self.assertTrue(all(len(chapter["text"]) <= 300 for chapter in chapters))


if __name__ == "__main__":
    unittest.main()
