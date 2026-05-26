# Framing brief — Event sourcing for financial transaction systems

Produced by `shield:research-framer` for the `/research` Phase 2 fan-out. Downstream
research streams must honor the PF7 voices and PF8 source-type matrix below;
the synthesis pass (`shield:framing-coverage-honored`, PM11) grades coverage.

## PF1 — Topic

Event sourcing for financial transaction systems — when to adopt, trade-offs,
and interaction with regulatory reconciliation (RBI 24h rule, MiFID II
reconstruction, GDPR right-to-erasure conflict with append-only ledgers).

## PF2 — Stakeholders

- Platform engineering team (owns the ledger)
- Compliance officer (owns regulatory reporting)
- Site reliability (owns replay-based recovery)

## PF3 — Decision being made

Adopt event sourcing for the transaction ledger in 2026, or stay with the
current double-entry SQL model.

## PF4 — Success criteria

Findings synthesis must directly answer: (1) does ES meet RBI/MiFID II/GDPR;
(2) what are the operational costs (snapshotting, replay time); (3) what do
practitioners regret post-adoption.

## PF5 — Out of scope

Frontend/UX changes, microservices migration, vendor procurement.

## PF6 — Risks and dependencies

- Regulator pushback on append-only vs GDPR erasure
- Operational cost of replay at production volume
- Practitioner survival bias in published case studies

## PF7 — Must-cite definitional/origin voices

The synthesis MUST quote each of these voices directly in the body (not just
References) — they define the field and any synthesis that omits them reads
as half-informed.

| Voice | Canonical artifact | Why must-cite |
|---|---|---|
| Greg Young | CQRS+ES talks (2010+), "Event Sourcing" keynote | Coined the modern pattern; defines the vocabulary |
| Martin Fowler | "Event Sourcing" article (martinfowler.com, 2005, updated 2017) | Most-cited reference work; defines the architectural shape |
| Vaughn Vernon | *Implementing Domain-Driven Design* (2013), ch. 8 | Practitioner canon; defines aggregate + event design |

## PF8 — Source-type coverage matrix

| Source type | Required? | Why |
|---|---|---|
| Peer-reviewed (log-structured storage, Calvin/Spanner ordering) | yes | Underpins durability + ordering claims |
| Regulatory/standards (RBI 24h rule, MiFID II Art. 16, GDPR Art. 17) | yes | Decision is fintech-weighted; regulator alignment is load-bearing |
| Vendor docs (EventStoreDB, Axon, Apache Kafka, AWS EventBridge) | yes | Concrete operational guidance the team will live with |
| Practitioner experience (post-mortems, podcast episodes, conference talks) | optional | Useful for regret signal, not load-bearing |
