# QuickGuide

QuickGuide is a local PDF search prototype with a Python API and browser interface. Its code includes document upload, semantic search, page navigation, and text-position endpoints for highlighting.

**Status:** Prototype. Current setup and search quality have not been independently verified in this review; check results against the original document.

## Start the project

Review [requirements.txt](requirements.txt) and the platform launcher before running it. The repository's Unix launcher creates a virtual environment, installs Python dependencies, and starts the application:

```sh
./qg.sh
```

The launcher directs the browser to `http://127.0.0.1:8080`. The application source also documents running `python main.py` from `src/` after dependencies are installed. A [Windows launcher](qg.bat) is included. Local model files may need to be downloaded; PDFs remain user-supplied inputs. These instructions are derived from source and were not run in this review.

## Explore

- [Application and API](src/main.py)
- [Detailed setup and usage notes](PROJECT_NOTES.md)
- [Project guide](docs/PROJECT_GUIDE.md) · [License review](docs/LICENSE_REVIEW.md)

## License

Project code is distributed under the [MIT License](LICENSE). PDF, model, and other dependencies have separate terms; consult the [license review](docs/LICENSE_REVIEW.md) and [dependency inventory](docs/DEPENDENCIES.csv).
