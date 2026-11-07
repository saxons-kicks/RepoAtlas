# RepoAtlas

**RepoAtlas** is a local-first repository intelligence catalog. It reconciles GitHub Stars with browser bookmarks, resolves repository identity, preserves fork relationships and enriches bookmark-only repositories with GitHub metadata.

It answers:

- Which repositories are both starred on GitHub and saved in browser bookmarks?
- Which are starred but not bookmarked, or bookmarked but not starred?
- Do two different URLs or owner/repo names resolve to the same GitHub repository?
- Is a repository a fork, who is its parent, and what is its upstream source?
- Which projects are archived, inactive, or missing metadata?
- Which categories and technical tags describe each repository?

## Design principles

- **Local-first:** imported data and generated catalogs remain on your computer.
- **No credential storage:** RepoAtlas reads `gh auth token`, `GITHUB_TOKEN` or `GH_TOKEN` at runtime. It never writes the token to disk.
- **Private by default:** `.repoatlas/`, `/data/local/`, `/data/private/` and `.env` are ignored by Git. Do not commit personal bookmark exports or generated catalogs.
- **Canonical identity:** GitHub's numeric repository ID is the primary identity. Lowercase `owner/repo` is the fallback for old exports or records without an ID.
- **Redirect-aware:** metadata lookups follow GitHub redirects and retain the original bookmark path as an alias.
- **Fork-aware:** forks remain separate repositories and keep their `parent` and upstream `source` relationships.
- **Explainable classification:** categories are deterministic and include the terms that triggered them. Tags provide additional filters; neither is a quality score.
- **Source-aware:** GitHub Star and browser bookmark are independent signals. A Star is not treated as proof of quality.
- **Non-destructive:** the application reads exports; it does not add/remove GitHub Stars or modify browser bookmarks.

## Requirements

- Python 3.11 or newer.
- GitHub CLI (`gh`) recommended for authentication, or an environment variable named `GITHUB_TOKEN` / `GH_TOKEN`.
- No third-party Python runtime dependencies.

## Install on Windows (PowerShell)

```powershell
# 1. Install GitHub CLI if needed
winget install --id GitHub.cli

# 2. Authenticate once in the terminal
gh auth login

# 3. Clone the repository and enter the project folder
git clone https://github.com/mateussmeneses/RepoAtlas.git
cd RepoAtlas

# 4. Create and activate an isolated Python environment
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 5. Install RepoAtlas in editable mode
python -m pip install -e .
```

The endpoint accepts fine-grained personal access tokens with **Starring: Read** user permission. RepoAtlas can also reuse the active `gh` token. If you use an environment token, set it only for the current PowerShell session and never write it to a tracked file:

```powershell
$env:GITHUB_TOKEN = "<your-token>"
```

RepoAtlas reads GitHub's authenticated-user Stars endpoint, paginates the results and requests `starred_at`. Repository metadata is obtained from the official repository endpoint. See [GitHub's starring REST API](https://docs.github.com/en/rest/activity/starring) and [repository REST API](https://docs.github.com/en/rest/repos/repos).

## First synchronization

Export your browser bookmarks as HTML (Chrome/Edge: Bookmark Manager → menu → Export bookmarks). Then run:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --github
```

Or use the normalized JSON produced by the bookmark organizer:

```powershell
repoatlas sync --bookmarks "C:\path\to\favoritos_organizados.json" --github
```

When `--github` is used, RepoAtlas automatically looks up bookmark-only repository names. This resolves repository renames/transfers where GitHub returns the same numeric repository ID and enriches those entries with description, language, license, topics, activity, archive status and fork relationships. It queries only unique bookmark names not already present in Stars.

To skip those extra lookups:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --github --no-enrich-bookmarks
```

The command writes these local files to `.repoatlas/`:

| File | Purpose |
|---|---|
| `catalog.json` | Schema 2.0 structured catalog with repository IDs, aliases, relations, tags and source membership |
| `catalog.csv` | Spreadsheet-friendly catalog with metadata and fork fields |
| `report.md` | Reconciliation, metadata lookup and fork report |
| `dashboard.html` | Searchable offline dashboard with status, category and fork filters |

Open `.repoatlas\dashboard.html` in your browser.

### Importing GitHub Stars from JSON

If you prefer to export Stars separately, pass the JSON response/list using:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --stars-json ".\stars.json"
```

The accepted JSON shape is either a list of GitHub repository objects or an object containing `repositories` or `items`. This mode uses the metadata present in the JSON and does not make additional GitHub repository lookups.

### Build a bookmarks-only catalog

To index bookmarks before connecting GitHub:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --bookmarks-only
```

Those entries are marked `not_compared`, not `bookmark_only`. A real comparison requires importing Stars.

## Identity, aliases and forks

Each GitHub repository has a stable numeric `repository_id`. RepoAtlas uses it to merge references even when their owner/repo paths differ. The original bookmark name is retained in `aliases` and `bookmark_repository_names`; the canonical `full_name` and URL come from GitHub metadata.

A different repository ID remains a separate catalog item, including forks. For forks, the catalog stores `parent_repository_id`, `parent_full_name`, `source_repository_id`, `source_full_name` and `fork_root_full_name`. This allows the dashboard and downstream consumers to group related projects without discarding fork-specific changes.

`metadata_status` describes the metadata lookup, for example `star_imported`, `enriched`, `not_checked`, `not_found`, `forbidden` or `rate_limited`. A GitHub HTTP 404 means the repository was not found by the current request or the token cannot access it; it does not prove deletion by itself.

### Catalog schema

The JSON root has `schema_version: "2.0"`, a `summary` and a `repositories` array. Each repository may include:

- Identity: `repository_id`, `identity_source`, `full_name`, `url`, `aliases`.
- GitHub metadata: description, homepage, language, topics, license, timestamps, default branch, Stars, forks, open issues and watchers.
- Relationships: `fork`, `parent_*`, `source_*` and `fork_root_*`.
- Curation: `categories`, `primary_category`, `category_labels`, `tags` and `classification_reasons`.
- Source signals: `sources`, `status`, `starred_at`, bookmark count and local bookmark context.
- Availability: `archived`, `disabled`, `visibility`, `metadata_status` and optional `metadata_error`.

See [docs/DATA_MODEL.md](docs/DATA_MODEL.md) for the full field definitions.

## Privacy and publishing

The default local catalog may include bookmark titles and folder paths that reveal internal project names or work systems. Keep `.repoatlas/` private. The repository contains no user catalog by design.

To create a sanitized JSON export, RepoAtlas excludes repositories marked private by GitHub or by a private bookmark folder, removes collection membership and bookmark paths, and omits metadata lookup errors:

```powershell
repoatlas export-public --input .repoatlas\catalog.json --output public-catalog.json
```

Review any generated export before publishing it. Public export is an additional safeguard, not a replacement for review.

## Development

```powershell
python -m unittest discover -s tests -v
```

## License

MIT. See `LICENSE`.
