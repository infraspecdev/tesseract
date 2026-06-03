# Design: How high-level architecture must be authored (C4-anchored)

**Date:** 2026-06-01
**Status:** Approved (design); pending implementation plan
**Branch:** `shield-hld-authoring`
**Author:** ashwinimanoj

## Problem

Shield has no single standard for *how high-level architecture must be authored*.
Guidance is scattered and inconsistent across PRD §5 (Architecture & flows) and
TRD §7 (High-Level Design), with no shared notion of the right level of
abstraction — so HLDs drift into implementation detail or stay too vague, and
nothing enforces a baseline.

## Goal

Define one C4-anchored standard for authoring high-level architecture, govern
both PRD §5 and TRD §7 with it, and make the "must" real via enforcement —
deterministic gates where checkable, semantic review where not.

## Decisions (from brainstorming)

| Topic | Decision |
|---|---|
| Backbone | **C4 model** sets the right level of abstraction |
| Surfaces | **PRD §5** (Context) + **TRD §7** (Container), governed consistently |
| What it pins down | Required content, diagram conventions, level-of-detail rules, quality bar |
| Enforcement | **Guidance + full enforcement** — teach in skill/templates; deterministic gate in `validate_trd.py`; semantic gate in `/plan-review` architect rubric |
| Out of scope | The mermaid-JS refactor, build-time render, standalone validators (all dropped) |

## Design

### Layer 1 — Teach (skill-referenced standard + templates)

**New `shield/skills/general/architecture-authoring.md`** — the single C4 standard, referenced by the doc skills. It defines:

**C4 → Shield mapping (the level-of-detail rule):**

| C4 level | Shield home | Stays at |
|---|---|---|
| **L1 System Context** — system as one box + users + external systems | **PRD §5 Architecture & flows** | product-readable, no internals |
| **L2 Container** — deployable/runtime units (services, datastores, queues, UIs) inside the system boundary + how they talk | **TRD §7 High-Level Design** (canonical HLD) | container granularity |
| **L3 Component / L4 Code** | **LLD** (`lld-docs`) | out of HLD entirely |

Component/Code-level detail in an HLD is a defect — it belongs in the LLD.

**Required content:**
- **PRD §5 (Context):** system as a single box; users/personas; external systems integrated with; the 1–2 primary end-to-end flows.
- **TRD §7 (Container):** container inventory (each unit → responsibility + tech); interfaces/contracts between containers; data flow; persistence boundary; trust/network/residency boundaries; the core request lifecycle including failure/recovery — all at container granularity.

**Diagram conventions (mermaid):**
- **Context** = flowchart; system node centered, users + externals around it.
- **Container** = flowchart with a `subgraph` for the system boundary; labeled edges (protocol/contract); datastore-shaped nodes.
- **Boundary** = `subgraph` per zone (region/account/network/trust).
- **Core flow** = `sequenceDiagram` including the failure path.
- Rules: consistent direction (LR context/container, TB boundary); node-id + human label; labeled edges; ~15-node ceiling; **no ASCII box-art**; mermaid source is not counted as a code block by plan-review.
- One canonical good example per type (context / container / boundary / sequence).

**Elicitation Q&A (required walk):** Before drafting §5/§7, the skill **must walk a fixed, C4-derived question set with the user** rather than generating the architecture from the PRD alone. The set (each may be answered `n/a — <reason>`):

1. **Actors & externals** — who/what uses the system; which external systems it integrates with; what crosses the system boundary.
2. **Containers** — the major runtime units (services, UIs, datastores, queues); which are **new vs. existing**; tech per unit.
3. **Interfaces** — how containers communicate: **sync** (REST/gRPC) vs **async** (events/queue); the key contracts.
4. **State & persistence** — where state lives; which container owns which data; the persistence boundary.
5. **Boundaries** — trust / network / region / account boundaries; data-residency constraints; what crosses each.
6. **Core flow & failure** — the primary request lifecycle end-to-end, including failure/recovery behavior.
7. **Architecture-shaping NFRs** — scale / latency / availability targets that force a structural choice.
8. **Major decisions** — build-vs-buy, sync-vs-async, single-vs-multi-region (feeds TRD §8 Alternatives).

**Hybrid skip rule:** before asking, the skill scans the research transcript + PRD; questions already answered there are **auto-filled and shown for confirmation, not re-asked** — only the gaps are walked.

**Unknowns are never fabricated:** when the user is unsure or a point is undecided, the skill records it in **TRD §12 Open Questions** (owner + resolve-by) — or **PRD §19 Open Questions** for §5-level uncertainty — instead of inventing structure. The HLD reflects real uncertainty.

**Wiring:** `prd-docs` (§5) and `plan-docs` (§7) templates + SKILL walks replace their inline diagram prose with a one-line link to `architecture-authoring.md` plus only the section-specific note (which C4 level that section targets), and run the elicitation Q&A above. `lld-docs` links it too, to mark the L2↔L3 boundary.

### Layer 2 — Deterministic gate (`validate_trd.py`)

Add §7 checks to `shield/scripts/validate_trd.py` (follows the existing `_emit(severity, code, message)` + `_section_bodies` pattern; §7 slug is `high-level-design`):
- **`hld_missing_diagram:high-level-design`** (FAIL) — §7 body contains no ` ```mermaid ` fence.
- **`hld_ascii_art:high-level-design`** (FAIL) — §7 body contains ASCII box-art glyphs (`┌ ┐ └ ┘ │ ─ +---`), which signal a non-mermaid diagram.

(Node-ceiling and "responsibility named" are *not* deterministic from mermaid source — left to Layer 1 guidance + Layer 3 review. PRD §5 has no TRD validator and §5 is optional, so its enforcement is semantic-only — Layer 3.)

### Layer 3 — Semantic gate (`/plan-review` architect rubric)

Add an HLD dimension to the architect persona in `shield/skills/general/plan-review/` (personas/dimensions/prompts) — the architect agent grades:
- Is the HLD at the **right C4 level** (Container for §7), with no L3/L4 leak?
- Does **every container name a responsibility and its interface**?
- Are the required diagrams present and adequate (container + core sequence, + boundary when zones exist)?
- Are genuine unknowns captured in §12 Open Questions rather than fabricated as confident structure?
- For PRD §5 (when reviewed): is there a Context diagram when the feature has external touchpoints?

### Milestone diagrams (every milestone carries one)

Each milestone must have a diagram showing the architecture state/delta it
delivers — consistent with the C4/mermaid conventions above. Because TRD §10 is
**rendered deterministically from `plan.json`**, the diagram is sidecar data, not
hand-written prose:

- **Schema** — `shield/schema/plan-sidecar.schema.json`: add an optional
  `diagram` field (non-empty mermaid string) to the milestone object, and bump
  the sidecar version. (Not JSON-`required` — that would retroactively break
  existing committed sidecars. The "must" is enforced by the version-gated check
  below, mirroring how `touches_lld` is skipped on older sidecars.)
- **Render** — `shield/scripts/render_trd_section.py` (`render_milestones`):
  emit the milestone's `diagram` as a ` ```mermaid ` block under that milestone's
  heading in §10. (The existing `validate_trd.py` `milestone_drift` check then
  guarantees the rendered §10 — diagram included — matches the sidecar.)
- **Hard gate** — `shield/scripts/validate_plan.py`: for sidecars at the new
  version, FAIL **`milestone_no_diagram:<id>`** when a milestone's `diagram` is
  missing/empty, and **`milestone_ascii_diagram:<id>`** when it contains ASCII
  box-art instead of mermaid. Older sidecars are grandfathered (skip), exactly
  like the existing `touches_lld` drift check.
- **Authoring** — the `architecture-authoring.md` standard states each milestone
  carries a diagram of the slice it delivers; `/plan`'s milestone walk elicits it
  (reusing the same C4 conventions). Unknown at milestone time → the milestone's
  diagram shows current intent and the gap goes to §12 Open Questions.

## Eval coverage

- **`validate_trd.py`** — pytest: a §7 fixture with no mermaid → `hld_missing_diagram`; a §7 with ASCII box-art → `hld_ascii_art`; a conforming §7 → passes (RED→GREEN).
- **`/plan-review` architect rubric** — a snapshot/eval fixture: an HLD with L3 leak / unnamed interfaces is flagged; a clean Container-level HLD passes. (Snapshot eval per the architect-agent pattern.)
- **End-to-end** — extend a `plan-docs` eval: a generated TRD §7 contains a container `flowchart` + `sequenceDiagram` and links the standard. Existing TRD §7 mermaid render tests still pass.
- **Elicitation Q&A** — end-to-end eval: when research/PRD leaves an architecture gap, the skill **asks** the relevant C4 question (rather than inventing); when the user answers "unsure", the point lands in §12 Open Questions, not as fabricated structure; and a question already answered by the PRD is **not** re-asked (auto-filled/confirmed).
- **Milestone diagrams** — `validate_plan.py` pytest: a sidecar whose milestone lacks `diagram` → `milestone_no_diagram`; ASCII box-art in a milestone diagram → `milestone_ascii_diagram`; a milestone with a valid mermaid `diagram` → passes. `render_trd_section.py` test: each milestone's `diagram` renders as a `pre`/` ```mermaid ` block under its §10 heading.

## Files touched

| File | Change |
|---|---|
| `shield/skills/general/architecture-authoring.md` | NEW — C4 standard + content + diagram conventions + examples + quality bar |
| `shield/skills/general/prd-docs/templates.md` + `SKILL.md` | §5 links the standard; section note = C4 Context |
| `shield/skills/general/plan-docs/trd-template.md` + `SKILL.md` | §7 links the standard; section note = C4 Container |
| `shield/skills/general/lld-docs/lld-template-*.md` | Link standard to mark the L2↔L3 boundary |
| `shield/scripts/validate_trd.py` | Add `hld_missing_diagram` + `hld_ascii_art` §7 checks |
| `shield/scripts/test_validate_trd*.py` | New §7-check tests |
| `shield/schema/plan-sidecar.schema.json` | Add optional `diagram` (mermaid) to milestone object; bump sidecar version |
| `shield/scripts/render_trd_section.py` | Render each milestone's `diagram` as a mermaid block in §10 |
| `shield/scripts/validate_plan.py` (+ tests) | Add `milestone_no_diagram` / `milestone_ascii_diagram` gates |
| `shield/skills/general/plan-review/{personas,dimensions,prompts}` | Architect HLD rubric dimension |
| `shield/evals/...` | validate_trd §7 fixtures + architect HLD eval + plan-docs §7 end-to-end |
| `.pre-commit-config.yaml` | Ensure validate_trd tests run on change |
| `.claude-plugin/marketplace.json` | Bump `2.25.0` → `2.26.0` |

## Non-goals

- No mermaid client-JS refactor, no build-time SVG render, no standalone mermaid validators (explicitly dropped this session).
- No re-authoring of existing HLDs in `docs/shield/**`; the standard applies going forward.
- No deterministic PRD §5 gate (no PRD validator exists; §5 is optional → semantic review only).
