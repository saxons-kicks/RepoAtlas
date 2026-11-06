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


if __name__ == "__main__":
    unittest.main()
