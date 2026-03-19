# Plan Review Persona Catalog

All agents are dispatched in **plan review mode** — lightweight checks focused on plan quality.

| Agent | Weight | Focus |
|-------|--------|-------|
| `shield:architecture-reviewer` | 1.0 | Service topology, scalability, HA, network design |
| `shield:security-reviewer` | 1.0 | Security posture, threat modeling, access control, testability |
| `shield:dx-engineer-reviewer` | 1.0 | Plan clarity, actionability, software architecture |
| `shield:cost-reviewer` | 0.7 | Cost awareness, right-sizing, environment tiering |
| `shield:agile-coach-reviewer` | 0.7 | Sprint-readiness, story quality, dependencies |
| `shield:operations-reviewer` | 0.7 | Monitoring, failure modes, backup, on-call readiness |
| `shield:product-manager-reviewer` | 0.7 | User impact, scope discipline, prioritization, business value |

## Dynamic Persona Selection

```dot
digraph persona_selection {
    rankdir=TB;
    node [shape=box];

    read [label="Read plan, extract keywords"];
    has_stories [label="Plan has stories?" shape=diamond];
    force_dx_ac [label="Force-include\nDX Engineer + Agile Coach"];
    count_triggers [label="Count trigger keyword\nmatches per agent"];
    enough [label="3+ agents selected?" shape=diamond];
    add_next [label="Add next-closest\nagent by trigger count"];
    announce [label="Announce selection\nto user with reasons"];

    read -> has_stories;
    has_stories -> force_dx_ac [label="yes"];
    has_stories -> count_triggers [label="no"];
    force_dx_ac -> count_triggers;
    count_triggers -> enough;
    enough -> announce [label="yes"];
    enough -> add_next [label="no"];
    add_next -> enough;
}
```

## Selection Rules

- **Always include** DX Engineer + Agile Coach when plan contains stories
- **Include** any agent with 2+ trigger keyword matches
- **Minimum 3** agents — backfill by trigger count if needed
- **Include** product-manager-reviewer when plan contains user-facing features, product decisions, or scope trade-offs (matched via trigger keywords)
- Announce which reviewers were selected and why before dispatching
