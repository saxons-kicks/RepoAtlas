# RepoAtlas

**RepoAtlas** is a local-first catalog that reconciles GitHub Stars with browser bookmarks. It answers three questions without conflating their meanings:

- Which repositories are both starred on GitHub and saved in browser bookmarks?
- Which repositories are starred but not bookmarked?
- Which repositories are bookmarked but not starred?

It imports Chrome/Edge/Firefox Netscape bookmark exports, reads the authenticated user's GitHub Stars through the official REST API, normalizes repository URLs, and builds a searchable offline dashboard plus JSON/CSV/Markdown exports.

## Design principles

- **Local-first:** all imported data and generated catalogs remain on your computer.
- **No credential storage:** RepoAtlas reads `gh auth token` or `GITHUB_TOKEN` at runtime. It never writes the token to disk.
- **Private by default:** `.repoatlas/`, `/data/local/`, `/data/private/`, and `.env` are ignored by Git. Do not commit personal bookmark exports or generated catalogs.
- **Explainable:** category classification is deterministic and records the terms that triggered it.
- **Source-aware:** GitHub Star and browser bookmark are independent signals. A Star is not treated as proof of quality.
- **Non-destructive:** the application reads exports; it does not add/remove GitHub Stars or modify browser bookmarks.

## Requirements

- Python 3.11 or newer.
- GitHub CLI (`gh`) recommended for authentication, or an environment variable named `GITHUB_TOKEN`.
- No third-party Python runtime dependencies.

## Install on Windows (PowerShell)

```powershell
# 1. Install GitHub CLI if needed
winget install --id GitHub.cli

# 2. Authenticate once in the terminal
 gh auth login

# 3. Clone the repository and enter the project folder
 git clone https://github.com/<your-user>/RepoAtlas.git
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

The application uses GitHub's authenticated-user Stars endpoint, paginates at up to 100 repositories per page, and asks for the `starred_at` timestamp. See [GitHub's starring REST API](https://docs.github.com/en/rest/activity/starring).

## First synchronization

Export your browser bookmarks as HTML (Chrome/Edge: Bookmark Manager → menu → Export bookmarks). Then run:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --github
```

Or use the normalized JSON produced by the bookmark organizer:

```powershell
repoatlas sync --bookmarks "C:\path\to\favoritos_organizados.json" --github
```

The command fetches all pages of `/user/starred` and writes these local files to `.repoatlas/`:

| File | Purpose |
|---|---|
| `catalog.json` | Structured source-aware catalog |
| `catalog.csv` | Spreadsheet-friendly catalog |
| `report.md` | Reconciliation report |
| `dashboard.html` | Searchable offline dashboard |

Open `.repoatlas\dashboard.html` in your browser.

### Importing GitHub Stars from JSON

If you prefer to export Stars separately, pass the JSON response/list using:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --stars-json ".\stars.json"
```

The accepted JSON shape is either a list of GitHub repository objects or an object containing `repositories` or `items`.

### Build a bookmarks-only catalog

To index bookmarks before connecting GitHub:

```powershell
repoatlas sync --bookmarks "$HOME\Downloads\bookmarks.html" --bookmarks-only
```

Those entries are marked `not_compared`, not `bookmark_only`. A real comparison requires importing Stars.

## Privacy and publishing

The default local catalog may include bookmark titles and folder paths that reveal internal project names or work systems. Keep `.repoatlas/` private. The repository contains no user catalog by design.

To create a sanitized JSON export, RepoAtlas excludes repositories marked private by GitHub or by a private bookmark folder, and removes the user-specific Star/Bookmark membership and bookmark paths:

```powershell
repoatlas export-public --input .repoatlas\catalog.json --output public-catalog.json
```

Review any generated export before publishing it. Public export omits membership data and personal bookmark labels/paths; it is an additional safeguard, not a replacement for review.

## Current scope (0.1.0)

- Netscape HTML and RepoAtlas JSON bookmark import.
- GitHub Stars import with pagination.
- Repository URL normalization, nested-link recognition, deduplication and source reconciliation.
- Explainable folder/keyword category tagging.
- Local JSON, CSV, Markdown report and offline HTML dashboard.
- Private-context flagging and sanitized JSON export.

Not included yet: GitHub webhooks, automatic bookmark-browser modification, semantic search, installing tools, repository quality scoring, or AI Workbench integration.

## Publish this project on GitHub

The local project can be published as `mateussmeneses/RepoAtlas`. First create an empty repository at [github.com/new](https://github.com/new), using `RepoAtlas` as the name. Do not initialize it with a README, license or `.gitignore`; these are already included. Then, from the extracted project folder:

```powershell
git init -b main
git add .
git commit -m "chore: initial RepoAtlas project"
git remote add origin https://github.com/mateussmeneses/RepoAtlas.git
git push -u origin main
```

Before pushing, confirm that `.repoatlas/`, browser exports, Stars exports and `.env` are not staged. The local catalog is intentionally not part of this repository.

## Development

```powershell
python -m unittest discover -s tests -v
```

## License

MIT. See `LICENSE`.
