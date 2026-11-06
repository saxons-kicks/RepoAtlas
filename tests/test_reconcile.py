import unittest

from repoatlas.models import Bookmark, StarredRepository
from repoatlas.reconcile import reconcile


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.bookmarks = [
            Bookmark("Repo both", "https://github.com/acme/both", ["Tecnologia", "QA & Testes"]),
            Bookmark("Repo bookmarked", "https://github.com/acme/bookmarked", ["Trabalho", "Interno"], private_context=True),
            Bookmark("Article", "https://example.com/article", ["Estudos"]),
        ]
        self.stars = [
            StarredRepository("acme/both", "https://github.com/acme/both", "Testing utility", "Python", 123, 4, False, "2026-10-01T00:00:00Z", "2026-10-02T00:00:00Z", "MIT", ["testing"]),
            StarredRepository("acme/starred", "https://github.com/acme/starred", "AI toolkit", "Python"),
        ]

    def test_classifies_both_sources(self):
        catalog, summary = reconcile(self.bookmarks, self.stars, compared=True)
        statuses = {item["full_name"]: item["status"] for item in catalog}
        self.assertEqual(statuses["acme/both"], "both")
        self.assertEqual(statuses["acme/bookmarked"], "bookmark_only")
        self.assertEqual(statuses["acme/starred"], "star_only")
        self.assertEqual(summary["both"], 1)
        self.assertEqual(summary["star_only"], 1)
        self.assertEqual(summary["bookmark_only"], 1)

    def test_bookmarks_only_does_not_mislabel_as_bookmark_only(self):
        catalog, summary = reconcile(self.bookmarks, [], compared=False)
        self.assertTrue(all(item["status"] == "not_compared" for item in catalog))
        self.assertEqual(summary["not_compared"], 2)

    def test_private_context_is_carried_only_as_boolean(self):
        catalog, _ = reconcile(self.bookmarks, self.stars, compared=True)
        internal = next(item for item in catalog if item["full_name"] == "acme/bookmarked")
        self.assertTrue(internal["private_context"])
        self.assertEqual(internal["bookmark_paths"], [["Trabalho", "Interno"]])

    def test_private_github_repository_is_flagged_for_local_handling(self):
        private_star = StarredRepository(
            full_name="acme/private-repo",
            html_url="https://github.com/acme/private-repo",
            private=True,
        )
        catalog, _ = reconcile([], [private_star], compared=True)
        self.assertTrue(catalog[0]["private_context"])
        self.assertTrue(catalog[0]["repository_private"])


if __name__ == "__main__":
    unittest.main()
