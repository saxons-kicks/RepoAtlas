"""Typed data structures used throughout RepoAtlas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Bookmark:
    title: str
    url: str
    folder_path: list[str] = field(default_factory=list)
    add_date: str | None = None
    private_context: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StarredRepository:
    """GitHub repository metadata plus optional Star membership details."""

    full_name: str
    html_url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int | None = None
    forks_count: int | None = None
    archived: bool = False
    pushed_at: str | None = None
    updated_at: str | None = None
    license_spdx: str | None = None
    topics: list[str] = field(default_factory=list)
    starred_at: str | None = None
    private: bool = False
    repository_id: str | None = None
    created_at: str | None = None
    default_branch: str | None = None
    visibility: str | None = None
    fork: bool = False
    parent_repository_id: str | None = None
    parent_full_name: str | None = None
    source_repository_id: str | None = None
    source_full_name: str | None = None
    homepage: str | None = None
    open_issues_count: int | None = None
    watchers_count: int | None = None
    disabled: bool = False
    aliases: list[str] = field(default_factory=list)
    metadata_status: str = "available"
    metadata_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
