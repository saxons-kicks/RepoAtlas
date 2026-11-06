"""Write local JSON, CSV, Markdown report and dashboard outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .dashboard import render_dashboard


def _json_dump(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outputs(output_dir: str | Path, catalog: list[dict[str, Any]], summary: dict[str, Any], source_bookmarks: str, stars_source: str) -> dict[str, str]:
    out = Path(output_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "1.0",
        "product": "RepoAtlas",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "sources": {"bookmarks": source_bookmarks, "github_stars": stars_source},
        "summary": summary,
        "repositories": catalog,
    }
    json_path = out / "catalog.json"
    csv_path = out / "catalog.csv"
    report_path = out / "report.md"
    dashboard_path = out / "dashboard.html"
    _json_dump(json_path, metadata)

    columns = [
        "full_name", "url", "status", "categories", "language", "stargazers_count", "forks_count",
        "archived", "pushed_at", "license", "bookmark_count", "private_context", "description",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for item in catalog:
            row = dict(item)
            row["categories"] = ";".join(item.get("category_labels") or [])
            writer.writerow(row)

    report = [
        "# RepoAtlas · Relatório local",
        "",
        f"Gerado em: {metadata['generated_at']}",
        "",
        "## Resumo",
        "",
        f"- Favoritos importados: **{summary['total_bookmarks']}**",
        f"- Repositórios GitHub nos favoritos: **{summary['unique_github_repositories_in_bookmarks']}**",
        f"- GitHub Stars importados: **{summary['github_stars_imported']}**",
        f"- Repositórios únicos no catálogo: **{summary['unique_repositories']}**",
        f"- Referências com contexto privado: **{summary['private_context_repositories']}**",
        "",
        "## Reconciliação",
        "",
        f"- Em ambos: **{summary['both']}**",
        f"- Somente GitHub Star: **{summary['star_only']}**",
        f"- Somente favorito: **{summary['bookmark_only']}**",
        f"- Aguardando comparação: **{summary['not_compared']}**",
        "",
    ]
    if not summary["comparison_performed"]:
        report += [
            "> A comparação ainda não foi executada. Conecte-se ao GitHub com `gh auth login` e rode novamente com `--github`, ou forneça um arquivo com `--stars-json`.",
            "",
        ]
    report += ["## Itens por status", ""]
    for status, label in (("both", "Em ambos"), ("star_only", "Somente Star"), ("bookmark_only", "Somente favorito"), ("not_compared", "Não comparado")):
        matching = [item for item in catalog if item["status"] == status]
        if matching:
            report.append(f"### {label} ({len(matching)})")
            report.extend(f"- [{item['full_name']}]({item['url']})" for item in matching)
            report.append("")
    report_path.write_text("\n".join(report).rstrip() + "\n", encoding="utf-8")
    dashboard_path.write_text(render_dashboard(catalog, summary), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "report": str(report_path), "dashboard": str(dashboard_path)}


def export_public_catalog(source: str | Path, destination: str | Path) -> dict[str, int]:
    """Create a sanitized export without repositories connected to private bookmark folders."""
    source_path = Path(source)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    original = payload.get("repositories", [])
    safe = []
    excluded = 0
    for item in original:
        if item.get("private_context") or item.get("repository_private"):
            excluded += 1
            continue
        public_item = dict(item)
        # Do not expose the user's personal collection membership or bookmark labels/paths.
        for key in ("sources", "status", "starred_at", "bookmark_titles", "bookmark_paths", "bookmark_count", "private_context", "repository_private", "classification_reasons"):
            public_item.pop(key, None)
        safe.append(public_item)
    payload["repositories"] = safe
    payload["sources"] = {"bookmarks": "omitted from public export", "github_stars": "omitted from public export"}
    payload["summary"] = {
        "unique_repositories": len(safe),
        "excluded_private_repositories": excluded,
        "comparison_performed": False,
    }
    destination_path = Path(destination).expanduser()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    _json_dump(destination_path, payload)
    return {"exported": len(safe), "excluded_private": excluded}
