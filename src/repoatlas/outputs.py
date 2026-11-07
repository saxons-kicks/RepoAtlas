"""Write local JSON, CSV, Markdown report and dashboard outputs."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dashboard import render_dashboard


def _json_dump(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outputs(output_dir: str | Path, catalog: list[dict[str, Any]], summary: dict[str, Any], source_bookmarks: str, stars_source: str) -> dict[str, str]:
    out = Path(output_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "2.0",
        "product": "RepoAtlas",
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
        "repository_id", "full_name", "url", "status", "categories", "tags", "language",
        "stargazers_count", "forks_count", "archived", "fork", "parent_full_name",
        "source_full_name", "created_at", "pushed_at", "updated_at", "default_branch",
        "license", "bookmark_count", "private_context", "metadata_status", "description",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for item in catalog:
            row = dict(item)
            row["categories"] = ";".join(item.get("category_labels") or [])
            row["tags"] = ";".join(item.get("tags") or [])
            writer.writerow(row)

    report = [
        "# RepoAtlas · Relatório local",
        "",
        f"Gerado em: {metadata['generated_at']}",
        "",
        "## Resumo",
        "",
        f"- Favoritos importados: **{summary['total_bookmarks']}**",
        f"- Repositórios GitHub nos favoritos (após identidade canônica): **{summary['unique_github_repositories_in_bookmarks']}**",
        f"- Nomes de repositórios distintos encontrados nos favoritos: **{summary['raw_unique_github_bookmark_names']}**",
        f"- GitHub Stars importados: **{summary['github_stars_imported']}**",
        f"- Repositórios únicos no catálogo: **{summary['unique_repositories']}**",
        f"- Repositórios com ID oficial do GitHub: **{summary['repositories_with_github_id']}**",
        f"- Aliases/redirecionamentos consolidados: **{summary['canonical_aliases_resolved']}**",
        f"- Forks identificados: **{summary['fork_repositories']}**",
        f"- Referências com contexto privado: **{summary['private_context_repositories']}**",
        "",
        "## Enriquecimento de metadados",
        "",
        f"- Consultas realizadas: **{summary['metadata_enrichment_attempted']}**",
        f"- Consultas concluídas: **{summary['metadata_enriched']}**",
        f"- Consultas sem metadados: **{summary['metadata_unavailable']}**",
        "",
        "Uma consulta HTTP 404 significa que o repositório não foi encontrado pelo token atual ou que o token não tem acesso; não prova, isoladamente, que o repositório foi excluído.",
        "",
        "## Reconciliação",
        "",
        f"- Em ambos: **{summary['both']}**",
        f"- Somente GitHub Star: **{summary['star_only']}**",
        f"- Somente favorito: **{summary['bookmark_only']}**",
        f"- Aguardando comparação: **{summary['not_compared']}**",
        "",
    ]
    if summary["metadata_status_counts"]:
        report += ["### Resultado das consultas", ""]
        for status, count in sorted(summary["metadata_status_counts"].items()):
            report.append(f"- `{status}`: **{count}**")
        report.append("")

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
            for item in matching:
                details = []
                if item.get("repository_id"):
                    details.append(f"ID `{item['repository_id']}`")
                if item.get("language"):
                    details.append(item["language"])
                if item.get("fork") and item.get("source_full_name"):
                    details.append(f"fork de `{item['source_full_name']}`")
                if item.get("archived"):
                    details.append("arquivado")
                if item.get("metadata_status") not in {"star_imported", "enriched", "available"}:
                    details.append(f"metadados: `{item['metadata_status']}`")
                suffix = f" — {' · '.join(details)}" if details else ""
                report.append(f"- [{item['full_name']}]({item['url']}){suffix}")
                for alias in item.get("aliases") or []:
                    report.append(f"  - Alias resolvido: `{alias}`")
            report.append("")

    fork_items = [item for item in catalog if item.get("fork")]
    if fork_items:
        report += ["## Relações de forks", ""]
        for item in fork_items:
            root = item.get("source_full_name") or item.get("parent_full_name") or "origem não identificada"
            report.append(f"- `{item['full_name']}` → `{root}`")
        report.append("")

    unavailable = [item for item in catalog if item.get("metadata_status") not in {"star_imported", "enriched", "available", "not_checked"}]
    if unavailable:
        report += ["## Revisar metadados", ""]
        for item in unavailable:
            reason = item.get("metadata_error") or "sem detalhe retornado"
            report.append(f"- `{item['full_name']}` — `{item['metadata_status']}`: {reason}")
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
        for key in (
            "sources", "status", "starred_at", "bookmark_titles", "bookmark_paths",
            "bookmark_repository_names", "bookmark_count", "private_context", "repository_private",
            "classification_reasons", "metadata_error",
        ):
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
