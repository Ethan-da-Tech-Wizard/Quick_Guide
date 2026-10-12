# QuickGuide

Local semantic PDF search with embedding-based retrieval, page navigation, and highlighted answers.

**Status:** Document-search prototype  
**Built with:** Python, local embeddings, browser UI

## Reading order

1. Read the root README for project purpose and setup navigation.
2. Follow the entry points below to find the implementation.
3. Use the file guide to locate individual modules, tests, assets, and configuration.
4. Check component licenses before redistributing dependencies or assets.

## Important paths

- [requirements.txt](../requirements.txt) — Python dependency requirements and optional dependency groups; install with the project’s documented interpreter and environment.
- [src/main.py](../src/main.py) — QuickGuide (QG) — FastAPI Application Defines `lifespan`, `serve_frontend`, `upload_document`, `list_documents`, `get_document`, `get_document_status` and 8 more top-level symbols.
- [qg.sh](../qg.sh) — Command-line automation for qg; review prerequisites and side effects before executing.
- [qg.bat](../qg.bat) — Command-line automation for qg; review prerequisites and side effects before executing.

## Structure

| Path | Role |
| --- | --- |
| [.github/](../.github/) | GitHub workflow and contributor configuration (1 tracked entries). |
| [docs/](../docs/) | Project documentation, decisions, and reference material (13 tracked entries). |
| [src/](../src/) | Application source and platform integration (16 tracked entries). |
| [tests/](../tests/) | Automated checks and test fixtures (3 tracked entries). |

## Scope

Models and source PDFs are separate downloads or local inputs. PyMuPDF and other PDF/ML dependencies retain their own licensing terms.

## Maintaining the guide

The file catalog is a source-inspection snapshot, not proof that every runtime path works. Update it when moving files or changing module responsibilities. The 2026-10-12 documentation review did not run every application, deploy services, or validate all historical performance claims.
