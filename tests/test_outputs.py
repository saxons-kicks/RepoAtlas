import json
import tempfile
import unittest
from pathlib import Path

from repoatlas.outputs import export_public_catalog


class PublicExportTests(unittest.TestCase):
    def test_export_removes_private_and_user_membership_fields(self):
        payload = {
            "sources": {"bookmarks": "C:/Users/private/bookmarks.html", "github_stars": "GitHub REST API"},
            "summary": {"comparison_performed": True},
            "repositories": [
                {"full_name": "acme/public", "url": "https://github.com/acme/public", "status": "both", "sources": ["github_star", "browser_bookmark"], "bookmark_paths": [["Favorites"]], "private_context": False},
                {"full_name": "acme/private", "url": "https://github.com/acme/private", "private_context": True},
                {"full_name": "acme/private-api", "url": "https://github.com/acme/private-api", "repository_private": True},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "catalog.json"
            destination = base / "nested" / "public.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            stats = export_public_catalog(source, destination)
            exported = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(stats, {"exported": 1, "excluded_private": 2})
        self.assertEqual(exported["repositories"][0]["full_name"], "acme/public")
        self.assertNotIn("sources", exported["repositories"][0])
        self.assertNotIn("bookmark_paths", exported["repositories"][0])
        self.assertEqual(exported["sources"]["bookmarks"], "omitted from public export")


if __name__ == "__main__":
    unittest.main()
