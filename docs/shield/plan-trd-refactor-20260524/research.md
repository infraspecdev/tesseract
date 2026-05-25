# HLD/LLD Best Practices — Refactor /shield plan to Produce a TRD

**Status:** Proposed
**Date:** 2026-05-24
**Context:** Shield's `/plan` produces a stories-first work-breakdown plus a `plan-architecture.md` companion. Industry convention is HLD → LLD; Shield is missing the high-level-design layer that justifies the work-breakdown. This research informs a refactor where `/plan` will emit a **TRD = HLD + PM-lens milestones**, with a separate **LLD** authored later per milestone, and **stories that reference both HLD and LLD sections**.

## Decision

`/plan` should emit a **TRD** that combines (a) a high-level design grounded in IEEE 1016 / Sommerville / Pressman section coverage, (b) PM-lens milestones derived from the HLD, (c) a Rollback Strategy section preserving the strongest property of today's `plan-architecture.md`, and (d) a story breakdown where each story has an additive `design_refs` array pointing to TRD and LLD sections. The TRD **replaces** today's `plan-architecture.md` (direct cutover, no feature flag, no side-by-side period).

**The TRD applies to both backend and infrastructure work** — same 14-section template, same anchor IDs, same eval, same `/plan-review` rubric. A few sections (Product Journey, Functional Requirements, APIs Involved) have domain-aware interpretation in the `/plan` prompt; pure-state changes can declare `n/a — <reason>` per section as the explicit escape (a pattern borrowed from the LLD sample's §12). Two genuinely-infra-favored properties of today's ADR-flavored `plan-architecture.md` are preserved in the unified template:
- **§8 Alternatives Considered** — where the "5 numbered decisions with trade-offs" pattern lives (VPC peering vs Transit Gateway, Aurora vs RDS, single vs multi-region).
- **§14 Rollback Strategy** — promoted to a first-class 14th section (terraform destroy plans, state recovery, blue/green flip back, traffic shift reversal for infra; data rollback, feature-flag toggle, key rotation, schema reversal for backend).

**LLDs are component-scoped, not milestone-scoped.** Each LLD document covers one C4-style Container or Component (a service, library, or module). A single LLD can be referenced by multiple milestones — milestone M1 and milestone M2 may both touch `lld-component-auth.md`, each updating different sections. The TRD §10 (Milestones) lists *which* LLDs each milestone touches; the LLDs themselves grow incrementally as milestones land. **LLDs are typically authored for backend components** where pre-implementation design has measurable value; infra plans rarely need an LLD layer since the declarative terraform/k8s code is the spec.

The recommended TRD template, reconciled across the reference TRD template and the industry consensus core, is:

1. **Document Overview** — title, status, authors, related PRD link, date
2. **Problem Statement** — what user/business/operational problem (links PRD; doesn't restate it)
3. **Objective & Scope** — goals, non-goals (Google design-doc convention)
4. **Product Journey** — end-to-end user flow (backend) / request lifecycle through the infra or operator journey (infra). `n/a — <reason>` permitted for pure-state changes.
5. **Functional Requirements** — what users can do (backend) / what the infra must support — capacity, regions, accounts, traffic patterns (infra). Links PRD where possible.
6. **Non-Functional Requirements** — SLAs, perf, security, observability (backend) / SLOs, RPO/RTO, cost ceiling, blast radius, multi-AZ tolerance (infra). Uber RFC convention.
7. **High-Level Design** — services + data flow (backend) / network topology + resource graph + dependency chain (infra). Block/sequence/architecture diagrams.
8. **Alternatives Considered** — what we didn't pick and why. **For infra plans, this is where the ADR-style "5 numbered decisions with trade-offs" pattern lives** — VPC peering vs Transit Gateway, Aurora vs RDS, single vs multi-region. Google + Larson convention.
9. **Cross-Cutting Concerns** — security, privacy, observability, multi-tenancy (backend) / IAM, encryption, observability, cost, multi-region, disaster recovery, compliance-region constraints (infra). Google + Uber.
10. **Milestones** — PM-lens phased breakdown derived from the HLD (backend) / phased rollout — dev → stage → prod, canary regions, blue/green flip, percentage cutover (infra). Reference TRD precedent.
11. **APIs Involved** — HTTP contracts touched (backend) / module interfaces + cloud-API surface + IAM boundaries + output values consumed by downstream stacks (infra).
12. **Open Questions** — known unknowns; surfaced for follow-up
13. **References** — links to PRD, LLDs (forward links, populated as LLDs land), ADRs, runbooks
14. **Rollback Strategy** — data rollback, feature-flag toggle, key rotation, schema reversal (backend) / terraform destroy plan, state recovery, blue/green flip back, traffic shift reversal (infra). Promoted from today's `plan-architecture.md` Rollback section.

Each milestone in §10 declares which LLDs it touches. The LLDs are authored separately (a future `/lld <component>` command) and follow the C4 model's Container/Component levels — one LLD per service, library, or module. Stories in `plan.json` get an optional `design_refs[]` field with `{doc, section_id, anchor_url, label}` — additive, backward-compatible with `/pm-sync`.

**`n/a — <reason>` escape per section.** Following the LLD sample's §12 pattern, any of the 14 sections may declare `n/a — <reason>` when the section genuinely doesn't apply (e.g., §4 Product Journey on a pure-state infra change). Vague TBDs and silent omissions are not allowed — the eval rejects them — but an explicit "n/a" with rationale passes. This keeps the structure intact across domains without forcing pretend-content.

### Canonical LLD template (14 sections — from sample PR #43)

The LLD template is anchored in [tesseract PR #43](https://github.com/infraspecdev/tesseract/pull/43) — `docs/superpowers/specs/2026-05-18-lld-sample.html` — a Bytebite user-signup sample that establishes the LLD shape Shield should generate:

| # | Section | Always-on? | Notes |
|---|---|---|---|
| 1 | Overview | Yes | Names which epics/PRD milestones this LLD serves — bidirectional with TRD §10 |
| 2 | Scope & non-goals | Yes | In-scope/out-of-scope lists |
| 3 | Module layout | Yes | File tree with `new`/`mod`/`unchanged` badges |
| 4 | Data model | Yes | Tables + Redis/cache namespaces with column-level detail |
| 5 | API contracts | Yes | Per-endpoint request/response (each endpoint gets its own sub-anchor, e.g., `#api-create-user`) |
| 6 | Sequence flows | Yes | Mermaid sequence diagrams (each flow gets its own sub-anchor, e.g., `#flow-signup`) |
| 7 | Error handling | Yes | Error codes + behavior matrix |
| 8 | Concurrency & state | Yes | Named race conditions and resolutions |
| 9 | **Configuration** | **Promote-on-demand** | Config values; lifted when the component needs them |
| 10 | Observability | Yes | Logs, metrics, traces |
| 11 | **Security & privacy** | **Promote-on-demand** | Auth, PII, threats; lifted when the component touches user data |
| 12 | Performance & scaling | Yes — **8 forced subsections** | 12.1 Load · 12.2 SLO · 12.3 Bottleneck · 12.4 Latency breakdown · 12.5 Capacity · 12.6 Scale-out lever · 12.7 Caches · 12.8 Degradation. *"n/a — <reason>"* is the only escape; vague prose is not allowed. |
| 13 | Open questions | Yes | Q#, question, options, owner, resolve-by table |
| 14 | Changelog | Yes | Every edit ties to a story ID + sections touched — closes the loop with `plan.json` `design_refs[]` |

**Header metadata** (above §1): Feature · Owner · Status · Linked PRD · Linked plans (plural — one LLD, many plans) · Version · Last updated.

**Why this shape works for Shield:**
- **Per-component scope** with `Linked plans` plural matches the user's "same LLD doc covered across multiple milestones" intent.
- **Stable kebab-case anchors** on every section AND subsection — directly addresses Confluence-style anchor-rot the research surfaced.
- **§12's 8 forced subsections** are the strongest anti-format-drift mechanism in the template: a fixture-based eval can mechanically check that all 8 are present and non-empty, with `"n/a — <reason>"` as the only allowed escape.
- **§14 Changelog with story IDs** is the inverse of `design_refs[]` on the story side — the LLD knows which stories touched it; the story knows which LLD sections it depends on. Bidirectional graph.
- **§9 + §11 promote-on-demand** acknowledges that not every component touches config or user data — keeps the template scoped to reality without losing the slot.

## Why Not Keep `plan-architecture.md`?

| | Today's `plan-architecture.md` | Proposed unified TRD |
|---|---|---|
| Domain coverage | De-facto infra/ADR-flavored | **Both infra and backend** — same template, domain-aware prompting per section |
| Origin | Shield convention; closer to ADR + HLD hybrid | IEEE 1016 + reference TRD template + Google design-doc lineage |
| HLD coverage | Solution sketch + 5 numbered decisions + PR sequencing | Full HLD viewpoint coverage: context, composition, interfaces, NFRs |
| NFRs | Implicit | Explicit §6 (forced for both domains — SLOs/RPO/RTO/cost matter for infra too) |
| Alternatives | Present (good) | Preserved in §8 — the ADR-style "decisions with trade-offs" pattern lives here |
| Rollback strategy | Present in plan-architecture.md | **Promoted to first-class §14** (universal) |
| Milestones | "Deliverables" as PR sequencing | First-class §10 — feature phases (backend) or phased rollout (infra) |
| Cross-cutting | Implicit | Explicit §9 — forces IAM/cost/observability/DR for infra |
| Story traceability | None (LLD-shaped content buried in `plan.json` descriptions) | Each story gets `design_refs[]` pointing to TRD/LLD sections |
| Reviewer rubric | Free-form | Structured — `/plan-review` grades 14 fixed sections (with `n/a — <reason>` escape) |

The unified TRD subsumes everything `plan-architecture.md` does well (decisions, alternatives, rollback) and adds the structural rigor that infra plans currently lack (forced NFRs, Cross-Cutting, first-class Milestones).

## What the Industry Recommends

### IEEE 1016-2009 — Software Design Descriptions
> *"A representation of a software design to be used for communicating design information to its stakeholders."*
>
> *"Design view: A representation comprised of one or more design elements to address a set of design concerns from a specified design viewpoint."*
> — [IEEE Std 1016-2009, Clause 3 — full PDF via Çankaya University](https://cengproject.cankaya.edu.tr/wp-content/uploads/sites/10/2017/12/SDD-ieee-1016-2009.pdf)

IEEE 1016 names 12 design viewpoints (Context, Composition, Logical, Dependency, Information, Patterns-use, Interface, Structure, Interaction, State dynamics, Algorithm, Resource). A defensible HLD-vs-LLD split treats the first ~7 (Context → Interface) as HLD and the last ~5 (Structure → Resource) as LLD. The proposed TRD §7 (HLD) covers Context + Composition + Logical + Interface viewpoints; §11 (APIs Involved) covers Interface explicitly. LLD covers Structure + State + Algorithm + Resource.

### Ian Sommerville, *Software Engineering* (10th ed., Ch. 6)
> *"Architectural design is concerned with understanding how a software system should be organized and designing the overall structure of that system."*
>
> *"Architectural design is the critical link between design and requirements engineering as it identifies the main structural components in a system and the relationships between them."*
>
> *"Architecture may be used as a focus of discussion by system stakeholders. … Analysis of whether the system can meet its non-functional requirements is possible. … The architecture may be reusable across a range of systems."*
> — Sommerville, Chapter 6 §6.1

Sommerville's three justifications for explicit architecture — stakeholder communication, NFR analysis, reuse — map directly to TRD §4 (Product Journey, stakeholder communication), §6 (NFRs explicit), §7 (HLD as reusable architectural template).

### Roger Pressman, *Software Engineering: A Practitioner's Approach* (8th ed.)
Pressman organizes design into four layers:
> *"Architectural design defines the relationship between major structural elements of the software, the architectural styles and design patterns that can be used to achieve the requirements defined for the system."*
>
> *"Component-level design transforms structural elements of the software architecture into procedural description of software components."*

Pressman's split — architectural + data + interface (HLD) vs. component-level (LLD) — is the cleanest textbook mapping for the TRD/LLD layering.

### Malte Ubl — "Design Docs at Google"
> *"The design doc is the place to write down the trade-offs you made in designing your software."*
>
> *"A short list of bullet points of what the goals of the system are, and, sometimes more importantly, what non-goals are."*
>
> *"This is where your organization can ensure that certain cross-cutting concerns such as security, privacy, and observability are always taken into consideration."*
>
> *"A clear indicator that a doc might not be necessary are design docs that are really implementation manuals. If a doc basically says 'This is how we are going to implement it' without going into trade-offs, alternatives, and explaining decision making … then it would probably have been a better idea to write the actual program right away."*
> — [Design Docs at Google, industrialempathy.com](https://www.industrialempathy.com/posts/design-docs-at-google/)

Google's template — Context · Goals/Non-goals · The design · Alternatives · Cross-cutting concerns — is the empirical template Shield's existing `plan-architecture.html` already resembles. Adopting it explicitly closes the gap.

### Will Larson — `lethain.com`
> *"Design documents describe the decisions and tradeoffs you've made in specific projects."*
>
> *"A batch of five design docs is the ideal ingredient for writing an effective strategy because design documents have what bad strategies lack: detailed specifics grounded in reality."*
>
> *"You should write a design document for any project whose capabilities will be used by numerous future projects … any work taking more than a month of engineering time."*
>
> *"Gather perspectives widely but write alone."*
> — [Writing an engineering strategy, lethain.com](https://lethain.com/eng-strategies/)

Larson's "design-doc-as-decision-artifact" framing reinforces that the TRD should privilege decisions and trade-offs over comprehensive specification. The "write alone" rule is implementation guidance for the `/plan` agent: produce a single, opinionated TRD per run, not a consensus-shaped one.

### Gergely Orosz — The Pragmatic Engineer
> *"Software engineers who write design docs for their architecture — and ask for reviews on it — often ship more maintainable architecture."*
>
> On Uber's RFC scale problems at >2,000 engineers: *"Noise: Hundreds of RFCs weekly overwhelmed experienced engineers; Ambiguity: Unclear which work required documentation; Discoverability: Documents scattered across Google Drive."*
> — [RFCs and Design Docs, blog.pragmaticengineer.com](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)

Orosz's account of design-doc value at scale supports adopting a uniform template for Shield's TRD output. Shield's `/plan` audience is one team per run, so the Uber-scale "tiered templates" remediation doesn't apply — a single 14-section template is the right level of structure.

### Simon Brown — The C4 model
> *"Container" — a separately runnable/deployable unit (e.g., a server-side web application, a single-page application, a desktop application, a mobile app, a database schema, a file system) that executes code or stores data.*
>
> *"Component" — a grouping of related functionality encapsulated behind a well-defined interface. From an implementation perspective, components are typically a collection of implementation classes/objects."*
> — [The C4 model for visualising software architecture, c4model.com](https://c4model.com/)

The C4 model's Container and Component levels are the natural granularity for LLD documents in Shield's setup. One LLD per Container (or per Component for finer-grained services) cleanly aligns with how engineers reason about ownership and deployability — and avoids the milestone-LLD-proliferation that per-milestone LLDs would cause for cross-cutting components.

### Reference TRD's actual practice (Notion workspace, internal evidence)
> Reference TRD Template (last edited 2025-11-04) explicitly: *"HLD — Objective: Explain how the system will behave end-to-end. Include: Block diagram or sequence diagram showing data flow between frontend, backend, and external services / Key microservices involved / Event triggers, queues, APIs, and DBs touched."*
>
> *"LLD — Objective: Capture how each component or service works internally. Include: Components / Class/State diagrams / Database schema changes / API Contracts / Non Functional Aspects (error handling, retry, config) / Caching or fallback mechanisms."*
> — [Reference TRD Template (Notion)](https://www.notion.so/29a1ab62faf5805ea7dadefb9d052af0)

**Observed deviations from the reference template in real artifacts:**
- Large features split HLD and LLD into **separate Notion pages**. One library LLD opens: *"The TRD describes what the library does and why. This LLD describes how."*
- Small features keep HLD+LLD inline but **omit the section labels** entirely — using functional headings like "Architecture Components" and "Implementation Plan."
- "Solutioning" is used as a sibling term to HLD (one HLD title: *"... — High-Level Design & Solutioning Document"*) — signals that decision-rationale lives next to the architecture, validating the Alternatives + Cross-Cutting sections.
- One reference TRD has an **explicit "Implementation Plan" section with 5 phases** — a real precedent for the proposed §10 Milestones.

**LLD granularity in the reference workspace is per-service/per-library** (one example LLD covers a single library and is referenced by whichever milestone touches it). Shield will adopt this convention: **LLDs are per-component (C4 Container/Component level)**, and the TRD's §10 Milestones declares which LLD components each milestone touches. A single LLD doc grows incrementally across milestones.

## How This Works in Practice — `/plan` Refactor Flow

```
PRD (optional)
   │
   ▼
/plan ────────────► TRD (HLD + Milestones)  ←── replaces plan-architecture.md
   │                  │
   │                  ├─ §1–9: HLD (problem, goals, design, NFRs, cross-cutting)
   │                  ├─ §10: Milestones — each lists touched LLD components
   │                  └─ §11–14: APIs, open Qs, references, rollback strategy
   │
   ▼
plan.json (stories with design_refs[])
   │
   ├──► /implement (consumes story + design_refs[])
   ├──► /pm-sync (consumes plan.json; design_refs[] become PM-tool links)
   └──► [future] /lld <component>  ──► per-component LLD doc (14-section template from PR #43)
              │
              ├─ Header: Linked plans = [plan/M1, plan/M2, ...]   ← bidirectional
              ├─ §1 Overview names the epics/milestones served
              ├─ §14 Changelog: each edit has Story ID + sections touched
              │
              ├─ M1 may touch [lld-component-auth.md, lld-component-api.md]
              ├─ M2 may touch [lld-component-api.md, lld-component-ui.md]
              └─ Same LLD doc grows incrementally across milestones; §14 records each touch
```

**Reference example:** [tesseract PR #43](https://github.com/infraspecdev/tesseract/pull/43) — `docs/superpowers/specs/2026-05-18-lld-sample.html`. Bytebite user-signup LLD. 704 lines of HTML, 14 sections, 12 always-on + 2 promote-on-demand, with stable kebab-case anchors on every section and subsection. This is the structural model `/lld` will emit.

### Story-to-design-section reference contract

Add an optional `design_refs[]` array to each story in `plan.json`:

```json
{
  "id": "E1-S1",
  "title": "Implement POST /users endpoint",
  "design_refs": [
    {
      "doc": "trd",
      "section_id": "high-level-design",
      "anchor_url": "trd.md#high-level-design",
      "label": "TRD §7 High-Level Design"
    },
    {
      "doc": "lld",
      "component": "user-service",
      "section_id": "api-create-user",
      "anchor_url": "lld-user-service.md#api-create-user",
      "label": "LLD §5.1 POST /users"
    }
  ]
}
```

**Properties:**
- **Additive** — adapters that don't understand `design_refs` ignore it. No `/pm-sync` schema break.
- **Component-scoped** — LLD refs include `component` so multiple stories across multiple milestones can point at the same LLD doc; the LLD's `Linked plans` header and §14 Changelog close the loop on the other side.
- **Stable kebab-case anchors** — `section_id` matches the LLD sample's explicit `id="..."` attributes (e.g., `#api-create-user`, `#perf-load`), not heading-derived. Confluence-style anchor-rot bugs (CONFSERVER-26897/28087/41483) don't apply because we author the IDs explicitly.
- **Subsection-resolvable** — points at `#api-create-user` (LLD §5.1), not just `#api-contracts` (LLD §5). Required for the precision the LLD sample establishes (per-endpoint, per-flow, per-perf-aspect anchors).
- **Forward-resolvable** — `lld` refs can be added when the LLD is authored; the TRD generator leaves them as TODO entries until then.
- **PM-sync adapter behavior:** Confluence/Jira → web link with anchor URL. ClickUp → URL custom field (+ optional Doc relate). Notion → URL property (+ optional Database relation).

### De-duplication contract (addresses the user's named risk)

| Concern | Owner doc | TRD treatment |
|---|---|---|
| User problem, personas, business impact | PRD | TRD §2 links the PRD; restates problem in 1 sentence max for self-containment |
| Functional requirements (what users do) | PRD | TRD §5 links PRD's user stories; doesn't restate them |
| Non-functional requirements | PRD names targets; TRD specifies architecture-level NFRs | TRD §6 |
| Architecture & design | TRD | TRD §7 |
| Alternatives & trade-offs | TRD | TRD §8 |
| Component-internal algorithms, schemas, contracts | LLD | TRD §11 lists *which* APIs; LLD specifies their internals |
| Work breakdown | plan.json | Plan generates stories; stories `design_refs[]` back to TRD/LLD |

Rule (paraphrased from Koko Product on PRD vs TRD): **"PRD owns *why*; TRD owns *how at architecture level*; LLD owns *how at component level*; plan owns *work breakdown*. Cross-references replace restatement."**

## Failure Modes & Countermeasures

Community research surfaced 10 named failure modes. Five are directly addressable by Shield's eval framework + structural choices:

| Failure mode | Source | Shield countermeasure |
|---|---|---|
| **Format drift across agent runs** — different sessions produce differently-shaped TRDs | User's stated risk + Cvet 2020 + acatton (Lobsters) — *"authors and reviewers felt that most of the RFC template was superfluous"* | **Schema-validated TRD eval**: a fixture-based eval asserts presence of §1–14, asserts each section is non-empty (with `n/a — <reason>` as the only allowed escape), asserts `design_refs[]` shape. Backend + infra positive fixtures both pass. RED → GREEN trail required per CLAUDE.md. |
| **Content duplication PRD↔TRD↔plan** — same content restated, drifts independently | User's stated risk + Plane.so + Koko Product — *"Keep the boundary clean."* | The de-duplication contract above + a `/plan-review` rule: flag any TRD section that restates PRD content verbatim. |
| **Undead documentation / silent divergence** — doc reflects an outdated reality | Doug Turnbull (softwaredoug.com) — *"most design docs lie to you. They're undead documentation"*; Lucas Costa — *"Either you update the doc (which nobody does) or you diverge from it silently"* | Shield's `/plan` re-runs **update the same files in place** (per current behavior). Combined with git history, the TRD is a snapshot at decision time. Recommend a `last_aligned_with: <commit-sha>` metadata field updated by `/implement` when stories close. |
| **Over-specification ("LLD too early")** — schema/API decisions before query patterns are understood | Lucas Costa — *"you have the least information at the beginning of a project, which is exactly when design docs ask you to make the most decisions"* | Defer LLD to per-milestone authoring. TRD §11 names *which* APIs change; LLD specifies their internals only when the milestone begins. |
| **Implementation-manual pseudo-code** — doc just narrates code with no trade-offs | Google design-docs doc — *"design docs that are really implementation manuals … it would probably have been a better idea to write the actual program right away"* | `/plan-review` rule: flag any HLD section that contains code blocks > N lines without an "Alternatives Considered" rationale. |

Five more failure modes (design-doc theatre, review-rubber-stamp, RFC firing-squad, authority fragmentation, template bloat) are governance issues not directly fixable by structural choices — flag as future `/plan-review` rubric expansions.

## Decisions Locked & Open Questions

### Decisions locked with the user (2026-05-24 → 2026-05-25)

1. **LLD granularity: strictly per-component (C4-inspired).** One LLD per Container or Component (service, library, module). Milestones list which LLDs they touch; LLDs grow incrementally as milestones land. LLDs are typically backend-only; infra rarely needs an LLD layer.
2. **No lean variant.** The full 14-section template is required for every TRD. (Orosz's tiered-template pattern applies at >2,000-engineer scale, not Shield's per-team scope.)
3. **Direct cutover.** `/plan` stops writing `plan-architecture.md` immediately. No feature flag, no side-by-side period. Existing `plan-architecture.md` files remain readable; no migration tool needed.
4. **Section enforcement: strict via eval, with `n/a — <reason>` escape.** All 14 TRD sections are required by the schema-validated eval. Missing any section is an eval failure with a named error. An explicit `n/a — <reason>` line counts as present; vague TBDs or empty sections fail.
5. **One TRD, two domains.** Same 14-section template applies to backend AND infrastructure work. Domain-aware prompting per section in `/plan`'s SKILL.md surfaces the right interpretation; the eval and `/plan-review` rubric do not fork.
6. **§14 Rollback Strategy is a first-class section.** Preserves the strongest property of today's `plan-architecture.md`.

### Open questions for the implementation phase

1. **`design_refs[]` resolution at PM-sync time.** Should adapters auto-create Confluence/Notion pages and link them, or only emit URLs and trust the user to author the pages? Recommendation: **emit URLs only** in v1; adapter authoring is a v2 enhancement.
2. **Section-ID stability.** TRD section anchors should be stable kebab-case slugs (`#high-level-design`), not heading-derived (which break on rename per Confluence CONFSERVER-26897/28087/41483). Concrete recommendation: emit explicit `{#section-id}` markdown anchors in the TRD template, and validate the slug set is the canonical 14 in the eval.
3. **TRD ↔ LLD linking direction.** TRD §10 lists LLDs each milestone touches (forward link). Should LLDs maintain backlinks to milestones/TRD? Recommendation: **yes, but auto-generated** — `/lld` reads the TRD, fills in a "Referenced By" section in the LLD pointing back to milestones. Avoids manual link-rot.
4. **`/pm-sync` adapter behavior for `design_refs[]`.** Confluence → web link with anchor URL. Jira → remote issue link. ClickUp → URL custom field. Notion → URL property. Open: should ClickUp/Notion also populate a Relationship/Database-relation if the design doc exists in the same tool? Recommendation: **v1 emits URL only**, structured relationships are v2.
5. **Eval shape for TRD.** Concrete eval design: a fixture TRD with all 14 sections present passes; fixtures missing any section fail with a named error per section. Bidirectional check: the LLM does not add unprompted sections (drift-by-addition). `n/a — <reason>` lines count as present; vague TBDs or empty sections do not. Coverage includes both backend and infra positive fixtures. All covered by `shield/evals/plan-trd.yaml` fixture set.

## Migration Path / Reversibility

The refactor is a direct cutover; reversibility cost is low:

- **Forward:** `/plan` adds TRD generation step before plan.md/plan.json. `plan-architecture.md` is replaced by `trd.md` immediately (no feature flag). Story schema gains optional `design_refs[]`. `/plan-review` gets new TRD-section rules. Estimated work: one PR for the `/plan` command + plan-docs SKILL.md changes, one PR for evals, one PR for `/plan-review` rule additions.
- **Reversal:** If the TRD approach proves wrong, revert `plan-docs/SKILL.md` to the pre-refactor template + restore `plan-architecture.md` generation. Existing `trd.md` files remain readable in old feature folders. `design_refs[]` is optional everywhere, so removing it is a no-op for downstream adapters.
- **Existing artifacts:** Pre-refactor feature folders keep their `plan-architecture.md` — no rewrite, no migration. New folders get `trd.md`. This is git-history-friendly and doesn't break anyone reading older docs.

## Summary

The TRD = HLD + PM-lens milestones + Rollback Strategy design is well-supported by the IEEE 1016 / Sommerville / Pressman lineage, mirrors the reference TRD template, and aligns with Google + Uber + Larson + Orosz modern practice. The **unified 14-section TRD template covers both backend and infrastructure work**, with domain-aware prompting per section and an explicit `n/a — <reason>` escape for sections that genuinely don't apply; the 14-section LLD template (anchored in [tesseract PR #43's Bytebite sample](https://github.com/infraspecdev/tesseract/pull/43)) is the per-component layer authored separately and is **typically backend-only** since infra code is declarative-spec-as-code. **LLDs are per-component (C4-inspired)** — a single LLD covers one Container or Component, lists multiple `Linked plans` in its header, and grows incrementally as milestones touch it; §14 Changelog records each touch with a Story ID. Story traceability via additive `design_refs[]` (component-scoped, subsection-precise) is the highest-signal way to link work to design without breaking `/pm-sync`. The two named risks (format drift, content duplication) have concrete countermeasures: schema-validated evals enforcing all sections (and §12's 8 forced subsections in the LLD), and a de-duplication contract ("PRD owns *why*, TRD owns *how at architecture*, LLD owns *how at component*, plan owns *work breakdown*"). The refactor is a direct cutover with no feature flag; reversal is a simple revert with no migration burden.

## Product Lens

### Scorecard (PM1–PM11)

| Dim | Name | Grade | Severity | Gap |
|---|---|---|---|---|
| PM1 | User impact clarity | **D** | Critical | Roles named abstractly ("reviewers", "engineers"); no quantified before/after per persona |
| PM2 | Problem–solution fit | **B** | Critical | Missing explicit Problem Statement section *before* Decision; named risks appear pre-problem |
| PM3 | Scope discipline | **B** | Important | 14 TRD + 14 LLD sections (+ §12's 8 forced subsections) reads kitchen-sink; no MVP cut explicit |
| PM4 | Prioritization rationale | **D** | Important | Three PRs listed without effort/impact tags or stated dependencies |
| PM5 | Stakeholder communicability | **D** | Important | Jargon-saturated; no plain-language summary a non-technical reader could follow |
| PM6 | Market / competitive awareness | **A** | Warning | Strong: `plan-architecture.md`, reference TRD, Google, Uber, IEEE 1016, C4, arc42, ADR all compared |
| PM7 | Adoption / rollout risk | **B** | Important | Technical risks covered; adoption-side risks (learning curve, change mgmt, partner buy-in) missing |
| PM8 | Success metrics defined | **F** | Important | No measurable post-ship outcome (no thresholds, targets, observable behaviors) |
| PM9 | Reversibility / exit cost | **A** | Warning | Strong: clean revert path, no migration burden, additive schema |
| PM10 | Business value alignment | **F** | Critical | No tie to business goal/OKR/customer escalation/compliance — justified entirely on engineering grounds |
| PM11 | Framing coverage honored | **B** | Important | All 5 PF7 voices quoted; PF8 "Vendor docs" category has refs but no verbatim body quote |

**Composite:** 2A · 3B · 3D · 2F (≈ C+ overall). **3 Critical gaps** to close before this is plan-ready: PM1 (user-impact quantification), PM2 (Problem Statement section), PM10 (business-value tie-in).

### User Impact Analysis

The proposed TRD refactor directly serves five user populations identified in the framing brief, and the research provides differentiated evidence for each:

- **Shield maintainer** — Highest leverage beneficiary. The named risks (format drift, content duplication) get concrete countermeasures: a schema-validated eval enforces all 14 TRD sections, and the de-duplication contract codifies ownership across PRD/TRD/LLD/plan. Risk of inaction: continued ad-hoc `plan-architecture.md` output that `/plan-review` can only grade free-form.
- **Staff/senior engineers reading the TRD** — Gain a predictable artifact grounded in IEEE 1016 viewpoints, Sommerville's three architecture justifications, and the reference TRD template. Research quantifies coverage: 12 IEEE viewpoints, split ~7 HLD / ~5 LLD; 14 canonical TRD sections; 14 canonical LLD sections (12 always-on + 2 promote-on-demand).
- **Junior/mid engineers consuming via `/implement`** — Gain unambiguous design pointers via `design_refs[]` with subsection-precision (e.g., `#api-create-user` not `#api-contracts`). Research cites the Bytebite sample (PR #43, 704 lines, kebab-case anchors on every section and subsection) as the concrete structural target.
- **`/plan-review` reviewer agents** — Gain stable section anchors enabling structured rubrics instead of free-form grading. Research surfaces five mechanically-enforceable rules.
- **`/pm-sync`** — Hard backward-compat constraint is **met**: `design_refs[]` is additive, adapters ignore unknown fields. No schema break.

**Unquantified gaps:**
- No estimate of how many existing feature folders carry `plan-architecture.md`. Direct-cutover migration risk is asserted "low" but not measured.
- No baseline for current `/plan-review` defect-catch rate vs. expected post-refactor rate.
- "Future LLD-authoring command" is described but its build effort is not estimated.

### Scope Recommendation

**Essential (MVP — ship in v1 cutover):**
1. `/plan` emits `trd.md` with the canonical 14 sections (replaces `plan-architecture.md`).
2. Stable kebab-case section anchors emitted explicitly as `{#section-id}` markdown anchors.
3. `plan.json` story schema gains optional additive `design_refs[]` with `{doc, section_id, anchor_url, label}`.
4. Schema-validated eval fixture pair (positive + missing-section negatives) under `shield/evals/plan-trd.yaml`.
5. `/plan-review` rules for the 14 required sections (with `n/a — <reason>` escape) + at least one duplication-detection rule.

**Defer (v2 enhancements):**
- `/lld <component>` command — template locked; authoring command is "future". v1 leaves `lld` refs as TODO entries.
- Adapter auto-creation of Confluence/Notion pages from `design_refs[]` — v1 emits URLs only.
- Structured ClickUp/Notion relationships — v1 emits URLs only.
- `last_aligned_with: <commit-sha>` metadata for undead-doc countermeasure.
- `/lld` auto-generated "Referenced By" backlinks.
- Governance failure-mode rules (design-doc theatre, review-rubber-stamp, etc.).

**Cut entirely:**
- Lean TRD variant — research locks this as **rejected**. Do not relitigate.
- Migration tool for existing `plan-architecture.md` — direct cutover, no migration.

### Prioritization Framework

| Priority | Work item | Effort | Impact | Dependency |
|---|---|---|---|---|
| **P0** | Schema-validated TRD eval fixture pair + section slug allow-list | M | **Very high** — strongest format-drift countermeasure; CLAUDE.md mandate | Section list locked (done) |
| **P0** | `/plan` command + `plan-docs/SKILL.md` updates to emit `trd.md` with 14 canonical sections, domain-aware prompting per section, and explicit `{#section-id}` anchors | L | **Very high** — the actual cutover | None |
| **P0** | `plan.json` story schema: additive `design_refs[]` | S | **High** — story traceability + `/implement` consumption | None (additive) |
| **P1** | `/plan-review` rules for required-section presence + 1 duplication-detection rule | M | High — converts free-form review into structured grading | P0 schema lands first |
| **P1** | `/pm-sync` adapter handling for `design_refs[]` URL emission (all four adapters) | M | Medium — read-only forward link in v1 | `design_refs[]` shape locked (done) |
| **P2** | `last_aligned_with` metadata + `/implement` update on story close | S | Medium — undead-doc countermeasure | After v1 stable |
| **P2** | `/plan-review` rules for remaining failure-mode countermeasures | M | Medium — incremental review quality | After P1 |
| **P3 (deferred)** | `/lld <component>` command + LLD eval fixtures | L | High *for LLD consumers* — but no LLD consumers exist yet | After v1, separate epic |
| **P3 (deferred)** | Adapter auto-creation of design-doc pages | L | Low — research recommends URL-only in v1 | After `/lld` |

**Sequencing rationale:** P0 items land together in the cutover PR (eval can't ship before generator; generator shouldn't ship without eval). `design_refs[]` is additive and zero-risk, so it goes in v1 even with no consumer yet — locking the contract early avoids a v2 migration. `/lld` is genuinely deferrable because the TRD references LLDs by URL with TODO entries until the command exists.

### Stakeholder Summary

Shield's `/plan` command today produces a work breakdown and a free-form architecture sketch (`plan-architecture.md`). Engineers reading the output have no predictable place to find the system design, and reviewers have no consistent shape to grade against. The research recommends replacing the free-form sketch with a **Technical Requirements Document (TRD)** — a 14-section template grounded in the IEEE software-design standard, mirrored from the reference TRD template, and consistent with how Google, Uber, and respected practitioners (Will Larson, Gergely Orosz) describe modern design-doc practice. The TRD covers the *what* and the *architecture-level how* of a feature. The deeper component-internal details (database schemas, API internals, race-condition handling) move to per-component **Low-Level Design (LLD)** documents authored separately when each milestone begins, following a 14-section template Shield already has a working sample for. Every story in the work plan gains an optional pointer to the exact section of the TRD or LLD it depends on, so an engineer picking up a story can find the design in one click. The change ships as a direct replacement with no migration burden — existing feature folders keep their old artifacts and stay readable. The two biggest risks of templated design docs (templates drifting in shape across runs, and the same content being restated in three places that then disagree) are addressed with an automated check that enforces the section list and a written ownership rule of which document owns which content. The first release lands the new TRD output, the schema-enforcing test, and the story-to-design pointers; the LLD command and richer reviewer rules follow in a second release.

### Critical gaps — user verdict (2026-05-24)

The three Critical-severity findings were reviewed with the requester. All three are acknowledged as artifacts of applying the full PM1–PM11 rubric (designed for PRDs / product features) to an internal-tooling research artifact. Verdict per gap:

1. **PM1 — Quantified user-impact per persona.** *Resolution:* the refactor's value is a baseline add to how tech teams currently work — the personas (plan author, reviewer, `/implement` consumer) all benefit uniformly. No additional quantification needed for an internal tooling change.
2. **PM2 — Explicit Problem Statement section.** *Resolution:* not required. Going to implementation directly; the Context paragraph at the top of this doc carries enough framing for engineering work.
3. **PM10 — Business-value tie-in.** *Resolution:* the value is to help tech teams iterate faster by automating planning steps that previously required free-form judgment. Not a business-OKR question for an internal Shield meta-tooling refactor.

PM8 (success metrics) and PM4/PM5 (prioritization rationale, stakeholder communicability) are Important but not blocking — folded into the implementation work where the Prioritization Framework table already addresses sequencing.

## References

- IEEE Std 1016-2009, "Software Design Descriptions." [Çankaya University full PDF](https://cengproject.cankaya.edu.tr/wp-content/uploads/sites/10/2017/12/SDD-ieee-1016-2009.pdf) · [IEEE Xplore](https://ieeexplore.ieee.org/document/5167255) · [Wikipedia summary](https://en.wikipedia.org/wiki/Software_design_description)
- Sommerville, I. (2015). *Software Engineering*, 10th ed. Pearson. Chapter 6 (Architectural Design) + Chapter 7 (Design and Implementation). [Pearson catalog](https://www.pearson.com/en-us/subject-catalog/p/software-engineering/P200000003258/9780137503148)
- Pressman, R., & Maxim, B. (2014). *Software Engineering: A Practitioner's Approach*, 8th ed. McGraw-Hill. Chapters 12–15 (Design Concepts, Architectural Design, Component-Level Design, UI Design). [Google Books](https://books.google.com/books/about/Software_Engineering_A_Practitioner_s_Ap.html?id=i8NmnAEACAAJ)
- Ubl, M. "Design Docs at Google." [industrialempathy.com](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Larson, W. "Writing an engineering strategy." [lethain.com/eng-strategies](https://lethain.com/eng-strategies/) · *An Elegant Puzzle: Systems of Engineering Management*
- Orosz, G. "Companies Using RFCs or Design Docs and Examples of These." [blog.pragmaticengineer.com/rfcs-and-design-docs](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)
- Bryar, C., & Carr, B. (2021). *Working Backwards: Insights, Stories, and Secrets from Inside Amazon*. [workingbackwards.com PR/FAQ summary](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)
- Costa, L. "Design docs are dead and we killed them." [lucasfcosta.com/blog/design-docs](https://www.lucasfcosta.com/blog/design-docs)
- Turnbull, D. "Throwaway PRs, not design docs." [softwaredoug.com](https://softwaredoug.com/blog/2024/12/14/throwaway-prs-not-design-docs)
- Cvet, M. "Goals and Failure Modes for RFCs and Technical Design Documents." [Better Programming, Medium, 2020](https://medium.com/better-programming/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff)
- Squarespace Engineering. "The Power of 'Yes, If'." [engineering.squarespace.com](https://engineering.squarespace.com/blog/2019/the-power-of-yes-if)
- Kashitsyn, R. "Effective design docs." [mmapped.blog](https://mmapped.blog/posts/31-effective-design-docs)
- McCaffrey, C. "Design docs, markdown, and Git." [caitiem20.wordpress.com](https://caitiem20.wordpress.com/2020/03/29/design-docs-markdown-and-git/)
- "Decoding the Dichotomy: PRD vs TRD." [Koko Product, Medium](https://medium.com/@kokoproduct/decoding-the-dichotomy-prd-vs-trd-67463a29aa84)
- "How to write a PRD that engineers actually read." [Plane.so blog](https://plane.so/blog/how-to-write-a-prd-that-engineers-actually-read)
- Atlassian. "Anchors in Confluence." [confluence.atlassian.com/doc/anchors-139442.html](https://confluence.atlassian.com/doc/anchors-139442.html)
- Atlassian. "Configuring issue linking." [confluence.atlassian.com/adminjiraserver/configuring-issue-linking-938847862.html](https://confluence.atlassian.com/adminjiraserver/configuring-issue-linking-938847862.html)
- ClickUp. "Intro to Relationships." [help.clickup.com/.../6304528030743](https://help.clickup.com/hc/en-us/articles/6304528030743-Intro-to-Relationships)
- Brown, S. "The C4 model for visualising software architecture." [c4model.com](https://c4model.com/)
- Notion. "Create links and backlinks." [notion.com/help/create-links-and-backlinks](https://www.notion.com/help/create-links-and-backlinks)
- HN thread on design-doc anti-patterns (item 44779428). [news.ycombinator.com/item?id=44779428](https://news.ycombinator.com/item?id=44779428)
- HN thread on RFC-process cost (item 18145205). [news.ycombinator.com/item?id=18145205](https://news.ycombinator.com/item?id=18145205)
- HN thread on over-specification (item 46221016). [news.ycombinator.com/item?id=46221016](https://news.ycombinator.com/item?id=46221016)
- Lobsters discussion on Design Docs at Google. [lobste.rs/s/rullsv](https://lobste.rs/s/rullsv/design_docs_at_google)
- ADR catalog. [adr.github.io](https://adr.github.io/)

### Internal references (Notion — reference workspace)

- [Reference TRD Template](https://www.notion.so/29a1ab62faf5805ea7dadefb9d052af0) (last edited 2025-11-04)
- Reference LLD example (per-library scope, 2026-05-10) — per-library LLD example
- Reference HLD example (module-first, 2026-04-15)
- Reference HLD example with "Solutioning" sibling label (2026-04-01)
- Reference HLD example (minimal, small features, 2026-05-21)
- Reference TRD with explicit 5-phase Implementation Plan precedent (2026-01-04)

### Internal references (Shield repo)

- `docs/shield/agent-behavior-decomposition-20260520/outputs/plan-architecture.html` — baseline ADR+HLD hybrid the TRD must improve on
- [tesseract PR #43](https://github.com/infraspecdev/tesseract/pull/43) — `docs/superpowers/specs/2026-05-18-lld-sample.html` — canonical 14-section LLD sample (Bytebite user-signup); reference structure for the `/lld` command

## Further Exploration

*Curated for going deeper; NOT cited in body above.*

### Books
- Bass, L., Clements, P., Kazman, R. (2021). *Software Architecture in Practice* (4th ed.). The module/component-and-connector/allocation viewtype taxonomy is a cleaner alternative to Pressman's four layers.
- Bryar, C., Carr, B. (2021). *Working Backwards.* Amazon's PR/FAQ tradition for the PRD-upstream framing.
- Fournier, C. (2017). *The Manager's Path.* ADRs vs design docs distinction in tech-lead chapters.

### Long-form blogs / articles
- Brown, S. "The C4 model for visualising software architecture." [c4model.com](https://c4model.com/) — quoted in body above; Container/Component levels are the chosen LLD granularity.
- arc42 template. [arc42.org](https://arc42.org/) — open-source 12-chapter architecture-doc scaffold widely used in DE/EU teams.
- ThoughtWorks. "Lightweight architecture decision records." For the "TRD = HLD + ADR" hybrid Shield is gravitating toward.

### Videos / talks
- Larson, W. on engineering strategy at LeadDev. For the "five design docs → one strategy" pattern.

### Courses
- (None curated this round — open opportunity.)

### Podcasts / podcast episodes
- *StaffEng Podcast* — multiple episodes on design-doc practice with senior+ engineers.

### Other
- Joel Henderson's ADR catalog. [adr.github.io](https://adr.github.io/) — patterns for ADRs as supplement to (not replacement of) HLD.
- HashiCorp's public RFC template. Useful comparison point for infra-leaning teams.
