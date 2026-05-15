---
name: 03-story-types-rewrite
skill_under_test: shield:prd-docs
scenario: A service-rewrite PRD should mark carried-over stories as "existing" and modified ones as "enhancement"
---

## Setup
```bash
mkdir -p docs/shield/inventory-rewrite
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
```

## Prompt
> Author a standard PRD for "inventory-rewrite": migrating a legacy MySQL-backed inventory service to a new event-driven design. The legacy service supports: (a) listing items by warehouse, (b) decrementing stock, (c) restocking, (d) low-stock alerts. The rewrite adds: real-time multi-warehouse aggregation. Behavior (a) is unchanged from the user's perspective; (b)(c) get tighter consistency guarantees; (d) is unchanged; aggregation is brand new.
>
> Walk §8 (Stories). Author at least one story per legacy behavior plus one for aggregation. Assign Types accordingly.

## Success criteria

### Structural
- \*\*Type:\*\* existing
- \*\*Type:\*\* enhancement
- \*\*Type:\*\* new
- \*\*Existing behavior:\*\*

### Qualitative
- Stories for behavior (a) listing and (d) low-stock alerts are typed `existing`.
- Stories for behavior (b) decrement and (c) restock are typed `enhancement` (with the consistency change called out in Existing-behavior).
- The aggregation story is typed `new`.
- No story has `Type: new` AND a non-"N/A" Existing-behavior field.

## Pass threshold
4 of 4 structural + 3 of 4 qualitative.
