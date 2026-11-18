// Program: Quick_Guide - app.js
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Browser-side logic for QuickGuide: loads documents, uploads PDFs, renders pages with PDF.js, runs searches, steps through matches and manages saved highlights.
/**
 * QuickGuide (QG) — Main Application JavaScript
 *
 * Handles: document management, search, PDF.js rendering,
 * multi-match navigation, and highlight color customization.
 */

// ── PDF.js Setup ────────────────────────────────
// Load the PDF.js library from a CDN. Top-level await works because this file is loaded as a module.
const pdfjsLib = await import('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs');
// PDF.js does heavy work in a background "worker" script; tell it where to find that file
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';

// ── State ───────────────────────────────────────
// Central place that remembers what the app is doing right now
const state = {
  // id of the open document (null when none)
  currentDocId: null,
  // the PDF.js document object for the open PDF
  pdfDoc: null,
  // page nearest the top of the viewer
  currentPage: 1,
  // number of pages in the open PDF
  totalPages: 0,
  // zoom factor used when drawing pages
  scale: 1.5,
  // results from the last search
  searchResults: [],
  matches: [],          // {page, rects: [{x0,y0,x1,y1}], text}
  // which match is selected (-1 = none)
  currentMatchIndex: -1,
  // color used to draw search-match highlights
  highlightColor: '#FFE066',
  // true while a search request is running (prevents double searches)
  isSearching: false,
  // true while an upload is running
  isUploading: false,
};

// ── DOM References ──────────────────────────────
// Shortcuts to the HTML elements we use, looked up once by their id
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
// The observer watches page boxes and tells us when one scrolls near the screen
// so we only draw pages that are needed (lazy rendering)
let pageObserver = null;
// Set of page numbers already drawn, to avoid drawing twice
const renderedPages = new Set();


// ══════════════════════════════════════════════════
// API Helpers
// ══════════════════════════════════════════════════

/**
 * Send a request to the server and return its JSON reply.
 * @param {string} method - HTTP verb such as 'GET', 'POST' or 'DELETE'.
 * @param {string} path - URL path, for example '/api/documents'.
 * @param {Object|FormData|null} body - Optional data to send.
 * @returns {Promise<any>} The parsed JSON response; throws an Error if the server reports a problem.
 */
async function api(method, path, body = null) {
  // Build the fetch options: method plus headers
  const opts = {
    method,
    headers: {},
  };
  // Plain objects are sent as JSON text
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  // File uploads (FormData) are sent as-is; the browser sets the headers
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  // Make the request and wait for the reply
  const res = await fetch(path, opts);
  // Status codes outside 200-299 mean an error; try to read the server's message
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

/**
 * Show a small pop-up message that disappears by itself after 4 seconds.
 * @param {string} message - Text to show.
 * @param {string} type - 'info', 'success' or 'error' (controls the color).
 */
function showToast(message, type = 'info') {
  // Create the toast element and add it to the page
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `qg-toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  // After 4 seconds fade it out, then remove it from the page 0.3 seconds later
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}


// ══════════════════════════════════════════════════
// Document Management
// ══════════════════════════════════════════════════

/**
 * Fetch the document list from the server and fill the dropdown.
 * Documents that are not 'ready' yet are shown but disabled.
 */
async function loadDocuments() {
  try {
    const docs = await api('GET', '/api/documents');
    // Reset the dropdown to just the placeholder option
    els.docSelect.innerHTML = '<option value="">— Select a document —</option>';
    // Add one <option> per document
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
    // (keeps the same document selected after the list is rebuilt)
    if (state.currentDocId) {
      els.docSelect.value = state.currentDocId;
    }
  } catch (e) {
    console.error('Failed to load documents:', e);
  }
}

/**
 * Upload a PDF to the server, show a progress pop-up, then open the new document.
 * @param {File} file - The PDF chosen by the user.
 */
async function uploadDocument(file) {
  state.isUploading = true;
  // Show the progress pop-up and set the starting bar width and message
  els.progressModal.style.display = 'flex';
  els.progressBar.style.width = '10%';
  els.progressMessage.textContent = 'Uploading PDF...';

  try {
    // FormData packages the file the way a web form would
    const formData = new FormData();
    formData.append('file', file);

    // Start upload
    els.progressBar.style.width = '30%';
    els.progressMessage.textContent = 'Processing & indexing... This may take a moment.';

    // Wait for the server to save, read and index the PDF (can take a while)
    const doc = await api('POST', '/api/documents/upload', formData);

    els.progressBar.style.width = '100%';
    els.progressMessage.textContent = 'Done! Your document is ready.';

    // After a short pause close the pop-up, select the new document and refresh the dropdown
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
  // Upload failed: hide the pop-up and tell the user why
    els.progressModal.style.display = 'none';
    showToast(`Upload failed: ${e.message}`, 'error');
  } finally {
  // Always runs, whether the upload worked or not
    state.isUploading = false;
  }
}

/**
 * Open a document in the viewer (or return to the welcome screen when none is chosen).
 * @param {string|number} docId - Id from the dropdown; empty means no document.
 */
async function selectDocument(docId) {
  // Nothing chosen: reset everything and show the welcome screen
  if (!docId) {
    state.currentDocId = null;
    state.pdfDoc = null;
    showPlaceholder();
    clearResults();
    els.btnDeleteDoc.style.display = 'none';
    return;
  }

  // Remember the chosen document and show the Delete button
  state.currentDocId = parseInt(docId);
  els.btnDeleteDoc.style.display = 'inline-flex';
  clearResults();

  try {
    // Load PDF with PDF.js
    // (the PDF file comes from the server's /pdf route)
    const url = `/api/documents/${docId}/pdf`;
    const loadingTask = pdfjsLib.getDocument(url);
    state.pdfDoc = await loadingTask.promise;
    state.totalPages = state.pdfDoc.numPages;
    state.currentPage = 1;

    // Swap the welcome screen for the PDF area and build empty page boxes
    hidePlaceholder();
    initScrollContainer();
  } catch (e) {
    showToast(`Failed to load PDF: ${e.message}`, 'error');
  }
}

/**
 * Ask for confirmation, then delete the open document on the server and reset the screen.
 */
async function deleteDocument() {
  if (!state.currentDocId) return;
  // confirm() shows a yes/no pop-up; stop if the user says no
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

/**
 * Create an empty, correctly sized box for every page of the open PDF.
 * The real drawing of each page happens later, only when it scrolls near the screen.
 */
async function initScrollContainer() {
  els.pdfContainer.innerHTML = '';
  renderedPages.clear();

  if (pageObserver) {
    pageObserver.disconnect();
  }

  // Calculate base dimensions
  // Use page 1 to estimate how big a page is (height divided by width = aspect ratio)
  const firstPage = await state.pdfDoc.getPage(1);
  const viewport = firstPage.getViewport({ scale: state.scale });
  const aspectRatio = viewport.height / viewport.width;

  // Fallback to viewport width if the container hasn't painted yet
  const containerWidth = els.pdfContainer.clientWidth;
  const safeWidth = containerWidth > 40 ? containerWidth - 40 : viewport.width;
  const wrapperWidth = Math.min(viewport.width, safeWidth);
  const estimatedHeight = wrapperWidth * Math.max(aspectRatio, 1.0);

  // Watch each page box; rootMargin makes the callback fire a little before the box is visible
  pageObserver = new IntersectionObserver(handleIntersection, {
    root: els.pdfContainer,
    rootMargin: '400px 0px 400px 0px', // Pre-render 400px outside viewport
    threshold: 0.01
  });

  // Create empty wrapper divs for all pages
  // One box (wrapper) per page, numbered from 1
  for (let i = 1; i <= state.totalPages; i++) {
    const wrapper = document.createElement('div');
    wrapper.className = 'qg-page-wrapper loading';
    wrapper.id = `page-wrapper-${i}`;
    wrapper.dataset.page = i;

    // Set estimated dimensions to reserve space
    wrapper.style.width = wrapperWidth + 'px';
    wrapper.style.height = estimatedHeight + 'px';

    // Add canvas and layers placeholders
    // Each box holds the page picture (canvas), an invisible text layer and a highlight layer
    wrapper.innerHTML = `
      <canvas class="qg-pdf-canvas"></canvas>
      <div class="qg-text-layer"></div>
      <div class="qg-highlight-layer"></div>
    `;

    // Put the box on the page and start watching it
    els.pdfContainer.appendChild(wrapper);
    pageObserver.observe(wrapper);
  }

  // Show the current page number now
  updatePageIndicatorContainer();

  // Also track which page is mostly in view to update the floating indicator
  els.pdfContainer.addEventListener('scroll', updatePageIndicatorContainer, { passive: true });
}

/**
 * Called by the IntersectionObserver when page boxes enter or leave view; draws pages that appeared.
 * @param {IntersectionObserverEntry[]} entries - The boxes whose visibility changed.
 */
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

/**
 * Draw one PDF page into its box: the picture, the selectable text layer, then highlights.
 * @param {number} pageNum - 1-based page number.
 * @param {HTMLElement} wrapper - The page box to draw into.
 */
async function renderPageIntoWrapper(pageNum, wrapper) {
  renderedPages.add(pageNum);

  // Ask PDF.js for this page and work out its size at the current zoom
  const page = await state.pdfDoc.getPage(pageNum);
  const viewport = page.getViewport({ scale: state.scale });

  // The canvas is the drawing surface for the page picture
  const canvas = wrapper.querySelector('.qg-pdf-canvas');
  const ctx = canvas.getContext('2d');

  // Use exact dimensions now that we have the specific page
  // Use exact dimensions now that we have the specific page (replaces the estimate)
  wrapper.style.width = viewport.width + 'px';
  wrapper.style.height = viewport.height + 'px';

  // Make the canvas as large as the page
  canvas.width = viewport.width;
  canvas.height = viewport.height;

  // Draw the page onto the canvas and wait until finished
  await page.render({ canvasContext: ctx, viewport }).promise;

  // Render invisible text layer for selection
  // The text layer sits on top so the user can select text with the mouse
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

  // Page is ready: remove the faded loading look
  wrapper.classList.remove('loading');

  // Draw highlights specific to this page
  drawHighlightsForPage(pageNum);
}

/**
 * Work out which page is nearest the top of the scroll area and update the floating 'Page X of Y' label.
 */
function updatePageIndicatorContainer() {
  if (!state.pdfDoc) return;
  els.floatingPageIndicator.style.display = 'block';

  // Find which wrapper is closest to the top of the container
  const containerTop = els.pdfContainer.scrollTop;
  // All page boxes, as an array so we can loop over them
  const wrappers = Array.from(els.pdfContainer.querySelectorAll('.qg-page-wrapper'));

  // Track the box whose top edge is closest to the scroll position
  let closestPage = 1;
  let minDiff = Infinity;

  wrappers.forEach(w => {
    const diff = Math.abs(w.offsetTop - containerTop);
    if (diff < minDiff) {
      minDiff = diff;
      closestPage = parseInt(w.dataset.page);
    }
  });

  // Save and display the result
  state.currentPage = closestPage;
  els.floatingPageIndicator.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
}

/**
 * Scroll the viewer to a page. (Despite the name it no longer draws; the observer draws pages.)
 * @param {number} pageNum - 1-based page number.
 */
async function renderPage(pageNum) {
  // Polyfill the old renderPage function for external compat
  const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
  if (wrapper) {
    wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/**
 * Show the welcome screen and hide the PDF area.
 */
function showPlaceholder() {
  els.viewerPlaceholder.style.display = 'flex';
  els.pdfContainer.style.display = 'none';
  if (els.floatingPageIndicator) els.floatingPageIndicator.style.display = 'none';
}

/**
 * Hide the welcome screen and show the PDF area.
 */
function hidePlaceholder() {
  els.viewerPlaceholder.style.display = 'none';
  els.pdfContainer.style.display = 'flex';
}


// ══════════════════════════════════════════════════
// Search
// ══════════════════════════════════════════════════

/**
 * Run a search for the text in the search box: validate, call the API, show results and match highlights.
 */
async function performSearch() {
  const query = els.searchInput.value.trim();
  // Need at least 3 characters (the server requires it too)
  if (!query || query.length < 3) {
    showToast('Please enter at least 3 characters', 'error');
    return;
  }

  // A document must be open first
  if (!state.currentDocId) {
    showToast('Please select a document first', 'error');
    return;
  }

  // Ignore clicks while a search is already running; show a spinner in the button
  if (state.isSearching) return;
  state.isSearching = true;
  els.btnSearch.innerHTML = '<span class="qg-spinner"></span>';

  try {
    // Ask the server for the best matching passages
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
  // Restore the button whatever happened
    state.isSearching = false;
    els.btnSearch.innerHTML = 'Search';
  }
}

/**
 * Fill the results list with one card per match.
 * @param {Array} results - Result objects from the server.
 * @param {string} query - The text that was searched (not used for drawing).
 */
function displayResults(results, query) {
  // No matches: show a friendly message and hide the toolbar
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

  // Build the cards as one HTML string, then insert it all at once
  let html = '';
  results.forEach((r, i) => {
    // Turn a 0-1 score into a whole-number percent
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

  // escapeHtml (used above) stops document text from being treated as HTML
  els.resultsContainer.innerHTML = html;

  // Attach click handlers
  // (clicking a card jumps to its match)
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.index);
      navigateToMatch(idx);
    });
  });
}

/**
 * Reset all search state, empty the results list and remove highlights from every page.
 */
function clearResults() {
  state.searchResults = [];
  state.matches = [];
  state.currentMatchIndex = -1;
  state.isSearching = false;

  // Reset the panel: empty list, show the empty-state message, hide the toolbar, clear the box
  els.resultsContainer.innerHTML = '';
  els.resultsContainer.style.display = 'none';
  els.emptyState.style.display = 'flex';
  els.highlightToolbar.style.display = 'none';
  els.searchInput.value = '';

  // Clear all page highlights
  // (empties each page's highlight layer)
  document.querySelectorAll('.qg-highlight-layer').forEach(layer => {
    layer.innerHTML = '';
  });

  // Re-draw saved highlights if needed
  // (saved highlights from the server are drawn again for every page)
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

/**
 * Turn search results into 'matches' with on-page rectangles so they can be highlighted and stepped through.
 * @param {Array} results - Search results from the server.
 * @param {string} query - The user's search text.
 */
async function buildMatches(results, query) {
  // Start with an empty match list
  state.matches = [];

  // Group results by page and get text positions
  // Group results by page number
  const pageGroups = {};
  results.forEach(r => {
    if (!pageGroups[r.page_number]) {
      pageGroups[r.page_number] = [];
    }
    pageGroups[r.page_number].push(r);
  });

  // Extract key phrases from the query for highlighting
  // (queryWords is computed here but is not used later in this function)
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);

  // Visit each page that has results
  for (const [pageStr, pageResults] of Object.entries(pageGroups)) {
    const page = parseInt(pageStr);

    // Try to get text positions for the user's query directly
    for (const result of pageResults) {
      try {
        // Ask the server where the query text sits on this page (rectangles as page fractions)
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

/**
 * Select a match: mark its result card as active, scroll to its page and redraw highlights.
 * @param {number} index - Position in state.matches.
 */
async function navigateToMatch(index) {
  // Ignore numbers outside the match list
  if (index < 0 || index >= state.matches.length) return;

  state.currentMatchIndex = index;
  const match = state.matches[index];

  // (remove 'active' from all cards, then add it to the one for this match)
  // Highlight active result card
  els.resultsContainer.querySelectorAll('.qg-result-card').forEach(c => c.classList.remove('active'));
  const activeCard = els.resultsContainer.querySelector(`[data-index="${match.resultIndex}"]`);
  if (activeCard) {
    activeCard.classList.add('active');
    activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // (scroll to the page if it is not the current one; otherwise just redraw its highlights)
  // Navigate to the page
  if (state.currentPage !== match.page) {
    await renderPage(match.page);
  } else {
    drawHighlightsForPage(match.page);
  }

  updateMatchCounter();
}

/**
 * Draw all highlight boxes on one page: search matches first, then saved user highlights fetched from the server.
 * @param {number} pageNum - 1-based page number.
 */
async function drawHighlightsForPage(pageNum) {
  // Find this page's box and its highlight layer; stop if either is missing
  const wrapper = document.getElementById(`page-wrapper-${pageNum}`);
  if (!wrapper) return;
  const highlightLayer = wrapper.querySelector('.qg-highlight-layer');
  if (!highlightLayer) return;

  // Clear old boxes before drawing again
  highlightLayer.innerHTML = '';

  // Matches that belong to this page
  const pageMatches = state.matches.filter(m => m.page === pageNum);
  const color = state.highlightColor;

  // Draw each match; the active one is drawn stronger
  pageMatches.forEach((match, i) => {
    const isActive = state.matches.indexOf(match) === state.currentMatchIndex;

    // Precise rectangles: one box per rectangle, positioned as percentages of the page size
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

        // (after a short delay, scroll so the active box is visible)
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
    } else if (isActive) {
    // No precise rects
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

  // (these come from the database via the highlights API)
  // Draw saved custom highlights
  if (!state.currentDocId) return;
  try {
    const highlights = await api('GET', `/api/documents/${state.currentDocId}/highlights?page=${pageNum}`);
    // Loop over the saved highlights returned for this page
    for (const h of highlights) {
      if (h.page_number !== pageNum) continue;

      try {
        // (a saved highlight stores text, so its position is looked up again each time)
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

/**
 * Update the 'Match X of Y' label.
 */
function updateMatchCounter() {
  els.matchCounter.textContent = state.matches.length > 0
    ? `Match ${state.currentMatchIndex + 1} of ${state.matches.length}`
    : 'No matches';
}

/**
 * Go to the next match, wrapping from the last back to the first.
 */
function nextMatch() {
  if (state.matches.length === 0) return;
  // The % (remainder) operator makes the index wrap around
  const next = (state.currentMatchIndex + 1) % state.matches.length;
  navigateToMatch(next);
}

/**
 * Go to the previous match, wrapping from the first to the last.
 */
function prevMatch() {
  if (state.matches.length === 0) return;
  const prev = (state.currentMatchIndex - 1 + state.matches.length) % state.matches.length;
  navigateToMatch(prev);
}


// ══════════════════════════════════════════════════
// Highlight Color Management
// ══════════════════════════════════════════════════

/**
 * Set the search-highlight color, update the picker and swatches, and redraw the current page.
 * @param {string} color - Color as a hex string such as '#FFE066'.
 */
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

/**
 * Make text safe to insert into HTML by turning special characters like < and & into harmless text.
 * @param {string} text - Raw text.
 * @returns {string} Escaped text.
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Convert a hex color to an rgba() string so transparency can be added.
 * @param {string} hex - Color like '#FFE066'.
 * @param {number} alpha - Opacity from 0 (invisible) to 1 (solid).
 * @returns {string} CSS color text.
 */
function hexToRgba(hex, alpha) {
  // Read the red, green and blue pairs of hex digits and convert them to numbers 0-255
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


// ══════════════════════════════════════════════════
// Tabs UI
// ══════════════════════════════════════════════════

// Clicking a tab shows its matching content area and hides the others
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

/**
 * Fetch all saved highlights for the open document and list them in the My Highlights tab.
 */
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

    // Build one card per highlight; the colored left border shows the highlight color
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

    // (clicking a card scrolls to its page)
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

    // (the small X button deletes after a confirmation; stopPropagation keeps the card click from firing too)
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

// (when the mouse is released over a page, any selected text can be saved as a highlight)
// Intercept mouse drag selections on the canvas to create custom highlights
els.pdfContainer.addEventListener('mouseup', async (e) => {
  if (!state.currentDocId) return;

  // Find which page box the mouse was released in; ignore releases elsewhere
  const wrapper = e.target.closest('.qg-page-wrapper');
  if (!wrapper) return;
  const pageNum = parseInt(wrapper.dataset.page);

  // The text the user has selected; ignore tiny selections
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text || text.length < 3) return;

  // (confirm() pop-up; cancelling clears the selection)
  // Ask for confirmation
  if (!confirm(`Save highlight for:\\n"${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"?`)) {
    selection.removeAllRanges();
    return;
  }

  try {
    // Save the highlight to the server (color is a fixed light blue)
    await api('POST', '/api/highlights', {
      document_id: state.currentDocId,
      page_number: pageNum,
      text_content: text,
      color: '#ADD8E6' // Custom Light Blue
    });

    showToast('Highlight saved!', 'success');
    selection.removeAllRanges();

    // (show the new highlight in the list)
    // Switch to Highlights tab if not already on it to show the new highlight
    const tabHighlights = document.querySelector('.qg-tab[data-target="highlights-view"]');
    if (tabHighlights && !tabHighlights.classList.contains('active')) {
      tabHighlights.click();
    } else {
      loadSavedHighlights();
    }

    // (redraw the page so the new highlight appears)
    // Refresh the specific wrapper to fetch and render the new highlight
    renderPageIntoWrapper(pageNum, wrapper);

  } catch (e) {
    showToast(`Highlight failed: ${e.message}`, 'error');
  }
});


// ══════════════════════════════════════════════════
// Event Listeners
// ══════════════════════════════════════════════════

// (the 'change' event fires when the user picks a different option)
// Document selection
els.docSelect.addEventListener('change', (e) => selectDocument(e.target.value));

// Upload
els.btnUpload.addEventListener('click', () => els.fileInput.click());
// When a file is chosen, upload it, then clear the input so the same file can be picked again
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

// (document-wide shortcuts: Ctrl or Cmd with K, left and right arrows, plus Escape)
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

// Start-up: fill the dropdown and set the default highlight color
loadDocuments();
changeHighlightColor('#FFE066');
