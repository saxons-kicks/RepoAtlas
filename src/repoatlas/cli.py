"""Command-line interface for RepoAtlas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .github_api import GitHubAPIError, load_stars
from .outputs import export_public_catalog, write_outputs
from .parsers import load_bookmarks
from .reconcile import reconcile


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repoatlas",
        description="Compare GitHub Stars with browser bookmarks and build a local catalog.",
    )
    parser.add_argument("--version", action="version", version=f"RepoAtlas {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    sync = commands.add_parser("sync", help="Import bookmarks and reconcile them with GitHub Stars.")
    sync.add_argument("--bookmarks", required=True, help="Browser bookmark export (.html) or normalized JSON.")
    source = sync.add_mutually_exclusive_group(required=True)
    source.add_argument("--github", action="store_true", help="Fetch all GitHub Stars using GitHub API and local auth.")
    source.add_argument("--stars-json", help="Import a JSON export of GitHub Stars instead of calling the API.")
    source.add_argument("--bookmarks-only", action="store_true", help="Build the catalog without comparing Stars yet.")
    sync.add_argument("--output", default=".repoatlas", help="Local output directory (default: .repoatlas).")

    public = commands.add_parser("export-public", help="Export catalog JSON excluding private bookmark contexts.")
    public.add_argument("--input", default=".repoatlas/catalog.json", help="Local catalog JSON.")
    public.add_argument("--output", default="public-catalog.json", help="Sanitized destination JSON.")

    return parser


def run_sync(args: argparse.Namespace) -> int:
    bookmarks = load_bookmarks(args.bookmarks)
    if args.bookmarks_only:
        stars = []
        compared = False
        stars_source = "not imported"
    else:
        stars = load_stars(stars_json=args.stars_json, use_github=args.github)
        compared = True
        stars_source = "GitHub REST API" if args.github else str(args.stars_json)
    catalog, summary = reconcile(bookmarks, stars, compared=compared)
    files = write_outputs(args.output, catalog, summary, str(Path(args.bookmarks)), stars_source)
    print("RepoAtlas · sincronização concluída")
    print(f"Favoritos lidos: {summary['total_bookmarks']}")
    print(f"Repositórios GitHub nos favoritos: {summary['unique_github_repositories_in_bookmarks']}")
    print(f"GitHub Stars importados: {summary['github_stars_imported']}")
    print(f"Repositórios no catálogo: {summary['unique_repositories']}")
    if compared:
        print(f"Em ambos: {summary['both']}")
        print(f"Somente Stars: {summary['star_only']}")
        print(f"Somente favoritos: {summary['bookmark_only']}")
    else:
        print("Comparação pendente: execute novamente com --github ou --stars-json.")
    print("\nArquivos gerados:")
    for kind, path in files.items():
        print(f"  {kind}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "sync":
            return run_sync(args)
        if args.command == "export-public":
            stats = export_public_catalog(args.input, args.output)
            print(f"Exportação concluída: {stats['exported']} repositórios; {stats['excluded_private']} removidos por contexto privado.")
            print(f"Arquivo: {args.output}")
            return 0
    except (OSError, ValueError, GitHubAPIError, json.JSONDecodeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    parser.error("Comando não reconhecido.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
