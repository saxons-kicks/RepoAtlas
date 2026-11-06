"""URL normalization and GitHub repository identity helpers."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

_GITHUB_HOSTS = {"github.com", "www.github.com"}
_NON_REPO_FIRST_SEGMENTS = {
    "about", "apps", "collections", "codespaces", "dashboard", "enterprise",
    "events", "explore", "features", "login", "marketplace", "new", "notifications",
    "orgs", "organizations", "pricing", "pulls", "search", "security", "settings",
    "sponsors", "topics", "trending", "users",
}


def canonical_url(url: str) -> str:
    """Normalize a URL for duplicate detection without changing its meaning."""
    value = (url or "").strip()
    if not value:
        return ""
    if "@github.com:" in value:  # git@github.com:owner/repo.git
        value = "https://github.com/" + value.split("@github.com:", 1)[1]
    elif value.startswith("git://github.com/"):
        value = "https://github.com/" + value.removeprefix("git://github.com/")
    elif not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value

    parts = urlsplit(value)
    scheme = parts.scheme.lower() or "https"
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+", "/", parts.path or "/").rstrip("/") or "/"
    if host in _GITHUB_HOSTS:
        path = path.removesuffix(".git")
        path = "/" + "/".join(p for p in path.split("/") if p).lower()
        if path == "":
            path = "/"
    # Fragments and query parameters are tracking/UI state for bookmark identity.
    return urlunsplit((scheme, host, path, "", ""))


def github_repo_full_name(url: str) -> str | None:
    """Return owner/repo for a GitHub repository or nested repository URL."""
    value = (url or "").strip()
    if "@github.com:" in value:
        value = "https://github.com/" + value.split("@github.com:", 1)[1]
    elif value.startswith("git://github.com/"):
        value = "https://github.com/" + value.removeprefix("git://github.com/")
    elif not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value

    parts = urlsplit(value)
    if (parts.hostname or "").lower().removeprefix("www.") != "github.com":
        return None
    segments = [s for s in parts.path.split("/") if s]
    if len(segments) < 2 or segments[0].lower() in _NON_REPO_FIRST_SEGMENTS:
        return None
    owner, repo = segments[0], segments[1]
    repo = repo.removesuffix(".git")
    if not owner or not repo or any(ch in owner + repo for ch in "<>\"' "):
        return None
    return f"{owner}/{repo}".lower()
