# RepoAtlas roadmap

## 0.1.0 — Local catalog and reconciliation
- [x] Import browser bookmark HTML and normalized JSON
- [x] Fetch GitHub Stars with pagination
- [x] Reconcile source membership
- [x] Export JSON, CSV, Markdown and offline HTML
- [x] Mark private bookmark contexts and support sanitized export

## 0.2.0 — Catalog enrichment
- [ ] Optional metadata refresh for bookmarked repositories not in Stars
- [ ] Detect deleted, renamed and archived repositories
- [ ] Capture repository license, topics, language and last push consistently for both sources
- [ ] Import/export a portable, documented schema

## 0.3.0 — Review and curation
- [ ] Review queue for broken links, archived repositories and ambiguous classifications
- [ ] Merge duplicate bookmark entries while preserving all source paths
- [ ] User-editable tags and notes stored locally
- [ ] Category rules configurable without editing Python source

## 0.4.0 — Integrations
- [ ] Optional GitHub Actions workflow for scheduled metadata refresh (no personal bookmark data)
- [ ] Stable read-only export contract for AI Workbench
- [ ] CLI support for additional bookmark managers

## Later
- [ ] Semantic search over descriptions and repository documentation
- [ ] Similar-repository and MCP/Skill redundancy discovery
- [ ] Browser extension for incremental bookmark import
