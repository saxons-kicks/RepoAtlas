# RepoAtlas data model

The catalog JSON emitted by RepoAtlas 0.2.0 uses schema version `2.0`.

## Identity

- `repository_id`: GitHub's stable numeric repository ID, serialized as a string. This is the primary identity key.
- `identity_source`: `github_repository_id` when the API provided an ID, otherwise `owner_repo_fallback`.
- `full_name`: canonical lowercase `owner/repo` name returned by GitHub, or the bookmark's owner/repo path when metadata is unavailable.
- `url`: canonical GitHub URL when metadata is available.
- `aliases`: noncanonical owner/repo paths that resolve to the same repository ID.
- `bookmark_repository_names`: distinct owner/repo paths extracted from browser bookmarks and reconciled to this repository.

Query strings, fragments, Git clone suffixes and casing differences are ignored while extracting bookmark repository names. A metadata lookup follows HTTP redirects and uses the returned repository ID to reconcile the redirected path with a Star entry.

## GitHub metadata

Metadata can include description, homepage, language, Stars, forks, open issues, watchers, archive/disabled state, visibility, creation/update/push timestamps, default branch, license, topics and metadata lookup status.

`metadata_status` values include:

| Value | Meaning |
|---|---|
| `star_imported` | Metadata was received as part of the authenticated Stars response |
| `enriched` | Metadata was fetched for a bookmark-only path |
| `not_checked` | No metadata request was made |
| `not_found` | GitHub returned HTTP 404; the repository may be absent or inaccessible to the current token |
| `forbidden` | GitHub denied the request |
| `rate_limited` | GitHub rate limit prevented the lookup |
| `unavailable` | GitHub returned an unavailable-resource status |
| `error` | Network or response error |

A 404 is not treated as proof of deletion because GitHub also returns 404 when the current token cannot access a private repository.

## Fork relationships

Forks remain distinct catalog entries because they have different repository IDs. The catalog records:

- `fork`: whether the repository is a fork.
- `parent_repository_id` and `parent_full_name`: direct parent fork/repository.
- `source_repository_id` and `source_full_name`: upstream source repository.
- `fork_root_repository_id` and `fork_root_full_name`: upstream source when available; otherwise the repository itself.

## Sources and comparison states

- `browser_bookmark`: a bookmark exported from the browser.
- `github_star`: a repository returned by the authenticated `/user/starred` endpoint.

| State | Meaning |
|---|---|
| `both` | Present in GitHub Stars and browser bookmarks after canonical identity resolution |
| `star_only` | Present in GitHub Stars, absent from browser bookmarks |
| `bookmark_only` | Present in browser bookmarks, absent from GitHub Stars |
| `not_compared` | Stars were not imported, so no comparison was performed |

## Privacy

A bookmark under a folder whose name contains `Trabalho`, `Work`, `Interno`, `Internal`, `Corporativo` or `Corporate` receives `private_context=true`. A GitHub repository marked `private=true` by the API is also treated as private. The local catalog retains this flag so the user can inspect their own context. The repository ignores local catalogs and provides a separate sanitized export command.

## Categories and tags

Categories are deterministic labels inferred from bookmark folders, repository name, description, language and GitHub topics. Multiple categories are permitted; `primary_category` is the first matching rule. `classification_reasons` explains the first matching term for each category.

`tags` combine GitHub topics, `category:<slug>`, `language:<name>` and structural labels such as `fork` and `archived`. They support filtering and discovery; they are not a repository quality score.
