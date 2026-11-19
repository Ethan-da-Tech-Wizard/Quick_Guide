// ==============================================================================
// Program: app.js
// Programmer: Ethan-da-Tech-Wizard
// Last Modified: November 18, 2026
// Purpose: Primary client-side application logic for QuickGuide web UI.
//          Coordinates dynamic PDF.js document rendering with continuous lazy-scroll,
//          manages asynchronous API communication for document uploads and semantic
//          searches, renders bounding-box highlight overlays, handles multi-match
//          keyboard/button navigation, and persists custom text highlights.
// ==============================================================================

// ── PDF.js Setup ────────────────────────────────
// Top-level await is allowed because index.html loads this file with type="module".
// PDF.js is fetched from the cdnjs CDN (an external network request), so the viewer
// needs internet access unless the browser has the module cached. The worker script is
// loaded from the same CDN version; PDF.js runs parsing/decoding in that worker thread.
const pdfjsLib = await import('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs');
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';

// ── State ───────────────────────────────────────
// Single mutable object holding everything the UI needs to remember between events.
// There is no framework: functions below read and write this object and then update the DOM.
const state = {
  // Database id of the selected document, or null when none is selected.
  currentDocId: null,
  // The loaded PDF.js document proxy (null until a PDF has been opened).
  pdfDoc: null,
  // currentPage is reset to 1 when a document opens, then kept in sync with the scroll
  // position by updatePageIndicatorContainer().
  currentPage: 1,
  totalPages: 0,
  // Render scale passed to PDF.js; 1.5 means 1.5 CSS pixels per PDF point.
  scale: 1.5,
  // Raw hits as returned by POST /api/search (text, page, score, snippet).
  searchResults: [],
  // Highlightable matches built from the hits; rects are the normalized 0-1 boxes.
  matches: [],          // {page, rects: [{x0,y0,x1,y1}], text}
  // Index into `matches` of the active match, or -1 when there is none.
  currentMatchIndex: -1,
  // Colour used to draw search-match overlays (saved highlights keep their own colour).
  highlightColor: '#FFE066',
  // isSearching / isUploading act as guards against overlapping requests.
  isSearching: false,
  isUploading: false,
};

// ── DOM References ──────────────────────────────
// Cache of DOM element handles, looked up once at load time. Every id here must exist
// in index.html; a missing id would yield null and fail on first use.
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
  floatingPageIndicator: document.getElementById('floating-page-indicator'),
  progressModal: document.getElementById('progress-modal'),
  progressBar: document.getElementById('progress-bar'),
  progressMessage: document.getElementById('progress-message'),
};

// ── Intersection Observer for Lazy Rendering ──
// Pages are rendered lazily: an IntersectionObserver fires when a page placeholder
// nears the viewport, and `renderedPages` remembers which pages are already drawn so
// they are not rendered twice.
let pageObserver = null;
const renderedPages = new Set();


// ══════════════════════════════════════════════════
// API Helpers
// ══════════════════════════════════════════════════

// Small fetch wrapper used for every backend call.
//   method - HTTP verb; path - URL; body - plain object (sent as JSON) or FormData
//   (sent as multipart, letting the browser set the Content-Type boundary itself).
// Returns the parsed JSON response. On a non-2xx status it throws an Error whose message
// is FastAPI's `detail` field when present, otherwise the HTTP status text.
async function api(method, path, body = null) {
  const opts = {
    method,
    headers: {},
  };
  // Do not set Content-Type manually for FormData: the browser must add the boundary.
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    // The error body may not be JSON (e.g. a proxy error page), so fall back to statusText.
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Shows a transient notification in the corner. `type` is a CSS class suffix:
// info, success or error. The toast fades out after 4 s and is removed 300 ms later,
// once the CSS transition has finished.
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

// Fetches the document list and rebuilds the <select>. Documents that are still being
// processed (or failed) are shown but disabled, so they cannot be opened.
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

    // Keep the current document selected after the list is rebuilt.
    // Restore selection
    if (state.currentDocId) {
      els.docSelect.value = state.currentDocId;
    }
  } catch (e) {
    console.error('Failed to load documents:', e);
  }
}

// Uploads a PDF and waits for the server to finish indexing it. The request does not
// return until extraction, chunking and embedding are done, so the progress bar values
// below are fixed milestones rather than real progress; /status exists but is not polled.
async function uploadDocument(file) {
  state.isUploading = true;
  els.progressModal.style.display = 'flex';
  els.progressBar.style.width = '10%';
  els.progressMessage.textContent = 'Uploading PDF...';

  try {
    const formData = new FormData();
    formData.append('file', file);

    // Starts the upload: FormData field name 'file' must match the FastAPI parameter.
    // Start upload
    els.progressBar.style.width = '30%';
    els.progressMessage.textContent = 'Processing & indexing... This may take a moment.';

    const doc = await api('POST', '/api/documents/upload', formData);

    els.progressBar.style.width = '100%';
    els.progressMessage.textContent = 'Done! Your document is ready.';

    // Short delay so the user sees "Done", then hide the modal and open the new document.
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
  // Always clear the flag, whether the upload succeeded or failed.
  } finally {
    state.isUploading = false;
  }
}

// Opens (or closes, when docId is empty) a document in the viewer. docId arrives as a
// string from the <select> element, hence the parseInt below.
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
    // PDF.js fetches the PDF from the backend and streams pages on demand.
    // Load PDF with PDF.js
    const url = `/api/documents/${docId}/pdf`;
    const loadingTask = pdfjsLib.getDocument(url);
    state.pdfDoc = await loadingTask.promise;
    state.totalPages = state.pdfDoc.numPages;
    state.currentPage = 1;

    hidePlaceholder();
    initScrollContainer();
  } catch (e) {
    showToast(`Failed to load PDF: ${e.message}`, 'error');
  }
}

// Deletes the current document after a browser confirm() prompt. The server removes the
// PDF, the vector index and the database rows.
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
// Continuous PDF Rendering
// ══════════════════════════════════════════════════

// Builds the continuous-scroll view. Instead of rendering all pages up front (slow
// for big PDFs), it creates one empty placeholder per page, sized by an estimate, and
// renders each page's canvas only when it comes near the viewport.
async function initScrollContainer() {
  els.pdfContainer.innerHTML = '';
  renderedPages.clear();

  if (pageObserver) {
    pageObserver.disconnect();
  }

  // Page 1 is measured to estimate the size of all placeholders, which assumes every page
  // has the same dimensions as page 1. Real size is applied when each page is rendered.
  // Calculate base dimensions
  const firstPage = await state.pdfDoc.getPage(1);
  const viewport = firstPage.getViewport({ scale: state.scale });
  const aspectRatio = viewport.height / viewport.width;

  // clientWidth is 0 if the container is still hidden; 40 px is padding/scrollbar allowance.
  // Fallback to viewport width if the container hasn't painted yet
  const containerWidth = els.pdfContainer.clientWidth;
  const safeWidth = containerWidth > 40 ? containerWidth - 40 : viewport.width;
  const wrapperWidth = Math.min(viewport.width, safeWidth);
  // Reserve at least a square's worth of height so the scrollbar is not wildly short.
  const estimatedHeight = wrapperWidth * Math.max(aspectRatio, 1.0);

  // rootMargin pre-loads pages 400 px before they scroll into view; a threshold of 0.01
  // means a page counts as visible as soon as 1% of it intersects.
  pageObserver = new IntersectionObserver(handleIntersection, {
    root: els.pdfContainer,
    rootMargin: '400px 0px 400px 0px', // Pre-render 400px outside viewport
    threshold: 0.01
  });

  // Create empty wrapper divs for all pages
  for (let i = 1; i <= state.totalPages; i++) {
    const wrapper = document.createElement('div');
    wrapper.className = 'qg-page-wrapper loading';
    wrapper.id = `page-wrapper-${i}`;
    wrapper.dataset.page = i;

    // Set estimated dimensions to reserve space
    wrapper.style.width = wrapperWidth + 'px';
    wrapper.style.height = estimatedHeight + 'px';

    // Add canvas and layers placeholders
    // Three stacked layers positioned absolutely by CSS: the canvas holds the pixels, the
    // text layer is transparent selectable text on top, and the highlight layer holds the
    // coloured rectangles.
    wrapper.innerHTML = `
      <canvas class="qg-pdf-canvas"></canvas>
      <div class="qg-text-layer"></div>
      <div class="qg-highlight-layer"></div>
    `;

    els.pdfContainer.appendChild(wrapper);
    pageObserver.observe(wrapper);
  }

  // Initial indicator text.
  updatePageIndicatorContainer();

  // Note: a new scroll listener is added every time a document is opened and is never
  // removed, so repeated opens stack duplicate listeners (harmless but redundant).
  // Also track which page is mostly in view to update the floating indicator
  els.pdfContainer.addEventListener('scroll', updatePageIndicatorContainer, { passive: true });
}

// IntersectionObserver callback: render any page that has just become visible.
function handleIntersection(entries) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const pageNum = parseInt(entry.target.dataset.page);
      if (!renderedPages.has(pageNum)) {
        renderPageIntoWrapper(pageNum, entry.target);
      }
    }
  });
}

// Draws one page into its placeholder: canvas pixels, selectable text layer, then any
// highlights. renderedPages is updated first so concurrent observer events cannot start
// a second render of the same page.
async function renderPageIntoWrapper(pageNum, wrapper) {
  renderedPages.add(pageNum);

  const page = await state.pdfDoc.getPage(pageNum);
  const viewport = page.getViewport({ scale: state.scale });

  const canvas = wrapper.querySelector('.qg-pdf-canvas');
  const ctx = canvas.getContext('2d');

  // Replace the estimated size with the real size now that the page is known.
  // Use exact dimensions now that we have the specific page
  wrapper.style.width = viewport.width + 'px';
  wrapper.style.height = viewport.height + 'px';

  // The canvas bitmap is sized to the viewport directly; no devicePixelRatio scaling is
  // applied, so output may look soft on high-DPI displays.
  canvas.width = viewport.width;
  canvas.height = viewport.height;

  await page.render({ canvasContext: ctx, viewport }).promise;

  // The text layer makes text selectable and is what the highlight-by-selection feature
  // reads from; failures there are non-fatal (the page is still readable).
  // Render invisible text layer for selection
  const textLayerDiv = wrapper.querySelector('.qg-text-layer');
  if (textLayerDiv) {
    textLayerDiv.style.width = viewport.width + 'px';
    textLayerDiv.style.height = viewport.height + 'px';
    textLayerDiv.innerHTML = '';

    try {
      const textContent = await page.getTextContent();
      await pdfjsLib.renderTextLayer({
        textContentSource: textContent,
        container: textLayerDiv,
        viewport: viewport,
        textDivs: []
      }).promise;
    } catch (err) {
      console.warn("Text layer rendering failed for page " + pageNum, err);
    }
  }

  wrapper.classList.remove('loading');

  // The 'loading' class is a styling hook (e.g. a placeholder look) for unrendered pages.
  // Draw highlights specific to this page
  drawHighlightsForPage(pageNum);
}

// Figures out which page is at the top of the scroll area and updates the floating
// "Page X of Y" badge. Picks the wrapper whose offsetTop is closest to scrollTop.
function updatePageIndicatorContainer() {
  if (!state.pdfDoc) return;
  els.floatingPageIndicator.style.display = 'block';

  // Find which wrapper is closest to the top of the container
  const containerTop = els.pdfContainer.scrollTop;
  const wrappers = Array.from(els.pdfContainer.querySelectorAll('.qg-page-wrapper'));

  let closestPage = 1;
  let minDiff = Infinity;

  wrappers.forEach(w => {
    const diff = Math.abs(w.offsetTop - containerTop);
    if (diff < minDiff) {
      minDiff = diff;
      closestPage = parseInt(w.dataset.page);
    }
  });

  state.currentPage = closestPage;
  els.floatingPageIndicator.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
}

// Scrolls the viewer to a page. Despite the name it does not draw anything; the page is
// rendered by the observer once it scrolls into range. Kept for older call sites.
async function renderPage(pageNum) {
  // Polyfill the old renderPage function for external compat
  const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
  if (wrapper) {
    wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Shows the welcome placeholder and hides the PDF area (no document selected).
function showPlaceholder() {
  els.viewerPlaceholder.style.display = 'flex';
  els.pdfContainer.style.display = 'none';
  if (els.floatingPageIndicator) els.floatingPageIndicator.style.display = 'none';
}

// Hides the placeholder and reveals the PDF scroll area.
function hidePlaceholder() {
  els.viewerPlaceholder.style.display = 'none';
  els.pdfContainer.style.display = 'flex';
}


// ══════════════════════════════════════════════════
// Search
// ══════════════════════════════════════════════════

// Runs a semantic search for the text in the search box, then displays result cards and
// builds highlight matches. Validates input and ignores re-entrant calls.
async function performSearch() {
  const query = els.searchInput.value.trim();
  // Minimum of 3 characters mirrors the server's SearchRequest.query min_length.
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
  // Spinner in the button signals progress and, together with isSearching, blocks double submits.
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
      // Each hit becomes a match that carries its page and highlight boxes.
      // Build matches array for multi-match navigation
      await buildMatches(state.searchResults, query);
    } else {
      showToast('No results found. Try a different question.', 'info');
    }

  } catch (e) {
    showToast(`Search failed: ${e.message}`, 'error');
  } finally {
    state.isSearching = false;
    // Restore the button label in every case.
    els.btnSearch.innerHTML = 'Search';
  }
}

// Renders the list of result cards. Snippet text goes through escapeHtml() because it
// comes from the PDF and is inserted via innerHTML (prevents HTML injection).
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

  // Event handlers are attached after innerHTML is set, since the elements are new.
  // Attach click handlers
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.index);
      navigateToMatch(idx);
    });
  });
}

// Resets all search state and UI (results list, toolbar, input, highlight overlays).
// Called when the document changes and when Escape is pressed.
function clearResults() {
  state.searchResults = [];
  state.matches = [];
  state.currentMatchIndex = -1;
  state.isSearching = false;

  els.resultsContainer.innerHTML = '';
  els.resultsContainer.style.display = 'none';
  els.emptyState.style.display = 'flex';
  els.highlightToolbar.style.display = 'none';
  els.searchInput.value = '';

  // Remove old overlays from every page, then redraw so saved highlights remain visible.
  // Clear all page highlights
  document.querySelectorAll('.qg-highlight-layer').forEach(layer => {
    layer.innerHTML = '';
  });

  // Re-draw saved highlights if needed
  // drawHighlightsForPage is async and fire-and-forget here; it silently skips pages
  // whose wrapper does not exist yet.
  if (state.currentPage) {
    // We don't renderPage() here to avoid loop, just rely on standard draw.
    // drawHighlightsForPage handles both custom and search matches.
    for (let i = 1; i <= state.totalPages; i++) {
      drawHighlightsForPage(i);
    }
  }
}


// ══════════════════════════════════════════════════
// Multi-Match Highlighting & Navigation
// ══════════════════════════════════════════════════

// Converts search hits into `state.matches`, asking the backend where the query text
// appears on each hit's page. Note: the same query string is sent for every result on a
// page (one request per result), and the backend highlights every word of the query,
// so hits on the same page get identical rectangles. Fallback: a match without
// rectangles still lets the UI jump to the page.
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
  // Words of 3 characters or fewer are dropped. queryWords is currently unused.
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);

  for (const [pageStr, pageResults] of Object.entries(pageGroups)) {
    const page = parseInt(pageStr);

    // Sequential awaits (not Promise.all) keep requests ordered and light on the server.
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
          // Even without exact coordinates the match is kept so navigation still works.
          // Fallback: create a simple match for the page
          state.matches.push({
            page,
            rects: [],
            text: result.snippet,
            resultIndex: results.indexOf(result),
          });
        }
      // Network or server error: degrade to a page-level match instead of failing the search.
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

  // Show the toolbar and jump to the first match.
  if (state.matches.length > 0) {
    els.highlightToolbar.style.display = 'block';
    state.currentMatchIndex = 0;
    updateMatchCounter();
    navigateToMatch(0);
  }
}

// Makes match number `index` the active one: updates the result-card styling, scrolls
// the card into view, brings the page into view and redraws highlights. Out-of-range
// indexes are ignored.
async function navigateToMatch(index) {
  if (index < 0 || index >= state.matches.length) return;

  state.currentMatchIndex = index;
  const match = state.matches[index];

  // Only one card may carry the 'active' class at a time.
  // Highlight active result card
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(c => c.classList.remove('active'));
  const activeCard = els.resultsContainer.querySelector(`[data-index="${match.resultIndex}"]`);
  if (activeCard) {
    activeCard.classList.add('active');
    activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // If the match is on another page, scroll there (the observer then renders it and
  // draws highlights); otherwise just redraw the overlay on the current page.
  // Navigate to the page
  if (state.currentPage !== match.page) {
    await renderPage(match.page);
  } else {
    drawHighlightsForPage(match.page);
  }

  updateMatchCounter();
}

// Redraws all overlays on one page: first search matches (active one brighter and
// scrolled to), then the user's saved highlights fetched from the server. Percent-based
// positions mean the overlays scale with the page wrapper, whatever its pixel size.
async function drawHighlightsForPage(pageNum) {
  const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
  if (!wrapper) return;
  const highlightLayer = wrapper.querySelector('.qg-highlight-layer');
  if (!highlightLayer) return;

  highlightLayer.innerHTML = '';

  // Matches belonging to this page; `isActive` marks the one currently selected.
  const pageMatches = state.matches.filter(m => m.page === pageNum);
  const color = state.highlightColor;

  pageMatches.forEach((match, i) => {
    const isActive = state.matches.indexOf(match) === state.currentMatchIndex;

    // Draw one box per rectangle returned by the backend, using the shared percent coordinates.
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
        highlightLayer.appendChild(div);

        // Wait 200 ms so the layout has settled before computing the scroll offset, then scroll
        // so the highlight sits about 100 px below the container's top.
        // Scroll into view if active
        if (isActive) {
          setTimeout(() => {
            const containerRect = els.pdfContainer.getBoundingClientRect();
            const highlightRect = div.getBoundingClientRect();
            const scrollTarget = highlightRect.top - containerRect.top + els.pdfContainer.scrollTop - 100;
            els.pdfContainer.scrollTo({ top: scrollTarget, behavior: 'smooth' });
          }, 200);
        }
      });
    // No coordinates: show a thin bar near the top of the page as a visible cue.
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
      highlightLayer.appendChild(div);
    }
  });

  // Saved highlights: stored text only (no coordinates), so each one is re-located on the
  // page with the text-positions endpoint every time the page is drawn.
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

            const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
            if (wrapper) {
              const highlightLayer = wrapper.querySelector('.qg-highlight-layer');
              if (highlightLayer) highlightLayer.appendChild(div);
            }
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

// Updates the "Match N of M" label (matches are 1-based for display).
function updateMatchCounter() {
  els.matchCounter.textContent = state.matches.length > 0
    ? `Match ${state.currentMatchIndex + 1} of ${state.matches.length}`
    : 'No matches';
}

// Moves to the next match, wrapping from the last back to the first.
function nextMatch() {
  if (state.matches.length === 0) return;
  const next = (state.currentMatchIndex + 1) % state.matches.length;
  navigateToMatch(next);
}

// Moves to the previous match; adding length before the modulo avoids a negative index.
function prevMatch() {
  if (state.matches.length === 0) return;
  const prev = (state.currentMatchIndex - 1 + state.matches.length) % state.matches.length;
  navigateToMatch(prev);
}


// ══════════════════════════════════════════════════
// Highlight Color Management
// ══════════════════════════════════════════════════

// Sets the colour used for search-match overlays, syncs the picker and swatches, and
// redraws the current page. Also called once at startup to initialise the UI state.
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

// Escapes text for safe HTML insertion by letting the browser do it: assigning to
// textContent and reading innerHTML turns <, >, & into entities.
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Converts "#RRGGBB" to an rgba() string so overlay opacity can be varied. Expects a
// full 6-digit hex value (as produced by <input type=color>); 3-digit forms are not handled.
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


// ══════════════════════════════════════════════════
// Tabs UI
// ══════════════════════════════════════════════════

// Tab switching between Search and My Highlights. Sibling panels are hidden, the clicked
// one is shown; display differs (block vs flex) because the highlights panel is a column
// flex container. The highlights list is reloaded each time its tab opens.
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

// Fetches this document's saved highlights and renders them as cards in the sidebar.
// Clicking a card scrolls to its page; the cross button deletes it.
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

    // Navigation uses the stored page only, since highlights have no saved coordinates.
    // Attach click to navigate
    container.querySelectorAll('.qg-result-card').forEach(card => {
      card.addEventListener('click', (e) => {
        // Clicks on the delete button must not also trigger navigation.
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
        // stopPropagation keeps the card's own click handler from firing as well.
        e.stopPropagation();
        if (confirm('Delete this highlight?')) {
          try {
            await api('DELETE', `/api/highlights/${btn.dataset.id}`);
            loadSavedHighlights();
            if (state.currentPage) {
              // Redraw the page so the removed highlight disappears from the overlay.
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

// Creating a highlight: when the user releases the mouse after dragging across text in
// the PDF, the selected text (from the transparent text layer) is offered for saving.
// Only the text and page are stored; the colour is fixed at light blue.
// Intercept mouse drag selections on the canvas to create custom highlights
els.pdfContainer.addEventListener('mouseup', async (e) => {
  if (!state.currentDocId) return;

  const wrapper = e.target.closest('.qg-page-wrapper');
  if (!wrapper) return;
  const pageNum = parseInt(wrapper.dataset.page);

  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text.length < 3) return;

  // Confirm before saving, so accidental drags do not create highlights. Note: the
  // source contains an escaped backslash-n (\\n), so the prompt shows a literal \n instead
  // of a line break.
  // Ask for confirmation
  if (!confirm(`Save highlight for:\\n"${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"?`)) {
    selection.removeAllRanges();
    return;
  }

  try {
    await api('POST', '/api/highlights', {
      document_id: state.currentDocId,
      page_number: pageNum,
      text_content: text,
      color: '#ADD8E6' // Custom Light Blue
    });

    showToast('Highlight saved!', 'success');
    selection.removeAllRanges();

    // After saving, switch to the Highlights tab (clicking it also reloads the list).
    // Switch to Highlights tab if not already on it to show the new highlight
    const tabHighlights = document.querySelector('.qg-tab[data-target="highlights-view"]');
    if (tabHighlights && !tabHighlights.classList.contains('active')) {
      tabHighlights.click();
    } else {
      loadSavedHighlights();
    }

    // Re-render this page so the new highlight is drawn immediately.
    // Refresh the specific wrapper to fetch and render the new highlight
    renderPageIntoWrapper(pageNum, wrapper);

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

// Match navigation
els.btnPrevMatch.addEventListener('click', prevMatch);
els.btnNextMatch.addEventListener('click', nextMatch);

// Highlight color
els.highlightColor.addEventListener('input', (e) => changeHighlightColor(e.target.value));
document.querySelectorAll('.qg-color-swatch').forEach(swatch => {
  swatch.addEventListener('click', () => changeHighlightColor(swatch.dataset.color));
});

// Keyboard shortcuts. Ctrl or Cmd (metaKey, for macOS) is accepted for the first three.
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

// Re-render on window resize. Because page wrappers have fixed pixel sizes, this just
// scrolls back to the current page; it does not re-layout the PDF.
// Window resize: re-render highlights
window.addEventListener('resize', () => {
  if (state.pdfDoc && state.currentPage) {
    renderPage(state.currentPage);
  }
});


// ══════════════════════════════════════════════════
// Initialize
// ══════════════════════════════════════════════════

// Startup: populate the document list, and initialise the colour controls.
loadDocuments();
changeHighlightColor('#FFE066');
