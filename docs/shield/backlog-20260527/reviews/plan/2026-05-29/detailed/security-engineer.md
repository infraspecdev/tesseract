# Security Engineer — Detailed Findings

> Back to [summary](../summary.md)

**Persona grade: A−.** Security-mature for its surface (single-actor local tool over a plaintext git-tracked store of developer idea text — no PII/auth/network). Threat model is honest, trust boundaries are clean, and security claims are pinned to executable, falsifiable ACs. The four folded prior-review findings are all present, correctly threat-framed, and sufficient. Lands A− (not A) because the recovery layer (N4) and single-writer claim (N5) rest on ordering/assumption guarantees not yet pinned to tests.

## Folded-finding verification

| Folded finding | Sufficient? |
|---|---|
| Malformed/partial read refused with `BacklogInvalid` (F5) | Yes — "single integrity primitive" (TRD §9), concrete AC |
| Concurrency eval: no corruption AND no lost entry | Yes — correctly distinguishes lost-entry (RMW race) from corruption (crash mid-write) |
| No-stamping eval (F6): plan.json byte-unchanged | Yes — byte-unchanged is the right assertion |
| Epic-name collision across features → ambiguous → stays | Yes — fixture exists (ambiguous-match-stays) |

## Evaluation points (A–F)

| # | Point | Grade |
|---|---|---|
| SE1 | Threat model coverage | A− |
| SE2 | Least-privilege design | A |
| SE3 | Data protection | A |
| SE4 | Secrets management | A |
| SE5 | Network security | N/A |
| SE6 | Access control | N/A |
| SE7 | Compliance | N/A |
| SE8 | Incident response | A− |
| SE9 | Acceptance criteria quality | A |
| SE10 | Edge case & rollback coverage | A− |
| SE11 | Integration test strategy | A |
| SE12 | Regression risk | A |
| SE13 | Environment validation | B+ |
| SE14 | Security validation | A− |

## Findings

| Priority | Point | Recommendation |
|---|---|---|
| P1 | SE10/SE1 (P1-a) | No detection for a violated single-writer assumption (N5). If violated, the outcome is a silent lost update. Add a cheap compare-before-replace: `capture()`/`remove()` carry the schema_version+entry-count (or mtime/hash) read at start and refuse `os.replace()` if the on-disk file changed underneath — converts a silent lost-update into a loud `BacklogInvalid` refusal **without a lockfile**. (Also resolves backend P1-1.) |
| P1 | SE14/SE9 (P1-b) | Write-side validation is asserted ("validate-or-refuse on read/write") but only read-side + crash-mid-write are tested. Add AC+eval: "`capture()` that would produce a schema-invalid document raises `BacklogInvalid` and leaves backlog.json byte-unchanged (no .tmp promoted)." |
| P1 | SE10/SE14 (P1-c) | The recovery-sink ordering (append-before-remove) is stated in prose but not pinned to a test. Strengthen the recovery-rehearsal eval to assert recoverability across a simulated crash at the ordering seam (after append/before remove; after remove/before commit). |
| P2 | SE1/SE8 (P2-a) | `.shield/backlog-removed.log` is a new write surface with no integrity story (no schema, no validate-or-refuse, git-tracked status unspecified). Specify tracked/ignored + read it back through a defined parser in the recovery eval. |
| P2 | SE13 (P2-b) | Dry-run isolation is a doc task, not a guarded invariant; the lazy sweep runs on every view. Make dry-run/fixture mode provably non-destructive (force kill switch off, or disable sweep when a fixture path is supplied) + add to the eval matrix. |
| P2 | SE1 (P2-c) | Migration is doc-only (correct for v1); add a forward note that any future `migrate()` must itself be validate-or-refuse (a half-migrated write is the next corruption vector). |

No P0 findings from security.
