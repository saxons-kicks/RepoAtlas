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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
