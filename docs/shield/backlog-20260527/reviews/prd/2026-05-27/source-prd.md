# Shield Backlog

## 1. Header
| Field | Value |
|---|---|
| Owner | @ashwinimanoj |
| Status | Draft |
| PRD type | Lean |
| Date created | 2026-05-27 |
| Last updated | 2026-05-27 |
| Linked design spec | null |
| Linked research | null |
| Decision-maker | @ashwinimanoj |
| Sign-off contacts | _(n/a for internal tooling)_ |
| Linked plans | _(auto-populated by /plan)_ |

## 2. Terminologies
| Term | Definition |
|---|---|
| Backlog | A project-level, ordered list of future work captured across the Shield workflow. Lives at `docs/shield/backlog.json`. |
| Backlog entry | One captured idea — a future epic, story, or task. May not be actionable when captured. Carries an order, a source (`user` \| `agent`), and a **feature + epic association** (either may be proposed-new until promotion). |
| Feature association | The feature an entry belongs to (a `docs/shield/<feature>/` folder). It is the **reconciliation key**: `manifest.json` is keyed by feature, so this is how an entry is matched to its pipeline progress. May be proposed-new until promotion. |
| Epic association | The epic an entry slots into when planned — an existing epic id (e.g. `EPIC-2`) or a proposed new epic. Acts as the **gate** at reconciliation: the entry is removed only when this epic's work appears in the feature's `plan.json`. |
| Promotion | Acting on a backlog entry by starting the appropriate Shield step for it — `/research`, `/prd`, `/plan`, or `/implement`. **The user decides which step**; the backlog does not auto-route. |
| Reconciliation | Keeping the backlog current: `manifest.json` locates the entry's feature and whether it has a `plan.json`; if so, the entry's epic is looked up there. The entry is removed once its epic's work appears in the feature's `plan.json` (`epics[].stories[]`). No ids are stamped — matching is by feature (manifest) + epic (plan). A `prd`-only feature does **not** trigger removal. |
| Agent-discovered entry | A backlog entry the agent adds on its own when it notices future work mid-task (vs. a user-created entry). |

## 3. Problem & context

Future work surfaces constantly while using Shield — during `/research`, while writing a PRD, mid-`/plan`, and especially during `/implement` ("we should also handle X later", "this whole area needs a rewrite"). Today there is **nowhere to park that work**. The options are bad: derail the current task to chase it, or drop it in a comment / memory / someone's head and lose it.

Concretely:
- There is no project-level, ordered place to capture "not now, but later" items. `plan.json` only holds work already committed to a milestone; `manifest.json` is an artifact index. Neither captures un-triaged future work.
- Ideas discovered by the agent mid-task have no home — they're mentioned once in conversation and gone.
- When future work *is* remembered, there's no consistent path from "loose idea" to "stories in a plan." Each pickup re-derives the epic, the feature, and the scope from scratch.

Why now: Shield's pipeline (`/research → /prd → /plan → /implement`) is mature, but it only handles work that's *already* been decided on. The gap is the staging area *before* that pipeline — where future work waits, ordered, until the user promotes it in.

## 4. Target users / personas
| ID | Persona | Goals | Frictions today |
|---|---|---|---|
| P1 | Developer/PM driving Shield | Capture future work without losing focus on the current task; come back later to an ordered list of what to pick up next | Future ideas get lost or derail the current task; no ordered "later" list at the project level |
| P2 | The agent (Claude) running a Shield task | Record follow-up work it discovers mid-task so the human doesn't have to remember it | Discovered work is mentioned once in chat then forgotten; no place to persist it |

## 5. Architecture & flows

A single global store `docs/shield/backlog.json` (sibling to `manifest.json`), a `/backlog` command to view it, a capture path usable from any Shield skill or by the user, and a **user-driven promotion**: the user picks an entry and starts whichever Shield step fits — `/research`, `/prd`, `/plan`, or `/implement`. Each entry carries an order, a source (`user` | `agent`), and a **feature + epic association**. **Reconciliation** reads `manifest.json` as the project-level index — to find each entry's feature, see whether it has a `plan.json`, and surface its pipeline status (research/prd/plan) in the `/backlog` view — then opens the flagged `plan.json` and removes any entry whose epic's work now appears there. A `prd`-only feature stays in the backlog; only plan-committed work is removed. No ids are tracked.

```mermaid
flowchart LR
  cap["Capture<br/>(user or agent, anytime)"] --> bl["backlog.json<br/>(ordered, project-level)"]
  bl --> view["/backlog<br/>(ordered list +<br/>per-entry pipeline status)"]
  man["manifest.json<br/>(feature index:<br/>research/prd/plan)"] --> view
  bl --> dec{"User decides<br/>next step"}
  dec --> research["/research"]
  dec --> prd["/prd"]
  dec --> plan["/plan"]
  dec --> impl["/implement"]
  man --> rec["Reconcile:<br/>epic's work in feature's plan.json<br/>→ remove from backlog"]
  plan --> rec
  rec --> bl
```

## 6. Goals & non-goals

### Goals
- Capture future work (epic / story / task granularity) at **any point** in the workflow — before a PRD exists, during planning, during implementation — without derailing the current task.
- Support **both** capture sources: user-created and agent-discovered.
- Keep the backlog **ordered** so there's a clear "what to pick up next."
- Every entry is **associated with a feature and an epic** — existing or proposed-new — and the agent **suggests a matching feature/epic** at capture or promotion time.
- A `/backlog` command **shows the current backlog**, ordered, with each entry's feature + epic association, source, and **pipeline status (research / prd / plan, read from `manifest.json`)** — so you can see what's been started (e.g. a prd written) without the entry being removed.
- Provide a **user-driven promotion path**: the user picks an entry and starts the Shield step they judge appropriate (`/research`, `/prd`, `/plan`, or `/implement`). The backlog suggests, but does not dictate, the next step.
- **Keep the backlog current**: when an entry's work appears in a feature's `plan.json`, the entry is removed automatically, so the backlog reflects only not-yet-planned work.

### Non-goals
- **Automatic end-of-task surfacing machinery** (hooks). The agent already calls out new entries conversationally; no dedicated surfacing mechanism in v1.
- **Per-feature backlogs.** v1 is a single global backlog.
- **A status/workflow engine.** The lifecycle is minimal: an entry exists in the backlog until its work lands in a `plan.json`, at which point it is removed. No multi-state machine.
- **Syncing the backlog to the PM tool** (ClickUp/Jira/etc.). The backlog is a pre-pipeline staging area; PM sync happens after promotion, via the existing `/pm-sync` on the resulting plan.
- **Replacing the PM tool's own backlog.** This is Shield-local triage, not a project-management backlog of record.

## 7. Success metrics
| Metric | Type | Target | Counter |
|---|---|---|---|
| Captured entries that get acted on (work started, or removed once it lands in a plan) vs. left to rot | Outcome | Majority of entries reach a terminal state (promoted/landed in a plan, or explicitly dropped) rather than rotting | Entries pile up un-triaged → backlog becomes a graveyard |
| Entries carrying a feature + epic association at promotion time | Quality | 100% — promotion cannot complete without a feature and epic | Forcing association makes capture so heavy nobody captures |
| Agent feature/epic-suggestion acceptance | Quality | Suggested feature/epic accepted often enough to save manual lookup | Bad suggestions that users routinely override |
| Capture friction | Adoption | Capturing an entry mid-task takes one step and does not interrupt the current task | Capture is so quick the backlog fills with low-signal noise |

## 8. Milestones
| ID | Name | Outcome | Exit criteria | Depends on |
|---|---|---|---|---|
| M1 | Capture + store + view | A global `backlog.json` exists; entries can be added (user + agent) with order, source, and feature + epic association; `/backlog` shows the ordered list with per-entry pipeline status from `manifest.json` | `backlog.json` schema defined; an entry can be captured from a skill or by the user; `/backlog` renders the ordered backlog with feature + epic and a research/prd/plan status read from `manifest.json` | — |
| M2 | Feature + epic association + suggestion | Every entry references a feature and an epic (existing or proposed new); the agent suggests a matching feature/epic | Capture prompts for a feature + epic; agent scans `manifest.json` features and known epics and proposes a match; user can accept, pick another, or create-new | M1 |
| M3 | Promotion + reconciliation | The user picks an entry and starts the Shield step they choose (`/research`, `/prd`, `/plan`, or `/implement`); once the entry's epic's work appears in the feature's `plan.json`, it is removed from the backlog | Reconciliation uses `manifest.json` (find feature, has-plan?) + `plan.json` (epic present?) — no ids stamped; a `prd`-only feature is **not** removed; `/backlog` reconciles on view; the user-chosen step is never overridden | M2 |

## 9. Open questions

- **Feature/epic discovery scope.** `manifest.json` lists features (the reconciliation key). Epics still live inside per-feature `plan.json` files, so confirming an entry's epic means opening the plan the manifest flags as having one. (Leaning: manifest as the index, open only flagged `plan.json` files; revisit if a project-level epic index is ever needed.)
- **Reconciliation matching (resolved):** no ids are stamped. An entry references a **feature** (matched against `manifest.json`) and an **epic** (confirmed in that feature's `plan.json`). The entry is removed only once its epic's work appears in the plan — a `prd`-only feature is **not** removed. Open: does reconciliation run on `/backlog` view, at the end of `/plan`, or both? (Leaning: on `/backlog` view, since the user drives promotion.)
- **Ordering scheme.** Single global rank (explicit integer order, like `orderindex`), priority buckets (P0/P1/P2), or both? (Leaning: explicit order field for v1.)
- **Entry granularity.** The ask says "epics/stories/tasks." Do we model a `kind` field, or treat every entry uniformly as "future work that becomes ≥1 story on promotion"? (Leaning: a `kind` hint, but promotion always yields stories.)
- **Dropped/rejected entries.** Do we need an explicit terminal state for "decided against," or is deleting the entry enough? (Deferred — see Out of scope.)

## 10. Out of scope / Non-goals

- Automatic end-of-task surfacing via hooks (the agent calls it out conversationally; revisit if that proves unreliable).
- Per-feature backlogs and a global↔per-feature promotion path.
- A `rejected`/`dropped` lifecycle state and the audit trail for declined ideas.
- `/pm-sync` of backlog entries to the PM tool before promotion.
- Cross-project / multi-repo backlogs.
- Reordering UX beyond editing the order field (no drag-and-drop, no auto-prioritization).

---

> **This is a lean PRD.** It intentionally omits the following standard sections:
> - Section 8 — User stories & scenarios
> - Section 9 — Functional requirements
> - Section 10 — Non-functional requirements
> - Section 11 — RBAC & permissions matrix
> - Section 12 — Dependencies
> - Section 13 — Risks & mitigations
> - Section 14 — Assumptions
> - Section 15 — Rollout plan (full — lean has its own §8 Milestones)
> - Section 16 — Cost & resource impact
> - Section 17 — GTM & customer-comms
> - Section 18 — Support / CX impact
>
> If scope grows or stakeholders need more detail, run `/prd` again — Shield
> will offer to add specific sections or upgrade to `standard`.
