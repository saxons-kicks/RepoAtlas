"""Read GitHub Stars and enrich repository metadata without storing credentials."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import Bookmark, StarredRepository
from .normalization import github_repo_full_name

API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"
USER_AGENT = "RepoAtlas/0.2.0"


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


def get_github_token() -> str | None:
    """Return the runtime token from the environment or GitHub CLI."""
    return _github_token()


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": USER_AGENT,
    }


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


def _related_repository(repo: dict[str, Any], key: str) -> tuple[str | None, str | None]:
    related = repo.get(key)
    if not isinstance(related, dict):
        return None, None
    repository_id = related.get("id")
    full_name = related.get("full_name")
    return (str(repository_id) if repository_id is not None else None, str(full_name).lower() if full_name else None)


def _to_starred(item: dict[str, Any]) -> StarredRepository | None:
    repo, starred_at = _repo_from_star_item(item)
    full_name = repo.get("full_name")
    html_url = repo.get("html_url")
    if not full_name or not html_url:
        return None
    repository_id = repo.get("id")
    parent_id, parent_name = _related_repository(repo, "parent")
    source_id, source_name = _related_repository(repo, "source")
    owner = repo.get("owner") if isinstance(repo.get("owner"), dict) else {}
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
        repository_id=str(repository_id) if repository_id is not None else None,
        created_at=repo.get("created_at"),
        default_branch=repo.get("default_branch"),
        visibility=repo.get("visibility") or ("private" if repo.get("private") else "public"),
        fork=bool(repo.get("fork", False)),
        parent_repository_id=parent_id,
        parent_full_name=parent_name,
        source_repository_id=source_id,
        source_full_name=source_name,
        homepage=repo.get("homepage") or None,
        open_issues_count=repo.get("open_issues_count"),
        watchers_count=repo.get("watchers_count"),
        disabled=bool(repo.get("disabled", False)),
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
    headers = _headers(auth)
    headers["Accept"] = "application/vnd.github.star+json"
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
                    repo.metadata_status = "star_imported"
                    results.append(repo)
        url = next_url
    return results


def fetch_repository_metadata(full_name: str, token: str | None = None) -> tuple[StarredRepository | None, str, str | None]:
    """Fetch one repository. urllib follows GitHub rename/transfer redirects."""
    auth = token or _github_token()
    if not auth:
        return None, "auth_missing", "Autenticação GitHub não encontrada."
    requested = (full_name or "").strip().strip("/")
    if not requested or len(requested.split("/")) != 2:
        return None, "invalid_name", "Identificador owner/repo inválido."

    encoded = urllib.parse.quote(requested, safe="/")
    request = urllib.request.Request(f"{API_ROOT}/repos/{encoded}", headers=_headers(auth))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        if exc.code == 404:
            return None, "not_found", "HTTP 404: repositório não encontrado ou sem acesso."
        if exc.code in {403, 429}:
            status = "rate_limited" if "rate limit" in detail.casefold() or exc.code == 429 else "forbidden"
            return None, status, f"HTTP {exc.code}: {detail}"
        if exc.code in {410, 451}:
            return None, "unavailable", f"HTTP {exc.code}: {detail}"
        return None, "error", f"HTTP {exc.code}: {detail}"
    except urllib.error.URLError as exc:
        return None, "error", str(exc.reason)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, "error", f"Resposta inválida do GitHub: {exc}"

    if not isinstance(payload, dict):
        return None, "error", "Resposta inesperada ao consultar o repositório."
    repository = _to_starred(payload)
    if repository is None:
        return None, "error", "O GitHub não retornou full_name e html_url."

    canonical_name = repository.full_name.lower()
    requested_name = requested.lower()
    repository.aliases = [requested_name] if requested_name != canonical_name else []
    repository.metadata_status = "enriched"
    return repository, "enriched", None


def enrich_bookmark_repositories(
    bookmarks: list[Bookmark],
    stars: list[StarredRepository],
    token: str | None = None,
) -> tuple[list[StarredRepository], dict[str, dict[str, str | None]]]:
    """Enrich unique bookmark-only names and resolve aliases by GitHub repository ID."""
    known_names = {repo.full_name.lower() for repo in stars}
    known_names.update(alias.lower() for repo in stars for alias in repo.aliases)
    candidates = sorted({
        name for bookmark in bookmarks
        if (name := github_repo_full_name(bookmark.url)) and name not in known_names
    })

    enriched: list[StarredRepository] = []
    lookup_results: dict[str, dict[str, str | None]] = {}
    for requested_name in candidates:
        repository, status, error = fetch_repository_metadata(requested_name, token=token)
        lookup_results[requested_name] = {
            "status": status,
            "repository_id": repository.repository_id if repository else None,
            "resolved_full_name": repository.full_name if repository else None,
            "error": error,
        }
        if repository:
            enriched.append(repository)
    return enriched, lookup_results


def load_stars(stars_json: str | None = None, use_github: bool = False) -> list[StarredRepository]:
    if stars_json:
        return _load_export(stars_json)
    if use_github:
        return fetch_user_stars()
    return []
