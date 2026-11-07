# RepoAtlas roadmap

## 0.1.0 — Local catalog and reconciliation
- [x] Import browser bookmark HTML and normalized JSON
- [x] Fetch GitHub Stars with pagination
- [x] Reconcile source membership
- [x] Export JSON, CSV, Markdown and offline HTML
- [x] Mark private bookmark contexts and support sanitized export

## 0.2.0 — Canonical identity and catalog enrichment
- [x] Use GitHub repository ID as primary identity with owner/repo fallback
- [x] Resolve GitHub repository renames/transfers through redirected metadata lookups
- [x] Preserve aliases and bookmark paths when multiple names resolve to one repository
- [x] Capture repository description, language, license, topics, activity and archive state
- [x] Preserve parent/source relationships for forks without collapsing separate fork repositories
- [x] Expand deterministic categories, technical tags and local dashboard filters
- [x] Version the JSON contract and document the data model
- [x] Add tests for canonical identity, aliases, metadata and fork relationships

## 0.3.0 — Review and curation
- [ ] Review queue for broken links, archived repositories and ambiguous classifications
- [ ] User-editable tags and notes stored locally
- [ ] Category rules configurable without editing Python source
- [ ] Metadata refresh policy and cache with ETag/conditional requests
- [ ] Repository activity trend and stale-project detection

## 0.4.0 — Integrations
- [ ] Optional GitHub Actions workflow for scheduled public metadata refresh (no personal bookmark data)
- [ ] Stable read-only export contract for AI Workbench
- [ ] CLI support for additional bookmark managers
- [ ] Export subsets by category, tags, language and project family

## Later
- [ ] Semantic search over descriptions and repository documentation
- [ ] Similar-repository and MCP/Skill redundancy discovery
- [ ] Browser extension for incremental bookmark import
- [ ] Contextual relevance ranking with explainable signals
