# Mermaid authoring

Shared rules for any Shield skill that emits a Mermaid diagram (LLDs, TRDs,
PRDs, architecture diagrams). Diagrams are validated by
`shield/scripts/validate_mermaid.py` against `mermaid@10` (the version
`shield/templates/shell.html` renders with). Following these rules avoids the
failures that validator catches.

## Hard rules (these break parsing)

- **No semicolons inside a `sequenceDiagram`.** Mermaid treats `;` as a
  statement separator, so text after it is re-parsed as a new line — even
  inside quotes or parentheses. Use `—`, or `,` inside `()`/`""`.
- **Never name an actor/participant a reserved word.** Reserved:
  `create`, `destroy`, `box`, `end`, `alt`, `else`, `opt`, `loop`, `par`,
  `and`, `critical`, `rect`, `break`, `note`, `activate`, `deactivate`,
  `participant`, `actor`, `autonumber`, `link`, `links`, `title`. Rename the
  identifier (the `as <alias>` text is free-form and may keep the real name).
- **Balance every block.** Each `alt`/`loop`/`opt`/`par`/`critical`/`rect`/
  `break`/`box` needs a matching `end`.

## Style (keeps diagrams parseable and readable)

- Keep message labels short; put detail in the prose around the diagram.
- Prefer simple identifiers (`A`, `Svc`, `DB`) with `as` aliases for display.
- One journey per diagram; split large flows.
