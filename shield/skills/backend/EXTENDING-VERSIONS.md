# Extending Spring/JVM Skills to Other Versions

This doc is the contract for adding support for a Spring Boot major version (or Java major version) that the current skills don't fully cover.

v1 of the backend domain targets:
- **Spring Boot 3.x** — uses `jakarta.*` packages, lambda-style `SecurityFilterChain` DSL, Java 17+ baseline
- **Java 17** — records (since 14), sealed types (since 17), pattern matching, var (since 10)

Codebases on older versions (Spring Boot 2.x with `javax.*` and `WebSecurityConfigurerAdapter`, or Java 11 without sealed types) get useful-but-imperfect review with a per-skill compatibility note.

## When to extend

Add explicit support for a new version when:
- A meaningful share of target codebases run that version (e.g., still on Spring Boot 2.7 for Java-LTS reasons)
- The differences are large enough that "degrade gracefully" produces too many false positives or misses important issues

## Two extension patterns

For each Spring SKILL.md, decide between **broaden** and **sibling**:

### Pattern A — Broaden (recommended when most checks are version-stable)

Edit the existing SKILL.md to cover both versions in its rubric.

1. Add the new version to the frontmatter:
   ```yaml
   spring_boot_versions: ["3.x", "2.x"]
   ```
2. In the Evaluation Points table, mark version-sensitive checks with a note column or an extra column:
   ```
   | W3 | @Valid | (SB3) jakarta.validation, (SB2) javax.validation | High |
   ```
3. Update the Version Compatibility section to remove the "degrades gracefully" caveats — those checks now have explicit version-aware guidance.
4. Update the fixture (or add a parallel fixture if dialect differences are significant).
5. Run RED-GREEN against both versions. Add oracle entries for the new version's variants.

### Pattern B — Sibling skill (recommended when the API surface differs significantly)

Create a new SKILL.md alongside.

1. Decide naming. Two conventions, pick one:
   - **Suffix:** `shield/skills/backend/spring-security-sb2/SKILL.md` (sibling of `spring-security`)
   - **Subfolder:** `shield/skills/backend/spring-security/sb2/SKILL.md` (and rename the existing to `.../sb3/SKILL.md`)
   The suffix convention is less disruptive. The subfolder convention is cleaner once you have 3+ versions. Pick once and stay consistent.

2. Add the new skill name to the agent's Spring sub-detection routing. Update the routing table so the agent loads the right skill for the detected version:
   ```
   Detected SB version | spring-security skill loaded
   ---|---
   3.x                  | backend-spring-security
   2.x                  | backend-spring-security-sb2
   ```

3. Build a parallel fixture if the version's API surface is incompatible (e.g., `shield/examples/spring-boot-api-sb2/`). Reuse the existing fixture if you only need a few file additions.

4. RED-GREEN against the parallel fixture.

5. Update the original skill's Version Compatibility section to point to the sibling.

## Spring-specific guidance

- **`spring-security`** — recommend Pattern B (sibling). The DSL is fundamentally different between SS5 (SB2) and SS6 (SB3); a single rubric makes both bad.
- **`spring-data`, `spring-web`, `spring-test`, `spring-config`** — Pattern A (broaden) usually fits. Most checks are framework-stable; differences are package names and a few specific deprecations.
- **`jvm-language-review`** — version axis is Java, not Spring Boot. Pattern A. Add Java-version columns to the Evaluation Points table that gate language-feature checks (records → Java 14+, sealed → Java 17+).

## Process checklist

When adding a new version:

- [ ] Update frontmatter `spring_boot_versions` (or Java equivalent)
- [ ] Update or add a Version Compatibility section
- [ ] Update agent's version-detection routing (if Pattern B)
- [ ] Add or extend fixture
- [ ] RED test the new version
- [ ] Write or update SKILL.md (or sibling)
- [ ] GREEN test the new version
- [ ] Update CHANGELOG / release notes
- [ ] Bump shield version

## Anti-patterns

- **Don't** add version checks to the agent that test for version inside skill code. The agent does detection once; skills declare their support and emit notes via the agent's contract.
- **Don't** stuff multi-version support into a single SKILL.md when Pattern B applies — readers can't tell which checks apply to their version.
- **Don't** silently apply SB3 checks to SB2 code. Always emit the compat note when the version is outside the skill's declared range.
- **Don't** create a sibling skill "just in case" — broaden first; only split when the rubric becomes confusing.
