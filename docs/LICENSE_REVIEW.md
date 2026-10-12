# License review — QuickGuide

Reviewed 2026-10-12. Original project code retains **MIT** terms in [LICENSE](../LICENSE).

The owner selected MIT for previously unlicensed original code. Existing licenses were preserved. This choice does not relicense copied code, dependencies, datasets, model weights, fonts, logos, or game assets.

## Preserved notices

- [LICENSE](../LICENSE)

## Dependency evidence

[DEPENDENCIES.csv](DEPENDENCIES.csv) lists 8 manifest and lockfile records. Repeated packages can appear under different manifests, versions, or development scopes. Registry metadata is evidence, not a replacement for the actual license text. For unpinned ranges, `metadata_version` is the version inspected and is not a claim about every install. Go and system/build tools can require notices beyond package-manager metadata.

| Component | Declared version | License evidence |
| --- | --- | --- |
| PyPI: fastapi | >=0.115.0 | [MIT](https://pypi.org/pypi/fastapi/json) |
| PyPI: uvicorn | >=0.30.0 | [BSD-3-Clause](https://pypi.org/pypi/uvicorn/json) |
| PyPI: python-multipart | >=0.0.9 | [Apache-2.0](https://pypi.org/pypi/python-multipart/json) |
| PyPI: aiofiles | >=24.1.0 | [Apache-2.0](https://pypi.org/pypi/aiofiles/json) |
| PyPI: PyMuPDF | >=1.24.0 | [Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License](https://pypi.org/pypi/PyMuPDF/json) |
| PyPI: sentence-transformers | >=3.0.0 | [Apache-2.0](https://pypi.org/pypi/sentence-transformers/json) |
| PyPI: faiss-cpu | >=1.8.0 | [MIT](https://pypi.org/pypi/faiss-cpu/json) |
| PyPI: numpy | >=1.26.0,<2.0.0 | [BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0](https://pypi.org/pypi/numpy/json) |

## Project-specific considerations

PyMuPDF uses AGPL or Artifex commercial terms ([upstream licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)). Review the combined application’s distribution/network-use obligations; a permissive project license does not substitute for a dependency license. Downloaded embedding models have their own terms.

## Remaining work before binary distribution

No unresolved registry-license lookup remains in the listed package records. System packages, downloaded tools/models, optional plugins, release binaries, and externally obtained assets need a build-specific inventory. This source review is not a blanket legal certification or a claim that every release artifact has been audited.
