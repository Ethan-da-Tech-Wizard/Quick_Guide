# QuickGuide (QG) — Problem Statement

**Version:** 1.0
**Date:** 2026-03-05

---

## The Problem

Professionals across construction, engineering, compliance, and education routinely work with **massive reference documents** — specifications, standards, codes, and manuals that can exceed 1,000 pages. When a field inspector needs a specific answer (e.g., *"What are the rules for how thick dirt should be compacted?"*), they face:

| Pain Point | Real-World Impact |
|---|---|
| **Manual search is slow** | Ctrl+F only matches exact keywords; natural-language questions yield nothing |
| **Information is buried** | A single answer may span multiple sections, tables, and footnotes |
| **Context switching** | Jumping between a search tool and the actual PDF page breaks focus |
| **No persistent highlights** | Users re-discover the same passages every time they open the document |
| **No multi-match navigation** | When answers span multiple locations, there's no way to jump between them |
| **Desktop-only tooling** | Most PDF tools don't work well on a phone in the field |

## Who It Affects

- **Construction inspectors** referencing compaction specs, rebar schedules, and material codes on-site
- **Design engineers** reviewing structural or mechanical standards during meetings
- **Students** navigating textbooks and study material for exam prep
- **Compliance auditors** searching lengthy regulatory documents across sections

## Why Existing Solutions Fall Short

| Solution | Limitation |
|---|---|
| **Adobe Acrobat / PDF readers** | Keyword-only search; no understanding of intent |
| **ChatGPT + PDF plugins** | Data leaves the device; requires internet; no direct in-PDF linking |
| **Full-text search databases** | Require developer setup; no end-user UI |
| **Custom RAG web apps** | Typically cloud-hosted; not local-first; no in-document highlighting |

## Desired Outcome

A **local-first, cross-platform application** that lets any user — with zero technical skill — do the following:

1. **Select** a PDF from their own file system and have it parsed, indexed, and stored permanently inside the app.
2. **Ask natural-language questions** via a simple prompt box and receive precise answers with page/section references.
3. **Click a link** that opens the PDF viewer and navigates directly to the relevant passage.
4. **See key phrases highlighted** in yellow by default, with the ability to change the highlight color at will.
5. **Jump between multiple highlighted sections** when the answer spans more than one location in the document.
6. **Work on any device** — Windows, macOS, Linux laptops, Android and iOS phones — entirely offline.

## Success Criteria

| Metric | Target |
|---|---|
| PDF ingestion (1,000 pages) | Searchable in ≤ 2 minutes on commodity hardware |
| Search accuracy | Correct passage in top-3 results ≥ 90% of the time |
| Click-to-highlight | One click from result → highlighted passage in the PDF viewer |
| Multi-match navigation | User can jump forward/backward between all highlighted matches |
| Offline operation | Zero cloud dependency for core features |
| Layman usability | A non-technical user can upload, search, and navigate without any instructions |
