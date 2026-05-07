# Test input: research-framing-event-sourcing

## Research topic

Event sourcing for financial transaction systems — when to adopt it, what trade-offs apply, and how it interacts with regulatory reconciliation requirements (RBI, GDPR, MiFID II), append-only ledgers, and replay-based recovery.

## Why this topic exercises the broader-coverage discipline

This topic has:

- **Clear definitional/origin voices.** Greg Young coined the modern event-sourcing pattern (CQRS+ES talks, 2010+); Martin Fowler's *Event Sourcing* article (martinfowler.com, 2005, updated 2017) is the most-cited reference; Vaughn Vernon's *Implementing Domain-Driven Design* (2013) carries the practitioner canon. These are X-post / blog / conference-talk style sources that fall *between* the "official sources / industry voices / community experience" stream taxonomy unless framing explicitly carves a place for them.

- **Multiple source-type categories that all matter.** Peer-reviewed (log-structured storage research, Kafka/Aeron papers, Calvin/Spanner ordering), regulatory/standards (RBI 24h rule, MiFID II reconstruction, GDPR right-to-erasure conflict with append-only), vendor docs (EventStoreDB, Axon, Apache Kafka, AWS EventBridge), practitioner experience (failure stories from teams that regretted ES, podcast episodes like Software Engineering Daily on event-driven), conference talks (DDD Europe, KafkaSummit).

- **Fintech weighting.** A research run on event sourcing for *consumer SaaS* would weight practitioner-experience heavy and regulatory low. The same topic for *financial transactions* must invert that — regulatory and standards become load-bearing. The framing output must reflect this topic-specific tuning.

A correct framing for this topic should produce both a Must-Cite Definitional/Origin Voices section (PF7) naming Young/Fowler/Vernon with their canonical artifacts, and a Source-Type Coverage Matrix (PF8) where regulatory/standards is marked required and weighted heavily. A framing that omits either of these fails the broader-coverage discipline that the plugin change is meant to enforce.
