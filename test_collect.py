import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("collect", ROOT / "collect.py")
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "sources.json").read_text())
        self.source = self.config["sources"][0]
        self.now = datetime(2026, 10, 30, 8, tzinfo=timezone.utc)
        self.item = {"title": "Spatial audio", "url": "https://aes.org/news/test/?utm_source=x#top",
                     "date": "2026-10-29T08:00:00Z", "description": "A useful update.", "search_text": "spatial audio"}

    def test_dates_reject_future_missing_old_and_naive(self):
        for value in [None, "2026-10-31T08:00:00Z", "2020-01-01T00:00:00Z", "2026-10-29T08:00:00"]:
            with self.assertRaises((ValueError, TypeError)):
                c.normalize({**self.item, "date": value}, self.source, self.config, self.now)

    def test_dedup_tracking_and_preserve_first_seen(self):
        record = c.normalize(self.item, self.source, self.config, self.now)
        second = c.normalize({**self.item, "url": "https://aes.org/news/test"}, self.source, self.config, self.now + timedelta(days=1))
        records = c.merge([record], [second])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["first_seen_at"], c.iso(self.now))
        self.assertEqual(records[0]["last_seen_at"], c.iso(self.now + timedelta(days=1)))

    def test_filter_url_and_plain_text(self):
        self.assertIsNone(c.normalize({**self.item, "title": "Video only", "search_text": "codec for pictures"}, self.source, self.config, self.now))
        for url in ["javascript:alert(1)", "https://evil.example/x", "https://user:pass@aes.org/x"]:
            with self.assertRaises(ValueError): c.normalize({**self.item, "url": url}, self.source, self.config, self.now)
        self.assertNotIn("alert", c.plain("<p>Text</p><script>alert(1)</script>"))

    def test_limit_diversity_and_history(self):
        records = []
        for i in range(9):
            source = self.config["sources"][i // 3]
            from urllib.parse import urlsplit
            url = "https://" + urlsplit(source["homepage"]).hostname + source.get("article_path_prefix", "/news/") + str(i)
            records.append(c.normalize({**self.item, "url": url}, source, self.config, self.now))
        selected = c.select(c.merge([], records), self.config, self.now)
        self.assertEqual(len(selected), 5)
        self.assertEqual(len({x["source_id"] for x in selected}), 3)
        self.assertEqual(len(records), 9)

    def test_rss_and_release_parser_reject_unpublished(self):
        raw = b'<rss><channel><item><title>A</title><link>https://aes.org/a</link><pubDate>Thu, 29 Oct 2026 08:00:00 GMT</pubDate><description>&lt;p&gt;HRTF&lt;/p&gt;</description></item></channel></rss>'
        self.assertEqual(c.rss_items(raw)[0]["description"], "HRTF")
        data = [{"tag_name": "v1", "html_url": "https://github.com/a/b/releases/tag/v1", "published_at": "2026-10-29T08:00:00Z"}, {"draft": True}, {"prerelease": True}]
        self.assertEqual(len(c.release_items(json.dumps(data).encode())), 1)
        with self.assertRaises(ValueError): c.rss_items(b'<!DOCTYPE x><rss/>')

    def test_headline_category_precedes_body_and_overviews_are_excluded(self):
        item = {**self.item, "title": "Dolby Atmos announcement", "search_text": "A panel also covers binaural audio."}
        self.assertEqual(c.normalize(item, self.source, self.config, self.now)["category"], "Produzione e ascolto immersivo")
        mpeg = self.config["sources"][1]
        item = {**self.item, "url": "https://www.mpeg.org/overview", "title": "Introduction to ISO/IEC", "search_text": "MPEG-I immersive audio"}
        self.assertIsNone(c.normalize(item, mpeg, self.config, self.now))

    def test_total_source_failure_preserves_archive_and_reports_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(c, "fetch", side_effect=lambda s: ([self.item], {"id": s["id"], "name": s["name"], "status": "ok"})):
                c.collect(ROOT / "sources.json", output)
            initial = json.loads((output / "history/articles.json").read_text())
            with patch.object(c, "fetch", side_effect=lambda s: ([], {"id": s["id"], "name": s["name"], "status": "error"})):
                c.collect(ROOT / "sources.json", output)
            self.assertEqual(json.loads((output / "history/articles.json").read_text()), initial)
            self.assertEqual(json.loads((output / "public/news-pilot.json").read_text())["status"], "error")


if __name__ == "__main__": unittest.main()
