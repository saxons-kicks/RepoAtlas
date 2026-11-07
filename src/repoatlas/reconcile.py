"""Merge GitHub Stars, bookmark aliases and enriched repository metadata."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .classify import CATEGORY_LABELS, build_tags, classify
from .models import Bookmark, StarredRepository
from .normalization import github_repo_full_name


def _identity(repository: StarredRepository) -> str:
    if repository.repository_id:
        return f"id:{repository.repository_id}"
    return f"name:{repository.full_name.lower()}"


def _merge_repository(existing: StarredRepository, incoming: StarredRepository) -> StarredRepository:
    """Fill missing fields while preserving Star-specific membership data."""
    for field_name in (
        "description", "language", "stargazers_count", "forks_count", "pushed_at",
        "updated_at", "license_spdx", "created_at", "default_branch", "visibility",
        "parent_repository_id", "parent_full_name", "source_repository_id",
        "source_full_name", "homepage", "open_issues_count", "watchers_count",
    ):
        if getattr(existing, field_name) in (None, "") and getattr(incoming, field_name) not in (None, ""):
            setattr(existing, field_name, getattr(incoming, field_name))
    existing.topics = sorted(set(existing.topics) | set(incoming.topics))
    existing.aliases = sorted(set(existing.aliases) | set(incoming.aliases))
    existing.archived = existing.archived or incoming.archived
    existing.private = existing.private or incoming.private
    existing.fork = existing.fork or incoming.fork
    existing.disabled = existing.disabled or incoming.disabled
    if existing.metadata_status == "available" and incoming.metadata_status != "available":
        existing.metadata_status = incoming.metadata_status
    return existing


def reconcile(
    bookmarks: list[Bookmark],
    stars: list[StarredRepository],
    compared: bool = True,
    enriched: list[StarredRepository] | None = None,
    lookup_results: dict[str, dict[str, str | None]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build a catalog using GitHub IDs when available and owner/repo as fallback."""
    enriched = enriched or []
    lookup_results = lookup_results or {}
    records: dict[str, StarredRepository] = {}
    starred_identities: set[str] = set()

    for repository in stars:
        key = _identity(repository)
        repository.metadata_status = "star_imported"
        records[key] = _merge_repository(records[key], repository) if key in records else repository
        starred_identities.add(key)

    for repository in enriched:
        key = _identity(repository)
        records[key] = _merge_repository(records[key], repository) if key in records else repository

    # Every known owner/repo path, including pre-rename names, points to one GitHub ID.
    alias_index: dict[str, str] = {}
    for key, repository in records.items():
        alias_index[repository.full_name.lower()] = key
        for alias in repository.aliases:
            alias_index[alias.lower()] = key

    bookmark_map: dict[str, list[Bookmark]] = defaultdict(list)
    bookmark_names: dict[str, set[str]] = defaultdict(set)
    non_github_bookmarks = 0
    raw_bookmark_names: set[str] = set()
    for bookmark in bookmarks:
        full_name = github_repo_full_name(bookmark.url)
        if not full_name:
            non_github_bookmarks += 1
            continue
        raw_bookmark_names.add(full_name)
        key = alias_index.get(full_name, f"name:{full_name}")
        if key not in records:
            records[key] = StarredRepository(
                full_name=full_name,
                html_url=f"https://github.com/{full_name}",
                metadata_status="not_checked",
            )
            alias_index[full_name] = key
        bookmark_map[key].append(bookmark)
        bookmark_names[key].add(full_name)

    catalog: list[dict[str, Any]] = []
    all_keys = sorted(set(records) | set(bookmark_map))
    for key in all_keys:
        repository = records[key]
        bm_items = bookmark_map.get(key, [])
        has_bookmark = bool(bm_items)
        has_star = key in starred_identities
        if not compared:
            status = "not_compared"
        elif has_star and has_bookmark:
            status = "both"
        elif has_star:
            status = "star_only"
        else:
            status = "bookmark_only"

        paths = [item.folder_path for item in bm_items]
        titles = [item.title for item in bm_items]
        categories, reasons = classify(
            paths,
            " ".join(titles) or repository.full_name,
            repository.description or "",
            repository.topics,
            repository.language or "",
            repository.full_name,
        )
        private_context = any(item.private_context for item in bm_items) or repository.private
        canonical_name = repository.full_name.lower()
        aliases = sorted(
            (set(repository.aliases) | bookmark_names.get(key, set())) - {canonical_name}
        )
        metadata_status = repository.metadata_status or "not_checked"
        metadata_error = repository.metadata_error
        for alias in bookmark_names.get(key, set()):
            result = lookup_results.get(alias)
            if result and metadata_status == "not_checked":
                metadata_status = result.get("status") or metadata_status
                metadata_error = result.get("error") or metadata_error

        is_fork = repository.fork or bool(repository.parent_repository_id or repository.parent_full_name)
        fork_root_id = repository.source_repository_id or repository.repository_id
        fork_root_name = repository.source_full_name or repository.full_name
        tags = build_tags(categories, repository.topics, repository.language, is_fork, repository.archived)

        catalog.append({
            "repository_id": repository.repository_id,
            "identity_source": "github_repository_id" if repository.repository_id else "owner_repo_fallback",
            "full_name": canonical_name,
            "name": canonical_name.split("/", 1)[-1],
            "owner": canonical_name.split("/", 1)[0],
            "url": repository.html_url or f"https://github.com/{canonical_name}",
            "aliases": aliases,
            "bookmark_repository_names": sorted(bookmark_names.get(key, set())),
            "description": repository.description,
            "homepage": repository.homepage,
            "language": repository.language,
            "stargazers_count": repository.stargazers_count,
            "forks_count": repository.forks_count,
            "open_issues_count": repository.open_issues_count,
            "watchers_count": repository.watchers_count,
            "archived": repository.archived,
            "disabled": repository.disabled,
            "repository_private": repository.private,
            "visibility": repository.visibility,
            "fork": is_fork,
            "parent_repository_id": repository.parent_repository_id,
            "parent_full_name": repository.parent_full_name,
            "source_repository_id": repository.source_repository_id,
            "source_full_name": repository.source_full_name,
            "fork_root_repository_id": fork_root_id,
            "fork_root_full_name": fork_root_name,
            "created_at": repository.created_at,
            "pushed_at": repository.pushed_at,
            "updated_at": repository.updated_at,
            "default_branch": repository.default_branch,
            "license": repository.license_spdx,
            "topics": repository.topics,
            "starred_at": repository.starred_at,
            "sources": (["github_star"] if has_star else []) + (["browser_bookmark"] if has_bookmark else []),
            "status": status,
            "bookmark_titles": titles,
            "bookmark_paths": paths,
            "bookmark_count": len(bm_items),
            "private_context": private_context,
            "metadata_status": metadata_status,
            "metadata_error": metadata_error,
            "categories": categories,
            "primary_category": categories[0],
            "category_labels": [CATEGORY_LABELS.get(category, category) for category in categories],
            "tags": tags,
            "classification_reasons": reasons,
        })

    counts = {key: sum(1 for item in catalog if item["status"] == key) for key in ("both", "star_only", "bookmark_only", "not_compared")}
    metadata_status_counts: dict[str, int] = defaultdict(int)
    for result in lookup_results.values():
        metadata_status_counts[str(result.get("status") or "unknown")] += 1
    canonical_aliases_resolved = sum(len(item["aliases"]) for item in catalog)
    summary = {
        "total_bookmarks": len(bookmarks),
        "github_bookmark_records": sum(len(items) for items in bookmark_map.values()),
        "unique_github_repositories_in_bookmarks": len(bookmark_map),
        "raw_unique_github_bookmark_names": len(raw_bookmark_names),
        "non_github_bookmarks": non_github_bookmarks,
        "github_stars_imported": len(starred_identities),
        "unique_repositories": len(catalog),
        "repositories_with_github_id": sum(1 for item in catalog if item["repository_id"]),
        "canonical_aliases_resolved": canonical_aliases_resolved,
        "fork_repositories": sum(1 for item in catalog if item["fork"]),
        "metadata_enrichment_attempted": len(lookup_results),
        "metadata_enriched": sum(1 for result in lookup_results.values() if result.get("status") == "enriched"),
        "metadata_unavailable": sum(1 for result in lookup_results.values() if result.get("status") not in {"enriched"}),
        "metadata_status_counts": dict(sorted(metadata_status_counts.items())),
        "comparison_performed": compared,
        "private_context_repositories": sum(1 for item in catalog if item["private_context"]),
        **counts,
    }
    return catalog, summary
