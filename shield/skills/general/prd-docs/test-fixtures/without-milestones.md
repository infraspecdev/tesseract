# Document Export to PDF

## 1. Header
| Field | Value |
|---|---|
| Owner | @ben.product |
| Status | Draft |
| PRD type | Standard |
| Date created | 2026-04-01 |
| Last updated | 2026-04-15 |
| Linked design spec | null |
| Linked research | null |
| Decision-maker | @product-lead |
| Sign-off contacts | Legal: @legal, Security: @sec-review, Support: @cx-lead |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Terminologies
| Term | Definition |
|---|---|
| WeasyPrint | An open-source Python library that converts HTML/CSS to PDF using the CSS Paged Media specification. |
| Headless Chromium | A Chrome browser instance run without a GUI, used here to render documents to PDF. |
| Pre-signed URL | A time-limited S3 URL that grants temporary read access without requiring AWS credentials. |
| Confidentiality footer | A legal notice printed on every page of an exported PDF identifying the document as proprietary. |

## 3. Problem & context
Enterprise users need to share workspace documents with external stakeholders (lawyers, auditors, board members) who cannot access the platform. Today they manually copy content into Google Docs or Word and reformat it — a process that takes 30–60 minutes per document and introduces errors. We lose ~15 enterprise expansion deals/quarter where auditors cite the lack of export as a blocker.

## 4. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | Marco — compliance manager | Export audit-ready documents in a standard format | Must manually reformat in Word; formatting never matches the platform |
| P2 | Sofia — executive assistant | Prepare polished PDF reports for board packages | Copy-paste loses tables; charts don't export cleanly |

## 5. Architecture & flows

_No notable architecture; flows described in stories._

## 6. Goals & non-goals
### Goals
1. Allow any authenticated user to export a workspace document as a PDF with a single click.
2. Preserve tables, inline code blocks, and images in the output.
3. Complete the export within 10 seconds for documents up to 100 pages.

### Non-goals
- Export to Word / ODT — separate workstream.
- Scheduled or recurring exports.
- PDF editing or annotation inside the platform.

## 7. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| PDF exports / week | Leading | ≥ 500 within 8 weeks of GA | — |
| Export success rate | Leading | ≥ 99% of initiated exports complete successfully | Export failure rate |
| Enterprise deal mentions | Lagging | Zero lost deals citing "no export" within 1 quarter | — |

**Dashboard plan:** Mixpanel funnel `document_export_pdf` — initiated, completed, failed.

## 8. User stories & scenarios

### Story US-1: Export a document to PDF
- **Type:** new
- **Existing behavior:** N/A
- **Persona:** P1
- **Goal:** Download a PDF that looks identical to the on-screen document.
- **Happy path:**
  1. P1 opens a document.
  2. P1 clicks "Export" → "Download as PDF".
  3. Backend generates PDF; download starts within 10 s.
  4. P1 opens PDF — all tables, images, and code blocks rendered correctly.
- **Error / timeout / abandon paths:** Generation fails → toast error with retry button; generation takes > 15 s → timeout toast.
- **Edge cases:** Document with 200+ pages — enforce 100-page limit with user-facing message.
- **State transitions:** none.
- **Cross-functional handoffs:** Legal review of PDF header (confidentiality notice).
- **Acceptance criteria (Given/When/Then):**
  - Given an authenticated user viewing a document, When they click "Download as PDF", Then a PDF is downloaded within 10 s.
  - Given a document exceeding 100 pages, When export is requested, Then the user receives an error message explaining the limit.

### Story US-2: PDF includes a confidentiality footer
- **Type:** new
- **Existing behavior:** N/A
- **Persona:** P1
- **Goal:** Ensure exported PDFs include a legal notice for compliance purposes.
- **Happy path:** P1 exports; every PDF page includes a footer "Confidential — {workspace name} — {export date}".
- **Error / timeout / abandon paths:** Footer missing → treat as export failure.
- **Edge cases:** Workspace name contains special characters — must be sanitised.
- **State transitions:** none.
- **Cross-functional handoffs:** Legal to approve footer text.
- **Acceptance criteria (Given/When/Then):**
  - Given any exported PDF, Then every page contains the footer "Confidential — {workspace name} — {export date}".

## 9. Functional requirements
- FR-1 (US-1): `POST /v1/documents/{id}/export/pdf` initiates PDF generation; returns a pre-signed S3 URL on completion.
- FR-2 (US-1): Generation timeout is 15 s; returns 504 if exceeded.
- FR-3 (US-1): Documents > 100 pages are rejected with 422 and an error message.
- FR-4 (US-2): Every page of the PDF includes the confidentiality footer.

## 10. Non-functional requirements
| NFR | Requirement |
|---|---|
| Performance | PDF generation p99 < 10 s for documents ≤ 50 pages |
| Security | Pre-signed S3 URL expires after 5 minutes; no unauthenticated export |
| Accessibility | N/A for PDF output; export trigger button meets WCAG 2.1 AA |
| Privacy | PDFs stored in S3 for 24 h then auto-deleted; no PII in logs |
| Telemetry / event taxonomy | `document.export.initiated`, `document.export.completed`, `document.export.failed` |
| i18n / l10n | N/A — PDF uses en-only footer text for now |

## 11. RBAC & permissions matrix
| Role | Can do |
|---|---|
| Authenticated member | Export any document they have read access to |
| Guest (view-only) | Cannot export |
| Admin | Can export any document in the workspace |

## 12. Dependencies
- **PDF rendering library** — WeasyPrint or headless Chromium; spike needed.
- **S3 bucket** — existing `export-artifacts` bucket; need lifecycle rule for 24-h deletion.
- **Transactional email** — no dependency (no email for this feature).

## 13. Risks & mitigations
| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | PDF renderer handles complex tables poorly | M | H | Spike with 5 representative documents; switch renderer if failure rate > 5% | @eng-lead |
| R2 | S3 storage costs spike if exports are large | L | M | Monitor p99 PDF size; enforce 50 MB cap per export | @infra |

## 14. Assumptions
| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | WeasyPrint or headless Chromium can render all document element types correctly | Unvalidated | Evaluate commercial PDF API (DocRaptor) as fallback |
| A2 | 100-page limit covers > 95% of enterprise documents | Unvalidated | Raise limit to 200 pages if enterprise feedback indicates need |

## 15. Rollout plan
- Flag plan: `pdf_export_v1` feature flag
- Canary: 5% → 25% → 100% over 1 week
- Kill-switch: revert flag
- Abort thresholds: export failure rate > 5%
- Data migration: none
- Backward compatibility: not applicable (new feature)

## 16. Cost & resource impact
| Component | Cost dimension | Estimate |
|---|---|---|
| Build cost | Engineering time | 2 engineers × 3 weeks |
| Run cost | S3 storage (24-h TTL) + compute | < $200/month at 500 exports/week |
| Counter-metric | Cost per export | Should not exceed $0.05 per export |

## 17. GTM & customer-comms
- Pricing / packaging implications: export included in Pro and Enterprise tiers.
- In-app messaging plan: tooltip on "Export" button on GA day.
- Release notes: changelog entry with screenshot of PDF output.
- CS / sales enablement: one-pager for AEs to use with blocked enterprise deals.
- Beta / early-access plan: 5 enterprise design partners in beta for 2 weeks.

## 18. Support / CX impact
- Day-1 ticket owner: @cx-lead
- Runbook: `docs/runbooks/pdf-export.md` — covers failure spikes, S3 access issues.
- Escalation path: CX → @eng-on-call → @ben.product.
- Sales enablement: AE one-pager attached to Notion deal-blocker tracker.
- Training plan: CX briefed via Loom before GA.

## 19. Open questions
| # | Question | Owner | Target resolution |
|---|---|---|---|
| OQ-1 | WeasyPrint vs. headless Chromium? | @eng-lead | 2026-04-20 (spike) |
| OQ-2 | Should guests be able to export with a watermark? | @product-lead | 2026-04-25 |

## 20. Out of scope / Non-goals
- Export to Word / ODT / HTML.
- Scheduled or recurring exports.
- PDF annotation or editing inside the platform.
- Bulk export of multiple documents.
