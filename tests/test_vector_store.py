# ==============================================================================
# Program: test_vector_store.py
# Purpose: Regression tests for src/services/vector_store.py. The module once
#          shipped with an IndentationError (the faiss.normalize_L2 call sat at the
#          wrong indent level), which made the whole app fail at import time.
# How to run: `python -m pytest tests/test_vector_store.py` (the behavioural test
#          needs numpy and is skipped when numpy is not installed).
# ==============================================================================

import ast
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
# The app uses flat imports (`from config import ...`), so src/ must be importable.
sys.path.insert(0, str(SRC))
sys.path.insert(0, os.fspath(SRC / "services"))


def test_vector_store_source_parses():
    """The file must be valid Python; this needs no third-party packages.

    Pins the original bug: an over-indented `self.index.add(...)` line raised
    IndentationError, so importing the module failed before any code could run.
    """
    source = (SRC / "services" / "vector_store.py").read_text(encoding="utf-8")
    compile(source, "vector_store.py", "exec")
    # Also check the structure: normalize_L2 must sit inside VectorStore.add's FAISS branch.
    tree = ast.parse(source)
    add = next(n for c in tree.body if isinstance(c, ast.ClassDef)
               for n in c.body if isinstance(n, ast.FunctionDef) and n.name == "add")
    assert any("normalize_L2" in ast.dump(n) for n in ast.walk(add))


def test_numpy_fallback_add_and_search_roundtrip(tmp_path, monkeypatch):
    """Importing the module and adding/searching vectors returns the nearest chunk.

    Forces the pure-NumPy fallback (HAS_FAISS False) so it runs without FAISS, and
    redirects VECTOR_DIR to a temp folder so no real index files are touched.
    """
    np = pytest.importorskip("numpy")
    from services import vector_store

    monkeypatch.setattr(vector_store, "HAS_FAISS", False)
    monkeypatch.setattr(vector_store, "VECTOR_DIR", tmp_path)

    store = vector_store.VectorStore(document_id=999)
    store.index_path = tmp_path / "doc_999.faiss"
    store.map_path = tmp_path / "doc_999.map"
    vectors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    store.add([10, 20], vectors)

    # A query close to the second vector must rank chunk 20 first.
    hits = store.search(np.array([0.0, 0.9, 0.1], dtype=np.float32), top_k=2)
    assert hits[0][0] == 20
