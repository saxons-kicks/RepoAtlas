"""Merge GitHub Stars and browser bookmarks into a repository catalog."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .classify import CATEGORY_LABELS, classify
from .models import Bookmark, StarredRepository
from .normalization import github_repo_full_name


def reconcile(bookmarks: list[Bookmark], stars: list[StarredRepository], compared: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bookmark_map: dict[str, list[Bookmark]] = defaultdict(list)
    non_github_bookmarks = 0
    for bookmark in bookmarks:
        full_name = github_repo_full_name(bookmark.url)
        if full_name:
            bookmark_map[full_name].append(bookmark)
        else:
            non_github_bookmarks += 1

    star_map = {repo.full_name.lower(): repo for repo in stars}
    all_names = sorted(set(bookmark_map) | set(star_map))
    catalog: list[dict[str, Any]] = []

    for full_name in all_names:
        bm_items = bookmark_map.get(full_name, [])
        star = star_map.get(full_name)
        has_bookmark = bool(bm_items)
        has_star = star is not None
        if not compared:
            status = "not_compared"
        elif has_star and has_bookmark:
            status = "both"
        elif has_star:
            status = "star_only"
        else:
            status = "bookmark_only"

        paths = [item.folder_path for item in bm_items]
        title = (star.full_name.split("/", 1)[-1] if star else (bm_items[0].title if bm_items else full_name))
        description = star.description if star else None
        topics = star.topics if star else []
        categories, reasons = classify(paths, title, description or "", topics)
        private_context = any(item.private_context for item in bm_items) or bool(star and star.private)

        catalog.append({
            "full_name": full_name,
            "name": full_name.split("/", 1)[-1],
            "owner": full_name.split("/", 1)[0],
            "url": star.html_url if star else f"https://github.com/{full_name}",
            "description": description,
            "language": star.language if star else None,
            "stargazers_count": star.stargazers_count if star else None,
            "forks_count": star.forks_count if star else None,
            "archived": star.archived if star else None,
            "repository_private": star.private if star else None,
            "pushed_at": star.pushed_at if star else None,
            "updated_at": star.updated_at if star else None,
            "license": star.license_spdx if star else None,
            "topics": topics,
            "starred_at": star.starred_at if star else None,
            "sources": (["github_star"] if has_star else []) + (["browser_bookmark"] if has_bookmark else []),
            "status": status,
            "bookmark_titles": [item.title for item in bm_items],
            "bookmark_paths": paths,
            "bookmark_count": len(bm_items),
            "private_context": private_context,
            "categories": categories,
            "category_labels": [CATEGORY_LABELS.get(category, category) for category in categories],
            "classification_reasons": reasons,
        })

    counts = {key: sum(1 for item in catalog if item["status"] == key) for key in ("both", "star_only", "bookmark_only", "not_compared")}
    summary = {
        "total_bookmarks": len(bookmarks),
        "github_bookmark_records": sum(len(items) for items in bookmark_map.values()),
        "unique_github_repositories_in_bookmarks": len(bookmark_map),
        "non_github_bookmarks": non_github_bookmarks,
        "github_stars_imported": len(star_map),
        "unique_repositories": len(catalog),
        "comparison_performed": compared,
        "private_context_repositories": sum(1 for item in catalog if item["private_context"]),
        **counts,
    }
    return catalog, summary
