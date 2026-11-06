import unittest

from repoatlas.normalization import canonical_url, github_repo_full_name


class NormalizationTests(unittest.TestCase):
    def test_repo_identity_from_nested_url(self):
        self.assertEqual(github_repo_full_name("https://github.com/Owner/Repo/tree/main/src?tab=readme"), "owner/repo")

    def test_repo_identity_from_git_remote(self):
        self.assertEqual(github_repo_full_name("git@github.com:Owner/Repo.git"), "owner/repo")

    def test_non_repository_github_pages_are_skipped(self):
        self.assertIsNone(github_repo_full_name("https://github.com/topics/python"))
        self.assertIsNone(github_repo_full_name("https://github.com/owner"))

    def test_url_tracking_data_removed(self):
        self.assertEqual(
            canonical_url("https://www.github.com/Owner/Repo?tab=readme#top"),
            "https://github.com/owner/repo",
        )


if __name__ == "__main__":
    unittest.main()
