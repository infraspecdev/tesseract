---
name: 04-walk-order
skill_under_test: shield:prd-docs
scenario: Verify Terminologies is deferred; §5 walked between Personas and Goals; story-coverage triggers between §6 and §8
---

## Setup
```bash
mkdir -p docs/shield/walk-order-test
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
```

## Prompt
> Author a standard PRD for "walk-order-test" — a simple feature for testing this skill's walk order. Before populating each section, announce the section name. When you defer a section, say "DEFERRED: §N <name>". When you invoke a sub-skill, say "INVOKE: <skill-name>". Output your full transcript of section announcements and sub-skill invocations (do not produce the PRD body itself).

## Success criteria

### Structural
- §1 Header
- DEFERRED: §2 Terminologies
- §3 Problem
- §4.*[Pp]ersona
- §5 Architecture
- §6 Goals
- INVOKE: shield:story-coverage
- §7.*[Mm]etric
- §8.*[Ss]tor
- §9.*[Ff]unctional
- §10.*([Nn]on-functional|NFR)
- §11.*(RBAC|[Pp]ermissions)
- §12.*[Dd]ependencies
- §13.*[Rr]isks
- §14.*[Aa]ssumptions
- INVOKE: shield:milestone-coverage
- §15.*[Rr]ollout
- §16.*[Cc]ost
- §17.*(GTM|[Cc]ustomer)
- §18.*[Ss]upport
- §19.*[Oo]pen
- §20

### Qualitative
- §2 Terminologies announcement appears AFTER §20 announcement (filled last).

## Pass threshold
22 of 22 structural + 1 of 1 qualitative.
