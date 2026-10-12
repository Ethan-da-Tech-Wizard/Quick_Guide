# QuickGuide

Local semantic PDF search with embedding-based retrieval, page navigation, and highlighted answers.

**Status:** Document-search prototype  
**Built with:** Python, local embeddings, browser UI

[Project guide](docs/PROJECT_GUIDE.md) · [Every file explained](docs/FILE_GUIDE.md) · [Licenses and dependencies](docs/LICENSE_REVIEW.md)

## Start here

- [requirements.txt](requirements.txt) — Python dependency requirements and optional dependency groups; install with the project’s documented interpreter and environment.
- [src/main.py](src/main.py) — QuickGuide (QG) — FastAPI Application Defines `lifespan`, `serve_frontend`, `upload_document`, `list_documents`, `get_document`, `get_document_status` and 8 more top-level symbols.
- [qg.sh](qg.sh) — Command-line automation for qg; review prerequisites and side effects before executing.
- [qg.bat](qg.bat) — Command-line automation for qg; review prerequisites and side effects before executing.

[Detailed setup, usage, and development notes](PROJECT_NOTES.md) preserve the previous project documentation.

## Repository layout

| Path | Role |
| --- | --- |
| [.github/](.github/) | GitHub workflow and contributor configuration (1 tracked entries). |
| [docs/](docs/) | Project documentation, decisions, and reference material (13 tracked entries). |
| [src/](src/) | Application source and platform integration (16 tracked entries). |
| [tests/](tests/) | Automated checks and test fixtures (3 tracked entries). |

## Scope and current limits

Models and source PDFs are separate downloads or local inputs. PyMuPDF and other PDF/ML dependencies retain their own licensing terms.

## License

Original project code retains **MIT** terms in [LICENSE](LICENSE). Third-party libraries, media, data, models, and tools retain their own terms. See the [license review](docs/LICENSE_REVIEW.md) and [dependency inventory](docs/DEPENDENCIES.csv).
