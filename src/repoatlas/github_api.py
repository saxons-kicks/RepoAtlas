"""Read the authenticated user's GitHub Stars without storing credentials."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import StarredRepository

API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"


class GitHubAPIError(RuntimeError):
    pass


def _github_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        return token.strip()
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True,
            check=True, timeout=10,
        )
        value = result.stdout.strip()
        return value or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _parse_link_header(header: str) -> str | None:
    for item in header.split(","):
        if 'rel="next"' in item:
            match = re.search(r"<([^>]+)>", item)
            if match:
                return match.group(1)
    return None


def _repo_from_star_item(item: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    # The application/vnd.github.star+json media type wraps the repo object.
    if isinstance(item.get("repo"), dict):
        return item["repo"], item.get("starred_at")
    return item, item.get("starred_at")


def _license_spdx(repo: dict[str, Any]) -> str | None:
    license_data = repo.get("license")
    if isinstance(license_data, dict):
        return license_data.get("spdx_id") or license_data.get("name")
    return None


def _to_starred(item: dict[str, Any]) -> StarredRepository | None:
    repo, starred_at = _repo_from_star_item(item)
    full_name = repo.get("full_name")
    html_url = repo.get("html_url")
    if not full_name or not html_url:
        return None
    return StarredRepository(
        full_name=str(full_name).lower(),
        html_url=str(html_url),
        description=repo.get("description"),
        language=repo.get("language"),
        stargazers_count=repo.get("stargazers_count"),
        forks_count=repo.get("forks_count"),
        archived=bool(repo.get("archived", False)),
        pushed_at=repo.get("pushed_at"),
        updated_at=repo.get("updated_at"),
        license_spdx=_license_spdx(repo),
        topics=list(repo.get("topics") or []),
        starred_at=starred_at,
        private=bool(repo.get("private", False)),
    )


def _load_export(path: str) -> list[StarredRepository]:
    with open(path, "r", encoding="utf-8-sig") as stream:
        payload = json.load(stream)
    rows: Any = payload.get("repositories", payload.get("items", [])) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("O arquivo de Stars precisa conter uma lista de repositórios.")
    result = []
    for item in rows:
        if isinstance(item, dict):
            repo = _to_starred(item)
            if repo:
                result.append(repo)
    return result


def fetch_user_stars(token: str | None = None) -> list[StarredRepository]:
    """Fetch every starred repository using GitHub's paginated REST endpoint."""
    auth = token or _github_token()
    if not auth:
        raise GitHubAPIError(
            "Autenticação GitHub não encontrada. Execute `gh auth login` ou defina "
            "GITHUB_TOKEN. Alternativamente, importe um JSON com `--stars-json`."
        )

    url: str | None = f"{API_ROOT}/user/starred?per_page=100&sort=created&direction=desc"
    headers = {
        "Accept": "application/vnd.github.star+json",
        "Authorization": f"Bearer {auth}",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "RepoAtlas/0.1.0",
    }
    results: list[StarredRepository] = []
    while url:
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                page = json.loads(response.read().decode("utf-8"))
                next_url = _parse_link_header(response.headers.get("Link", ""))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code == 401:
                raise GitHubAPIError("GitHub rejeitou a autenticação (401). Execute `gh auth login` novamente.") from exc
            if exc.code == 403:
                raise GitHubAPIError(f"GitHub bloqueou a consulta (403). Verifique permissões e rate limit: {detail}") from exc
            raise GitHubAPIError(f"Falha na API do GitHub ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"Não foi possível acessar a API do GitHub: {exc.reason}") from exc

        if not isinstance(page, list):
            raise GitHubAPIError("Resposta inesperada da API de GitHub Stars.")
        for item in page:
            if isinstance(item, dict):
                repo = _to_starred(item)
                if repo:
                    results.append(repo)
        url = next_url
    return results


def load_stars(stars_json: str | None = None, use_github: bool = False) -> list[StarredRepository]:
    if stars_json:
        return _load_export(stars_json)
    if use_github:
        return fetch_user_stars()
    return []
