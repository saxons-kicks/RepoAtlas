# RepoAtlas data model

## Sources

- `browser_bookmark`: a bookmark exported from the browser.
- `github_star`: a repository returned by the authenticated `/user/starred` endpoint.

Each source is represented independently. Repository identity is `lowercase(owner/repo)`; URL query strings and fragments are ignored when identifying GitHub repositories.

## Comparison states

| State | Meaning |
|---|---|
| `both` | Present in GitHub Stars and browser bookmarks |
| `star_only` | Present in GitHub Stars, absent from browser bookmarks |
| `bookmark_only` | Present in browser bookmarks, absent from GitHub Stars |
| `not_compared` | Stars were not imported, so no comparison was performed |

## Privacy

A bookmark under a folder whose name contains `Trabalho`, `Work`, `Interno`, `Internal`, `Corporativo`, or `Corporate` receives `private_context=true`. A GitHub repository marked `private=true` by the API is also treated as private. The local catalog retains this flag so the user can inspect their own context. The repository ignores local catalogs and provides a separate sanitized export command.

## Categories

Categories are deterministic labels inferred from bookmark folders, repository title, description and GitHub topics. The output includes `classification_reasons`; this is a navigation aid, not an endorsement or repository quality score.
