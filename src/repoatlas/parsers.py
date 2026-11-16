"""Import browser bookmark HTML and RepoAtlas/browser bookmark JSON."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .models import Bookmark

_ROOT_FOLDERS = {
    "bookmarks bar", "bar bookmarks", "barra de favoritos", "barra de marcadores",
    "other bookmarks", "outros favoritos", "favoritos", "bookmarks",
}
_PRIVATE_FOLDER_PATTERN = re.compile(
    r"(?<!\w)(?:trabalho|work|interno|internal|corporativo|corporate)(?!\w)",
    re.IGNORECASE,
)


def _private_path(path: list[str]) -> bool:
    """Detect private-context folders using whole words, not substrings."""
    return any(_PRIVATE_FOLDER_PATTERN.search(folder) for folder in path)


class _NetscapeBookmarksParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.folder_stack: list[str] = []
        self.pending_folder: str | None = None
        self.h3_parts: list[str] = []
        self.reading_h3 = False
        self.anchor_attrs: dict[str, str] | None = None
        self.anchor_parts: list[str] = []
        self.bookmarks: list[Bookmark] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "h3":
            self.reading_h3 = True
            self.h3_parts = []
        elif tag.lower() == "dl":
            if self.pending_folder is not None:
                name = self.pending_folder.strip()
                if name and name.casefold() not in _ROOT_FOLDERS:
                    self.folder_stack.append(name)
                self.pending_folder = None
        elif tag.lower() == "a":
            self.anchor_attrs = attrs_dict
            self.anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "h3":
            self.pending_folder = "".join(self.h3_parts).strip()
            self.reading_h3 = False
        elif lower == "a" and self.anchor_attrs is not None:
            attrs = self.anchor_attrs
            url = attrs.get("href", "").strip()
            title = "".join(self.anchor_parts).strip() or url
            if url:
                path = list(self.folder_stack)
                self.bookmarks.append(
                    Bookmark(
                        title=title,
                        url=url,
                        folder_path=path,
                        add_date=attrs.get("add_date") or None,
                        private_context=_private_path(path),
                    )
                )
            self.anchor_attrs = None
            self.anchor_parts = []
        elif lower == "dl":
            if self.folder_stack:
                self.folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.reading_h3:
            self.h3_parts.append(data)
        if self.anchor_attrs is not None:
            self.anchor_parts.append(data)


def _json_bookmarks(path: Path) -> list[Bookmark]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows: Any = payload.get("bookmarks", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("O JSON não contém uma lista 'bookmarks'.")
    bookmarks: list[Bookmark] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or row.get("href") or "").strip()
        if not url:
            continue
        path_value = row.get("organized_path") or row.get("folder_path") or row.get("source_path") or []
        if isinstance(path_value, str):
            folder_path = [p for p in path_value.replace("\\", "/").split("/") if p]
        elif isinstance(path_value, list):
            folder_path = [str(p) for p in path_value if p]
        else:
            folder_path = []
        bookmarks.append(
            Bookmark(
                title=str(row.get("title") or row.get("name") or url).strip(),
                url=url,
                folder_path=folder_path,
                add_date=str(row.get("source_add_date") or row.get("add_date") or "") or None,
                private_context=bool(row.get("private_context", False)) or _private_path(folder_path),
            )
        )
    return bookmarks


def load_bookmarks(source: str | Path) -> list[Bookmark]:
    """Load a Netscape HTML export or JSON file."""
    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de favoritos não encontrado: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _json_bookmarks(path)
    if suffix in {".html", ".htm"}:
        parser = _NetscapeBookmarksParser()
        parser.feed(path.read_text(encoding="utf-8-sig", errors="replace"))
        parser.close()
        return parser.bookmarks
    raise ValueError("Formato não suportado. Use exportação do navegador em HTML ou JSON.")
