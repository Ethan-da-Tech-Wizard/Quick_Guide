/**
 * QuickGuide (QG) — Main Application JavaScript
 *
 * Handles: document management, search, PDF.js rendering,
 * multi-match navigation, and highlight color customization.
 */

// ── PDF.js Setup ────────────────────────────────
const pdfjsLib = await import('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs');
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';

// ── State ───────────────────────────────────────
const state = {
  currentDocId: null,
  pdfDoc: null,
  currentPage: 1,
  totalPages: 0,
  scale: 1.5,
  searchResults: [],
  matches: [],          // {page, rects: [{x0,y0,x1,y1}], text}
  currentMatchIndex: -1,
  highlightColor: '#FFE066',
  isSearching: false,
  isUploading: false,
};

// ── DOM References ──────────────────────────────
const els = {
  docSelect: document.getElementById('doc-select'),
  btnUpload: document.getElementById('btn-upload'),
  fileInput: document.getElementById('file-input'),
  btnDeleteDoc: document.getElementById('btn-delete-doc'),
  searchInput: document.getElementById('search-input'),
  btnSearch: document.getElementById('btn-search'),
  searchHint: document.getElementById('search-hint'),
  resultsContainer: document.getElementById('qg-results'),
  emptyState: document.getElementById('empty-state'),
  highlightToolbar: document.getElementById('qg-highlight-toolbar'),
  btnPrevMatch: document.getElementById('btn-prev-match'),
  btnNextMatch: document.getElementById('btn-next-match'),
  matchCounter: document.getElementById('match-counter'),
  highlightColor: document.getElementById('highlight-color'),
  viewerPlaceholder: document.getElementById('viewer-placeholder'),
  pdfContainer: document.getElementById('pdf-container'),
  pdfCanvas: document.getElementById('pdf-canvas'),
  highlightLayer: document.getElementById('highlight-layer'),
  pageNav: document.getElementById('page-nav'),
  btnPrevPage: document.getElementById('btn-prev-page'),
  btnNextPage: document.getElementById('btn-next-page'),
  pageIndicator: document.getElementById('page-indicator'),
  progressModal: document.getElementById('progress-modal'),
  progressBar: document.getElementById('progress-bar'),
  progressMessage: document.getElementById('progress-message'),
};


// ══════════════════════════════════════════════════
// API Helpers
// ══════════════════════════════════════════════════

async function api(method, path, body = null) {
  const opts = {
    method,
    headers: {},
  };
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `qg-toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}


// ══════════════════════════════════════════════════
// Document Management
// ══════════════════════════════════════════════════

async function loadDocuments() {
  try {
    const docs = await api('GET', '/api/documents');
    els.docSelect.innerHTML = '<option value="">— Select a document —</option>';
    docs.forEach(doc => {
      const opt = document.createElement('option');
      opt.value = doc.id;
      opt.textContent = `${doc.filename} (${doc.page_count} pages)`;
      if (doc.status !== 'ready') {
        opt.textContent += ` [${doc.status}]`;
        opt.disabled = true;
      }
      els.docSelect.appendChild(opt);
    });

    // Restore selection
    if (state.currentDocId) {
      els.docSelect.value = state.currentDocId;
    }
  } catch (e) {
    console.error('Failed to load documents:', e);
  }
}

async function uploadDocument(file) {
  state.isUploading = true;
  els.progressModal.style.display = 'flex';
  els.progressBar.style.width = '10%';
  els.progressMessage.textContent = 'Uploading PDF...';

  try {
    const formData = new FormData();
    formData.append('file', file);

    // Start upload
    els.progressBar.style.width = '30%';
    els.progressMessage.textContent = 'Processing & indexing... This may take a moment.';

    const doc = await api('POST', '/api/documents/upload', formData);

    els.progressBar.style.width = '100%';
    els.progressMessage.textContent = 'Done! Your document is ready.';

    setTimeout(() => {
      els.progressModal.style.display = 'none';
      state.currentDocId = doc.id;
      loadDocuments().then(() => {
        els.docSelect.value = doc.id;
        selectDocument(doc.id);
      });
      showToast(`"${doc.filename}" uploaded and indexed!`, 'success');
    }, 800);

  } catch (e) {
    els.progressModal.style.display = 'none';
    showToast(`Upload failed: ${e.message}`, 'error');
  } finally {
    state.isUploading = false;
  }
}

async function selectDocument(docId) {
  if (!docId) {
    state.currentDocId = null;
    state.pdfDoc = null;
    showPlaceholder();
    clearResults();
    els.btnDeleteDoc.style.display = 'none';
    return;
  }

  state.currentDocId = parseInt(docId);
  els.btnDeleteDoc.style.display = 'inline-flex';
  clearResults();

  try {
    // Load PDF with PDF.js
    const url = `/api/documents/${docId}/pdf`;
    const loadingTask = pdfjsLib.getDocument(url);
    state.pdfDoc = await loadingTask.promise;
    state.totalPages = state.pdfDoc.numPages;
    state.currentPage = 1;

    hidePlaceholder();
    renderPage(state.currentPage);
    updatePageNav();
  } catch (e) {
    showToast(`Failed to load PDF: ${e.message}`, 'error');
  }
}

async function deleteDocument() {
  if (!state.currentDocId) return;
  if (!confirm('Are you sure you want to delete this document? This cannot be undone.')) return;

  try {
    await api('DELETE', `/api/documents/${state.currentDocId}`);
    showToast('Document deleted', 'success');
    state.currentDocId = null;
    state.pdfDoc = null;
    showPlaceholder();
    clearResults();
    els.btnDeleteDoc.style.display = 'none';
    loadDocuments();
  } catch (e) {
    showToast(`Delete failed: ${e.message}`, 'error');
  }
}


// ══════════════════════════════════════════════════
// PDF Rendering
// ══════════════════════════════════════════════════

async function renderPage(pageNum) {
  if (!state.pdfDoc) return;

  const page = await state.pdfDoc.getPage(pageNum);
  const viewport = page.getViewport({ scale: state.scale });

  const canvas = els.pdfCanvas;
  const ctx = canvas.getContext('2d');
  canvas.width = viewport.width;
  canvas.height = viewport.height;

  // Clear highlight layer
  els.highlightLayer.innerHTML = '';
  els.highlightLayer.style.width = viewport.width + 'px';
  els.highlightLayer.style.height = viewport.height + 'px';

  // Position highlight layer over canvas
  const containerRect = els.pdfContainer.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();

  await page.render({ canvasContext: ctx, viewport }).promise;

  // Reposition highlight layer after render
  requestAnimationFrame(() => {
    const rect = canvas.getBoundingClientRect();
    const parentRect = els.pdfContainer.getBoundingClientRect();
    els.highlightLayer.style.left = (rect.left - parentRect.left + els.pdfContainer.scrollLeft) + 'px';
    els.highlightLayer.style.top = (rect.top - parentRect.top + els.pdfContainer.scrollTop) + 'px';
    els.highlightLayer.style.width = rect.width + 'px';
    els.highlightLayer.style.height = rect.height + 'px';

    // Draw highlights for this page
    drawHighlightsForPage(pageNum);
  });

  state.currentPage = pageNum;
  updatePageNav();
}

function updatePageNav() {
  els.pageNav.style.display = state.pdfDoc ? 'flex' : 'none';
  els.pageIndicator.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
  els.btnPrevPage.disabled = state.currentPage <= 1;
  els.btnNextPage.disabled = state.currentPage >= state.totalPages;
}

function showPlaceholder() {
  els.viewerPlaceholder.style.display = 'flex';
  els.pdfContainer.style.display = 'none';
  els.pageNav.style.display = 'none';
}

function hidePlaceholder() {
  els.viewerPlaceholder.style.display = 'none';
  els.pdfContainer.style.display = 'flex';
}


// ══════════════════════════════════════════════════
// Search
// ══════════════════════════════════════════════════

async function performSearch() {
  const query = els.searchInput.value.trim();
  if (!query || query.length < 3) {
    showToast('Please enter at least 3 characters', 'error');
    return;
  }

  if (!state.currentDocId) {
    showToast('Please select a document first', 'error');
    return;
  }

  if (state.isSearching) return;
  state.isSearching = true;
  els.btnSearch.innerHTML = '<span class="qg-spinner"></span>';

  try {
    const data = await api('POST', '/api/search', {
      document_id: state.currentDocId,
      query: query,
      top_k: 10,
    });

    state.searchResults = data.results || [];
    displayResults(state.searchResults, query);

    if (state.searchResults.length > 0) {
      // Build matches array for multi-match navigation
      await buildMatches(state.searchResults, query);
    } else {
      showToast('No results found. Try a different question.', 'info');
    }

  } catch (e) {
    showToast(`Search failed: ${e.message}`, 'error');
  } finally {
    state.isSearching = false;
    els.btnSearch.innerHTML = 'Search';
  }
}

function displayResults(results, query) {
  if (results.length === 0) {
    els.resultsContainer.innerHTML = `
      <div class="qg-empty-state">
        <div class="qg-empty-icon">🔍</div>
        <p>No results found for your query. Try rephrasing your question.</p>
      </div>`;
    els.highlightToolbar.style.display = 'none';
    return;
  }

  els.emptyState.style.display = 'none';

  let html = '';
  results.forEach((r, i) => {
    const scorePercent = Math.round(r.score * 100);
    html += `
      <div class="qg-result-card" data-index="${i}" data-page="${r.page_number}">
        <div class="qg-result-header">
          <span class="qg-result-page">📄 Page ${r.page_number}</span>
          <span class="qg-result-score">${scorePercent}% match</span>
        </div>
        <p class="qg-result-snippet">${escapeHtml(r.snippet)}</p>
        <a class="qg-result-link" href="#" data-index="${i}">
          → Go to this section
        </a>
      </div>`;
  });

  els.resultsContainer.innerHTML = html;

  // Attach click handlers
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.index);
      navigateToMatch(idx);
    });
  });
}

function clearResults() {
  state.searchResults = [];
  state.matches = [];
  state.currentMatchIndex = -1;
  els.resultsContainer.innerHTML = `
    <div class="qg-empty-state" id="empty-state">
      <div class="qg-empty-icon">📖</div>
      <p>Select a document and ask a question to get started.</p>
    </div>`;
  els.highlightToolbar.style.display = 'none';
  els.highlightLayer.innerHTML = '';
}


// ══════════════════════════════════════════════════
// Multi-Match Highlighting & Navigation
// ══════════════════════════════════════════════════

async function buildMatches(results, query) {
  state.matches = [];

  // Group results by page and get text positions
  const pageGroups = {};
  results.forEach(r => {
    if (!pageGroups[r.page_number]) {
      pageGroups[r.page_number] = [];
    }
    pageGroups[r.page_number].push(r);
  });

  // Extract key phrases from the query for highlighting
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);

  for (const [pageStr, pageResults] of Object.entries(pageGroups)) {
    const page = parseInt(pageStr);

    // Try to get text positions for the user's query directly
    for (const result of pageResults) {
      try {
        const posData = await api('GET',
          `/api/documents/${state.currentDocId}/text-positions?page=${page}&q=${encodeURIComponent(query)}`
        );

        if (posData.rects && posData.rects.length > 0) {
          state.matches.push({
            page,
            rects: posData.rects,
            text: result.snippet,
            resultIndex: results.indexOf(result),
          });
        } else {
          // Fallback: create a simple match for the page
          state.matches.push({
            page,
            rects: [],
            text: result.snippet,
            resultIndex: results.indexOf(result),
          });
        }
      } catch {
        state.matches.push({
          page,
          rects: [],
          text: result.snippet,
          resultIndex: results.indexOf(result),
        });
      }
    }
  }

  if (state.matches.length > 0) {
    els.highlightToolbar.style.display = 'block';
    state.currentMatchIndex = 0;
    updateMatchCounter();
    navigateToMatch(0);
  }
}

async function navigateToMatch(index) {
  if (index < 0 || index >= state.matches.length) return;

  state.currentMatchIndex = index;
  const match = state.matches[index];

  // Highlight active result card
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(c => c.classList.remove('active'));
  const activeCard = els.resultsContainer.querySelector(`[data-index="${match.resultIndex}"]`);
  if (activeCard) {
    activeCard.classList.add('active');
    activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Navigate to the page
  if (state.currentPage !== match.page) {
    await renderPage(match.page);
  } else {
    drawHighlightsForPage(match.page);
  }

  updateMatchCounter();
}

async function drawHighlightsForPage(pageNum) {
  els.highlightLayer.innerHTML = '';

  const pageMatches = state.matches.filter(m => m.page === pageNum);
  const color = state.highlightColor;

  pageMatches.forEach((match, i) => {
    const isActive = state.matches.indexOf(match) === state.currentMatchIndex;

    if (match.rects.length > 0) {
      match.rects.forEach(rect => {
        const div = document.createElement('div');
        div.className = `qg-highlight-rect${isActive ? ' active-match' : ''}`;
        div.style.left = (rect.x0 * 100) + '%';
        div.style.top = (rect.y0 * 100) + '%';
        div.style.width = (rect.width * 100) + '%';
        div.style.height = (rect.height * 100) + '%';
        div.style.background = hexToRgba(color, isActive ? 0.6 : 0.35);
        div.style.borderColor = hexToRgba(color, 0.9);
        els.highlightLayer.appendChild(div);

        // Scroll into view if active
        if (isActive) {
          setTimeout(() => {
            const containerRect = els.pdfContainer.getBoundingClientRect();
            const highlightRect = div.getBoundingClientRect();
            const scrollTarget = highlightRect.top - containerRect.top + els.pdfContainer.scrollTop - 100;
            els.pdfContainer.scrollTo({ top: scrollTarget, behavior: 'smooth' });
          }, 100);
        }
      });
    } else if (isActive) {
      // No precise rects — show a page-level indicator
      const div = document.createElement('div');
      div.className = 'qg-highlight-rect active-match';
      div.style.left = '5%';
      div.style.top = '10%';
      div.style.width = '90%';
      div.style.height = '4px';
      div.style.background = hexToRgba(color, 0.8);
      div.style.borderColor = color;
      els.highlightLayer.appendChild(div);
    }
  });

  // Draw saved custom highlights
  if (!state.currentDocId) return;
  try {
    const highlights = await api('GET', `/api/documents/${state.currentDocId}/highlights?page=${pageNum}`);
    for (const h of highlights) {
      if (h.page_number !== pageNum) continue;

      try {
        // Fetch precise text positioning for this custom highlight
        const posData = await api('GET', `/api/documents/${state.currentDocId}/text-positions?page=${pageNum}&q=${encodeURIComponent(h.text_content)}`);

        if (posData.rects && posData.rects.length > 0) {
          posData.rects.forEach(rect => {
            const div = document.createElement('div');
            div.className = 'qg-highlight-rect';
            div.style.left = (rect.x0 * 100) + '%';
            div.style.top = (rect.y0 * 100) + '%';
            div.style.width = (rect.width * 100) + '%';
            div.style.height = (rect.height * 100) + '%';
            div.style.background = hexToRgba(h.color, 0.45);
            div.style.borderColor = h.color;
            div.style.borderWidth = '1px';
            div.style.borderStyle = 'solid';
            div.title = "Saved Highlight: " + h.text_content;
            els.highlightLayer.appendChild(div);
          });
        }
      } catch (err) {
        console.warn('Could not locate highlight on page', err);
      }
    }
  } catch (e) {
    console.error('Failed to load saved highlights for page', pageNum, e);
  }
}

function updateMatchCounter() {
  els.matchCounter.textContent = state.matches.length > 0
    ? `Match ${state.currentMatchIndex + 1} of ${state.matches.length}`
    : 'No matches';
}

function nextMatch() {
  if (state.matches.length === 0) return;
  const next = (state.currentMatchIndex + 1) % state.matches.length;
  navigateToMatch(next);
}

function prevMatch() {
  if (state.matches.length === 0) return;
  const prev = (state.currentMatchIndex - 1 + state.matches.length) % state.matches.length;
  navigateToMatch(prev);
}


// ══════════════════════════════════════════════════
// Highlight Color Management
// ══════════════════════════════════════════════════

function changeHighlightColor(color) {
  state.highlightColor = color;
  els.highlightColor.value = color;

  // Update swatch active state
  document.querySelectorAll('.qg-color-swatch').forEach(s => {
    s.classList.toggle('active', s.dataset.color === color);
  });

  // Re-draw highlights
  if (state.currentPage && state.matches.length > 0) {
    drawHighlightsForPage(state.currentPage);
  }
}


// ══════════════════════════════════════════════════
// Utility
// ══════════════════════════════════════════════════

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


// ══════════════════════════════════════════════════
// Tabs UI
// ══════════════════════════════════════════════════

document.querySelectorAll('.qg-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Hide all
    document.querySelectorAll('.qg-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.qg-tab-content').forEach(c => {
      c.classList.remove('active');
      c.style.display = 'none';
    });

    // Show clicked
    tab.classList.add('active');
    const target = document.getElementById(tab.dataset.target);
    target.classList.add('active');
    if (tab.dataset.target === 'search-view') {
      target.style.display = 'block';
    } else {
      target.style.display = 'flex';
      loadSavedHighlights();
    }
  });
});


// ══════════════════════════════════════════════════
// Saved Highlights Management (Light Blue)
// ══════════════════════════════════════════════════

async function loadSavedHighlights() {
  if (!state.currentDocId) return;

  try {
    const highlights = await api('GET', `/api/documents/${state.currentDocId}/highlights`);
    const container = document.getElementById('qg-highlights-list');

    if (highlights.length === 0) {
      container.innerHTML = `
        <div class="qg-empty-state" id="empty-highlights-state">
          <div class="qg-empty-icon">🖍️</div>
          <p>No highlights yet. Select text on the PDF to save it.</p>
        </div>`;
      return;
    }

    let html = '';
    highlights.forEach(h => {
      html += `
        <div class="qg-result-card" data-page="${h.page_number}">
          <div class="qg-result-header">
            <span class="qg-result-page">📄 Page ${h.page_number}</span>
            <button class="qg-btn-sm btn-delete-highlight" data-id="${h.id}" title="Delete highlight" style="color:var(--danger); border:none; background:transparent">✖</button>
          </div>
          <p class="qg-result-snippet" style="border-left: 4px solid ${h.color}; padding-left: 8px;">${escapeHtml(h.text_content)}</p>
        </div>`;
    });

    container.innerHTML = html;

    // Attach click to navigate
    container.querySelectorAll('.qg-result-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete-highlight')) return; // ignore delete clicks
        const page = parseInt(card.dataset.page);
        if (state.currentPage !== page) {
          renderPage(page);
        }
      });
    });

    // Attach click to delete
    container.querySelectorAll('.btn-delete-highlight').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm('Delete this highlight?')) {
          try {
            await api('DELETE', `/api/highlights/${btn.dataset.id}`);
            loadSavedHighlights();
            if (state.currentPage) {
              renderPage(state.currentPage); // redraw current page without it
            }
          } catch (err) {
            showToast('Failed to delete highlight', 'error');
          }
        }
      });
    });

  } catch (e) {
    showToast(`Failed to load highlights: ${e.message}`, 'error');
  }
}

// Intercept mouse drag selections on the canvas to create custom highlights
els.pdfContainer.addEventListener('mouseup', async () => {
  if (!state.currentDocId || !state.currentPage) return;

  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text.length < 3) return;

  // Ask for confirmation
  if (!confirm(`Save highlight for:\\n"${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"?`)) {
    selection.removeAllRanges();
    return;
  }

  try {
    await api('POST', '/api/highlights', {
      document_id: state.currentDocId,
      page_number: state.currentPage,
      text_content: text,
      color: '#ADD8E6' // Custom Light Blue
    });

    showToast('Highlight saved!', 'success');
    selection.removeAllRanges();

    // Switch to Highlights tab if not already on it to show the new highlight
    const tabHighlights = document.querySelector('.qg-tab[data-target="highlights-view"]');
    if (tabHighlights && !tabHighlights.classList.contains('active')) {
      tabHighlights.click();
    } else {
      loadSavedHighlights();
    }

    // Overwrite the current search matches if any with a fresh un-matched page so the custom highlights render properly?
    // Actually, just re-rendering the page is best to fetch backend highlights.
    // Wait, the backend draws API highlights separately? No, our JS draws highlights based on `state.matches`.
    // We need to also fetch backend highlights in `drawHighlightsForPage`. Let's augment `renderPage` or `drawHighlightsForPage`.
    renderPage(state.currentPage);

  } catch (e) {
    showToast(`Highlight failed: ${e.message}`, 'error');
  }
});


// ══════════════════════════════════════════════════
// Event Listeners
// ══════════════════════════════════════════════════

// Document selection
els.docSelect.addEventListener('change', (e) => selectDocument(e.target.value));

// Upload
els.btnUpload.addEventListener('click', () => els.fileInput.click());
els.fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    uploadDocument(e.target.files[0]);
    e.target.value = '';
  }
});

// Delete
els.btnDeleteDoc.addEventListener('click', deleteDocument);

// Search
els.btnSearch.addEventListener('click', performSearch);
els.searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') performSearch();
});

// Page navigation
els.btnPrevPage.addEventListener('click', () => {
  if (state.currentPage > 1) renderPage(state.currentPage - 1);
});
els.btnNextPage.addEventListener('click', () => {
  if (state.currentPage < state.totalPages) renderPage(state.currentPage + 1);
});

// Match navigation
els.btnPrevMatch.addEventListener('click', prevMatch);
els.btnNextMatch.addEventListener('click', nextMatch);

// Highlight color
els.highlightColor.addEventListener('input', (e) => changeHighlightColor(e.target.value));
document.querySelectorAll('.qg-color-swatch').forEach(swatch => {
  swatch.addEventListener('click', () => changeHighlightColor(swatch.dataset.color));
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl+K: Focus search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    els.searchInput.focus();
  }
  // Ctrl+→: Next match
  if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowRight') {
    e.preventDefault();
    nextMatch();
  }
  // Ctrl+←: Previous match
  if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowLeft') {
    e.preventDefault();
    prevMatch();
  }
  // Esc: Clear results
  if (e.key === 'Escape') {
    clearResults();
    if (state.currentPage) renderPage(state.currentPage);
  }
});

// Window resize: re-render highlights
window.addEventListener('resize', () => {
  if (state.pdfDoc && state.currentPage) {
    renderPage(state.currentPage);
  }
});


// ══════════════════════════════════════════════════
// Initialize
// ══════════════════════════════════════════════════

loadDocuments();
changeHighlightColor('#FFE066');
