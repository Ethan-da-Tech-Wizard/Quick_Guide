# QuickGuide (QG) — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2026-03-05

---

## 1 Product Vision

> *Select a PDF. Ask a question. Get taken straight to the answer — highlighted and ready to read.*

QuickGuide transforms large, static PDFs into **searchable knowledge bases** that live entirely on the user's own device. A cozy, layman-friendly interface replaces page-flipping with natural-language search, one-click navigation, and persistent color-coded highlighting.

## 2 Target Personas

| Persona | Context | Key Need |
|---|---|---|
| **Field Inspector** | On-site with a phone, limited connectivity | Quick offline answers from a 1,000-page spec |
| **Design Engineer** | At a workstation reviewing standards | Semantic search + highlighted evidence |
| **Student** | Laptop or tablet, studying a textbook | Ask questions, see highlighted answers in context |
| **Compliance Auditor** | Reviewing regulatory docs across OSes | Cross-platform consistency, persistent highlights |

## 3 User Stories

### US-01 — Select & Ingest a PDF
> *As a user, I want to select a PDF from my file system so the app indexes it for future queries.*

**Acceptance Criteria:**
- The main screen has a clear **"Select a Document"** button.
- User picks a PDF from their local file system; the app copies it to its managed storage location.
- Accept PDFs up to 2,000 pages / 200 MB.
- A progress indicator shows ingestion status (extracting → embedding → complete).
- The PDF is stored permanently until the user explicitly removes it.

### US-02 — Ask a Natural-Language Question
> *As a user, I want to type a question in plain English and get relevant passages.*

**Acceptance Criteria:**
- A prompt box is always visible on the main screen.
- Results appear within 3 seconds for a 1,000-page document.
- Each result shows: page number, FULL scrollable text snippet, and a relevance badge.
- If no document is selected, a friendly message tells the user to select one first.

### US-03 — Navigate to the Answer
> *As a user, I want to click a result and be taken directly to the passage in the PDF viewer.*

**Acceptance Criteria:**
- One click scrolls the embedded PDF.js viewer to the exact page and passage.
- The matching phrase(s) are auto-highlighted in the viewer.
- The viewer opens on the correct page — no manual scrolling needed.

### US-04 — Highlight with Customizable Colors
> *As a user, I want found phrases highlighted in yellow by default, with the option to change the color.*

**Acceptance Criteria:**
- Default highlight color is **yellow (#FFE066)**.
- A color picker in the toolbar lets the user change the highlight color at any time.
- Each individual highlight can have its own color.
- Highlights persist across sessions (saved locally).

### US-05 — Jump Between Multiple Matches
> *As a user, when my query matches multiple locations, I want to jump between them easily.*

**Acceptance Criteria:**
- A navigation toolbar shows "Match 1 of N" with ◀ / ▶ arrows.
- Clicking ▶ jumps to the next highlighted section, scrolling the PDF automatically.
- All matched sections are highlighted and numbered.

### US-06 — Cross-Platform Access
> *As a user, I want the same experience on my phone, laptop, and desktop.*

**Acceptance Criteria:**
- Runs on Windows, macOS, Linux, Android, and iOS.
- Responsive layout adapts: side-by-side on desktop, stacked on mobile.
- Launched via a clickable **QG logo** on desktop.

### US-07 — Manage Document Library
> *As a user, I want to manage a library of uploaded PDFs.*

**Acceptance Criteria:**
- List all uploaded documents with name, page count, and upload date.
- Select any document to make it the active search target.
- Delete a document to reclaim storage.

### US-08 — Custom Mouse-Drag Highlighting & Dashboard
> *As a user, I want to drag my mouse to highlight any text I find interesting completely independently from my searches, and keep track of them in a single view.*

**Acceptance Criteria:**
- User can highlight text by selecting it with their mouse (defaults to Light Blue).
- A separate "My Highlights" tab in the UI sidebar displays a list of all manually saved highlights.
- Clicking on a saved highlight instantly navigates the PDF to that exact page.
- User can delete custom highlights from the dashboard.

## 4 Feature Priority (MoSCoW)

| Priority | Feature |
|---|---|
| **Must Have** | PDF selection & ingestion, semantic search, result → page navigation, phrase highlighting (yellow default), multi-match jumping, local storage |
| **Should Have** | Color customization, multi-document library, progress indicators, QG desktop launcher |
| **Could Have** | Annotation export, search history, dark mode toggle |
| **Won't Have (v1)** | Cloud sync, multi-user auth, OCR for scanned PDFs, internet-connected LLM |

## 5 UX Principles

1. **Cozy & inviting** — warm colors, rounded corners, soft shadows. The UI should feel like a comfortable reading nook, not a technical tool.
2. **One-action access** — from query to highlighted passage in ≤ 2 clicks.
3. **Layman-friendly** — no jargon, clear labels, obvious buttons. A first-time user completes a search without any documentation.
4. **Minimal chrome** — the PDF viewer is the hero; controls stay out of the way.
5. **Offline-first** — every feature works without a network connection (after initial setup).
6. **Responsive** — phone and desktop share the same codebase and design language.

## 6 Non-Functional Requirements (Summary)

| Attribute | Target |
|---|---|
| Ingestion speed | ≤ 2 min for 1,000 pages |
| Query latency | ≤ 3 s |
| Max PDF size | 200 MB / 2,000 pages |
| Storage footprint | ≤ 2× original PDF size (text + embeddings) |
| Privacy | Zero network calls for core features |
| Launchability | Double-click QG logo starts the app and opens the browser |
