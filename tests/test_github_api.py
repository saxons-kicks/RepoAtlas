import json
import unittest
from unittest.mock import patch

from repoatlas.github_api import fetch_user_stars


class FakeResponse:
    def __init__(self, payload, link=""):
        self._payload = json.dumps(payload).encode("utf-8")
        self.headers = {"Link": link}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._payload


class GitHubApiTests(unittest.TestCase):
    @patch("repoatlas.github_api.urllib.request.urlopen")
    def test_paginates_starred_repositories_and_keeps_star_timestamp(self, urlopen):
        first = [{"starred_at": "2026-10-01T12:00:00Z", "repo": {
            "full_name": "octo-org/first", "html_url": "https://github.com/octo-org/first",
            "description": "First", "private": False, "topics": ["python"]
        }}]
        second = [{"starred_at": "2026-10-02T12:00:00Z", "repo": {
            "full_name": "octo-org/second", "html_url": "https://github.com/octo-org/second",
            "description": "Second", "private": True
        }}]
        urlopen.side_effect = [
            FakeResponse(first, '<https://api.github.com/user/starred?per_page=100&page=2>; rel="next"'),
            FakeResponse(second),
        ]
        repos = fetch_user_stars(token="test-token")
        self.assertEqual([repo.full_name for repo in repos], ["octo-org/first", "octo-org/second"])
        self.assertEqual(repos[0].starred_at, "2026-10-01T12:00:00Z")
        self.assertTrue(repos[1].private)
        self.assertEqual(urlopen.call_count, 2)


    @patch("repoatlas.github_api.urllib.request.urlopen")
    def test_repository_metadata_keeps_id_and_fork_origin(self, urlopen):
        from repoatlas.github_api import fetch_repository_metadata

        payload = {
            "id": 42,
            "full_name": "octo-org/forked-tool",
            "html_url": "https://github.com/octo-org/forked-tool",
            "description": "Forked utility",
            "fork": True,
            "parent": {"id": 7, "full_name": "upstream/tool"},
            "source": {"id": 7, "full_name": "upstream/tool"},
            "license": {"spdx_id": "MIT"},
            "topics": ["qa", "automation"],
            "default_branch": "main",
            "created_at": "2026-01-01T00:00:00Z",
            "visibility": "public",
        }
        urlopen.return_value = FakeResponse(payload)
        repository, status, error = fetch_repository_metadata("old-owner/old-name", token="test-token")
        self.assertEqual(status, "enriched")
        self.assertIsNone(error)
        self.assertEqual(repository.repository_id, "42")
        self.assertEqual(repository.parent_repository_id, "7")
        self.assertEqual(repository.source_full_name, "upstream/tool")
        self.assertEqual(repository.aliases, ["old-owner/old-name"])
        self.assertEqual(repository.license_spdx, "MIT")

    @patch("repoatlas.github_api.fetch_repository_metadata")
    def test_enrichment_only_queries_bookmark_names_absent_from_stars(self, fetch_metadata):
        from repoatlas.github_api import enrich_bookmark_repositories
        from repoatlas.models import Bookmark, StarredRepository

        stars = [StarredRepository("acme/existing", "https://github.com/acme/existing", repository_id="1")]
        bookmarks = [
            Bookmark("Existing", "https://github.com/acme/existing"),
            Bookmark("Renamed", "https://github.com/old-owner/old-name"),
        ]
        resolved = StarredRepository(
            "new-owner/new-name",
            "https://github.com/new-owner/new-name",
            repository_id="2",
            aliases=["old-owner/old-name"],
            metadata_status="enriched",
        )
        fetch_metadata.return_value = (resolved, "enriched", None)
        enriched, results = enrich_bookmark_repositories(bookmarks, stars, token="test-token")
        fetch_metadata.assert_called_once_with("old-owner/old-name", token="test-token")
        self.assertEqual(len(enriched), 1)
        self.assertEqual(results["old-owner/old-name"]["resolved_full_name"], "new-owner/new-name")


if __name__ == "__main__":
    unittest.main()
