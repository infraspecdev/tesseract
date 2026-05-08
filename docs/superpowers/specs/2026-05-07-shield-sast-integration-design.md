# Shield — SAST Integration Design

**Status:** Draft
**Date:** 2026-05-07
**Marketplace:** Tesseract
**Plugin:** Shield
**Target:** Plan 4 (after Plan 3 ships)

## Context

Plans 1–3 ship a backend domain to shield: 13 skills (7 agnostic + 6 Spring/JVM), the `backend-reviewer` agent, the `/review-backend` command, and SDLC integration into `/plan`, `/plan-review`, `/implement`. Each skill is a markdown rubric an LLM agent applies to source code.

Honest assessment: a meaningful portion of the 65 oracle checks across our skills are pattern-detectable issues that SAST tools handle deterministically, faster, and cheaper than the LLM. Specifically:
- ~40% of checks are pure pattern detection (annotations, imports, calls) — better suited to SAST
- ~30% are pattern + light flow analysis — feasible in either, SAST advantageous
- ~30% are genuine LLM territory (god class detection, YAGNI, deployment-safety reasoning, AC verification)

The skills' value is the LLM-only checks (architecture, semantic understanding, intent inference, pre-implementation reasoning). The pattern-detectable checks duplicate work SAST does better. Plan 4 introduces a **hybrid model**: SAST tools run alongside skills for the deterministic checks; skills focus on the judgment layer.

## Goals

- Add a SAST integration layer to shield that complements (not replaces) skill-based review
- Use an adapter pattern so multiple SAST tools can plug in independently
- Ship two reference adapters that validate the abstraction across genuinely different tools: Semgrep (CLI, JSON output, custom rules) and SonarQube Community (server, REST API / SARIF output)
- Keep SAST opt-in (default off) so existing repos see no behavior change until they enable it
- Reuse shield's existing patterns: `~/.shield/credentials.json` for secrets, `.shield.json` for project config, Python adapter scripts under `shield/adapters/`

## Non-goals

- Replace skills with SAST. Skills' judgment-only checks remain the unique value.
- Cherry-pick rule mappings between shield and SAST. Earlier draft proposed a `recommended-rules.md` mapping doc; honest analysis showed the maintenance cost (drift between doc and adapter code, custom-rule-pack-vs-community-rule confusion, one-direction-only mapping) exceeded the user value (users enable big rule packs, not individual rule IDs).
- Cross-tool finding correlation beyond simple location-based dedup
- Branch analysis on SonarQube (Developer Edition feature; not available in Community)
- Suppression in `.shield.json`. v1 uses tool-native suppression only (`@SuppressWarnings`, `// nosemgrep`). If noise becomes a problem, add `sast.suppress` config in a follow-on.

## Architecture & data flow

```
User runs: /review-backend
       │
       ▼
┌──────────────────────────────────────────────┐
│  backend-reviewer agent                      │
│                                              │
│  1. Stack/Spring/version detection (existing) │
│                                              │
│  2. Configuration lookup (NEW)               │
│     Read .shield.json → sast.adapters list.  │
│     Empty list → SAST inactive.              │
│                                              │
│  3. Parallel dispatch (NEW)                  │
│     ├── SAST adapters (concurrent per tool)  │
│     │     Layered fallback per adapter:      │
│     │       a. Consume existing output       │
│     │          (mtime newer than HEAD commit) │
│     │       b. Invoke tool locally           │
│     │          (only if installed)           │
│     │       c. Best-effort skip + note       │
│     │                                        │
│     ├── Skill review (existing, in parallel) │
│     └── Specialist agents (existing)         │
│                                              │
│  4. Aggregation + dedup (NEW)                │
│     Same finding (file path + ±2 line range  │
│     overlap) → collapse to one entry citing  │
│     all sources.                             │
│                                              │
│  5. Output (extended)                        │
│     Module-grouped sections (existing) +     │
│     "Repo-wide SAST findings" section for    │
│     SAST findings without skill overlap.     │
└──────────────────────────────────────────────┘
```

**Key behaviors:**

- **Opt-in.** No SAST runs unless `sast.adapters` lists adapter names in `.shield.json`. Default empty.
- **Layered fallback per adapter.** Each adapter tries three modes in order: consume existing output → invoke locally → best-effort skip. Stale output (mtime older than HEAD commit) is treated as missing, falling through to invoke.
- **Parallel execution.** SAST adapters and skill review run concurrently. No coupling — each produces normalized findings independently.
- **Source labeling.** Every finding has a `source` field: `skill | semgrep | sonarqube | specialist:<name>`. Merged duplicates show all sources.
- **Best-effort messaging.** When a tool isn't installed/configured, the adapter emits one line in the report header (e.g., *"semgrep adapter — tool not available; SAST coverage best-effort"*) and returns zero findings. The review still completes.

## Adapter framework

### Directory layout

```
shield/adapters/sast/
  ├── README.md              — what's here, contract for adding a new adapter
  ├── finding-schema.md      — normalized finding shape
  ├── severity-mapping.md    — tool-native → normalized severity reference
  ├── GETTING-STARTED.md     — onboarding: install, configure, opt-in
  ├── semgrep/
  │   ├── adapter.md         — invocation contract, configuration, fallback rules
  │   ├── adapter.py         — runtime: invocation + JSON parsing + normalization
  │   ├── rules/             — shield-shipped Semgrep rule packs
  │   │   ├── spring-security.yml
  │   │   ├── spring-data.yml
  │   │   ├── spring-config.yml
  │   │   └── spring-web.yml
  │   └── tests/
  │       ├── fixtures/      — sample `semgrep --json` outputs
  │       └── test_adapter.py
  └── sonarqube/
      ├── adapter.md
      ├── adapter.py         — runtime: SARIF/REST parsing + normalization
      ├── examples/
      │   └── sonar-project.properties
      └── tests/
          ├── fixtures/      — sample SARIF + REST API JSON outputs
          └── test_adapter.py
```

`adapter.md` is the LLM-readable contract; `adapter.py` is the runtime that does the work. Mirrors `shield/adapters/clickup/server/`.

### Adapter contract

**Inputs:**
- `target_path` — path to review (subtree or whole repo)
- `changed_files` — list of files in scope (or `null` for full); SAST always operates on whole repo regardless
- `detected_versions` — `{ spring_boot: "3.2.0", java: "17" }` when relevant
- `config` — adapter's section from `.shield.json` (paths, server URLs, etc.)
- `credentials` — adapter's section from `~/.shield/credentials.json` (loaded by the same logic the clickup adapter uses)

**Behavior (layered fallback, in order):**
1. **Consume existing output.** Look for output at known paths (configurable). If found AND mtime is newer than HEAD commit → parse and return.
2. **Invoke locally.** Tool installed and configured → run it on `target_path`. Parse output.
3. **Best-effort skip.** Tool not available or invocation fails → emit a one-line header note, return zero findings.

**Output:** list of normalized findings + adapter metadata (`source` name, version detected, mode used, runtime in seconds).

### Normalized finding schema

```yaml
source: "semgrep"               # adapter name
rule_id: "java.spring.security.csrf-disabled"  # tool-native rule ID
file: "shield/examples/.../SecurityConfig.java"  # relative to repo root
lines: "27"                     # single line or "27-29" range
severity: "high"                # normalized: high | medium | low
category: "security"            # normalized: security | code-quality | performance | reliability | style
message: "CSRF protection disabled without a stateless justification"
fix_hint: "Either re-enable CSRF or document the stateless rationale"  # optional
```

**Dedup keys:** `file` (exact) + `lines` (overlapping range within ±2). No `mapped_skill` field — earlier draft included one; honest analysis showed location-based dedup is sufficient and avoids the maintenance burden of a skill↔rule mapping.

### Severity normalization

Reference table in `severity-mapping.md`:

| Tool-native | Normalized |
|---|---|
| Semgrep `ERROR` | high |
| Semgrep `WARNING` | medium |
| Semgrep `INFO` | low |
| SonarQube `BLOCKER`, `CRITICAL` | high |
| SonarQube `MAJOR` | medium |
| SonarQube `MINOR`, `INFO` | low |

Each adapter's `adapter.py` does the mapping when emitting findings. Edge cases default to `medium` and the adapter logs the mismatch.

## Configuration model

Reuses the clickup pattern (existing in `shield/adapters/clickup/server/config.py`):

```
~/.shield/credentials.json         (gitignored, secrets only)
{
  "clickup":   { "api_token": "..." },
  "sonarqube": {
    "url": "https://sonar.example.com",
    "token": "...",
    "project_key": "..."
  }
}

.shield.json                       (committed, project marker + non-secret config)
{
  "project": "tesseract",
  "sast": {
    "adapters": ["semgrep", "sonarqube"],
    "semgrep": {
      "config": "p/spring-boot-best-practices"   // optional override; default = shield rule pack
    },
    "sonarqube": {
      "consume_path": "target/sonar/report-task.txt"  // optional override
    }
  }
}
```

**SonarQube credential lookup order:**
1. `~/.shield/credentials.json` → `sonarqube` block
2. Env vars: `SHIELD_SONAR_URL`, `SHIELD_SONAR_TOKEN`, `SHIELD_SONAR_PROJECT_KEY`
3. Any required value still missing → adapter emits "best-effort skip" note

**Semgrep credentials:** none required. Optional Semgrep Cloud token (`SEMGREP_APP_TOKEN`) is supported by the tool natively but not used by shield's adapter.

**Empty `sast.adapters` list = SAST off.** Default for repos that haven't opted in. No surprises.

## Per-adapter behavior

### Semgrep adapter

- **Default mode:** invoke locally (Semgrep is fast — seconds for typical repos)
- **Configuration:** uses shield's custom rule pack at `shield/adapters/sast/semgrep/rules/` by default; user can override with `sast.semgrep.config` (path or Semgrep registry pack ID)
- **Output format:** Semgrep `--json` parsed via stdlib `json` module
- **Severity mapping:** ERROR→high, WARNING→medium, INFO→low
- **Tool detection:** `semgrep --version` exit code; if non-zero or command not found, fall through
- **Custom rule pack scope:** Spring Boot 3.x patterns identified across our skills (`csrf().disable()`, `NoOpPasswordEncoder`, `@Transactional` private, `anyRequest().permitAll()`, missing `@Modifying`, hardcoded secrets in YAML, `@ConfigurationProperties` without prefix, etc.). Each rule's `metadata.shield-area` field self-documents which area it parallels — informational only, not load-bearing.
- **v1 limitation:** custom rules target Spring Boot 3.x patterns. SB2 patterns will not match (e.g., `WebSecurityConfigurerAdapter` chained DSL). Documented in `adapter.md`.

### SonarQube adapter

- **Default mode:** consume-only (don't invoke locally; SonarQube full scans take minutes). User runs SonarQube in their CI; shield reads the output.
- **Output sources** (in order):
  1. `target/sonar/report-task.txt` (Maven default) — contains task URL → fetch SARIF via REST API at `{url}/api/projects/{project_key}/issues`
  2. Custom path from `sast.sonarqube.consume_path`
  3. Direct REST API: `GET {url}/api/issues/search?componentKeys={project_key}` using credentials
- **Stale check:** mtime of `report-task.txt` (or fetched-at timestamp) older than HEAD commit time → re-fetch via REST API, OR best-effort skip if API unreachable
- **Output format:** SARIF (preferred) or REST API JSON; both parsed
- **Severity mapping:** BLOCKER/CRITICAL→high, MAJOR→medium, MINOR/INFO→low
- **Local invoke fallback:** if no consumable output AND `sonar-scanner` is on PATH AND credentials are configured → run `sonar-scanner` locally. Slow; last resort before best-effort skip.

## Output format

The existing report format gets one new section after module-grouped findings:

```
## Backend Review

**Scope:** {N files in M modules}
**Stacks detected:** Java/Kotlin · Spring Boot 3.2.0 · Java 17
**Skills applied:** 13 (7 agnostic + 6 framework)
**SAST adapters:** semgrep (invoked, 12 findings) · sonarqube (consumed, mtime stale → re-fetched, 47 findings)
**Specialists consulted:** security, architecture, agile-coach, operations, dx-engineer, product-manager

### Module: services/api/

| Severity | Source | Skill / Rule | File | Lines | Finding |
|---|---|---|---|---|---|
| High | skill+semgrep | spring-security:SS1 + java.spring.security.noop-encoder | config/SecurityConfig.java | 17-20 | NoOpPasswordEncoder stores plaintext |
| High | skill | code-quality-review:Q1 | service/UserService.java | 9-13 | God class |
| Medium | semgrep | java.spring.config.value-for-typed | config/AppConfig.java | 27 | Use @ConfigurationProperties |
...

### Repo-wide SAST findings (no skill mapping)

| Severity | Source | Rule | File | Lines | Finding |
|---|---|---|---|---|---|
| Medium | sonarqube | java:S1144 | service/LegacyUtil.java | 42 | Unused private method |
...

### Specialist Findings
...

### Summary

- Total findings: 73 (skill: 38, SAST-skill-overlap: 8, SAST-only: 27)
- High: 19; Medium: 41; Low: 13
- Modules with no findings: services/admin/
```

The "SAST-only" line in the summary tells users at a glance how much value SAST added beyond what skills caught.

## Test strategy (hybrid)

**Default suite (always runs in CI, fast):**
- `shield/adapters/sast/<tool>/tests/fixtures/` — real SAST output samples captured once and committed (`semgrep --json` dump, SonarQube SARIF export, REST API JSON response)
- `test_adapter.py` feeds fixtures to `adapter.py` parser; verifies normalization, severity mapping, schema compliance, dedup keys
- No tool install needed for these tests

**Optional integration suite (gated by `pytest -m integration`):**
- CI installs Semgrep via `pip install semgrep`; runs SonarQube in Docker
- Adapters run end-to-end against the spring-boot-api fixture
- Verifies adapter actually catches expected violations (e.g., `csrf().disable()` in `SecurityConfig.java` produces a Semgrep finding via shield's rule pack)
- Slow (minutes); run before release or on demand

**RED-GREEN for shield's custom Semgrep rules:**
Each rule pack file ships paired test fixtures: a "trigger" file (violating pattern) and a "no-trigger" file (similar but correct). `semgrep --test` validates this — same pattern Semgrep itself uses.

## Error handling

| Failure mode | Behavior |
|---|---|
| Tool not installed | Best-effort skip; one-line note in report header |
| Tool installed but fails (non-zero exit) | Best-effort skip; log error message in report |
| Existing output unparseable | Treat as missing; fall through to invoke |
| Existing output stale (mtime older than HEAD commit) | Treat as missing; fall through to invoke |
| Credentials missing for SonarQube | Best-effort skip with note pointing at `~/.shield/credentials.json` |
| `sast.adapters` references unknown adapter name | Skip with warning; continue with known adapters |
| All adapters skip (empty list or all unavailable) | Review proceeds skill-only; report header notes "SAST inactive" |

## v1 deliverable summary

**New files:**
- `shield/adapters/sast/README.md`
- `shield/adapters/sast/finding-schema.md`
- `shield/adapters/sast/severity-mapping.md`
- `shield/adapters/sast/GETTING-STARTED.md`
- `shield/adapters/sast/semgrep/` — `adapter.md`, `adapter.py`, 4 rule pack files, test fixtures, `test_adapter.py`
- `shield/adapters/sast/sonarqube/` — `adapter.md`, `adapter.py`, sample `sonar-project.properties`, test fixtures, `test_adapter.py`

**Modified files:**
- `shield/agents/backend-reviewer.md` — parallel SAST dispatch logic, output format extended with "SAST adapters" header line and "Repo-wide SAST findings" section
- `shield/adapters/clickup/server/config.py` — extend the credentials-loading helper to also recognize `sonarqube` block (or factor into a shared `shield/lib/credentials.py`)
- `.claude-plugin/marketplace.json` — bump shield to next minor version

**Estimated 8–10 tasks** in the implementation plan.

## Out of scope (deferred)

- **`recommended-rules.md` mapping doc.** Considered and rejected — earlier discussion concluded the maintenance burden exceeds the user value.
- **`.shield.json` `sast.suppress` config.** v1 relies on tool-native suppression. Add later if noise becomes a problem.
- **Branch analysis for SonarQube.** Paid feature; Community Edition limitation.
- **Cross-tool finding correlation.** Beyond simple location-based dedup, no semantic correlation across tools.
- **Spring Boot 2.x rule packs.** Custom Semgrep rules target SB3. Following the version-extensibility pattern from Plan 2's `EXTENDING-VERSIONS.md`, SB2 rule packs can be added as `rules/spring-security-sb2.yml` etc. when needed.
- **Kotlin-specific Semgrep rules.** Defer with the Kotlin fixture work (already deferred from Plan 2).
- **Additional adapters.** Plan 5+ candidates: SpotBugs (+ FindSecBugs, spotbugs-spring), gitleaks, CodeQL, Snyk Code, Sonatype.
- **CI workflow generation.** shield does not generate the user's CI config (e.g., GitHub Actions workflows for Semgrep / SonarQube). Users wire those up themselves.
- **Suppression UI / fix application.** SAST findings appear in the report but shield doesn't apply auto-fixes for them in v1.

## Versioning notes

Per `CLAUDE.md`:
- Bump shield in `.claude-plugin/marketplace.json` only — no `version` field added to `shield/.claude-plugin/plugin.json`.
- The exact target version depends on Plan 3's bump. Plan 4 = next minor after Plan 3.
