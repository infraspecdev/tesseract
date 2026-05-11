# RED Baseline — Research Skill Without Phase 1 Enhancement

**Date:** 2026-05-11
**Skill version tested:** pre-Phase C (Phase 1 Q&A + repo-scan not yet active)
**Fixtures used:** small-node-app, minimal-repo

---

## Fixture 1: small-node-app

**Simulated invocation:** `/research "add multi-factor authentication"`

### Behavior without repo-scan.md + qa-topics.md

**Step 1 — Clarify topic:**
The old SKILL.md Step 1 was: "Clarify topic — skip if user provided context."
- Since user provided a topic ("add multi-factor authentication"), this was skipped.
- No repo scan performed. Shield has no information about Node/TS, Postgres, Redis, Google OAuth, Stripe, SOC2, or canary deployment.

**Step 2 — PM framing:**
- PM agent dispatched with only the topic string "add multi-factor authentication."
- PM agent has to make assumptions about the tech stack; it invents generic stakeholders without knowing the actual stack (Node/TypeScript, Postgres) or compliance context (SOC2).
- PM framing output is generic: "B2B SaaS, unknown user segment, unknown system constraints."

**Step 3 — Parallel research agents:**
- 3 agents dispatched with PM framing context (generic).
- All 3 agents search for "MFA implementation" without any stack-specific filtering. Results include Java-based, Python-based, and Node-based libraries indiscriminately.
- Agents do NOT know that passport-google-oauth20 is already present — so they recommend starting auth from scratch rather than extending it.
- Agents do NOT know SOC2 compliance is required — so they omit SOC2-specific MFA requirements.

**Step 4 — Synthesize findings:**
- Synthesis is generic MFA comparison (TOTP vs SMS vs FIDO2), not Node/TypeScript specific.
- No mention of passport strategy for MFA, no mention of existing Redis (useful for OTP session storage), no mention of canary rollout implications.

**Questions the old skill WOULD have asked (if clarify was not skipped):**
- "What decision or question are you trying to answer?"
- "Any constraints or preferences to bias toward?"
(2 questions, both generic — no structure, no depth modes, no skip rules)

**Key gaps identified:**
1. No repo scan → tech context is entirely generic, requiring user to re-explain their stack
2. No structured Q&A → PM framing has no product context (who are users, what is the problem, success criteria)
3. No compliance-awareness → SOC2 requirements missed entirely
4. No skip rules → if user mentions "Node app with passport", the skill still asks about stack anyway
5. No Phase 2 gate → research runs immediately on a poorly scoped topic; no chance to capture product context first
6. Findings are purely external research (findings.md only) — no internal product/tech context transcript

---

## Fixture 2: minimal-repo

**Simulated invocation:** `/research "add multi-factor authentication"`

### Behavior without repo-scan.md + qa-topics.md

**Step 1 — Clarify topic:** Skipped (topic provided).
**Step 2 — PM framing:** Generic, same as above.
**Step 3 — Parallel agents:** Generic MFA research.

**Key difference from small-node-app:**
- For minimal-repo, the old skill's behavior is _identical_ — it can't distinguish between a rich Node app and a bare README project, because it never scans.
- This is the correct behavior for minimal-repo in Phase 1 too (no detections → full Q&A), but the old skill doesn't do any Q&A either.

---

## Summary: What the old skill misses

| Check | Old skill (pre-Phase C) | Expected with Phase C |
|---|---|---|
| Stack auto-detection | No — always asks or assumes | Yes — scans package.json + tsconfig.json |
| Integrations auto-detection | No | Yes — scans package.json deps |
| Compliance awareness | No | Yes — scans CLAUDE.md for SOC2 |
| Deployment context | No | Yes — scans .github/workflows |
| Structured product Q&A | No — only 2 open-ended clarify questions | Yes — 14 topics with skip rules |
| Depth modes | No | Yes — lean / standard / deep |
| Skip rules | No | Yes — repo scan + invocation context + prior transcripts |
| Phase 2 opt-in gate | No — external research runs immediately | Yes — Phase 1 first, Phase 2 offered |
| transcript.md output | No — only findings.md | Yes — always present |

**Verdict: RED confirmed.** The old skill provides no structured context-gathering and no repo awareness. Phase 1 enhancement is clearly additive.
